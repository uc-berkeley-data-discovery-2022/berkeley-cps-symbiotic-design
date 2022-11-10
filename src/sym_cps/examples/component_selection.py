from sym_cps.optimizers.component_selection.component_selection import ComponentSelectionContract
from sym_cps.representation.tools.parsers.parse import parse_library_and_seed_designs


class Test_Selection:
    def __init__(self):
        self.c_library, self.designs = parse_library_and_seed_designs()
        self.component_selection = ComponentSelectionContract(c_library=self.c_library)

    def test_component_selection(self):
        """Loading Library and Seed Designs"""
        design_concrete, design_topology = self.designs["TestQuad"]
        """Perform the contract-based component selection"""

        """Check initial Component"""
        print("Check initial component")
        self.component_selection.check_selection(design_topology=design_topology, design_concrete=design_concrete)
        """Selection"""
        propeller, motor, battery = self.component_selection.select_hackathon(
            design_topology=design_topology, design_concrete=None, max_iter=10, timeout_millisecond=10000
        )
        """Verify the Selection"""
        print("Check Result")
        self.component_selection.check_selection(
            design_topology=design_topology, motor=motor, battery=battery, propeller=propeller
        )
        return propeller, motor, battery

    def test_general_component_selection(self):
        """Loading Library and Seed Designs"""
        design_concrete, design_topology = self.designs["TestQuad"]
        """Perform the contract-based component selection"""

        """Check initial Component"""
        print("Check initial component")
        self.component_selection.check_selection_general(
            design_topology=design_topology, design_concrete=design_concrete
        )
        """Selection"""
        print("Start Selection")
        component_dict = self.component_selection.select_general(
            design_topology=design_topology, design_concrete=design_concrete, max_iter=10, timeout_millisecond=300000
        )
        """Verify the Selection"""
        print("Check Result")
        self.component_selection.check_selection_general(design_topology=design_topology, component_dict=component_dict)
        return component_dict

    def run_general_evaluation(self, component_dict):
        design_concrete, design_topology = self.designs["TestQuad"]
        self.component_selection.check_selection(design_topology=design_topology, component_dict=component_dict)
        """Set the component for selection"""
        self.component_selection.replace_with_component(component_dict=component_dict)
        design_concrete.name += "_comp_opt"
        design_concrete.evaluate()
        print(design_concrete.evaluation_results)

    def run_evaluation(self, propeller, motor, battery):
        design_concrete, design_topology = self.designs["TestQuad"]
        self.component_selection.check_selection(
            design_topology=design_topology, motor=motor, battery=battery, propeller=propeller
        )
        """Set the component for selection"""
        self.component_selection.replace_with_component(
            design_concrete=design_concrete, propeller=propeller, motor=motor, battery=battery
        )
        design_concrete.name += "_comp_opt"
        design_concrete.evaluate()
        # # call the pipeline for evaluation
        # design_json_path = designs_folder / design_concrete.name / "design_swri.json"
        # ret = evaluate_design(
        #     design_json_path=design_json_path, metadata={"extra_info": "full evaluation example"}, timeout=800
        # )
        print(design_concrete.evaluation_results)

    def check_general_combination(self, component_dict):
        design_concrete, design_topology = self.designs["TestQuad"]
        self.component_selection.check_selection_general(design_topology=design_topology, component_dict=component_dict)

    def check_combination(self, propeller, motor, battery):
        design_concrete, design_topology = self.designs["TestQuad"]
        self.component_selection.check_selection(
            design_topology=design_topology, motor=motor, battery=battery, propeller=propeller
        )


