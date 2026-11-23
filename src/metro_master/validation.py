"""Invariants scientifiques partagés par toutes les interfaces du noyau."""

from __future__ import annotations

from math import isfinite
from typing import Iterable, Protocol

from .quantities import compatible_units, parse_unit


class ScientificValidationError(ValueError):
    """Une entrée viole un invariant numérique ou métrologique."""


class ComponentWithUnit(Protocol):
    name: str
    unit: str


def require_text(name: str, value: object, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ScientificValidationError(f"{name} must be a string")
    if value != value.strip():
        raise ScientificValidationError(f"{name} must not have surrounding whitespace")
    if not allow_empty and not value:
        raise ScientificValidationError(f"{name} must not be empty")
    return value


def require_finite(name: str, value: float) -> float:
    if isinstance(value, bool):
        raise ScientificValidationError(f"{name} must be finite")
    try:
        finite = isfinite(value)
    except (TypeError, OverflowError) as error:
        raise ScientificValidationError(f"{name} must be a finite number") from error
    if not finite:
        raise ScientificValidationError(f"{name} must be finite")
    return value


def require_non_negative(name: str, value: float) -> float:
    require_finite(name, value)
    if value < 0:
        raise ScientificValidationError(f"{name} must be non-negative")
    return value


def require_positive(name: str, value: float) -> float:
    require_finite(name, value)
    if value <= 0:
        raise ScientificValidationError(f"{name} must be positive")
    return value


def require_correlation(name: str, value: float) -> float:
    require_finite(name, value)
    if not -1 <= value <= 1:
        raise ScientificValidationError(f"{name} must be in [-1, 1]")
    return value


def require_nonzero_justification(
    name: str, value: float, justification: str | None
) -> str:
    text = "" if justification is None else require_text(
        f"{name}_justification", justification, allow_empty=True
    )
    if value != 0 and not text:
        raise ScientificValidationError(
            f"a non-zero {name} requires {name}_justification"
        )
    return text


def validate_compatible_units(components: Iterable[ComponentWithUnit]) -> str:
    """Return the common unit or reject a budget the model cannot dimensionally prove.

    The current first-order model stores scalar sensitivities without sensitivity
    units. Components may use different scales of the same dimension; propagation
    normalizes them to the first declared unit.
    """

    items = list(components)
    declared = []
    for component in items:
        require_text(f"unit for {component.name}", component.unit, allow_empty=True)
        declared.append(component.unit)
    unique = set(declared)
    if "" in unique and len(unique) > 1:
        raise ScientificValidationError(
            "all uncertainty components must declare the common unit or all leave it unspecified"
        )
    for unit in unique:
        parse_unit(unit)
    common = declared[0] if declared else ""
    if any(not compatible_units(common, unit) for unit in unique):
        details = ", ".join(
            f"{component.name}={component.unit!r}" for component in items
        )
        raise ScientificValidationError(
            f"incompatible uncertainty component units: {details}"
        )
    return common


def validate_covariance_bound(
    covariance: float,
    left_standard_uncertainty: float,
    right_standard_uncertainty: float,
) -> None:
    """Enforce the Cauchy-Schwarz covariance bound."""

    require_finite("covariance", covariance)
    require_non_negative("left_standard_uncertainty", left_standard_uncertainty)
    require_non_negative("right_standard_uncertainty", right_standard_uncertainty)
    bound = left_standard_uncertainty * right_standard_uncertainty
    tolerance = 1e-12 * max(1.0, bound, abs(covariance))
    if abs(covariance) > bound + tolerance:
        raise ScientificValidationError(
            "covariance violates the Cauchy-Schwarz bound for the stated uncertainties"
        )
