from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass

from aenum import Enum, auto


class SymbolType(Enum):
    UNOCCUPIED = auto()
    FUSELAGE = auto()
    EMPTY = auto()
    HUB = auto()
    TUBE = auto()
    ROTOR = auto()
    WING = auto()
    CONNECTOR = auto()


@dataclass(frozen=True)
class Symbol:
    symbol_type = SymbolType.UNOCCUPIED

    @property
    @abstractmethod
    def is_terminal(self):
        pass

    @property
    def is_start(self):
        return False


@dataclass(frozen=True)
class TSymbol(Symbol):
    """Terminal Symbol"""

    @property
    def is_terminal(self):
        return True


@dataclass(frozen=True)
class NTSymbol(Symbol):
    """Non-Terminal Symbol"""

    @property
    def is_terminal(self):
        return False


@dataclass(frozen=True)
class Unoccupied(NTSymbol):
    symbol_type = SymbolType.UNOCCUPIED


@dataclass(frozen=True)
class Fuselage(TSymbol):
    symbol_type = SymbolType.FUSELAGE


@dataclass(frozen=True)
class Rotor(TSymbol):
    symbol_type = SymbolType.ROTOR


@dataclass(frozen=True)
class Tube(TSymbol):
    symbol_type = SymbolType.TUBE


@dataclass(frozen=True)
class Wing(TSymbol):
    symbol_type = SymbolType.WING


@dataclass(frozen=True)
class Connector(TSymbol):
    symbol_type = SymbolType.CONNECTOR


@dataclass(frozen=True)
class Empty(TSymbol):
    symbol_type = SymbolType.EMPTY
