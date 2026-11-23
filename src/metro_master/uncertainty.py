"""Propagation linéaire des incertitudes avec corrélations explicites."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import inf, isclose, sqrt
from typing import Iterable

from .models import Correlation, UncertaintyComponent
from .validation import require_positive, validate_compatible_units


@dataclass(frozen=True, slots=True)
class VarianceTerm:
    kind: str
    names: tuple[str, ...]
    value: float
    owners: tuple[str, ...]
    correlation: float | None = None


@dataclass(frozen=True, slots=True)
class BudgetResult:
    combined_variance: float
    combined_standard_uncertainty: float
    coverage_factor: float
    expanded_uncertainty: float
    effective_degrees_of_freedom: float | None
    correlation_matrix: tuple[tuple[float, ...], ...]
    terms: tuple[VarianceTerm, ...]
    diagonal_variance_by_owner: dict[str, float]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        if self.effective_degrees_of_freedom == inf:
            data["effective_degrees_of_freedom"] = "infinity"
        return data


def _is_positive_semidefinite(matrix: list[list[float]], tolerance: float = 1e-12) -> bool:
    """LDLᵀ check that accepts semi-definite matrices without NumPy."""

    n = len(matrix)
    lower = [[0.0] * n for _ in range(n)]
    diagonal = [0.0] * n
    for i in range(n):
        lower[i][i] = 1.0
        pivot = matrix[i][i] - sum(
            lower[i][k] * lower[i][k] * diagonal[k] for k in range(i)
        )
        if pivot < -tolerance:
            return False
        diagonal[i] = 0.0 if abs(pivot) <= tolerance else pivot
        for j in range(i + 1, n):
            residual = matrix[j][i] - sum(
                lower[j][k] * lower[i][k] * diagonal[k] for k in range(i)
            )
            if diagonal[i] == 0.0:
                if abs(residual) > tolerance:
                    return False
                lower[j][i] = 0.0
            else:
                lower[j][i] = residual / diagonal[i]
    return True


def build_correlation_matrix(
    components: Iterable[UncertaintyComponent],
    correlations: Iterable[Correlation] = (),
) -> list[list[float]]:
    components = list(components)
    names = [item.name for item in components]
    if len(names) != len(set(names)):
        raise ValueError("component names must be unique")
    positions = {name: index for index, name in enumerate(names)}
    size = len(names)
    matrix = [[0.0] * size for _ in range(size)]
    for index in range(size):
        matrix[index][index] = 1.0

    seen: dict[tuple[int, int], float] = {}
    for item in correlations:
        if item.left not in positions or item.right not in positions:
            raise ValueError(f"unknown component in correlation: {item.left}, {item.right}")
        i, j = sorted((positions[item.left], positions[item.right]))
        key = (i, j)
        if key in seen and not isclose(seen[key], item.coefficient, abs_tol=1e-15):
            raise ValueError(f"conflicting correlations for {item.left}/{item.right}")
        seen[key] = item.coefficient
        matrix[i][j] = matrix[j][i] = item.coefficient

    if not _is_positive_semidefinite(matrix):
        raise ValueError("correlation matrix is not positive semi-definite")
    return matrix


def _effective_degrees_of_freedom(
    components: list[UncertaintyComponent], combined_variance: float
) -> float:
    denominator = 0.0
    for component in components:
        if component.degrees_of_freedom is None:
            continue
        contribution = component.sensitivity * component.standard_uncertainty
        denominator += contribution**4 / component.degrees_of_freedom
    if denominator == 0:
        return inf
    return combined_variance**2 / denominator


def propagate_linear(
    components: Iterable[UncertaintyComponent],
    correlations: Iterable[Correlation] = (),
    *,
    coverage_factor: float = 2.0,
) -> BudgetResult:
    """Apply ``u²(y) = cᵀ U c`` to a first-order measurement model.

    Degrees of freedom are calculated by Welch-Satterthwaite only when all
    off-diagonal correlations are zero. For correlated inputs the function
    returns ``None`` instead of presenting an unjustified approximation.
    """

    components = list(components)
    correlations = list(correlations)
    if not components:
        raise ValueError("at least one uncertainty component is required")
    require_positive("coverage_factor", coverage_factor)
    validate_compatible_units(components)
    matrix = build_correlation_matrix(components, correlations)

    terms: list[VarianceTerm] = []
    by_owner: dict[str, float] = {}
    variance = 0.0
    for i, left in enumerate(components):
        diagonal = (left.sensitivity * left.standard_uncertainty) ** 2
        variance += diagonal
        by_owner[left.owner] = by_owner.get(left.owner, 0.0) + diagonal
        terms.append(VarianceTerm("diagonal", (left.name,), diagonal, (left.owner,)))
        for j in range(i + 1, len(components)):
            right = components[j]
            rho = matrix[i][j]
            cross = (
                2
                * left.sensitivity
                * right.sensitivity
                * rho
                * left.standard_uncertainty
                * right.standard_uncertainty
            )
            variance += cross
            if rho != 0:
                terms.append(
                    VarianceTerm(
                        "covariance",
                        (left.name, right.name),
                        cross,
                        (left.owner, right.owner),
                        rho,
                    )
                )

    tolerance = 1e-12 * max(1.0, sum(abs(term.value) for term in terms))
    if variance < -tolerance:
        raise ValueError("combined variance is negative; check covariance model")
    variance = max(0.0, variance)
    standard = sqrt(variance)
    has_correlation = any(matrix[i][j] != 0 for i in range(len(matrix)) for j in range(i))
    warnings: list[str] = []
    if has_correlation:
        effective_dof = None
        warnings.append(
            "Effective degrees of freedom are not estimated for correlated inputs; "
            "justify a coverage factor by another validated method."
        )
    else:
        effective_dof = _effective_degrees_of_freedom(components, variance)
    if any(term.kind == "covariance" and len(set(term.owners)) > 1 for term in terms):
        warnings.append(
            "Cross-owner covariance terms are reported separately and are not allocated "
            "to either owner."
        )

    return BudgetResult(
        combined_variance=variance,
        combined_standard_uncertainty=standard,
        coverage_factor=coverage_factor,
        expanded_uncertainty=coverage_factor * standard,
        effective_degrees_of_freedom=effective_dof,
        correlation_matrix=tuple(tuple(row) for row in matrix),
        terms=tuple(terms),
        diagonal_variance_by_owner=by_owner,
        warnings=tuple(warnings),
    )

