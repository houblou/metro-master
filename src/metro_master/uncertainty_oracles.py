"""Vérifications optionnelles avec des bibliothèques reconnues et non embarquées."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib
from importlib import metadata
from math import inf, isclose

from .uncertainty_study import UncertaintyStudyResult


@dataclass(frozen=True, slots=True)
class OracleResult:
    oracle: str
    available: bool
    status: str
    version: str | None
    combined_standard_uncertainty: float | None
    absolute_difference: float | None
    details: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _version(distribution: str) -> str | None:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None


def _correlation_lookup(study: UncertaintyStudyResult) -> dict[tuple[str, str], float]:
    values: dict[tuple[str, str], float] = {}
    for item in study.correlations:
        values[tuple(sorted((item.left, item.right)))] = item.coefficient
    return values


def _result(
    name: str,
    version: str | None,
    value: float,
    expected: float,
    details: str,
) -> OracleResult:
    difference = abs(value - expected)
    matches = isclose(value, expected, rel_tol=1e-10, abs_tol=1e-12)
    return OracleResult(
        oracle=name,
        available=True,
        status="match" if matches else "mismatch",
        version=version,
        combined_standard_uncertainty=value,
        absolute_difference=difference,
        details=details,
    )


def verify_with_uncertainties(study: UncertaintyStudyResult) -> OracleResult:
    """Cross-check the combined uncertainty with the BSD ``uncertainties`` package."""

    try:
        module = importlib.import_module("uncertainties")
    except ImportError:
        return OracleResult(
            "uncertainties",
            False,
            "unavailable",
            None,
            None,
            None,
            "Install the 'verification' extra to enable this oracle.",
        )
    contributions = [item.output_contribution for item in study.components]
    correlations = _correlation_lookup(study)
    covariance = []
    for left in study.components:
        row = []
        for right in study.components:
            if left.name == right.name:
                rho = 1.0
            else:
                rho = correlations.get(tuple(sorted((left.name, right.name))), 0.0)
            row.append(rho * left.output_contribution * right.output_contribution)
        covariance.append(row)
    values = module.correlated_values([0.0] * len(contributions), covariance)
    combined = sum(values)
    value = float(module.std_dev(combined))
    return _result(
        "uncertainties",
        _version("uncertainties"),
        value,
        study.budget.combined_standard_uncertainty,
        "Full covariance matrix reconstructed from signed standard contributions.",
    )


def verify_with_gtc(study: UncertaintyStudyResult) -> OracleResult:
    """Cross-check the standard uncertainty with MSL's MIT-licensed GTC package."""

    try:
        module = importlib.import_module("GTC")
    except ImportError:
        return OracleResult(
            "GTC",
            False,
            "unavailable",
            None,
            None,
            None,
            "Install the 'verification' extra to enable this oracle.",
        )
    correlations = _correlation_lookup(study)
    has_correlation = any(value != 0 for value in correlations.values())
    uncertain_values = []
    for item in study.components:
        degrees = inf if has_correlation or item.degrees_of_freedom is None else item.degrees_of_freedom
        uncertain_values.append(
            module.ureal(
                0.0,
                abs(item.output_contribution),
                degrees,
                label=item.name,
                independent=not has_correlation,
            )
        )
    for i, left in enumerate(study.components):
        for j in range(i + 1, len(study.components)):
            right = study.components[j]
            rho = correlations.get(tuple(sorted((left.name, right.name))), 0.0)
            if rho == 0:
                continue
            left_sign = -1.0 if left.output_contribution < 0 else 1.0
            right_sign = -1.0 if right.output_contribution < 0 else 1.0
            module.set_correlation(rho * left_sign * right_sign, uncertain_values[i], uncertain_values[j])
    combined = sum(uncertain_values)
    value = float(combined.u)
    details = "Signed correlations applied to GTC elementary uncertain reals."
    if has_correlation and any(item.degrees_of_freedom is not None for item in study.components):
        details += " Degrees of freedom were set to infinity for this standard-uncertainty cross-check only."
    return _result(
        "GTC",
        _version("GTC"),
        value,
        study.budget.combined_standard_uncertainty,
        details,
    )


def verify_with_external_oracles(
    study: UncertaintyStudyResult,
) -> tuple[OracleResult, ...]:
    return (verify_with_gtc(study), verify_with_uncertainties(study))

