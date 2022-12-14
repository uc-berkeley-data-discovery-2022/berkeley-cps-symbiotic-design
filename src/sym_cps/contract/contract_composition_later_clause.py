import math

from sym_cps.contract.tool.contract_tool import ContractManager, ContractTemplate
from sym_cps.representation.library.elements.library_component import LibraryComponent


class Hackathon2Contract(object):
    def __init__(self, table_dict, c_library):
        self._table_dict = table_dict
        self._c_library = c_library
        self._manager = None

    def check_selection(
        self,
        num_battery,
        num_motor,
        battery: LibraryComponent,
        motors: list[LibraryComponent],
        propellers: list[LibraryComponent],
        body_weight=0,
        motor_ratio: list[float] | None = None,
    ):
        self.compose(
            num_battery=num_battery,
            num_motor=num_motor,
            motors=[[motor] for motor in motors],
            propellers=[[prop] for prop in propellers],
            batteries=[battery],
            motor_ratio=motor_ratio,
            body_weight=body_weight,
            better_selection_encoding=True,
            obj_lower_bound=0,
        )
        self._manager.solve()
        objective = self._manager.calculate_objective()
        print(f"Check Completed (objective: {objective})")
        return objective

    def optimize(self, max_iter=0, timeout_millisecond=100000):
        self._manager.solve_optimize(max_iter=max_iter, timeout_millisecond=timeout_millisecond)
        selection_result = self._manager.get_component_selection()
        if selection_result is None:
            return None
        component_dict = self._collect_result(selection_result=selection_result)
        return component_dict

    def _collect_result(self, selection_result):
        component_dict = {
            "Motor": {"lib": [None] * self._num_motor},
            "Propeller": {"lib": [None] * self._num_motor},
            "Battery": {"lib": [None]},
        }
        for inst, cand in selection_result.items():
            # print(inst.instance_name, inst.template_name, inst.index)
            if inst.template_name in component_dict:
                # print(len(component_dict[inst.template_name]["lib"]))
                component_dict[inst.template_name]["lib"][inst.index] = cand

        if any(cand is None for cand in component_dict["Propeller"]["lib"]):
            print("Error: Some Component is not assigned")
        if any(cand is None for cand in component_dict["Motor"]["lib"]):
            print("Error: Some Component is not assigned")
        if any(cand is None for cand in component_dict["Battery"]["lib"]):
            print("Error: Some Component is not assigned")

        return component_dict

    def compose(
        self,
        num_battery,
        num_motor,
        better_selection_encoding=True,
        batteries: list[LibraryComponent] = None,
        motors: list[list[LibraryComponent]] = None,
        propellers: list[list[LibraryComponent]] = None,
        body_weight=0,
        obj_lower_bound=None,
        motor_ratio: list[float] | None = None,
    ):
        self._num_motor = num_motor
        self._num_battery = num_battery

        if propellers is None:
            propellers = [list(self._c_library.components_in_type["Propeller"])] * num_motor
            # propellers = [[self._c_library.components["apc_propellers_6x4E"],
            #                self._c_library.components["apc_propellers_15x6E"],
            #                self._c_library.components["apc_propellers_26x15E"]] ] * num_motor
        if motors is None:
            motors = [list(self._c_library.components_in_type["Motor"])] * num_motor
            # motors = [[ self._c_library.components["t_motor_AT2312KV1400"],
            #             self._c_library.components["t_motor_AntigravityMN4006KV380"],
            #             self._c_library.components["t_motor_AntigravityMN1005V2KV90"]
            #             ] ] * num_motor
        if batteries is None:
            batteries = list(self._c_library.components_in_type["Battery"])
            # batteries = [  self._c_library.components["TurnigyGraphene1000mAh2S75C"],
            #                 self._c_library.components["TurnigyGraphene1400mAh4S75C"],
            #                 self._c_library.components["TurnigyGraphene3000mAh6S75C"]
            #                 ]
        if motor_ratio is None:
            motor_ratio = [1] * self._num_motor
        if len(motor_ratio) != self._num_motor:
            print("The ratio list does not match the number of motors!")

        self.set_contract()
        self.set_system(motor_ratio=motor_ratio)

        motor_insts = []
        prop_insts = []
        self._manager = ContractManager(self.hackathon_property_interface_fn)
        for i in range(self._num_motor):
            motor_inst = self._contracts["Motor"].instantiate(f"MotorInst_{i}")
            prop_inst = self._contracts["Propeller"].instantiate(f"PropellerInst_{i}")
            motor_insts.append(motor_inst)
            prop_insts.append(prop_inst)
            self._manager.add_instance(motor_inst)
            self._manager.add_instance(prop_inst)
            self._manager.set_selection(inst=prop_inst, candidate_list=propellers[i])
            self._manager.set_selection(inst=motor_inst, candidate_list=motors[i])
        batt_inst = self._contracts["Battery"].instantiate(f"BatteryInst")
        batt_contr_inst = self._contracts["BatteryController"].instantiate(f"BatteryControllerInst")
        system_inst = self._contracts["System"].instantiate(f"System")
        self._manager.add_instance(batt_inst)
        self._manager.set_selection(inst=batt_inst, candidate_list=batteries)
        self._manager.add_instance(batt_contr_inst)
        self._manager.set_selection(inst=batt_contr_inst, candidate_list=None)
        self._manager.add_instance(system_inst)
        self._manager.set_selection(inst=system_inst, candidate_list=None)
        # make connection
        # connect propeller to motor
        propeller_motor_connection = [
            ("torque_prop", "torque_motor"),
            ("omega_prop", "omega_motor"),
            ("shaft_motor", "shaft_motor"),
        ]

        for i in range(self._num_motor):
            self._manager.compose(prop_insts[i], motor_insts[i], propeller_motor_connection)
        # connect motor to batt_contr
        for i in range(self._num_motor):
            motor_batt_contr_connection = [("I_motor", f"I_motor_{i}"), ("V_motor", f"V_motor_{i}")]
            self._manager.compose(motor_insts[i], batt_contr_inst, motor_batt_contr_connection)
        # connect battery to batt_contr
        batt_contr_connection = [("I_batt", "I_battery"), ("V_battery", "V_battery")]
        self._manager.compose(batt_inst, batt_contr_inst, batt_contr_connection)

        for i in range(self._num_motor):
            # connect propeller to system
            system_prop_connection = [(f"W_prop_{i}", f"W_prop"), (f"thrust_prop_{i}", f"thrust"), ("rho", "rho")]
            self._manager.compose(system_inst, prop_insts[i], system_prop_connection)
            # connect motor to system
            system_motor_connection = [(f"W_motor_{i}", f"W_motor")]
            self._manager.compose(system_inst, motor_insts[i], system_motor_connection)

        system_battery_connection = [("W_batt", "W_batt"), ("I_battery", "I_batt"), ("batt_capacity", "capacity")]
        self._manager.compose(system_inst, batt_inst, system_battery_connection)
        # set objective
        objective_expr = system_inst.get_var("thrust_sum") - system_inst.get_var("weight_sum")
        objective_val = obj_lower_bound

        def objective_fn():
            thrust_sum = self._manager.get_metric_inst(system_inst, "thrust_sum")
            weight_sum = self._manager.get_metric_inst(system_inst, "weight_sum")
            return thrust_sum - weight_sum

        self._manager.set_objective(expr=objective_expr, value=objective_val, evaluate_fn=objective_fn)

    def set_system(self, motor_ratio, body_weight=0):
        system_port_name_list = (
            ["rho", "thrust_sum", "weight_sum", "I_battery", "batt_capacity"]
            + [f"W_motor_{i}" for i in range(self._num_motor)]
            + [f"W_prop_{i}" for i in range(self._num_motor)]
            + [f"W_batt"]
            + [f"thrust_prop_{i}" for i in range(self._num_motor)]
        )
        system_property_name_list = []

        def system_assumption(vs, props):
            return [vs["I_battery"] == vs["batt_capacity"] * 3600 / 400]

        def system_guarantee(vs, props):
            thrust_sum = sum([vs[f"thrust_prop_{i}"] for i in range(self._num_motor)])
            weight_sum = (
                vs["W_batt"]
                + body_weight
                + sum([vs[f"W_prop_{i}"] for i in range(self._num_motor)])
                + sum([vs[f"W_motor_{i}"] for i in range(self._num_motor)])
            ) * 9.81
            ret_clauses = (
                [
                    vs[f"thrust_prop_{i}"] * motor_ratio[i] == vs[f"thrust_prop_{i+1}"] * motor_ratio[i + 1]
                    for i in range(self._num_motor - 1)
                ]
                + [vs["thrust_sum"] >= vs["weight_sum"]]
                + [vs["thrust_sum"] == thrust_sum]
                + [vs["weight_sum"] == weight_sum]
                + [vs["rho"] == 1.225]
            )

            return ret_clauses

        system_contract = ContractTemplate(
            name="System",
            port_name_list=system_port_name_list,
            property_name_list=system_property_name_list,
            guarantee=system_guarantee,
            assumption=system_assumption,
        )
        self._contracts["System"] = system_contract

    def set_contract(self):
        self._contracts = {}

        propeller_port_name_list = ["rho", "omega_prop", "torque_prop", "thrust", "shaft_motor"]
        # propeller_property_name_list = ["C_p", "C_t", "diameter", "shaft_prop", "W_prop"]
        propeller_property_name_list = ["W_prop"]

        def propeller_assumption(vs, props):
            return [props["shaft_prop"] >= vs["shaft_motor"], props["C_p"] >= 0]

        def propeller_guarantee(vs, props):
            return [
                vs["torque_prop"]
                == props["C_p"] * vs["rho"] * vs["omega_prop"] ** 2 * props["diameter"] ** 5 / (2 * 3.14159265) ** 3,
                vs["thrust"]
                == (props["C_t"] * vs["rho"] * vs["omega_prop"] ** 2 * props["diameter"] ** 4 / (2 * 3.14159265) ** 2),
                vs["omega_prop"] >= 0,
            ]

        propeller_contract = ContractTemplate(
            name="Propeller",
            port_name_list=propeller_port_name_list,
            property_name_list=propeller_property_name_list,
            guarantee=propeller_guarantee,
            assumption=propeller_assumption,
        )
        self._contracts["Propeller"] = propeller_contract

        motor_port_name_list = ["torque_motor", "omega_motor", "I_motor", "V_motor"]
        # motor_property_name_list = ["I_max_motor", "P_max_motor", "K_t", "K_v", "W_motor", "R_w", "I_idle", "shaft_motor"]
        motor_property_name_list = ["W_motor", "shaft_motor"]

        def motor_assumption(vs, props):
            return [vs["V_motor"] * vs["I_motor"] < props["P_max_motor"], vs["I_motor"] < props["I_max_motor"]]

        def motor_guarantee(vs, props):
            return [
                vs["I_motor"] * props["R_w"] == vs["V_motor"] - vs["omega_motor"] / props["K_v"],
                vs["torque_motor"]
                == props["K_t"]
                / props["R_w"]
                * (vs["V_motor"] - props["R_w"] * props["I_idle"] - vs["omega_motor"] / props["K_v"]),
            ]

        motor_contract = ContractTemplate(
            name="Motor",
            port_name_list=motor_port_name_list,
            property_name_list=motor_property_name_list,
            guarantee=motor_guarantee,
            assumption=motor_assumption,
        )
        self._contracts["Motor"] = motor_contract

        battery_port_name_list = ["I_batt"]
        # battery_property_name_list = ["capacity", "W_batt", "I_max", "V_battery"]
        battery_property_name_list = ["capacity", "W_batt", "V_battery"]

        def battery_assumption(vs, props):
            return [vs["I_batt"] < props["I_max"]]

        def battery_guarantee(vs, props):
            return []

        battery_contract = ContractTemplate(
            name="Battery",
            port_name_list=battery_port_name_list,
            property_name_list=battery_property_name_list,
            guarantee=battery_guarantee,
            assumption=battery_assumption,
        )

        self._contracts["Battery"] = battery_contract

        # NOTE: Old code has incorrect property name list
        battery_controller_port_name_list = (
            ["V_battery", "I_battery"]
            + [f"I_motor_{i}" for i in range(self._num_motor)]
            + [f"V_motor_{i}" for i in range(self._num_motor)]
        )
        battery_controller_property_name_list = []

        def battery_controller_assumption(vs, props):
            return [vs[f"V_motor_{i}"] <= vs["V_battery"] for i in range(self._num_motor)]

        def battery_controller_guarantee(vs, props):
            i_sum = sum([vs[f"I_motor_{i}"] for i in range(self._num_motor)])
            return [i_sum == vs["I_battery"] * 0.95]

        battery_controller_contract = ContractTemplate(
            name="BatteryController",
            port_name_list=battery_controller_port_name_list,
            property_name_list=battery_controller_property_name_list,
            guarantee=battery_controller_guarantee,
            assumption=battery_controller_assumption,
        )

        self._contracts["BatteryController"] = battery_controller_contract

        # system contract

    def hackathon_property_interface_fn(self, component: LibraryComponent):
        if component.comp_type.id == "Propeller":
            return self.hackthon_get_propeller_property(propeller=component, table_dict=self._table_dict)
        elif component.comp_type.id == "Battery":
            return self.hackthon_get_battery_property(battery=component, num_battery=self._num_battery)
        elif component.comp_type.id == "Motor":
            return self.hackthon_get_motor_property(motor=component)
        elif component.comp_type.id == "BatteryController":
            return {}

    @staticmethod
    def hackthon_get_propeller_property(propeller, table_dict):
        # ports get value

        diameter: float = propeller.properties["DIAMETER"].value / 1000
        shaft_prop: float = propeller.properties["SHAFT_DIAMETER"].value
        # print(table.get_value(rpm = 13000, v = 90, label="Cp"))
        table = table_dict[propeller]
        C_p: float = table.get_value(rpm=10000, v=0, label="Cp")  # 0.0659
        C_t: float = table.get_value(rpm=10000, v=0, label="Ct")  # 0.1319

        W_prop = propeller.properties["WEIGHT"].value
        return {
            "C_p": C_p,
            "C_t": C_t,
            "W_prop": W_prop,
            "diameter": diameter,
            "shaft_prop": shaft_prop,
            "name": propeller.id,
        }

    @staticmethod
    def hackthon_get_motor_property(motor):
        R_w: float = motor.properties["INTERNAL_RESISTANCE"].value / 1000  # Ohm
        K_t: float = motor.properties["KT"].value
        K_v: float = motor.properties["KV"].value * (2 * math.pi) / 60  # rpm/V to rad/(V-sec)
        I_idle: float = motor.properties["IO_IDLE_CURRENT_10V"].value
        W_motor = motor.properties["WEIGHT"].value
        I_max_motor = motor.properties["MAX_CURRENT"].value
        P_max_motor = motor.properties["MAX_POWER"].value
        shaft__motor: float = motor.properties["SHAFT_DIAMETER"].value
        return {
            "R_w": R_w,
            "K_t": K_t,
            "K_v": K_v,
            "I_idle": I_idle,
            "W_motor": W_motor,
            "I_max_motor": I_max_motor,
            "P_max_motor": P_max_motor,
            "shaft_motor": shaft__motor,
            "name": motor.id,
        }

    @staticmethod
    def hackthon_get_battery_property(battery, num_battery):
        capacity: float = battery.properties["CAPACITY"].value * num_battery / 1000  # mAh -> Ah
        W_batt: float = battery.properties["WEIGHT"].value * num_battery
        V_battery: float = battery.properties["VOLTAGE"].value
        I_max: float = (battery.properties["CONT_DISCHARGE_RATE"].value) * capacity  # convert to mA
        return {"capacity": capacity, "W_batt": W_batt, "V_battery": V_battery, "I_max": I_max, "name": battery.id}
