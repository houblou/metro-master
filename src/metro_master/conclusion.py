"""Vérification déterministe des affirmations numériques d'une conclusion LLM."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isclose, isfinite
from typing import Any, Iterable

from .validation import require_text


MAX_CONCLUSION_CLAIMS = 64


@dataclass(frozen=True, slots=True)
class ConclusionClaim:
    request_id: str
    result_pointer: str
    stated_value: float
    statement: str
    unit: str = ""

    def __post_init__(self) -> None:
        require_text("conclusion request_id", self.request_id)
        pointer = require_text("conclusion result_pointer", self.result_pointer)
        if not pointer.startswith("/"):
            raise ValueError("conclusion result_pointer must be a JSON Pointer")
        if isinstance(self.stated_value, bool) or not isinstance(
            self.stated_value, (int, float)
        ):
            raise TypeError("conclusion stated_value must be numeric")
        if not isfinite(float(self.stated_value)):
            raise ValueError("conclusion stated_value must be finite")
        require_text("conclusion statement", self.statement)
        require_text("conclusion unit", self.unit, allow_empty=True)

    @classmethod
    def from_dict(cls, value: object) -> "ConclusionClaim":
        if not isinstance(value, dict):
            raise TypeError("each conclusion claim must be an object")
        required = {"request_id", "result_pointer", "stated_value", "statement"}
        optional = {"unit"}
        missing = required - set(value)
        unknown = set(value) - required - optional
        if missing:
            raise ValueError(
                f"conclusion claim is missing fields: {', '.join(sorted(missing))}"
            )
        if unknown:
            raise ValueError(
                f"conclusion claim has unknown fields: {', '.join(sorted(unknown))}"
            )
        return cls(
            request_id=value["request_id"],
            result_pointer=value["result_pointer"],
            stated_value=value["stated_value"],
            statement=value["statement"],
            unit=value.get("unit", ""),
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ClaimVerification:
    claim: ConclusionClaim
    status: str
    actual_value: float | None = None
    absolute_error: float | None = None
    error: str = ""


@dataclass(frozen=True, slots=True)
class ConclusionVerificationReport:
    status: str
    claims: tuple[ClaimVerification, ...]
    successful_calculation_ids: tuple[str, ...]
    rejected_calculation_ids: tuple[str, ...]
    uncovered_calculation_ids: tuple[str, ...]
    scope: str = "numeric_claims_only"
    semantic_review_required: bool = True

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CompletionReport:
    verdict: str
    issues: tuple[str, ...]
    calculation_count: int
    traced_calculation_count: int
    audit_present: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _unescape_pointer_token(token: str) -> str:
    return token.replace("~1", "/").replace("~0", "~")


def resolve_json_pointer(value: object, pointer: str) -> object:
    current = value
    for raw_token in pointer.split("/")[1:]:
        token = _unescape_pointer_token(raw_token)
        if isinstance(current, dict):
            if token not in current:
                raise KeyError(f"result pointer does not exist: {pointer}")
            current = current[token]
        elif isinstance(current, (list, tuple)):
            try:
                index = int(token)
            except ValueError as error:
                raise KeyError(f"invalid array index in result pointer: {pointer}") from error
            if index < 0 or index >= len(current):
                raise KeyError(f"array index outside result pointer: {pointer}")
            current = current[index]
        else:
            raise KeyError(f"result pointer traverses a scalar: {pointer}")
    return current


def verify_conclusion(turns: Iterable[Any]) -> ConclusionVerificationReport:
    calculations: dict[str, list[Any]] = {}
    rejected_ids = []
    all_turns = tuple(turns)
    for turn in all_turns:
        for record in turn.calculations:
            calculations.setdefault(record.request.id, []).append(record)
            if record.status != "ok":
                rejected_ids.append(record.request.id)

    successful_ids = tuple(
        sorted(
            identifier
            for identifier, records in calculations.items()
            if len(records) == 1 and records[0].status == "ok"
        )
    )
    final_claims = all_turns[-1].conclusion_claims if all_turns else ()
    if not calculations and not final_claims:
        return ConclusionVerificationReport(
            "not_applicable", (), (), (), ()
        )
    if calculations and not final_claims:
        return ConclusionVerificationReport(
            "unverified",
            (),
            successful_ids,
            tuple(sorted(set(rejected_ids))),
            successful_ids,
        )

    verifications = []
    covered = set()
    for claim in final_claims:
        records = calculations.get(claim.request_id, [])
        if not records:
            verifications.append(
                ClaimVerification(
                    claim,
                    "failed",
                    error="claim references an unknown calculation request",
                )
            )
            continue
        if len(records) != 1:
            verifications.append(
                ClaimVerification(
                    claim,
                    "failed",
                    error="calculation request id is ambiguous across turns",
                )
            )
            continue
        record = records[0]
        if record.status != "ok" or record.result is None:
            verifications.append(
                ClaimVerification(
                    claim,
                    "failed",
                    error="claim references a rejected calculation",
                )
            )
            continue
        try:
            actual = resolve_json_pointer(record.result, claim.result_pointer)
        except KeyError as error:
            verifications.append(
                ClaimVerification(claim, "failed", error=str(error))
            )
            continue
        if isinstance(actual, bool) or not isinstance(actual, (int, float)):
            verifications.append(
                ClaimVerification(
                    claim,
                    "failed",
                    error="result pointer does not reference a numeric value",
                )
            )
            continue
        actual_value = float(actual)
        stated = float(claim.stated_value)
        error_value = abs(actual_value - stated)
        matches = isclose(actual_value, stated, rel_tol=1e-9, abs_tol=1e-12)
        actual_unit = str(record.result.get("unit", ""))
        unit_matches = not claim.unit or claim.unit == actual_unit
        failure = ""
        if not matches:
            failure = "stated value differs from deterministic result"
        elif not unit_matches:
            failure = (
                f"stated unit {claim.unit!r} differs from deterministic unit "
                f"{actual_unit!r}"
            )
        verifications.append(
            ClaimVerification(
                claim,
                "verified" if matches and unit_matches else "failed",
                actual_value=actual_value,
                absolute_error=error_value,
                error=failure,
            )
        )
        if matches and unit_matches:
            covered.add(claim.request_id)

    uncovered = tuple(sorted(set(successful_ids) - covered))
    status = (
        "verified"
        if verifications
        and all(item.status == "verified" for item in verifications)
        and not uncovered
        else "failed"
    )
    return ConclusionVerificationReport(
        status,
        tuple(verifications),
        successful_ids,
        tuple(sorted(set(rejected_ids))),
        uncovered,
    )


def evaluate_completion(
    turns: Iterable[Any],
    verification: ConclusionVerificationReport,
    *,
    required_agents: Iterable[str] = (),
    actual_agents: Iterable[str] = (),
) -> CompletionReport:
    """Convertit les contrôles techniques en verdict final non contournable."""

    all_turns = tuple(turns)
    calculations = tuple(
        record for turn in all_turns for record in getattr(turn, "calculations", ())
    )
    issues: list[str] = []
    audit_present = bool(all_turns and all_turns[-1].agent == "METRO-AUDIT")
    if not audit_present:
        issues.append("METRO-AUDIT est absent ou n'est pas le dernier rôle exécuté")

    required = set(required_agents)
    actual = set(actual_agents)
    missing_critical = sorted(
        required.intersection({"MODEL-COMPILER", "METRO-AUDIT"}) - actual
    )
    if missing_critical:
        issues.append("rôles critiques omis: " + ", ".join(missing_critical))

    traced = 0
    invalid_trace = False
    rejected = False
    conditional = False
    for record in calculations:
        if record.status != "ok":
            rejected = True
            issues.append(
                f"calcul {record.request.id} rejeté: {record.error_type or 'erreur'}"
            )
        if record.provenance_status == "conditional":
            conditional = True
        if record.trace is None:
            invalid_trace = True
            issues.append(f"calcul {record.request.id} sans trace canonique")
            continue
        try:
            record.trace.verify()
            traced += 1
        except ValueError:
            invalid_trace = True
            issues.append(f"trace invalide pour le calcul {record.request.id}")

    if verification.status == "failed":
        issues.append("la conclusion diverge des résultats déterministes")
    elif verification.status == "unverified":
        issues.append("des calculs réussis ne sont pas couverts par METRO-AUDIT")

    if rejected or invalid_trace or verification.status == "failed":
        verdict = "NON VALIDE"
    elif not audit_present or missing_critical or verification.status == "unverified":
        verdict = "INCOMPLET"
    elif verification.status == "verified":
        verdict = "VALIDÉ SOUS CONDITIONS" if conditional else "VALIDÉ"
    else:
        verdict = "VALIDÉ SOUS CONDITIONS"
        issues.append("aucun résultat numérique ne relève du vérificateur de claims")

    return CompletionReport(
        verdict,
        tuple(dict.fromkeys(issues)),
        len(calculations),
        traced,
        audit_present,
    )
