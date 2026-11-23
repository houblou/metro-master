"""Grandeurs et conversions déterministes du noyau minimal.

Le module couvre les unités courantes du laboratoire sans dépendance externe.
Les unités inconnues, logarithmiques ou contextuelles sont refusées. L'adaptateur
Pint optionnel étend les conversions sans modifier ces invariants.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
import importlib
import re
from typing import Any


FACTOR_PATTERN = re.compile(
    r"^(?P<name>[A-Za-zµμ°%]+)(?:\^(?P<power>-?\d+))?$"
)


@dataclass(frozen=True, slots=True)
class UnitSpec:
    symbol: str
    dimensions: tuple[tuple[str, int], ...]
    scale: float
    offset: float = 0.0


class DependencyUnavailable(RuntimeError):
    """Une extension optionnelle demandée n'est pas installée."""


def _dims(**values: int) -> tuple[tuple[str, int], ...]:
    return tuple(sorted((key, value) for key, value in values.items() if value))


UNITS: dict[str, UnitSpec] = {
    "1": UnitSpec("1", (), 1.0),
    "%": UnitSpec("%", (), 0.01),
    "m": UnitSpec("m", _dims(L=1), 1.0),
    "mm": UnitSpec("mm", _dims(L=1), 1e-3),
    "µm": UnitSpec("µm", _dims(L=1), 1e-6),
    "um": UnitSpec("um", _dims(L=1), 1e-6),
    "nm": UnitSpec("nm", _dims(L=1), 1e-9),
    "kg": UnitSpec("kg", _dims(M=1), 1.0),
    "g": UnitSpec("g", _dims(M=1), 1e-3),
    "mg": UnitSpec("mg", _dims(M=1), 1e-6),
    "s": UnitSpec("s", _dims(T=1), 1.0),
    "ms": UnitSpec("ms", _dims(T=1), 1e-3),
    "min": UnitSpec("min", _dims(T=1), 60.0),
    "h": UnitSpec("h", _dims(T=1), 3600.0),
    "K": UnitSpec("K", _dims(Theta=1), 1.0),
    "°C": UnitSpec("°C", _dims(Theta=1), 1.0, 273.15),
    "degC": UnitSpec("degC", _dims(Theta=1), 1.0, 273.15),
    "A": UnitSpec("A", _dims(I=1), 1.0),
    "mA": UnitSpec("mA", _dims(I=1), 1e-3),
    "V": UnitSpec("V", _dims(M=1, L=2, T=-3, I=-1), 1.0),
    "mV": UnitSpec("mV", _dims(M=1, L=2, T=-3, I=-1), 1e-3),
    "N": UnitSpec("N", _dims(M=1, L=1, T=-2), 1.0),
    "Pa": UnitSpec("Pa", _dims(M=1, L=-1, T=-2), 1.0),
    "hPa": UnitSpec("hPa", _dims(M=1, L=-1, T=-2), 1e2),
    "kPa": UnitSpec("kPa", _dims(M=1, L=-1, T=-2), 1e3),
    "MPa": UnitSpec("MPa", _dims(M=1, L=-1, T=-2), 1e6),
    "bar": UnitSpec("bar", _dims(M=1, L=-1, T=-2), 1e5),
    "Hz": UnitSpec("Hz", _dims(T=-1), 1.0),
    "L": UnitSpec("L", _dims(L=3), 1e-3),
    "mL": UnitSpec("mL", _dims(L=3), 1e-6),
}


def _combine(
    left: dict[str, int], right: tuple[tuple[str, int], ...], multiplier: int
) -> dict[str, int]:
    result = dict(left)
    for dimension, power in right:
        result[dimension] = result.get(dimension, 0) + multiplier * power
        if result[dimension] == 0:
            del result[dimension]
    return result


