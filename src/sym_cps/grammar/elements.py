from __future__ import annotations

import abc
import json
from dataclasses import dataclass, field

import numpy as np
from sym_cps.grammar.rules import generate_random_topology, Grid
from sym_cps.shared.paths import grammar_rules_path

rule_dict = json.load(open(grammar_rules_path))


@dataclass
class AbstractComponent(abc.ABC):
    grid_position: tuple[int, int, int]
    base_name: str = ""
    id: str = ""
    connections: set[AbstractConnection] = field(default_factory=set)
    parameters: {} = field(default_factory=dict)

    def add_connection(self, abstract_connection: AbstractConnection):
        self.connections.add(abstract_connection)


@dataclass
class Fuselage(AbstractComponent):
    instance_n: int = 1

    def __post_init__(self):
        self.base_name = "Fuselage_str"
        self.instance_id = f"Fuselage_str_instance_{self.instance_n}"


@dataclass
class Propeller(AbstractComponent):
    instance_n: int = 1

    def __post_init__(self):
        self.base_name = "Propeller_str"
        self.instance_id = f"Propeller_str_instance_{self.instance_n}"


@dataclass
class Wing(AbstractComponent):
    instance_n: int = 1

    def __post_init__(self):
        self.base_name = "Wing"
        self.instance_id = f"Wing_instance_{self.instance_n}"


@dataclass
class Connector(AbstractComponent):
    instance_n: int = 1

    def __post_init__(self):
        self.base_name = "Connector"
        self.instance_id = f"Connector_instance_{self.instance_n}"


@dataclass
class Tube(AbstractComponent):
    instance_n: int = 1

    def __post_init__(self):
        self.base_name = "Tube"
        self.instance_id = f"Tube_instance_{self.instance_n}"


@dataclass
class Hub(AbstractComponent):
    instance_n: int = 1

    def __post_init__(self):
        self.base_name = "Hub"
        self.instance_id = f"Hub_instance_{self.instance_n}"


@dataclass
class AbstractConnection:
    component_a: AbstractComponent
    component_b: AbstractComponent

    @property
    def key(self) -> str:
        a1 = self.component_a.id
        b1 = self.component_b.id
        if (a1) >= (b1):
            return f"{a1}-{b1}"
        return f"{b1}-{a1}"

    def __eq__(self, other: object):
        if not isinstance(other, AbstractConnection):
            return NotImplementedError
        return self.key == other.key

    def __hash__(self):
        return abs(hash(self.key))

    def __post_init__(self):
        self.component_a.add_connection(self)
        self.component_b.add_connection(self)

    @property
    def euclid_distance(self):
        position_a = self.component_a.grid_position
        position_b = self.component_b.grid_position
        point1 = np.array(position_a)
        point2 = np.array(position_b)
        return np.linalg.norm(point1 - point2)

    @property
    def relative_position_from_a_to_b(self) -> tuple[int, int]:
        """returns the steps  (right(pos)/left(neg), top(pos)/bottom(neg))
        from component_a to _component_b"""

        position_a = self.component_a.grid_position
        position_b = self.component_b.grid_position

        # position_b.x - position_a.x
        # position_b.z - position_a.z

        rel_right = position_b[0] - position_a[0]
        rel_top = position_b[2] - position_a[2]

        return rel_right, rel_top

    @property
    def relative_position_from_b_to_a(self) -> tuple[int, int]:
        """returns the steps  (right(pos)/left(neg), top(pos)/bottom(neg))
        from component_b to _component_a"""

        (rel_right, rel_top) = self.relative_position_from_a_to_b

        return -rel_right, -rel_top

