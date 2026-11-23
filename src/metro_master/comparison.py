"""Outils de comparaison avec séparation explicite banc/référence."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt
from statistics import mean, stdev
from typing import Iterable

from .validation import (
    require_correlation,
    require_finite,
    require_non_negative,
    require_nonzero_justification,
    require_text,
    validate_covariance_bound,
)


class IdentifiabilityError(ValueError):
    """Le modèle ne permet pas d'identifier l'incertitude propre au banc."""


def _non_negative(name: str, value: float) -> None:
    require_non_negative(name, value)


def _correlation(value: float) -> None:
    require_correlation("correlation", value)


def difference_standard_uncertainty(
    bench_standard_uncertainty: float,
    reference_standard_uncertainty: float,
    *,
    correlation: float = 0.0,
) -> float:
    _non_negative("bench_standard_uncertainty", bench_standard_uncertainty)
    _non_negative("reference_standard_uncertainty", reference_standard_uncertainty)
    _correlation(correlation)
    covariance = correlation * bench_standard_uncertainty * reference_standard_uncertainty
    variance = (
        bench_standard_uncertainty**2
        + reference_standard_uncertainty**2
        - 2 * covariance
    )
    tolerance = 1e-12 * max(
        1.0, bench_standard_uncertainty**2 + reference_standard_uncertainty**2
    )
    if variance < -tolerance:
        raise ValueError("difference variance is negative")
    return sqrt(max(0.0, variance))


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    bench_value: float
    reference_value: float
    difference: float
    correction_to_apply_to_bench: float
    bench_standard_uncertainty: float
    reference_standard_uncertainty: float
    correlation: float
    correlation_justification: str
    covariance: float
    difference_standard_uncertainty: float
    zeta: float | None
    warning: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def compare_results(
    bench_value: float,
    reference_value: float,
    bench_standard_uncertainty: float,
    reference_standard_uncertainty: float,
    *,
    correlation: float = 0.0,
    correlation_justification: str = "",
) -> ComparisonResult:
    require_finite("bench_value", bench_value)
    require_finite("reference_value", reference_value)
    justification = require_nonzero_justification(
        "correlation", correlation, correlation_justification
    )
    difference = bench_value - reference_value
    u_difference = difference_standard_uncertainty(
        bench_standard_uncertainty,
        reference_standard_uncertainty,
        correlation=correlation,
    )
    covariance = correlation * bench_standard_uncertainty * reference_standard_uncertainty
    zeta = None if u_difference == 0 else difference / u_difference
    return ComparisonResult(
        bench_value=bench_value,
        reference_value=reference_value,
        difference=difference,
        correction_to_apply_to_bench=-difference,
        bench_standard_uncertainty=bench_standard_uncertainty,
        reference_standard_uncertainty=reference_standard_uncertainty,
        correlation=correlation,
        correlation_justification=justification,
        covariance=covariance,
        difference_standard_uncertainty=u_difference,
        zeta=zeta,
        warning=(
            "u(d) describes the comparison difference. It is not, by itself, "
            "the uncertainty of the bench."
        ),
    )


def zeta_score(
    difference: float,
    bench_standard_uncertainty: float,
    reference_standard_uncertainty: float,
    *,
    correlation: float = 0.0,
) -> float:
    require_finite("difference", difference)
    denominator = difference_standard_uncertainty(
        bench_standard_uncertainty,
        reference_standard_uncertainty,
        correlation=correlation,
    )
    if denominator == 0:
        raise ZeroDivisionError("zeta score is undefined for zero difference uncertainty")
    return difference / denominator


def normalized_error(
    difference: float,
    bench_expanded_uncertainty: float,
    reference_expanded_uncertainty: float,
    *,
    correlation: float = 0.0,
) -> float:
    """Return E_n using comparable expanded uncertainties.

    The two expanded uncertainties must refer to compatible coverage conventions.
    Correlation is accepted only when it is justified for those same results.
    """

    require_finite("difference", difference)
    denominator = difference_standard_uncertainty(
        bench_expanded_uncertainty,
        reference_expanded_uncertainty,
        correlation=correlation,
    )
    if denominator == 0:
        raise ZeroDivisionError("normalized error is undefined for a zero denominator")
    return difference / denominator


@dataclass(frozen=True, slots=True)
class PairedStatistics:
    count: int
    mean_bench: float
    mean_reference: float
    mean_difference: float
    correction_to_apply_to_bench: float
    standard_deviation_of_differences: float
    standard_uncertainty_of_mean_difference: float
    warning: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def paired_statistics(
    bench_readings: Iterable[float], reference_readings: Iterable[float]
) -> PairedStatistics:
    bench = list(bench_readings)
    reference = list(reference_readings)
    if len(bench) != len(reference):
        raise ValueError("bench and reference series must have the same length")
    if len(bench) < 2:
        raise ValueError("at least two paired readings are required")
    for index, item in enumerate(bench):
        require_finite(f"bench_readings[{index}]", item)
    for index, item in enumerate(reference):
        require_finite(f"reference_readings[{index}]", item)
    differences = [left - right for left, right in zip(bench, reference, strict=True)]
    standard_deviation = stdev(differences)
    return PairedStatistics(
        count=len(bench),
        mean_bench=mean(bench),
        mean_reference=mean(reference),
        mean_difference=mean(differences),
        correction_to_apply_to_bench=-mean(differences),
        standard_deviation_of_differences=standard_deviation,
        standard_uncertainty_of_mean_difference=standard_deviation / sqrt(len(differences)),
        warning=(
            "The paired dispersion contains all varying effects present in the sequence. "
            "Do not add the same repeatability components again without a decomposition."
        ),
    )


@dataclass(frozen=True, slots=True)
class BenchSeparationResult:
    bench_variance: float
    bench_standard_uncertainty: float
    difference_variance: float
    reference_variance: float
    covariance: float
    identifiability_justification: str
    assumptions: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def separate_bench_uncertainty(
    difference_standard_uncertainty: float,
    reference_standard_uncertainty: float,
    *,
    covariance: float,
    identifiability_confirmed: bool = False,
    identifiability_justification: str = "",
) -> BenchSeparationResult:
    """Solve ``u_b² = u_d² - u_r² + 2 cov(b,r)`` conditionally.

    This inverse operation is deliberately guarded. It is valid only when the
    supplied variance of differences and covariance refer to the same model,
    and every relevant bench-only contribution is represented.
    """

    if identifiability_confirmed is not True:
        raise IdentifiabilityError(
            "bench uncertainty is not identifiable from u(d) and u(reference) alone; "
            "confirm the measurement model, covariance and completeness explicitly"
        )
    require_text("identifiability_justification", identifiability_justification)
    _non_negative("difference_standard_uncertainty", difference_standard_uncertainty)
    _non_negative("reference_standard_uncertainty", reference_standard_uncertainty)
    require_finite("covariance", covariance)
    difference_variance = difference_standard_uncertainty**2
    reference_variance = reference_standard_uncertainty**2
    bench_variance = difference_variance - reference_variance + 2 * covariance
    tolerance = 1e-12 * max(1.0, difference_variance + reference_variance + abs(covariance))
    if bench_variance < -tolerance:
        raise IdentifiabilityError(
            "the assumptions yield a negative bench variance; the model or inputs are inconsistent"
        )
    bench_variance = max(0.0, bench_variance)
    bench_standard_uncertainty = sqrt(bench_variance)
    validate_covariance_bound(
        covariance,
        bench_standard_uncertainty,
        reference_standard_uncertainty,
    )
    return BenchSeparationResult(
        bench_variance=bench_variance,
        bench_standard_uncertainty=bench_standard_uncertainty,
        difference_variance=difference_variance,
        reference_variance=reference_variance,
        covariance=covariance,
        identifiability_justification=identifiability_justification,
        assumptions=(
            "u(d), u(reference) and covariance belong to the same comparison model",
            "all relevant bench-only contributions are represented",
            "no component measured in paired dispersion is double-counted",
            "the result is valid only for the stated domain and conditions",
        ),
    )

