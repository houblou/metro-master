"""Traces canoniques et vérifiables des calculs déterministes."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import platform
from typing import Any, Mapping

from .version import __version__


TRACE_SCHEMA_VERSION = 1


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def canonical_sha256(value: object) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class CalculationTrace:
    schema_version: int
    trace_id: str
    created_at: str
    execution_origin: str
    request_sha256: str
    payload_sha256: str
    operation: str
    module: dict[str, object]
    engine: dict[str, object]
    evidence: tuple[dict[str, str], ...]
    assumptions: tuple[str, ...]
    execution: dict[str, object]
    status: str
    result_sha256: str
    error_type: str
    error: str
    previous_trace_sha256: str
    trace_sha256: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def verify(self) -> None:
        payload = self.to_dict()
        integrity = str(payload.pop("trace_sha256"))
        payload.pop("created_at")
        if integrity != canonical_sha256(payload):
            raise ValueError(f"calculation trace integrity mismatch: {self.trace_id}")


def _evidence_digests(request: Mapping[str, Any]) -> tuple[dict[str, str], ...]:
    digests = []
    for item in request.get("evidence", ()):
        if not isinstance(item, Mapping):
            continue
        digests.append(
            {
                "field_path": str(item.get("field_path", "")),
                "source_ref": str(item.get("source_ref", "")),
                "evidence_type": str(item.get("evidence_type", "")),
                "excerpt_sha256": canonical_sha256(str(item.get("excerpt", ""))),
            }
        )
    return tuple(digests)


def build_calculation_trace(
    *,
    request: Mapping[str, Any],
    module: Mapping[str, object],
    status: str,
    result: Mapping[str, object] | None,
    execution_origin: str,
    provenance_required: bool,
    provenance_status: str,
    previous_trace_sha256: str = "",
    error_type: str = "",
    error: str = "",
) -> CalculationTrace:
    request_value = dict(request)
    request_hash = canonical_sha256(request_value)
    result_hash = canonical_sha256(dict(result)) if result is not None else ""
    payload: dict[str, object] = {
        "schema_version": TRACE_SCHEMA_VERSION,
        "trace_id": f"calc-{request_hash[:20]}",
        "execution_origin": execution_origin,
        "request_sha256": request_hash,
        "payload_sha256": canonical_sha256(request_value.get("payload", {})),
        "operation": str(request_value.get("operation", "")),
        "module": dict(module),
        "engine": {
            "metrology_lab_ai_version": __version__,
            "python_version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "dependencies": {},
        },
        "evidence": _evidence_digests(request_value),
        "assumptions": tuple(str(item) for item in request_value.get("assumptions", ())),
        "execution": {
            "deterministic": True,
            "provenance_required": provenance_required,
            "provenance_status": provenance_status,
            "seed": None,
            "rng": None,
            "tolerances": {},
            "convergence": None,
        },
        "status": status,
        "result_sha256": result_hash,
        "error_type": error_type,
        "error": error,
        "previous_trace_sha256": previous_trace_sha256,
    }
    integrity = canonical_sha256(payload)
    trace = CalculationTrace(
        created_at=datetime.now(timezone.utc).isoformat(),
        trace_sha256=integrity,
        **payload,
    )
    trace.verify()
    return trace
