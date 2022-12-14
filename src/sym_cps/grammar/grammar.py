from __future__ import annotations

import itertools
import json
import random
from dataclasses import dataclass
from pathlib import Path

from aenum import Enum
from matplotlib.figure import Figure

from sym_cps.grammar.symbols import (
    Connector,
    Empty,
    Fuselage,
    Rotor,
    Symbol,
    SymbolType,
    Unoccupied,
    Wing,
    symbols_colors,
)
from sym_cps.shared.paths import grammar_rules_processed_path
from sym_cps.tools.figures import DirectionsGrid


class Direction(Enum):
    ego = 0
    front = 1
    bottom = 2
    left = 3
    right = 4
    top = 5
    rear = 6


@dataclass
class Grammar:
    rules: list[Rule]

    """TODO"""

    @classmethod
    def from_json(cls, rules_json_path: Path) -> Grammar:
        return Grammar.from_dict(json.load(open(rules_json_path)))

    @classmethod
    def from_dict(cls, rules_dict: dict) -> Grammar:
        """ "TODO"""
        rules = []
        """"e.g.."""
        for rule_id, elements in rules_dict.items():
            rules.append(Rule.from_dict(elements))

        return cls(rules=rules)

    def learn_from_isomorphisms(self):
        """ "TODO by Pier"""


@dataclass
class Rule:
    conditions: ConditionSet
    production: Production
    name: str = "rule"

    """TODO"""

    def matches(self, state: LocalState) -> LocalState | None:
        if self.conditions.matches(state):
            return self.production.apply(state)
        return None

    @classmethod
    def from_dict(cls, rule_dict: dict) -> Rule:
        cs = ConditionSet.from_dict(rule_dict["conditions"])
        connection = None
        if "connection" in rule_dict["production"].keys():
            connection = Direction[rule_dict["production"]["connection"]]
        symbol_name = rule_dict["production"]["ego"]

        if symbol_name == "UNOCCUPIED":
            symbol = Unoccupied()
        elif symbol_name == "FUSELAGE":
            symbol = Fuselage()
        elif symbol_name == "EMPTY":
            symbol = Empty()
        elif symbol_name == "ROTOR":
            symbol = Rotor()
        elif symbol_name == "CONNECTOR":
            symbol = Connector()
        elif symbol_name == "WING":
            symbol = Wing()
        else:
            print(f"{symbol_name} not present")
            raise AttributeError

        pr = Production(ego=symbol, connection=connection)

        return Rule(conditions=cs, production=pr)


@dataclass
class ConditionSet:
    front: set[SymbolType]
    bottom: set[SymbolType]
    left: set[SymbolType]
    right: set[SymbolType]
    top: set[SymbolType]
    rear: set[SymbolType]
    ego: SymbolType = SymbolType.UNOCCUPIED

    @classmethod
    def from_dict(cls, conditions):
        all_dirs = {}
        for direction, symbol_types in conditions.items():
            all_dirs[direction] = set()
            for symbol_type in symbol_types:
                all_dirs[direction].add(SymbolType[symbol_type])
            if len(all_dirs[direction]) == 0:
                all_dirs[direction] = {SymbolType.ANY}
        return cls(
            front=all_dirs["front"],
            bottom=all_dirs["bottom"],
            left=all_dirs["left"],
            right=all_dirs["right"],
            top=all_dirs["top"],
            rear=all_dirs["rear"],
        )

    def matches(self, state: LocalState):
        return (
            state.ego.symbol_type in self.ego
            and state.front.symbol_type in self.front
            and state.bottom.symbol_type in self.bottom
            and state.left.symbol_type in self.left
            and state.right.symbol_type in self.right
            and state.top.symbol_type in self.top
            and state.rear.symbol_type in self.rear
        )

    def draw_condition(self):
        return Condition(
            front=random.choice(list(self.front)),
            bottom=random.choice(list(self.bottom)),
            left=random.choice(list(self.left)),
            right=random.choice(list(self.right)),
            top=random.choice(list(self.top)),
            rear=random.choice(list(self.rear)),
        )

    def get_all_conditions(self) -> list[Condition]:
        conditions: list[Condition] = []
        res = itertools.product(
            list(self.front), list(self.bottom), list(self.left), list(self.right), list(self.top), list(self.rear)
        )
        for elem in res:
            print(elem)
        for (f, b, l, ri, t, re) in itertools.product(
            *[list(self.front), list(self.bottom), list(self.left), list(self.right), list(self.top), list(self.rear)]
        ):
            conditions.append(Condition(f, b, l, ri, t, re))
        return conditions


@dataclass
class Condition:
    front: SymbolType
    bottom: SymbolType
    left: SymbolType
    right: SymbolType
    top: SymbolType
    rear: SymbolType
    ego: SymbolType = SymbolType.UNOCCUPIED

    @property
    def plot(self) -> Figure:
        local_grid = DirectionsGrid(
            front=symbols_colors[self.front],
            bottom=symbols_colors[self.bottom],
            left=symbols_colors[self.left],
            right=symbols_colors[self.right],
            top=symbols_colors[self.top],
            rear=symbols_colors[self.rear],
        )
        return local_grid.plot


@dataclass
class SymbolConnection:
    symbol_a: Symbol
    symbol_b: Symbol


@dataclass
class LocalState:
    ego: Symbol
    front: Symbol
    bottom: Symbol
    left: Symbol
    right: Symbol
    top: Symbol
    rear: Symbol


@dataclass
class Production:
    ego: Symbol
    connection: Direction | None

    def apply(self, state: LocalState) -> LocalState:
        state.ego = self.ego
        if self.connection is not None:
            connection = SymbolConnection(self.ego, getattr(state, self.connection.name))
            state.connections.add(connection)
        return state


if __name__ == "__main__":
    grammar = Grammar.from_json(rules_json_path=grammar_rules_processed_path)
    print(grammar)
