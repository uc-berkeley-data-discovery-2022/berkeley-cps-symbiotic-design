from sym_cps.shared.paths import prop_table_folder
from sym_cps.representation.library.elements.library_component import LibraryComponent
from enum import Enum, auto

class PerfTableParsingStage(Enum):
    RPM_READING = auto()
    LABEL_READING = auto()
    UNIT_READING = auto()
    TABLE_READING = auto()


class PerfTable(object):
    """Data structure for holding a propTable"""
    """2 dimensioned data - (RPM, V)"""
    def __init__(self, propeller: LibraryComponent | None = None):
        self.rpm_list = []
        self.columns = []
        self.rpm_table = []

        if propeller is not None:
            self.parse_prop_table(propeller=propeller)
    
    def _update_columns(self, columns: list[str]):
        self.columns = columns


    def print_table(self):
        print("RPM list: ")
        print(self.rpm_list)
        for rpm, table in zip(self.rpm_list, self.rpm_table):
            print(f"RPM = {rpm}:")
            for label in self.columns:
                print(f"{label: >8}", end="")
            print("")
            for v_entry in table:
                for entry in v_entry:
                    print(f"{entry: >8}", end="")
                print("")

           


    def parse_prop_table(self, propeller: LibraryComponent):
        file_name = propeller.properties["Performance_File"].value
        file_path = prop_table_folder / file_name

        state = PerfTableParsingStage.RPM_READING
        rpm_table = []
        with open(file_path, "r") as table_file:
            for line in table_file.readlines():
                tokens = line.split()
                if len(tokens) == 0:
                    continue
                #print(tokens)



                if state == PerfTableParsingStage.RPM_READING:
                    if len(tokens) > 2 and tokens[1] == "RPM":
                        rpm = int(tokens[3])
                        self.rpm_list.append(rpm)
                        state = PerfTableParsingStage.LABEL_READING

                elif state == PerfTableParsingStage.LABEL_READING:
                    labels = tokens
                    self.columns = tokens
                    state = PerfTableParsingStage.UNIT_READING
                
                elif state == PerfTableParsingStage.UNIT_READING:
                    state = PerfTableParsingStage.TABLE_READING

                elif state == PerfTableParsingStage.TABLE_READING:
                    if len(tokens) > 2 and tokens[1] == "RPM":
                        rpm = int(tokens[3])
                        self.rpm_list.append(rpm)
                        self.rpm_table.append(rpm_table.copy())
                        rpm_table.clear()
                        state = PerfTableParsingStage.LABEL_READING       
                        continue
                    values = []
                    for token in tokens:
                        try:
                            val = float(token)
                        except:
                            val = -float("nan")
                        values.append(val)
                    rpm_table.append(values)
            # last table
            self.rpm_table.append(rpm_table)
                




    def get_value(self, rpm: float, v: float, label: str):
        # locate the rpm list, return the smaller one
        # using the four values to get the estimation
        try:
            idx = self.columns.index(label)
        except ValueError:
            print("The column label does not exist!")
            return None

        # binary search the rpm
        first = 0
        last = len(self.rpm_list)-1
        while last - first > 1:
            midpoint = (first + last) // 2
            if self.rpm_list[midpoint] > rpm:
                last = midpoint
            elif self.rpm_list[midpoint] < rpm:
                first = midpoint
            else:
                first = midpoint
                last = midpoint + 1

        rpm1 = self.rpm_list[first]
        rpm2 = self.rpm_list[last]
        # binary search the v in both table
        first_v_small = 0
        last_v_small = len(self.rpm_table[first])-1
        while last_v_small - first_v_small > 1:
            midpoint = (first_v_small + last_v_small) // 2
            if self.rpm_table[first][midpoint][0] > v:
                last_v_small = midpoint
            elif self.rpm_table[first][midpoint][0] < v:
                first_v_small = midpoint
            else:
                first_v_small = midpoint
                last_v_small = midpoint + 1     

        val11 = self.rpm_table[first][first_v_small][idx]
        v11 = self.rpm_table[first][first_v_small][0]
        val12 = self.rpm_table[first][last_v_small][idx]
        v12 = self.rpm_table[first][last_v_small][0]

        first_v_large = 0
        last_v_large = len(self.rpm_table[last])-1
        while last_v_large - first_v_large > 1:
            midpoint = (first_v_large + last_v_large) // 2
            if self.rpm_table[last][midpoint][0] > v:
                last_v_large = midpoint
            elif self.rpm_table[last][midpoint][0] < v:
                first_v_large = midpoint
            else:
                first_v_large = midpoint
                last_v_large = midpoint + 1 

        val21 = self.rpm_table[last][first_v_large][idx]
        v21 = self.rpm_table[last][first_v_large][0]
        val22 = self.rpm_table[last][last_v_large][idx]
        v22 = self.rpm_table[last][last_v_large][0]


        #interpolate/extrapolate the value
        v_m1 = ((v12 - v) * val11 + (v - v11) * val12)/(v12 - v11)
        v_m2 = ((v22 - v) * val21 + (v - v21) * val22)/(v22 - v21)
        ret = ((rpm2 - rpm) * v_m1 + (rpm - rpm1) * v_m2)/(rpm2 - rpm1)
        # debug
        # print("rpm: ", rpm1, rpm2)
        # print("v1:", v11, v12)
        # print("v2:", v21, v22)
        # print("val:", val11, val12, val21, val22)
        # print("mid val:", v_m1, v_m2)
        return ret

        #return rpm_list[i]