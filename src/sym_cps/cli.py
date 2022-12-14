"""Module that contains the command line application."""
import argparse
import pickle
from copy import deepcopy
from pathlib import Path
from typing import List, Optional

from sym_cps.evaluation import evaluate_design
from sym_cps.examples.library import export_library
from sym_cps.grammar import AbstractGrid
from sym_cps.representation.design.abstract import AbstractDesign
from sym_cps.representation.design.concrete import DConcrete
from sym_cps.representation.design.human import HumanDesign
from sym_cps.representation.tools.optimize import find_components
from sym_cps.scripts import generate_random_instance_id, get_latest_evaluated_design_number, get_random_new_topology
from sym_cps.shared.paths import aws_folder, data_folder, designs_folder
from sym_cps.tools.update_library import export_all_designs, update_dat_files_library


def _parse_design(args: Optional[List[str]] = None) -> DConcrete:
    parser = argparse.ArgumentParser(prog="sym-cps")
    parser.add_argument("--abstract_json", type=str, help="Specify the abstract json to parse")
    parser.add_argument("--grid", type=str, help="Specify the grid dat file")
    opts = parser.parse_args(args=args)
    print(f"args: {opts}")
    if opts.abstract_json is not None:
        file = data_folder / "custom_designs" / opts.abstract_json
        print(f"Parsing file {file}")
        if file.suffix == "":
            file_str = str(file)
            file_str += ".json"
            file = Path(file_str)
        human_topology = HumanDesign.from_json(file)
        return human_topology.to_concrete()
    elif opts.grid is not None:
        file = data_folder / "custom_designs" / opts.grid
        print(f"Parsing file {file}")
        if file.suffix == "":
            file_str = str(file)
            file_str += ".dat"
            file = Path(file_str)
        with open(file, "rb") as pickle_file:
            abstract_grid: AbstractGrid = pickle.load(pickle_file)
            new_design = AbstractDesign(abstract_grid.name)
            new_design.parse_grid(abstract_grid)
            return new_design.to_concrete()

    raise AttributeError


def generate_random(args: Optional[List[str]] = None):

    parser = argparse.ArgumentParser(prog="sym-cps")
    parser.add_argument("--n", type=int, default=1, help="Specify the number of  random designs")
    parser.add_argument("--n_wings_max", type=int, default=-1, help="Specify the max number of wings")
    parser.add_argument("--n_props_max", type=int, default=-1, help="Specify the max number of propellers")
    parser.add_argument("--no_optimization", default=False, action="store_true")
    opts = parser.parse_args(args=args)
    print(f"args: {opts}")

    index = get_latest_evaluated_design_number()

    random_call_id = generate_random_instance_id()
    random_session_seed = str(random_call_id)

    for i in range((index + 1), (index + opts.n + 1)):
        print(f"Random iteration {i}")
        design_tag = f"grammar_{random_call_id}"
        design_index = i

        new_design: AbstractDesign = get_random_new_topology(
            design_tag, design_index, opts.n_wings_max, opts.n_props_max
        )
        new_design.save()
        d_concrete = new_design.to_concrete()
        d_concrete.choose_default_components_for_empty_ones()
        d_concrete.export_all()
        d_concrete.evaluate()

        print(f"Optimizing Components")
        new_d_concrete = deepcopy(d_concrete)
        find_components(new_d_concrete)
        d_concrete.export_all()
        d_concrete.evaluate()


def _evaluate_grid_path(grid_file_path: Path):
    with open(grid_file_path, "rb") as pickle_file:
        abstract_grid: AbstractGrid = pickle.load(pickle_file)
        print(f"Building AbstractDesign")
        new_design = AbstractDesign(abstract_grid.name)
        new_design.parse_grid(abstract_grid)
        new_design.optimize_and_evaluate_script()


def evaluate_random(args: Optional[List[str]] = None):
    parser = argparse.ArgumentParser(prog="sym-cps")
    parser.add_argument("--n", type=int, default=-1, help="Specify the number (ID) of design to evaluate")
    opts = parser.parse_args(args=args)
    print(f"args: {opts}")
    if opts.n == -1:
        print("Evaluating all randomly generated designs in the designs folder")
        """Evaluate all"""
        for path in Path(designs_folder).iterdir():
            if path.is_dir():
                if "__grammar_" in str(path):
                    grid_file = path / "grid.dat"
                    print(f"Parsing file {grid_file}")
                    _evaluate_grid_path(grid_file)
    else:
        for path in Path(designs_folder).iterdir():
            if path.is_dir():
                path_split = str(path).split("__")
                print(path_split)
                if len(path_split) > 1:
                    try:
                        path_split_2 = str(path_split[0]).split("challenge_data/output/designs/")
                        n = int(path_split_2[1])
                        if n == opts.n:
                            grid_file = path / "grid.dat"
                            print(f"Parsing file {grid_file}")
                            _evaluate_grid_path(grid_file)
                    except:
                        continue


def update_all() -> int:
    update_dat_files_library()

    from sym_cps.reverse_engineering.components_analysis import components_analysis
    from sym_cps.reverse_engineering.parameters_analysis import common_parameters_across_all_designs

    print("Updating default parameters")
    common_parameters_across_all_designs()
    print("Updating default components")
    components_analysis()

    export_library()
    export_all_designs()

    return 0


def export_designs() -> int:
    export_all_designs()
    return 0


def load_custom_design(args: Optional[List[str]] = None) -> int:
    dconcrete = _parse_design(args)
    dconcrete.export_all()
    return 0


def evaluate_abstract_design(args: Optional[List[str]] = None) -> int:
    dconcrete = _parse_design(args)
    dconcrete.choose_default_components_for_empty_ones()
    for component in dconcrete.components:
        print(component.library_component.id)
        if component.library_component is None:
            print(f"{component} HAS NONE")
    dconcrete.export_all()
    dconcrete.evaluate()
    return 0


def evaluate_design_swri(args: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="sym-cps")
    parser.add_argument(
        "design_name", type=str, help="Specify the design name to evaluate the existing design_swri_orog.json"
    )
    opts = parser.parse_args(args=args)
    print(f"args: {opts}")
    print(opts.design_name)
    design_json_path = aws_folder / "examples" / opts.design_name / "design_swri_orog.json"
    # output_folder / "designs" / opts.design_name / "design_swri_orog.json"
    ret = evaluate_design(
        design_json_path=design_json_path, metadata={"extra_info": "full evaluation example"}, timeout=800
    )
    print(ret)
    return 0


if __name__ == "__main__":
    # dconcrete = _parse_design(["--abstract_json=grid/test_quad_cargo_test"])
    # dconcrete = _parse_design(["--grid=grid/test_quad_cargo_grid.dat"])
    # dconcrete.export_all()
    # evaluate_abstract_design(["--abstract_json=custom_test_quad_cargo"])
    # _stats_cleanup()
    # import pdb

    # pdb.run('generate_random(["--n=1", "--n_wings_max=0"])')
    generate_random(["--n=1", "--n_wings_max=0"])
    # evaluate_random(["--n=4"])
