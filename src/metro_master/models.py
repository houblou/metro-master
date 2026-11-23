"""Structures de données explicites du noyau métrologique."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .validation import (
    require_correlation,
    require_finite,
    require_non_negative,
    require_nonzero_justification,
    require_positive,
    require_text,
)


VALID_OWNERS = {"bench", "reference", "shared", "transfer", "comparison"}


@dataclass(frozen=True, slots=True)
class UncertaintyComponent:
    """Une grandeur d'entrée exprimée sous forme d'incertitude-type.

    ``owner`` force la séparation entre ce qui appartient au banc, à la
    référence, aux effets partagés, à l'étalon de transfert ou au protocole.
    """

    name: str
    standard_uncertainty: float
    sensitivity: float = 1.0
    owner: str = "bench"
    unit: str = ""
    degrees_of_freedom: float | None = None
    distribution: str = "unspecified"
    source: str = ""
    notes: str = ""
    sensitivity_unit: str = "1"

    def __post_init__(self) -> None:
        require_text("component name", self.name)
        require_non_negative(
            f"standard_uncertainty for {self.name}", self.standard_uncertainty
        )
        require_finite(f"sensitivity for {self.name}", self.sensitivity)
        if self.owner not in VALID_OWNERS:
            allowed = ", ".join(sorted(VALID_OWNERS))
            raise ValueError(f"owner must be one of: {allowed}")
        if self.degrees_of_freedom is not None:
            require_positive("degrees_of_freedom", self.degrees_of_freedom)
        require_text(f"unit for {self.name}", self.unit, allow_empty=True)
        require_text(f"distribution for {self.name}", self.distribution)
        require_text(f"source for {self.name}", self.source, allow_empty=True)
        require_text(f"notes for {self.name}", self.notes, allow_empty=True)
        require_text(f"sensitivity_unit for {self.name}", self.sensitivity_unit)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "UncertaintyComponent":
        return cls(**value)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Correlation:
    left: str
    right: str
    coefficient: float
    justification: str = ""

    def __post_init__(self) -> None:
        require_text("correlation left", self.left)
        require_text("correlation right", self.right)
        if self.left == self.right:
            raise ValueError("a correlation requires two distinct component names")
        require_correlation("correlation coefficient", self.coefficient)
        require_nonzero_justification(
            "correlation", self.coefficient, self.justification
        )

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Correlation":
        return cls(**value)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

