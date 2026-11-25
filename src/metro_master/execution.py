"""Exécution vérifiable des calculs demandés par la CLI ou les agents."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from math import isclose, isfinite
import re
from typing import Any

from .conclusion import ConclusionClaim, MAX_CONCLUSION_CLAIMS
from .comparison import (
    compare_results,
    normalized_error,
    paired_statistics,
    separate_bench_uncertainty,
)
from .models import Correlation, UncertaintyComponent
from .module_registry import (
    CORE_RESERVED_MODULE_IDS,
    FormulaCalculationModule,
    ModuleRegistry,
    ModuleStore,
    NativeCalculationModule,
    validate_module_id,
)
from .research import MAX_RESEARCH_REQUESTS_PER_TURN, ResearchRequest
from .trace import CalculationTrace, build_calculation_trace
from .uncertainty import propagate_linear
from .uncertainty_study import build_uncertainty_study
from .validation import require_correlation, require_nonzero_justification, require_text


BUILTIN_OPERATIONS = set(CORE_RESERVED_MODULE_IDS)
MAX_CALCULATION_REQUESTS_PER_TURN = 16
MAX_MODULE_PROPOSALS_PER_TURN = 4
EVIDENCE_TYPES = frozenset({"provided", "derived", "method_choice", "assumption"})
NUMBER_PATTERN = re.compile(
    r"(?<![\w.])[-+]?(?:\d+(?:[.,]\d*)?|[.,]\d+)(?:[eE][-+]?\d+)?"
)


class ProvenanceValidationError(ValueError):
    """Raised when a compiled calculation is not traceable to its source text."""


@dataclass(frozen=True, slots=True)
class InputEvidence:
    field_path: str
    source_ref: str
    excerpt: str
    evidence_type: str

    def __post_init__(self) -> None:
        path = require_text("evidence field_path", self.field_path)
        if not path.startswith("/"):
            raise ValueError("evidence field_path must be a JSON Pointer")
        require_text("evidence source_ref", self.source_ref)
        require_text("evidence excerpt", self.excerpt)
        evidence_type = require_text("evidence type", self.evidence_type)
        if evidence_type not in EVIDENCE_TYPES:
            raise ValueError(f"invalid evidence type: {evidence_type}")

    @classmethod
    def from_dict(cls, value: object) -> "InputEvidence":
        if not isinstance(value, dict):
            raise TypeError("each evidence entry must be an object")
        required = {"field_path", "source_ref", "excerpt", "evidence_type"}
        missing = required - set(value)
        unknown = set(value) - required
        if missing:
            raise ValueError(
                f"evidence entry is missing fields: {', '.join(sorted(missing))}"
            )
        if unknown:
            raise ValueError(
                f"evidence entry has unknown fields: {', '.join(sorted(unknown))}"
            )
        return cls(
            value["field_path"],
            value["source_ref"],
            value["excerpt"],
            value["evidence_type"],
        )


@dataclass(frozen=True, slots=True)
class CalculationRequest:
    id: str
    operation: str
    payload: dict[str, Any]
    evidence: tuple[InputEvidence, ...] = ()
    assumptions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        require_text("calculation request id", self.id)
        if len(self.id) > 128 or any(
            character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
            for character in self.id
        ):
            raise ValueError(
                "calculation request id may contain only letters, digits, dot, underscore or hyphen"
            )
        validate_module_id(self.operation)
        if not isinstance(self.payload, dict):
            raise TypeError("calculation payload must be an object")
        if not isinstance(self.evidence, tuple) or not all(
            isinstance(item, InputEvidence) for item in self.evidence
        ):
            raise TypeError("calculation evidence must be a tuple of InputEvidence")
        if not isinstance(self.assumptions, tuple) or not all(
            isinstance(item, str) and item.strip() for item in self.assumptions
        ):
            raise TypeError("calculation assumptions must be non-empty strings")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "CalculationRequest":
        if not isinstance(value, dict):
            raise TypeError("each calculation request must be an object")
        unknown = set(value) - {
            "id",
            "operation",
            "payload",
            "evidence",
            "assumptions",
        }
        missing = {"id", "operation", "payload"} - set(value)
        if missing:
            raise ValueError(
                f"calculation request is missing fields: {', '.join(sorted(missing))}"
            )
        if unknown:
            raise ValueError(
                f"calculation request has unknown fields: {', '.join(sorted(unknown))}"
            )
        identifier = require_text("calculation request id", value.get("id"))
        operation = require_text("calculation operation", value.get("operation"))
        payload = value.get("payload")
        if not isinstance(payload, dict):
            raise TypeError("calculation payload must be an object")
        evidence_value = value.get("evidence", [])
        if not isinstance(evidence_value, list):
            raise TypeError("calculation evidence must be an array")
        if len(evidence_value) > 256:
            raise ValueError("at most 256 calculation evidence entries are allowed")
        evidence = tuple(InputEvidence.from_dict(item) for item in evidence_value)
        assumptions_value = value.get("assumptions", [])
        if not isinstance(assumptions_value, list) or not all(
            isinstance(item, str) and item.strip() for item in assumptions_value
        ):
            raise TypeError("calculation assumptions must be an array of non-empty strings")
        return cls(
            identifier,
            operation,
            payload,
            evidence,
            tuple(item.strip() for item in assumptions_value),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CalculationRecord:
    request: CalculationRequest
    status: str
    result: dict[str, object] | None = None
    error_type: str | None = None
    error: str | None = None
    provenance_checked: bool = False
    provenance_status: str = "not_checked"
    provenance_warnings: tuple[str, ...] = ()
    trace: CalculationTrace | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ParsedAgentResponse:
    message: str
    calculation_requests: tuple[CalculationRequest, ...] = ()
    module_proposals: tuple[dict[str, Any], ...] = ()
    research_requests: tuple[ResearchRequest, ...] = ()
    conclusion_claims: tuple[ConclusionClaim, ...] = ()


def parse_agent_response(response: str) -> ParsedAgentResponse:
    """Parse the optional structured envelope while preserving plain-text adapters."""

    if not isinstance(response, str) or not response.strip():
        raise ValueError("agent response must be a non-empty string")
    response = response.strip()
    try:
        value = json.loads(response)
    except json.JSONDecodeError:
        return ParsedAgentResponse(response)
    if not isinstance(value, dict) or not {
        "calculation_requests",
        "module_proposals",
        "research_requests",
        "conclusion_claims",
    }.intersection(value):
        return ParsedAgentResponse(response)

    allowed_fields = {
        "message",
        "calculation_requests",
        "module_proposals",
        "research_requests",
        "conclusion_claims",
    }
    unknown_fields = set(value) - allowed_fields
    if unknown_fields:
        raise ValueError(
            "structured agent response has unknown fields: "
            + ", ".join(sorted(unknown_fields))
        )

    message = value.get("message", "")
    if not isinstance(message, str):
        raise TypeError("structured agent response message must be a string")
    message = message.strip()
    requests_value = value.get("calculation_requests", [])
    if not isinstance(requests_value, list):
        raise TypeError("calculation_requests must be an array")
    if len(requests_value) > MAX_CALCULATION_REQUESTS_PER_TURN:
        raise ValueError(
            f"at most {MAX_CALCULATION_REQUESTS_PER_TURN} calculations are allowed per turn"
        )
    requests = tuple(CalculationRequest.from_dict(item) for item in requests_value)
    ids = [item.id for item in requests]
    if len(ids) != len(set(ids)):
        raise ValueError("calculation request ids must be unique within an agent turn")
    proposals_value = value.get("module_proposals", [])
    if not isinstance(proposals_value, list):
        raise TypeError("module_proposals must be an array")
    if len(proposals_value) > MAX_MODULE_PROPOSALS_PER_TURN:
        raise ValueError(
            f"at most {MAX_MODULE_PROPOSALS_PER_TURN} module proposals are allowed per turn"
        )
    proposals = []
    for proposal in proposals_value:
        if not isinstance(proposal, dict):
            raise TypeError("each module proposal must be an object")
        proposals.append(proposal)
    research_value = value.get("research_requests", [])
    if not isinstance(research_value, list):
        raise TypeError("research_requests must be an array")
    if len(research_value) > MAX_RESEARCH_REQUESTS_PER_TURN:
        raise ValueError(
            f"at most {MAX_RESEARCH_REQUESTS_PER_TURN} research requests are allowed per turn"
        )
    research_requests = tuple(
        ResearchRequest.from_dict(item) for item in research_value
    )
    research_ids = [item.id for item in research_requests]
    if len(research_ids) != len(set(research_ids)):
        raise ValueError("research request ids must be unique within an agent turn")
    claims_value = value.get("conclusion_claims", [])
    if not isinstance(claims_value, list):
        raise TypeError("conclusion_claims must be an array")
    if len(claims_value) > MAX_CONCLUSION_CLAIMS:
        raise ValueError(
            f"at most {MAX_CONCLUSION_CLAIMS} conclusion claims are allowed per turn"
        )
    conclusion_claims = tuple(
        ConclusionClaim.from_dict(item) for item in claims_value
    )
    if (
        not message
        and not requests
        and not proposals
        and not research_requests
        and not conclusion_claims
    ):
        raise ValueError(
            "structured agent response must contain a message, calculation request, "
            "module proposal or research request"
        )
    if not message:
        message = "Structured request submitted."
    return ParsedAgentResponse(
        message=message,
        calculation_requests=requests,
        module_proposals=tuple(proposals),
        research_requests=research_requests,
        conclusion_claims=conclusion_claims,
    )


class DeterministicEngine:
    """Single interface to all publishable numerical operations."""

    def __init__(self, registry: ModuleRegistry | None = None) -> None:
        self.registry = registry or ModuleRegistry()
        native_modules = (
            NativeCalculationModule("budget", "1.0.0", "Linear uncertainty budget", self._budget),
            NativeCalculationModule("compare", "1.0.0", "Correlated comparison", self._compare),
            NativeCalculationModule("paired", "1.0.0", "Paired observations", self._paired),
            NativeCalculationModule("separate", "1.0.0", "Conditional bench separation", self._separate),
            NativeCalculationModule(
                "uncertainty-study",
                "1.0.0",
                "Four-stage GUM uncertainty study",
                self._uncertainty_study,
            ),
        )
        for module in native_modules:
            self.registry.register(module)

    @classmethod
    def from_store(cls, store: ModuleStore) -> "DeterministicEngine":
        engine = cls()
        engine.load_store(store)
        return engine

    def load_store(self, store: ModuleStore) -> None:
        """Reload all active governed formula modules without restarting the process."""

        self.registry.remove_kind("formula")
        for record in store.active_records():
            self.registry.register(FormulaCalculationModule(record.definition))

    def calculate(self, request: CalculationRequest) -> dict[str, object]:
        return self.registry.calculate(request.operation, request.payload)

    def list_modules(self) -> tuple[dict[str, object], ...]:
        return self.registry.describe()

    def execute(
        self,
        request: CalculationRequest,
        *,
        require_provenance: bool = False,
        evidence_text: str = "",
        evidence_sources: dict[str, str] | None = None,
        execution_origin: str = "structured_input",
        previous_trace_sha256: str = "",
    ) -> CalculationRecord:
        descriptor: dict[str, object]
        try:
            descriptor = self.registry.descriptor(request.operation)
        except (KeyError, TypeError, ValueError):
            descriptor = {
                "id": request.operation,
                "version": "unknown",
                "title": "Unknown calculation module",
                "kind": "unknown",
                "algorithm_id": "unknown",
                "implementation_sha256": "",
                "validation_suite_sha256": "",
            }
        try:
            provenance_status = "not_checked"
            warnings: tuple[str, ...] = ()
            if require_provenance:
                provenance_status, warnings = validate_calculation_provenance(
                    request,
                    evidence_text,
                    evidence_sources=evidence_sources,
                )
            result = self.calculate(request)
            trace = build_calculation_trace(
                request=request.to_dict(),
                module=descriptor,
                status="ok",
                result=result,
                execution_origin=execution_origin,
                provenance_required=require_provenance,
                provenance_status=provenance_status,
                previous_trace_sha256=previous_trace_sha256,
            )
            return CalculationRecord(
                request,
                "ok",
                result=result,
                provenance_checked=require_provenance,
                provenance_status=provenance_status,
                provenance_warnings=warnings,
                trace=trace,
            )
        except (KeyError, TypeError, ValueError, ArithmeticError) as error:
            provenance_status = "rejected" if require_provenance else "not_checked"
            trace = build_calculation_trace(
                request=request.to_dict(),
                module=descriptor,
                status="rejected",
                result=None,
                execution_origin=execution_origin,
                provenance_required=require_provenance,
                provenance_status=provenance_status,
                previous_trace_sha256=previous_trace_sha256,
                error_type=type(error).__name__,
                error=str(error),
            )
            return CalculationRecord(
                request,
                "rejected",
                error_type=type(error).__name__,
                error=str(error),
                provenance_checked=require_provenance,
                provenance_status=provenance_status,
                trace=trace,
            )

    def reject(
        self,
        request: CalculationRequest,
        *,
        error_type: str,
        error: str,
        execution_origin: str,
        previous_trace_sha256: str = "",
    ) -> CalculationRecord:
        try:
            descriptor = self.registry.descriptor(request.operation)
        except (KeyError, TypeError, ValueError):
            descriptor = {
                "id": request.operation,
                "version": "unknown",
                "title": "Unknown calculation module",
                "kind": "unknown",
                "algorithm_id": "unknown",
                "implementation_sha256": "",
                "validation_suite_sha256": "",
            }
        trace = build_calculation_trace(
            request=request.to_dict(),
            module=descriptor,
            status="rejected",
            result=None,
            execution_origin=execution_origin,
            provenance_required=True,
            provenance_status="rejected",
            previous_trace_sha256=previous_trace_sha256,
            error_type=error_type,
            error=error,
        )
        return CalculationRecord(
            request,
            "rejected",
            error_type=error_type,
            error=error,
            provenance_checked=True,
            provenance_status="rejected",
            trace=trace,
        )

    @staticmethod
    def _budget(payload: dict[str, Any]) -> dict[str, object]:
        DeterministicEngine._validate_payload_fields(
            payload,
            required={"components"},
            optional={"correlations", "coverage_factor", "output_unit"},
            operation="budget",
        )
        components_value = payload["components"]
        correlations_value = payload.get("correlations", [])
        if not isinstance(components_value, list):
            raise TypeError("components must be an array")
        if not isinstance(correlations_value, list):
            raise TypeError("correlations must be an array")
        components = [UncertaintyComponent.from_dict(item) for item in components_value]
        correlations = [Correlation.from_dict(item) for item in correlations_value]
        result = propagate_linear(
            components,
            correlations,
            coverage_factor=payload.get("coverage_factor", 2.0),
            output_unit=payload.get("output_unit"),
        ).to_dict()
        return result

    @staticmethod
    def _uncertainty_study(payload: dict[str, Any]) -> dict[str, object]:
        return build_uncertainty_study(payload).to_dict()

    @staticmethod
    def _compare(payload: dict[str, Any]) -> dict[str, object]:
        DeterministicEngine._validate_payload_fields(
            payload,
            required={
                "bench_value",
                "reference_value",
                "bench_standard_uncertainty",
                "reference_standard_uncertainty",
            },
            optional={
                "correlation",
                "correlation_justification",
                "bench_expanded_uncertainty",
                "reference_expanded_uncertainty",
                "expanded_correlation",
                "expanded_correlation_justification",
                "unit",
            },
            operation="compare",
        )
        correlation = payload.get("correlation", 0.0)
        correlation_justification = payload.get("correlation_justification", "")
        result = compare_results(
            bench_value=payload["bench_value"],
            reference_value=payload["reference_value"],
            bench_standard_uncertainty=payload["bench_standard_uncertainty"],
            reference_standard_uncertainty=payload["reference_standard_uncertainty"],
            correlation=correlation,
            correlation_justification=correlation_justification,
        )
        output = result.to_dict()
        output["unit"] = require_text(
            "compare unit", payload.get("unit", ""), allow_empty=True
        )
        expanded_keys = {
            "bench_expanded_uncertainty",
            "reference_expanded_uncertainty",
        }
        if expanded_keys.intersection(payload):
            if not expanded_keys.issubset(payload):
                raise ValueError(
                    "both expanded uncertainties are required to calculate E_n"
                )
            expanded_correlation = payload.get("expanded_correlation", correlation)
            require_correlation("expanded_correlation", expanded_correlation)
            expanded_justification = payload.get(
                "expanded_correlation_justification",
                correlation_justification if expanded_correlation == correlation else "",
            )
            expanded_justification = require_nonzero_justification(
                "expanded_correlation",
                expanded_correlation,
                expanded_justification,
            )
            output["normalized_error"] = normalized_error(
                result.difference,
                payload["bench_expanded_uncertainty"],
                payload["reference_expanded_uncertainty"],
                correlation=expanded_correlation,
            )
            output["expanded_correlation"] = expanded_correlation
            output["expanded_correlation_justification"] = expanded_justification
            output["normalized_error_warning"] = (
                "Interpret only with compatible expanded-uncertainty coverage conventions."
            )
        return output

    @staticmethod
    def _paired(payload: dict[str, Any]) -> dict[str, object]:
        DeterministicEngine._validate_payload_fields(
            payload,
            required={"bench_readings", "reference_readings"},
            optional={"unit"},
            operation="paired",
        )
        output = paired_statistics(
            payload["bench_readings"], payload["reference_readings"]
        ).to_dict()
        output["unit"] = require_text(
            "paired unit", payload.get("unit", ""), allow_empty=True
        )
        return output

    @staticmethod
    def _separate(payload: dict[str, Any]) -> dict[str, object]:
        DeterministicEngine._validate_payload_fields(
            payload,
            required={
                "difference_standard_uncertainty",
                "reference_standard_uncertainty",
                "covariance",
            },
            optional={
                "identifiability_confirmed",
                "identifiability_justification",
                "unit",
            },
            operation="separate",
        )
        output = separate_bench_uncertainty(
            difference_standard_uncertainty=payload["difference_standard_uncertainty"],
            reference_standard_uncertainty=payload["reference_standard_uncertainty"],
            covariance=payload["covariance"],
            identifiability_confirmed=payload.get("identifiability_confirmed", False),
            identifiability_justification=payload.get(
                "identifiability_justification", ""
            ),
        ).to_dict()
        output["unit"] = require_text(
            "separate unit", payload.get("unit", ""), allow_empty=True
        )
        return output

    @staticmethod
    def _validate_payload_fields(
        payload: object,
        *,
        required: set[str],
        optional: set[str] = frozenset(),
        operation: str,
    ) -> None:
        if not isinstance(payload, dict):
            raise TypeError(f"{operation} payload must be an object")
        missing = required - set(payload)
        unknown = set(payload) - required - optional
        if missing:
            raise ValueError(
                f"{operation} payload is missing fields: {', '.join(sorted(missing))}"
            )
        if unknown:
            raise ValueError(
                f"{operation} payload has unknown fields: {', '.join(sorted(unknown))}"
            )


def _pointer_escape(value: object) -> str:
    return str(value).replace("~", "~0").replace("/", "~1")


def _required_evidence_paths(
    value: object,
    prefix: str = "",
    field_name: str = "",
) -> dict[str, object]:
    paths: dict[str, object] = {}
    if isinstance(value, bool):
        paths[prefix or "/"] = value
        return paths
    if isinstance(value, (int, float)):
        paths[prefix or "/"] = float(value)
        return paths
    if isinstance(value, str) and field_name.endswith("unit"):
        paths[prefix or "/"] = value
        return paths
    if isinstance(value, dict):
        for key, item in value.items():
            paths.update(
                _required_evidence_paths(
                    item,
                    f"{prefix}/{_pointer_escape(key)}",
                    str(key),
                )
            )
    elif isinstance(value, list):
        for index, item in enumerate(value):
            paths.update(
                _required_evidence_paths(item, f"{prefix}/{index}", field_name)
            )
    return paths


def _normalize_excerpt(value: str) -> str:
    return " ".join(value.casefold().split())


def _excerpt_contains_value(excerpt: str, expected: object) -> bool:
    if isinstance(expected, bool):
        normalized = _normalize_excerpt(excerpt)
        accepted = {"true", "vrai", "oui"} if expected else {"false", "faux", "non"}
        return any(token in normalized.split() for token in accepted)
    if isinstance(expected, str):
        return _normalize_excerpt(expected) in _normalize_excerpt(excerpt)
    for token in NUMBER_PATTERN.findall(excerpt):
        try:
            value = float(token.replace(",", "."))
        except ValueError:
            continue
        if isfinite(value) and isclose(
            value, float(expected), rel_tol=1e-12, abs_tol=1e-15
        ):
            return True
    return False


def _require_explicit_compiled_fields(request: CalculationRequest) -> None:
    payload = request.payload
    if request.operation == "uncertainty-study":
        required_payload = {
            "model",
            "influences",
            "type_a",
            "type_b",
            "correlations",
            "coverage_factor",
            "coverage_justification",
            "correlation_justification",
            "propagation_justification",
        }
        missing_payload = required_payload - set(payload)
        if missing_payload:
            raise ProvenanceValidationError(
                "compiled uncertainty study must explicitly declare: "
                + ", ".join(sorted(missing_payload))
            )
        model = payload.get("model")
        if not isinstance(model, dict):
            raise ProvenanceValidationError(
                "compiled uncertainty study requires an explicit model object"
            )
        if (
            not isinstance(model.get("output_unit"), str)
            or not model["output_unit"].strip()
        ):
            raise ProvenanceValidationError(
                "compiled uncertainty study requires a non-empty model output_unit"
            )
        influences = payload.get("influences")
        if not isinstance(influences, list) or not influences:
            raise ProvenanceValidationError(
                "compiled uncertainty study requires an explicit influence register"
            )
        type_a = payload.get("type_a")
        type_b = payload.get("type_b")
        if not isinstance(type_a, list) or not isinstance(type_b, list):
            raise ProvenanceValidationError(
                "compiled uncertainty study type_a and type_b must be explicit arrays"
            )
        if not type_a and not type_b:
            raise ProvenanceValidationError(
                "compiled uncertainty study requires at least one evaluated component"
            )
        correlations = payload.get("correlations")
        if not isinstance(correlations, list):
            raise ProvenanceValidationError(
                "compiled uncertainty study correlations must be an explicit array"
            )
        if not correlations and not any(
            "correl" in assumption.casefold() for assumption in request.assumptions
        ):
            raise ProvenanceValidationError(
                "an empty uncertainty-study correlation model requires an explicit assumption"
            )
    elif request.operation == "budget":
        required_payload = {
            "components",
            "correlations",
            "coverage_factor",
            "output_unit",
        }
        missing_payload = required_payload - set(payload)
        if missing_payload:
            raise ProvenanceValidationError(
                "compiled budget must explicitly declare: "
                + ", ".join(sorted(missing_payload))
            )
        if not isinstance(payload.get("output_unit"), str) or not payload[
            "output_unit"
        ].strip():
            raise ProvenanceValidationError(
                "compiled budget requires an explicit non-empty output_unit"
            )
        components = payload.get("components")
        if not isinstance(components, list) or not components:
            raise ProvenanceValidationError(
                "compiled budget requires at least one explicit component"
            )
        component_fields = {
            "name",
            "standard_uncertainty",
            "sensitivity",
            "sensitivity_unit",
            "owner",
            "unit",
            "distribution",
            "source",
            "degrees_of_freedom",
        }
        for index, component in enumerate(components):
            if not isinstance(component, dict):
                raise ProvenanceValidationError(
                    f"compiled budget component {index} must be an object"
                )
            missing = component_fields - set(component)
            if missing:
                raise ProvenanceValidationError(
                    f"compiled budget component {index} hides defaults for: "
                    + ", ".join(sorted(missing))
                )
            if not isinstance(component.get("unit"), str) or not component["unit"].strip():
                raise ProvenanceValidationError(
                    f"compiled budget component {index} requires an explicit non-empty unit"
                )
        correlations = payload.get("correlations")
        if not isinstance(correlations, list):
            raise ProvenanceValidationError(
                "compiled budget correlations must be an explicit array"
            )
        if not correlations and not any(
            token in assumption.casefold()
            for assumption in request.assumptions
            for token in ("correl", "corrél")
        ):
            raise ProvenanceValidationError(
                "an empty correlation model requires an explicit assumption"
            )
    elif request.operation == "compare":
        explicit = {
            "bench_value",
            "reference_value",
            "bench_standard_uncertainty",
            "reference_standard_uncertainty",
            "correlation",
            "correlation_justification",
            "unit",
        }
        missing = explicit - set(payload)
        if missing:
            raise ProvenanceValidationError(
                "compiled comparison hides defaults for: "
                + ", ".join(sorted(missing))
            )
        if not isinstance(payload.get("unit"), str) or not payload["unit"].strip():
            raise ProvenanceValidationError(
                "compiled comparison requires an explicit non-empty unit"
            )
        if payload.get("correlation") == 0 and not any(
            "correl" in assumption.casefold() for assumption in request.assumptions
        ):
            raise ProvenanceValidationError(
                "a zero comparison correlation requires an explicit assumption"
            )
    elif request.operation == "paired":
        missing = {"bench_readings", "reference_readings", "unit"} - set(payload)
        if missing:
            raise ProvenanceValidationError(
                "compiled paired analysis is missing: "
                + ", ".join(sorted(missing))
            )
        if not isinstance(payload.get("unit"), str) or not payload["unit"].strip():
            raise ProvenanceValidationError(
                "compiled paired analysis requires an explicit non-empty unit"
            )
    elif request.operation == "separate":
        explicit = {
            "difference_standard_uncertainty",
            "reference_standard_uncertainty",
            "covariance",
            "identifiability_confirmed",
            "identifiability_justification",
            "unit",
        }
        missing = explicit - set(payload)
        if missing:
            raise ProvenanceValidationError(
                "compiled separation hides defaults for: "
                + ", ".join(sorted(missing))
            )
        if not isinstance(payload.get("unit"), str) or not payload["unit"].strip():
            raise ProvenanceValidationError(
                "compiled separation requires an explicit non-empty unit"
            )


def validate_calculation_provenance(
    request: CalculationRequest,
    evidence_text: str = "",
    *,
    evidence_sources: dict[str, str] | None = None,
) -> tuple[str, tuple[str, ...]]:
    """Require auditable evidence for every critical compiled input value."""

    _require_explicit_compiled_fields(request)
    required_paths = _required_evidence_paths(request.payload)
    if not required_paths:
        raise ProvenanceValidationError(
            "compiled calculation contains no critical input to verify"
        )
    if not request.evidence:
        raise ProvenanceValidationError(
            "compiled calculation has no input evidence"
        )
    evidence_by_path: dict[str, InputEvidence] = {}
    for item in request.evidence:
        if item.field_path in evidence_by_path:
            raise ProvenanceValidationError(
                f"duplicate evidence for {item.field_path}"
            )
        if item.field_path not in required_paths:
            raise ProvenanceValidationError(
                f"evidence targets an unknown or non-critical field: {item.field_path}"
            )
        evidence_by_path[item.field_path] = item
    missing = sorted(set(required_paths) - set(evidence_by_path))
    if missing:
        raise ProvenanceValidationError(
            "critical inputs without evidence: " + ", ".join(missing)
        )
    trusted_sources = evidence_sources or {"user_request": evidence_text}
    if not isinstance(trusted_sources, dict) or not all(
        isinstance(key, str)
        and key.strip()
        and isinstance(value, str)
        for key, value in trusted_sources.items()
    ):
        raise TypeError("evidence_sources must map source references to text")
    warnings = []
    for path, item in evidence_by_path.items():
        excerpt = _normalize_excerpt(item.excerpt)
        if not _excerpt_contains_value(item.excerpt, required_paths[path]):
            raise ProvenanceValidationError(
                f"evidence excerpt for {path} does not contain its declared value"
            )
        if item.evidence_type in {"provided", "derived"}:
            source_text = trusted_sources.get(item.source_ref)
            if source_text is None:
                raise ProvenanceValidationError(
                    f"evidence source for {path} is not trusted: {item.source_ref}"
                )
            if excerpt not in _normalize_excerpt(source_text):
                raise ProvenanceValidationError(
                    f"evidence excerpt for {path} is absent from its trusted source"
                )
        else:
            if not item.source_ref.startswith("declared:"):
                raise ProvenanceValidationError(
                    f"declared evidence for {path} must use a declared: source_ref"
                )
            warnings.append(
                f"{path} uses declared {item.evidence_type}: {item.excerpt}"
            )
    status = "conditional" if warnings or request.assumptions else "verified"
    if request.assumptions:
        warnings.extend(
            f"declared assumption: {assumption}" for assumption in request.assumptions
        )
    return status, tuple(warnings)