def parse_unit(unit: str) -> UnitSpec:
    if not isinstance(unit, str) or unit != unit.strip():
        raise ValueError("unit must be a string without surrounding whitespace")
    if unit == "":
        return UnitSpec("", (), 1.0)
    if unit in UNITS:
        return UNITS[unit]
    text = unit.replace(" ", "")
    parts = re.split(r"([*/])", text)
    if not parts or any(part == "" for part in parts):
        raise ValueError(f"invalid unit expression: {unit!r}")
    dimensions: dict[str, int] = {}
    scale = 1.0
    sign = 1
    factor_expected = True
    for part in parts:
        if factor_expected:
            match = FACTOR_PATTERN.fullmatch(part)
            if match is None:
                raise ValueError(f"unknown or invalid unit factor: {part!r}")
            name = match.group("name").replace("μ", "µ")
            specification = UNITS.get(name)
            if specification is None:
                raise ValueError(f"unknown unit: {name!r}")
            if specification.offset:
                raise ValueError("affine temperature units cannot appear in compounds")
            power = int(match.group("power") or "1") * sign
            if abs(power) > 16:
                raise ValueError("unit exponent exceeds the supported range")
            dimensions = _combine(dimensions, specification.dimensions, power)
            scale *= specification.scale**power
        else:
            if part not in {"*", "/"}:
                raise ValueError(f"invalid unit operator: {part!r}")
            sign = 1 if part == "*" else -1
        factor_expected = not factor_expected
    if factor_expected:
        raise ValueError(f"unit expression ends with an operator: {unit!r}")
    return UnitSpec(unit, tuple(sorted(dimensions.items())), scale)


def compatible_units(left: str, right: str) -> bool:
    return parse_unit(left).dimensions == parse_unit(right).dimensions


def multiply_unit_specs(left: UnitSpec, right: UnitSpec) -> UnitSpec:
    dimensions = _combine(dict(left.dimensions), right.dimensions, 1)
    symbol = right.symbol
    if not right.dimensions and right.scale == 1.0:
        symbol = left.symbol
    elif not left.dimensions and left.scale == 1.0:
        symbol = right.symbol
    else:
        symbol = f"{left.symbol}*{right.symbol}"
    return UnitSpec(
        symbol,
        tuple(sorted(dimensions.items())),
        left.scale * right.scale,
    )


def contribution_unit(input_unit: str, sensitivity_unit: str) -> UnitSpec:
    """Unité de ``c_i u(x_i)`` ; les décalages ne s'appliquent pas aux écarts."""

    return multiply_unit_specs(parse_unit(input_unit), parse_unit(sensitivity_unit))


def convert_between_specs(value: float, source: UnitSpec, target: UnitSpec) -> float:
    if not isfinite(value):
        raise ValueError("quantity contribution must be finite")
    if source.dimensions != target.dimensions:
        raise ValueError(
            f"incompatible contribution units: {source.symbol!r} and {target.symbol!r}"
        )
    return float(value) * source.scale / target.scale


def convert_value(
    value: float,
    from_unit: str,
    to_unit: str,
    *,
    difference: bool = False,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ValueError("quantity value must be finite")
    source = parse_unit(from_unit)
    target = parse_unit(to_unit)
    if source.dimensions != target.dimensions:
        raise ValueError(f"incompatible units: {from_unit!r} and {to_unit!r}")
    if difference:
        return float(value) * source.scale / target.scale
    si_value = float(value) * source.scale + source.offset
    return (si_value - target.offset) / target.scale


def convert_standard_uncertainty(value: float, from_unit: str, to_unit: str) -> float:
    return convert_value(value, from_unit, to_unit, difference=True)


class PintQuantityAdapter:
    """Adaptateur optionnel explicite ; aucun repli silencieux n'est autorisé."""

    def __init__(self) -> None:
        try:
            pint = importlib.import_module("pint")
        except ImportError as error:
            raise DependencyUnavailable(
                "Pint is not installed; install the 'units' extra to use this adapter"
            ) from error
        self._registry: Any = pint.UnitRegistry()

    def convert_value(
        self,
        value: float,
        from_unit: str,
        to_unit: str,
        *,
        difference: bool = False,
    ) -> float:
        if difference:
            source_delta = {
                "°C": "delta_degC",
                "degC": "delta_degC",
                "K": "kelvin",
            }.get(from_unit, from_unit)
            target_delta = {
                "°C": "delta_degC",
                "degC": "delta_degC",
                "K": "kelvin",
            }.get(to_unit, to_unit)
            quantity = self._registry.Quantity(value, source_delta)
            return float(quantity.to(target_delta).magnitude)
        return float(self._registry.Quantity(value, from_unit).to(to_unit).magnitude)
