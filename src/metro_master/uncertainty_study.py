"""Parcours GUM traçable en quatre étapes pour les bilans d'incertitude."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from math import fsum, inf, isclose, isfinite, sqrt
from statistics import fmean, stdev
from typing import Any

from .models import Correlation, UncertaintyComponent, VALID_OWNERS
from .quantities import (
    contribution_unit,
    convert_between_specs,
    parse_unit,
)
from .uncertainty import BudgetResult, build_correlation_matrix, propagate_linear
from .validation import require_finite, require_non_negative, require_positive, require_text


SCHEMA_VERSION = "uncertainty-study-v1"
VALID_BUDGET_SCOPES = frozenset(
    {"bench", "reference", "transfer", "comparison", "overall"}
)
BUDGET_SCOPE_OWNERS = {
    "bench": frozenset({"bench", "shared"}),
    "reference": frozenset({"reference", "shared"}),
    "transfer": frozenset({"transfer", "shared"}),
    "comparison": frozenset(VALID_OWNERS),
    "overall": frozenset(VALID_OWNERS),
}
INFLUENCE_CATEGORIES = frozenset(
    {"method", "means", "environment", "operator", "object", "measurand", "other"}
)
# Alias public conservé pour les intégrations 0.9.6 ; le nom canonique est
# désormais ``INFLUENCE_CATEGORIES`` car le registre n'est pas un diagramme.
ISHIKAWA_CATEGORIES = INFLUENCE_CATEGORIES
INFLUENCE_TREATMENTS = frozenset({"component", "covered", "excluded"})
TYPE_B_DISTRIBUTIONS = frozenset(
    {"normal", "rectangular", "triangular", "arcsine", "unspecified"}
)
TYPE_B_VALUE_KINDS = frozenset(
    {"standard_uncertainty", "expanded_uncertainty", "half_width", "resolution_step"}
)


def _strict_object(
    value: object,
    *,
    required: set[str],
    optional: set[str] = frozenset(),
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{label} must be an object")
    missing = required - set(value)
    unknown = set(value) - required - optional
    if missing:
        raise ValueError(f"{label} is missing fields: {', '.join(sorted(missing))}")
    if unknown:
        raise ValueError(f"{label} has unknown fields: {', '.join(sorted(unknown))}")
    return value


def _finite_sequence(value: object, *, label: str, minimum: int = 1) -> tuple[float, ...]:
    if not isinstance(value, list):
        raise TypeError(f"{label} must be an array")
    if not minimum <= len(value) <= 100_000:
        raise ValueError(f"{label} must contain between {minimum} and 100000 values")
    result = []
    for index, item in enumerate(value):
        if isinstance(item, bool) or not isinstance(item, (int, float)) or not isfinite(item):
            raise ValueError(f"{label}[{index}] must be finite")
        result.append(float(item))
    return tuple(result)


def _optional_degrees_of_freedom(value: object) -> float | None:
    if value is None:
        return None
    return require_positive("degrees_of_freedom", value)


def _owner(value: object) -> str:
    owner = require_text("owner", value)
    if owner not in VALID_OWNERS:
        raise ValueError("owner must be one of: " + ", ".join(sorted(VALID_OWNERS)))
    return owner


def _budget_scope(value: object) -> str:
    scope = require_text("budget_scope", value)
    if scope not in VALID_BUDGET_SCOPES:
        raise ValueError(
            "budget_scope must be one of: " + ", ".join(sorted(VALID_BUDGET_SCOPES))
        )
    return scope


@dataclass(frozen=True, slots=True)
class ModelVariable:
    symbol: str
    name: str
    unit: str
    description: str
    estimate: float | None = None

    @classmethod
    def from_dict(cls, value: object) -> "ModelVariable":
        data = _strict_object(
            value,
            required={"symbol", "name", "unit", "description"},
            optional={"estimate"},
            label="measurement model variable",
        )
        symbol = require_text("variable symbol", data["symbol"])
        if "$" in symbol or "\n" in symbol:
            raise ValueError("variable symbol must be plain LaTeX without dollar delimiters")
        unit = require_text("variable unit", data["unit"])
        parse_unit(unit)
        estimate = data.get("estimate")
        if estimate is not None:
            estimate = require_finite(f"estimate for {symbol}", estimate)
        return cls(
            symbol=symbol,
            name=require_text("variable name", data["name"]),
            unit=unit,
            description=require_text("variable description", data["description"]),
            estimate=estimate,
        )


@dataclass(frozen=True, slots=True)
class MeasurementModelSpec:
    measurand: str
    symbol: str
    output_unit: str
    equation_latex: str
    decision: str
    conditions: str
    variables: tuple[ModelVariable, ...]

    @classmethod
    def from_dict(cls, value: object) -> "MeasurementModelSpec":
        data = _strict_object(
            value,
            required={
                "measurand",
                "symbol",
                "output_unit",
                "equation_latex",
                "decision",
                "conditions",
                "variables",
            },
            label="measurement model",
        )
        symbol = require_text("measurand symbol", data["symbol"])
        equation = require_text("measurement equation", data["equation_latex"])
        if "$" in symbol or "$" in equation:
            raise ValueError(
                "symbols and equation_latex must omit dollar delimiters; the renderer adds them"
            )
        output_unit = require_text("output unit", data["output_unit"])
        parse_unit(output_unit)
        variables_value = data["variables"]
        if not isinstance(variables_value, list) or not variables_value:
            raise ValueError("measurement model variables must be a non-empty array")
        variables = tuple(ModelVariable.from_dict(item) for item in variables_value)
        symbols = [item.symbol for item in variables]
        if len(symbols) != len(set(symbols)):
            raise ValueError("measurement model variable symbols must be unique")
        return cls(
            measurand=require_text("measurand", data["measurand"]),
            symbol=symbol,
            output_unit=output_unit,
            equation_latex=equation,
            decision=require_text("measurement decision", data["decision"]),
            conditions=require_text("measurement conditions", data["conditions"]),
            variables=variables,
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class InfluenceEntry:
    id: str
    category: str
    description: str
    treatment: str
    component_name: str | None
    justification: str
    source_ref: str

    @classmethod
    def from_dict(cls, value: object) -> "InfluenceEntry":
        data = _strict_object(
            value,
            required={
                "id",
                "category",
                "description",
                "treatment",
                "component_name",
                "justification",
                "source_ref",
            },
            label="uncertainty influence",
        )
        category = require_text("influence category", data["category"])
        if category not in INFLUENCE_CATEGORIES:
            raise ValueError(
                "influence category must be one of: "
                + ", ".join(sorted(INFLUENCE_CATEGORIES))
            )
        treatment = require_text("influence treatment", data["treatment"])
        if treatment not in INFLUENCE_TREATMENTS:
            raise ValueError(
                "influence treatment must be one of: "
                + ", ".join(sorted(INFLUENCE_TREATMENTS))
            )
        component_name = data["component_name"]
        if component_name is not None:
            component_name = require_text("influence component_name", component_name)
        if treatment in {"component", "covered"} and component_name is None:
            raise ValueError(f"{treatment} influence requires component_name")
        if treatment == "excluded" and component_name is not None:
            raise ValueError("excluded influence must not reference a component")
        return cls(
            id=require_text("influence id", data["id"]),
            category=category,
            description=require_text("influence description", data["description"]),
            treatment=treatment,
            component_name=component_name,
            justification=require_text("influence justification", data["justification"]),
            source_ref=require_text("influence source_ref", data["source_ref"]),
        )


@dataclass(frozen=True, slots=True)
class EvaluatedComponent:
    name: str
    evaluation_type: str
    input_estimate: float | None
    source_value: float
    value_kind: str
    distribution: str
    divisor: float
    standard_uncertainty: float
    degrees_of_freedom: float | None
    unit: str
    sensitivity: float
    sensitivity_unit: str
    owner: str
    source: str
    justification: str
    sensitivity_justification: str
    notes: str
    formula: str
    observations: tuple[float, ...] = ()
    sample_size: int | None = None
    output_contribution: float = 0.0
    output_unit: str = ""

    def to_uncertainty_component(self) -> UncertaintyComponent:
        return UncertaintyComponent(
            name=self.name,
            standard_uncertainty=self.standard_uncertainty,
            sensitivity=self.sensitivity,
            owner=self.owner,
            unit=self.unit,
            degrees_of_freedom=self.degrees_of_freedom,
            distribution=self.distribution,
            source=self.source,
            notes=self.notes,
            sensitivity_unit=self.sensitivity_unit,
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class IndependentVerification:
    method: str
    combined_variance: float
    combined_standard_uncertainty: float
    matches_engine: bool
    absolute_difference: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class UncertaintyStudyResult:
    schema_version: str
    budget_scope: str
    model: MeasurementModelSpec
    influences: tuple[InfluenceEntry, ...]
    components: tuple[EvaluatedComponent, ...]
    correlations: tuple[Correlation, ...]
    budget: BudgetResult
    independent_verification: IndependentVerification
    coverage_justification: str
    correlation_justification: str
    propagation_justification: str
    latex_note: str
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "budget_scope": self.budget_scope,
            "model": self.model.to_dict(),
            "influence_register": _group_influences(self.influences),
            # Alias de compatibilité avec les résultats 0.9.6.
            "ishikawa": _group_influences(self.influences),
            "influences": [asdict(item) for item in self.influences],
            "components": [item.to_dict() for item in self.components],
            "correlations": [item.to_dict() for item in self.correlations],
            "budget": self.budget.to_dict(),
            "independent_verification": self.independent_verification.to_dict(),
            "coverage_justification": self.coverage_justification,
            "correlation_justification": self.correlation_justification,
            "propagation_justification": self.propagation_justification,
            "latex_note": self.latex_note,
            "warnings": list(self.warnings),
        }


def evaluate_type_a(value: object) -> EvaluatedComponent:
    data = _strict_object(
        value,
        required={
            "name",
            "observations",
            "unit",
            "sensitivity",
            "sensitivity_unit",
            "owner",
            "source",
            "conditions",
            "independence_justification",
            "sensitivity_justification",
        },
        optional={"notes"},
        label="Type A component",
    )
    observations = _finite_sequence(data["observations"], label="observations", minimum=2)
    unit = require_text("Type A unit", data["unit"])
    sensitivity_unit = require_text("Type A sensitivity_unit", data["sensitivity_unit"])
    parse_unit(unit)
    parse_unit(sensitivity_unit)
    mean = fmean(observations)
    sample_standard_deviation = stdev(observations, xbar=mean)
    standard_uncertainty = sample_standard_deviation / sqrt(len(observations))
    conditions = require_text("Type A conditions", data["conditions"])
    independence = require_text(
        "Type A independence_justification", data["independence_justification"]
    )
    notes = require_text("Type A notes", data.get("notes", ""), allow_empty=True)
    combined_notes = "; ".join(
        item for item in (f"conditions: {conditions}", f"independence: {independence}", notes) if item
    )
    return EvaluatedComponent(
        name=require_text("Type A name", data["name"]),
        evaluation_type="A",
        input_estimate=mean,
        source_value=sample_standard_deviation,
        value_kind="sample_standard_deviation",
        distribution="type_a_sample_mean",
        divisor=sqrt(len(observations)),
        standard_uncertainty=standard_uncertainty,
        degrees_of_freedom=float(len(observations) - 1),
        unit=unit,
        sensitivity=require_finite("Type A sensitivity", data["sensitivity"]),
        sensitivity_unit=sensitivity_unit,
        owner=_owner(data["owner"]),
        source=require_text("Type A source", data["source"]),
        justification=f"{conditions}; {independence}",
        sensitivity_justification=require_text(
            "Type A sensitivity_justification", data["sensitivity_justification"]
        ),
        notes=combined_notes,
        formula="u_A(x_bar) = s(x) / sqrt(n)",
        observations=observations,
        sample_size=len(observations),
    )


def evaluate_type_b(value: object) -> EvaluatedComponent:
    data = _strict_object(
        value,
        required={
            "name",
            "value",
            "value_kind",
            "distribution",
            "distribution_justification",
            "unit",
            "sensitivity",
            "sensitivity_unit",
            "owner",
            "source",
            "degrees_of_freedom",
            "sensitivity_justification",
        },
        optional={"coverage_factor", "estimate", "notes"},
        label="Type B component",
    )
    source_value = require_non_negative("Type B value", data["value"])
    value_kind = require_text("Type B value_kind", data["value_kind"])
    if value_kind not in TYPE_B_VALUE_KINDS:
        raise ValueError(
            "Type B value_kind must be one of: "
            + ", ".join(sorted(TYPE_B_VALUE_KINDS))
        )
    distribution = require_text("Type B distribution", data["distribution"])
    if distribution not in TYPE_B_DISTRIBUTIONS:
        raise ValueError(
            "Type B distribution must be one of: "
            + ", ".join(sorted(TYPE_B_DISTRIBUTIONS))
        )
    justification = require_text(
        "Type B distribution_justification", data["distribution_justification"]
    )
    coverage_factor = data.get("coverage_factor")
    if value_kind == "expanded_uncertainty":
        if coverage_factor is None:
            raise ValueError("expanded Type B uncertainty requires coverage_factor")
        divisor = require_positive("Type B coverage_factor", coverage_factor)
        formula = "u_B(x) = U / k"
    elif coverage_factor is not None:
        raise ValueError("coverage_factor is only valid for expanded_uncertainty")
    elif value_kind == "standard_uncertainty":
        divisor = 1.0
        formula = "u_B(x) = u(x)"
    elif value_kind == "resolution_step":
        if distribution != "rectangular":
            raise ValueError("resolution_step requires a rectangular distribution")
        divisor = sqrt(12.0)
        formula = "u_B(x) = q / sqrt(12)"
    else:
        divisors = {
            "rectangular": sqrt(3.0),
            "triangular": sqrt(6.0),
            "arcsine": sqrt(2.0),
        }
        if distribution not in divisors:
            raise ValueError(
                "half_width requires rectangular, triangular or arcsine distribution"
            )
        divisor = divisors[distribution]
        formula = {
            "rectangular": "u_B(x) = a / sqrt(3)",
            "triangular": "u_B(x) = a / sqrt(6)",
            "arcsine": "u_B(x) = a / sqrt(2)",
        }[distribution]
    unit = require_text("Type B unit", data["unit"])
    sensitivity_unit = require_text("Type B sensitivity_unit", data["sensitivity_unit"])
    parse_unit(unit)
    parse_unit(sensitivity_unit)
    input_estimate = data.get("estimate")
    if input_estimate is not None:
        input_estimate = require_finite("Type B estimate", input_estimate)
    return EvaluatedComponent(
        name=require_text("Type B name", data["name"]),
        evaluation_type="B",
        input_estimate=input_estimate,
        source_value=source_value,
        value_kind=value_kind,
        distribution=distribution,
        divisor=divisor,
        standard_uncertainty=source_value / divisor,
        degrees_of_freedom=_optional_degrees_of_freedom(data["degrees_of_freedom"]),
        unit=unit,
        sensitivity=require_finite("Type B sensitivity", data["sensitivity"]),
        sensitivity_unit=sensitivity_unit,
        owner=_owner(data["owner"]),
        source=require_text("Type B source", data["source"]),
        justification=justification,
        sensitivity_justification=require_text(
            "Type B sensitivity_justification", data["sensitivity_justification"]
        ),
        notes=require_text("Type B notes", data.get("notes", ""), allow_empty=True),
        formula=formula,
    )


def _group_influences(influences: tuple[InfluenceEntry, ...]) -> dict[str, list[dict[str, object]]]:
    grouped = {category: [] for category in sorted(INFLUENCE_CATEGORIES)}
    for influence in influences:
        grouped[influence.category].append(asdict(influence))
    return grouped


def _normalize_components(
    components: tuple[EvaluatedComponent, ...], output_unit: str
) -> tuple[EvaluatedComponent, ...]:
    target = parse_unit(output_unit)
    normalized = []
    for item in components:
        source = contribution_unit(item.unit, item.sensitivity_unit)
        contribution = convert_between_specs(
            item.sensitivity * item.standard_uncertainty,
            source,
            target,
        )
        normalized.append(
            replace(item, output_contribution=contribution, output_unit=output_unit)
        )
    return tuple(normalized)


def _verify_matrix_form(
    components: tuple[EvaluatedComponent, ...],
    correlations: tuple[Correlation, ...],
    engine_budget: BudgetResult,
) -> IndependentVerification:
    core_components = [item.to_uncertainty_component() for item in components]
    matrix = build_correlation_matrix(core_components, correlations)
    contributions = [item.output_contribution for item in components]
    variance = fsum(
        contributions[i] * matrix[i][j] * contributions[j]
        for i in range(len(contributions))
        for j in range(len(contributions))
    )
    tolerance = 1e-12 * max(1.0, abs(engine_budget.combined_variance), abs(variance))
    matches = isclose(
        variance,
        engine_budget.combined_variance,
        rel_tol=1e-12,
        abs_tol=tolerance,
    )
    if not matches:
        raise ArithmeticError(
            "independent matrix verification disagrees with the uncertainty engine"
        )
    return IndependentVerification(
        method="independent_full_matrix_sum",
        combined_variance=variance,
        combined_standard_uncertainty=sqrt(max(0.0, variance)),
        matches_engine=True,
        absolute_difference=abs(variance - engine_budget.combined_variance),
    )


def _md(value: object) -> str:
    return " ".join(str(value).split()).replace("|", "\\|").replace("$", "\\$")


def _number(value: float) -> str:
    if value == inf:
        return "\\infty"
    return format(value, ".12g")


def _signed_sum(values: list[float]) -> str:
    if not values:
        return "0"
    chunks = [_number(values[0])]
    for value in values[1:]:
        sign = "+" if value >= 0 else "-"
        chunks.append(f" {sign} {_number(abs(value))}")
    return "".join(chunks)


def render_uncertainty_note(
    budget_scope: str,
    model: MeasurementModelSpec,
    influences: tuple[InfluenceEntry, ...],
    components: tuple[EvaluatedComponent, ...],
    correlations: tuple[Correlation, ...],
    budget: BudgetResult,
    verification: IndependentVerification,
    coverage_justification: str,
    correlation_justification: str,
    propagation_justification: str,
) -> str:
    """Render a deterministic French Markdown note with strict LaTeX blocks."""

    lines = [
        "---",
        f'title: "Bilan d’incertitude — {_md(model.measurand)}"',
        f'schema: "{SCHEMA_VERSION}"',
        'status: "calcul déterministe à auditer"',
        "---",
        "",
        f"# Bilan d’incertitude — {_md(model.measurand)}",
        "",
        "## 1. Mandat et conditions",
        "",
        f"- **Décision attendue :** {_md(model.decision)}",
        f"- **Mesurande :** {_md(model.measurand)}",
        f"- **Périmètre du budget :** `{_md(budget_scope)}`",
        f"- **Unité de sortie :** `{_md(model.output_unit)}`",
        f"- **Conditions :** {_md(model.conditions)}",
        "",
        "## 2. Registre structuré des sources d’incertitude",
        "",
        "| Catégorie | Influence | Traitement | Composante | Justification | Source |",
        "|---|---|---|---|---|---|",
    ]
    for item in influences:
        lines.append(
            "| "
            + " | ".join(
                (
                    _md(item.category),
                    _md(item.description),
                    _md(item.treatment),
                    _md(item.component_name or "—"),
                    _md(item.justification),
                    _md(item.source_ref),
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## 3. Équation de mesure",
            "",
            "Le modèle retenu pour le calcul est :",
            "",
            "$$",
            model.equation_latex,
            "$$",
            "",
            "### Définition des symboles",
            "",
            "| Symbole | Grandeur | Valeur | Unité | Définition |",
            "|---|---|---:|---|---|",
        ]
    )
    for variable in model.variables:
        estimate = "—" if variable.estimate is None else _number(variable.estimate)
        lines.append(
            f"| `{_md(variable.symbol)}` | {_md(variable.name)} | {estimate} | "
            f"`{_md(variable.unit)}` | {_md(variable.description)} |"
        )
    lines.extend(
        [
            "",
            "## 4. Évaluation des composantes et contributions",
            "",
            "Type A et Type B indiquent la méthode d’évaluation, pas le caractère aléatoire ou systématique de l’effet.",
            "",
            "Une ligne individuelle décrit une composante et sa contribution. Seul le résultat après composition de toutes les contributions et covariances est une incertitude-type composée.",
            "",
            "| Composante | Estimation de l’entrée | Type | Source | Distribution | Diviseur | Incertitude-type de l’entrée | Sensibilité | Contribution au mesurande | Degrés de liberté |",
            "|---|---:|---|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for item in components:
        degrees = "∞" if item.degrees_of_freedom is None else _number(item.degrees_of_freedom)
        estimate = "—" if item.input_estimate is None else (
            f"{_number(item.input_estimate)} `{_md(item.unit)}`"
        )
        lines.append(
            f"| {_md(item.name)} | {estimate} | {item.evaluation_type} | {_md(item.source)} | "
            f"{_md(item.distribution)} | {_number(item.divisor)} | "
            f"{_number(item.standard_uncertainty)} `{_md(item.unit)}` | "
            f"{_number(item.sensitivity)} `{_md(item.sensitivity_unit)}` | "
            f"{_number(item.output_contribution)} `{_md(item.output_unit)}` | {degrees} |"
        )
    for item in components:
        lines.extend(["", f"### {_md(item.name)} — évaluation Type {item.evaluation_type}", ""])
        if item.evaluation_type == "A":
            observations = ",\\;".join(_number(value) for value in item.observations)
            lines.extend(
                [
                    "La série conservée est :",
                    "",
                    "$$",
                    f"x = ({observations})\\;\\mathrm{{{_md(item.unit)}}},\\qquad "
                    f"n={item.sample_size}",
                    "$$",
                    "",
                    "La moyenne et l’écart-type expérimental de la série valent :",
                    "",
                    "$$",
                    f"\\bar{{x}}={_number(item.input_estimate)},\\qquad "
                    f"s(x)={_number(item.source_value)}\\;\\mathrm{{{_md(item.unit)}}}",
                    "$$",
                    "",
                    "La dispersion est convertie en incertitude-type de la moyenne.",
                    "",
                    "$$",
                    "u_A(\\bar{x}) = \\frac{s(x)}{\\sqrt{n}}",
                    "$$",
                    "",
                    "Application numérique traçable :",
                    "",
                    "$$",
                    f"u_A(\\bar{{x}}) = \\frac{{{_number(item.source_value)}}}"
                    f"{{\\sqrt{{{item.sample_size}}}}} = {_number(item.standard_uncertainty)}"
                    f"\\;\\mathrm{{{_md(item.unit)}}}",
                    "$$",
                ]
            )
        else:
            latex_formula = {
                "standard_uncertainty": "u_B(x) = u(x)",
                "expanded_uncertainty": "u_B(x) = \\frac{U}{k}",
                "resolution_step": "u_B(x) = \\frac{q}{\\sqrt{12}}",
                "half_width": "u_B(x) = \\frac{a}{d}",
            }[item.value_kind]
            lines.extend(
                [
                    f"La distribution `{_md(item.distribution)}` est retenue pour la raison suivante : {_md(item.justification)}",
                    "",
                    "$$",
                    latex_formula,
                    "$$",
                    "",
                    "Application numérique traçable :",
                    "",
                    "$$",
                    f"u_B(x) = \\frac{{{_number(item.source_value)}}}"
                    f"{{{_number(item.divisor)}}} = {_number(item.standard_uncertainty)}"
                    f"\\;\\mathrm{{{_md(item.unit)}}}",
                    "$$",
                ]
            )
        lines.extend(
            [
                "",
                f"Justification du coefficient de sensibilité : {_md(item.sensitivity_justification)}",
                "",
                "La contribution signée au mesurande vaut :",
                "",
                "$$",
                f"c_i u(x_i) = {_number(item.sensitivity)}"
                f"\\;\\mathrm{{{_md(item.sensitivity_unit)}}} \\times "
                f"{_number(item.standard_uncertainty)}"
                f"\\;\\mathrm{{{_md(item.unit)}}} = "
                f"{_number(item.output_contribution)}\\;\\mathrm{{{_md(item.output_unit)}}}",
                "$$",
            ]
        )
    lines.extend(
        [
            "",
            "## 5. Composition et corrélations",
            "",
            f"Évaluation globale des corrélations : {_md(correlation_justification)}",
            "",
            "| Composante gauche | Composante droite | Coefficient | Justification |",
            "|---|---|---:|---|",
        ]
    )
    if correlations:
        for item in correlations:
            lines.append(
                f"| {_md(item.left)} | {_md(item.right)} | "
                f"{_number(item.coefficient)} | {_md(item.justification)} |"
            )
    else:
        lines.append("| — | — | 0 déclaré | aucune paire non nulle |")
    lines.extend(
        [
            "",
            f"Validité de la propagation linéaire : {_md(propagation_justification)}",
            "",
            "La loi de propagation avec les covariances explicites est :",
            "",
            "$$",
            "u_c^2(y) = \\sum_{i=1}^{N} c_i^2u^2(x_i)"
            " + 2\\sum_{i=1}^{N-1}\\sum_{j=i+1}^{N}"
            "c_ic_j\\,u(x_i,x_j)",
            "$$",
            "",
            "Les termes numériques enregistrés par le moteur donnent :",
            "",
            "$$",
            f"u_c^2(y) = {_signed_sum([term.value for term in budget.terms])}"
            f" = {_number(budget.combined_variance)}\\;\\mathrm{{{_md(budget.unit)}^2}}",
            "$$",
            "",
            "Donc :",
            "",
            "$$",
            f"u_c(y) = {_number(budget.combined_standard_uncertainty)}"
            f"\\;\\mathrm{{{_md(budget.unit)}}}",
            "$$",
            "",
            "## 6. Incertitude élargie",
            "",
            f"Le facteur de couverture est justifié ainsi : {_md(coverage_justification)}",
            "",
            "$$",
            "U = k\\,u_c(y)",
            "$$",
            "",
            "$$",
            f"U = {_number(budget.coverage_factor)} \\times "
            f"{_number(budget.combined_standard_uncertainty)} = "
            f"{_number(budget.expanded_uncertainty)}\\;\\mathrm{{{_md(budget.unit)}}}",
            "$$",
            "",
            "## 7. Vérifications",
            "",
            f"- Vérification matricielle indépendante : `{'conforme' if verification.matches_engine else 'écart'}`.",
            f"- Écart absolu sur la variance : `{_number(verification.absolute_difference)}`.",
            "- Les unités des contributions ont été converties vers l’unité du mesurande.",
            "- Les données, hypothèses et exclusions restent visibles dans les artefacts de l’étude.",
        ]
    )
    if budget.warnings:
        lines.extend(["", "### Avertissements du moteur", ""])
        lines.extend(f"- {_md(item)}" for item in budget.warnings)
    lines.extend(
        [
            "",
            "## 8. Résultat conditionnel",
            "",
            f"Le résultat calculé est associé à une incertitude-type composée de "
            f"**{_number(budget.combined_standard_uncertainty)} {_md(budget.unit)}** et à "
            f"une incertitude élargie de **{_number(budget.expanded_uncertainty)} "
            f"{_md(budget.unit)}** avec le facteur déclaré **k = "
            f"{_number(budget.coverage_factor)}**.",
            "",
            "Ce résultat reste soumis à la validation méthodologique de GUM-EXPERT et au verdict de METRO-AUDIT.",
            "",
        ]
    )
    return "\n".join(lines)


def build_uncertainty_study(payload: object) -> UncertaintyStudyResult:
    """Build and calculate the complete four-stage uncertainty workflow."""

    data = _strict_object(
        payload,
        required={
            "model",
            "influences",
            "type_a",
            "type_b",
            "correlations",
            "coverage_factor",
            "coverage_justification",
            "correlation_justification",
            "propagation_justification",
        },
        optional={"budget_scope"},
        label="uncertainty study",
    )
    budget_scope_value = data.get("budget_scope")
    budget_scope = (
        "unspecified" if budget_scope_value is None else _budget_scope(budget_scope_value)
    )
    model = MeasurementModelSpec.from_dict(data["model"])
    influences_value = data["influences"]
    if not isinstance(influences_value, list) or not influences_value:
        raise ValueError("uncertainty influence register must be a non-empty array")
    influences = tuple(InfluenceEntry.from_dict(item) for item in influences_value)
    influence_ids = [item.id for item in influences]
    if len(influence_ids) != len(set(influence_ids)):
        raise ValueError("uncertainty influence ids must be unique")

    type_a_value = data["type_a"]
    type_b_value = data["type_b"]
    if not isinstance(type_a_value, list) or not isinstance(type_b_value, list):
        raise TypeError("type_a and type_b must be arrays")
    components = tuple(
        [evaluate_type_a(item) for item in type_a_value]
        + [evaluate_type_b(item) for item in type_b_value]
    )
    if not components:
        raise ValueError("at least one Type A or Type B component is required")
    component_names = [item.name for item in components]
    if len(component_names) != len(set(component_names)):
        raise ValueError("uncertainty component names must be unique")

    if budget_scope != "unspecified":
        allowed_owners = BUDGET_SCOPE_OWNERS[budget_scope]
        forbidden = sorted(
            {item.owner for item in components if item.owner not in allowed_owners}
        )
        if forbidden:
            raise ValueError(
                f"budget_scope '{budget_scope}' cannot include component owners: "
                + ", ".join(forbidden)
                + ". Evaluate reference/transfer uncertainty in its own budget or mark "
                "the source as covered by the calibrated parameter that carries it."
            )

    referenced = {
        item.component_name
        for item in influences
        if item.treatment in {"component", "covered"}
    }
    unknown = sorted(name for name in referenced if name not in set(component_names))
    if unknown:
        raise ValueError("influence register references unknown components: " + ", ".join(unknown))
    direct_components = {
        item.component_name for item in influences if item.treatment == "component"
    }
    missing = sorted(set(component_names) - direct_components)
    if missing:
        raise ValueError(
            "uncertainty components without a direct influence-register entry: "
            + ", ".join(missing)
        )

    correlations_value = data["correlations"]
    if not isinstance(correlations_value, list):
        raise TypeError("correlations must be an array")
    correlations = tuple(Correlation.from_dict(item) for item in correlations_value)
    coverage_factor = require_positive("coverage_factor", data["coverage_factor"])
    coverage_justification = require_text(
        "coverage_justification", data["coverage_justification"]
    )
    correlation_justification = require_text(
        "correlation_justification", data["correlation_justification"]
    )
    propagation_justification = require_text(
        "propagation_justification", data["propagation_justification"]
    )
    components = _normalize_components(components, model.output_unit)
    core_components = [item.to_uncertainty_component() for item in components]
    budget = propagate_linear(
        core_components,
        correlations,
        coverage_factor=coverage_factor,
        output_unit=model.output_unit,
    )
    verification = _verify_matrix_form(components, correlations, budget)
    note = render_uncertainty_note(
        budget_scope,
        model,
        influences,
        components,
        correlations,
        budget,
        verification,
        coverage_justification,
        correlation_justification,
        propagation_justification,
    )
    warnings = list(budget.warnings)
    if budget_scope == "unspecified":
        warnings.append(
            "Budget scope is not declared; ownership separation and double counting "
            "cannot be audited deterministically."
        )
    if not type_a_value:
        warnings.append("No Type A component is present; confirm that no repeatability data apply.")
    if not type_b_value:
        warnings.append("No Type B component is present; confirm documentary influences are complete.")
    return UncertaintyStudyResult(
        schema_version=SCHEMA_VERSION,
        budget_scope=budget_scope,
        model=model,
        influences=influences,
        components=components,
        correlations=correlations,
        budget=budget,
        independent_verification=verification,
        coverage_justification=coverage_justification,
        correlation_justification=correlation_justification,
        propagation_justification=propagation_justification,
        latex_note=note,
        warnings=tuple(warnings),
    )