if __name__ == "__main__":
    tester = Test_Selection()
    # propeller, motor, battery = tester.test_component_selection()
    component_dict = tester.test_general_component_selection()
    # propeller = c_library.components["62x6_2_3200_51_1390"]
    # motor = c_library.components["Rex30"]
    # battery = c_library.components["TurnigyGraphene6000mAh3S75C"]

    # propeller = tester.c_library.components["apc_propellers_22x12WE"]
    # motor = tester.c_library.components["U8_Lite_KV150"]
    # battery = tester.c_library.components["TurnigyGraphene6000mAh6S75C"]

    # propeller = tester.c_library.components["apc_propellers_22x12WE"]
    # motor = tester.c_library.components["U8_Lite_KV150"]
    # battery = tester.c_library.components["TurnigyGraphene6000mAh6S75C"]

    # propeller = tester.c_library.components["apc_propellers_8x3_8SF"]
    # motor = tester.c_library.components["KDE5215XF220"]
    # battery = tester.c_library.components["TurnigyGraphene4000mAh4S75C"]

    # TestQuad seed design choice
    # propeller = tester.c_library.components["apc_propellers_7x5E"]
    # motor = tester.c_library.components["kde_direct_KDE2315XF885"]
    # battery = tester.c_library.components["TurnigyGraphene3000mAh6S75C"]

    # propeller = tester.c_library.components["apc_propellers_5_5x2_5"]
    # motor = tester.c_library.components["t_motor_MN22041400KV"]
    # battery = tester.c_library.components["TurnigyGraphene1400mAh4S75C"]

    # propeller = tester.c_library.components["apc_propellers_14x12E"]
    # motor = tester.c_library.components["t_motor_MN22041400KV"]
    # battery = tester.c_library.components["TurnigyGraphene1600mAh4S75C"]

    # propeller = tester.c_library.components["apc_propellers_8_8x8_9"]
    # motor = tester.c_library.components["kde_direct_KDE2814XF_515"]
    # battery = tester.c_library.components["TurnigyGraphene4000mAh6S75C"]

    # This one works well for TestQuad
    # Propeller: apc_propellers_19x10E
    # Motor: kde_direct_KDE3510XF_475
    # Battery: TurnigyGraphene6000mAh3S75C

    # This one works well for TestQuad
    # propeller = tester.c_library.components["apc_propellers_12x4_5MR"]
    # motor = tester.c_library.components["t_motor_MN3110KV780"]
    # battery = tester.c_library.components["TurnigyGraphene6000mAh6S75C"]

    # This one works well for TestQuad
    # propeller = tester.c_library.components["apc_propellers_9x6"]
    # motor = tester.c_library.components["t_motor_MN3510KV700"]
    # battery = tester.c_library.components["TurnigyGraphene5000mAh6S75C"]

    # This one works well for TestQuad
    # Propeller: apc_propellers_9x4
    # Motor: kde_direct_KDE3510XF_715
    # Battery: TurnigyGraphene5000mAh6S75C

    # This one works well for TestQuad
    # propeller = tester.c_library.components["apc_propellers_9x7_5"]
    # motor = tester.c_library.components["t_motor_AT4125KV540"]
    # battery = tester.c_library.components["TurnigyGraphene4000mAh6S75C"]

    # This one works well for TestQuad
    # propeller = tester.c_library.components["apc_propellers_16x4E"]
    # motor = tester.c_library.components["Antigravity_MN5008_KV340"]
    # battery = tester.c_library.components["TurnigyGraphene4000mAh6S75C"]

    # This one works well for TestQuad
    # Propeller: apc_propellers_27x13E
    # Motor: Antigravity_MN8012_KV100
    # Battery: TurnigyGraphene5000mAh6S75C

    # propeller = tester.c_library.components["apc_propellers_9x3N"]
    # motor = tester.c_library.components["t_motor_AT2820KV1250"]
    # battery = tester.c_library.components["TurnigyGraphene6000mAh4S75C"]

    # MotorInst_0: t_motor_AT2820KV1050
    # PropellerInst_0: apc_propellers_10x4_5MR
    # MotorInst_1: t_motor_AT2820KV1050
    # PropellerInst_1: apc_propellers_10x4_5MR
    # MotorInst_2: t_motor_AT2820KV1050
    # PropellerInst_2: apc_propellers_10x4_5MR
    # MotorInst_3: t_motor_AT2820KV1050
    # PropellerInst_3: apc_propellers_10x4_5MR
    # BatteryInst: Tattu25C11000mAh6S1PHV

    # tester.check_combination(propeller=propeller, motor=motor, battery=battery)
    # tester.run_evaluation(propeller=propeller, motor=motor, battery=battery)
    # build_contract_library()
