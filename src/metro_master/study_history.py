"""Historique append-only des études avec chaîne d'intégrité SHA-256."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any
from uuid import uuid4

from .validation import require_text


STUDY_ID_PATTERN = re.compile(r"^study-[a-z0-9][a-z0-9_-]{7,95}$")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_hash(value: dict[str, object]) -> str:
    return sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _study_id(value: object) -> str:
    identifier = require_text("study id", value)
    if not STUDY_ID_PATTERN.fullmatch(identifier):
        raise ValueError(
            "study id must start with 'study-' and contain 14 to 102 lowercase "
            "letters, digits, underscores or hyphens"
        )
    return identifier


@dataclass(frozen=True, slots=True)
class StudyReference:
    study_id: str
    revision: int
    integrity_sha256: str


@dataclass(frozen=True, slots=True)
class StudySnapshot:
    schema_version: int
    study_id: str
    revision: int
    created_at: str
    request: str
    orchestration: dict[str, Any]
    previous_sha256: str
    integrity_sha256: str

    @classmethod
    def from_dict(cls, value: object) -> "StudySnapshot":
        required = {
            "schema_version",
            "study_id",
            "revision",
            "created_at",
            "request",
            "orchestration",
            "previous_sha256",
            "integrity_sha256",
        }
        if not isinstance(value, dict) or set(value) != required:
            raise ValueError("invalid study snapshot structure")
        if value["schema_version"] != 1:
            raise ValueError("unsupported study snapshot schema")
        identifier = _study_id(value["study_id"])
        revision = value["revision"]
        if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
            raise ValueError("study revision must be a positive integer")
        created_at = require_text("study created_at", value["created_at"])
        try:
            datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("study created_at must be ISO-8601") from error
        request = require_text("study request", value["request"])
        orchestration = value["orchestration"]
        if not isinstance(orchestration, dict):
            raise TypeError("study orchestration must be an object")
        previous = require_text(
            "study previous_sha256", value["previous_sha256"], allow_empty=True
        )
        if previous and not re.fullmatch(r"[a-f0-9]{64}", previous):
            raise ValueError("study previous_sha256 is invalid")
        integrity = require_text("study integrity_sha256", value["integrity_sha256"])
        payload = {key: value[key] for key in required - {"integrity_sha256"}}
        if integrity != _canonical_hash(payload):
            raise ValueError(f"{identifier} revision {revision}: integrity mismatch")
        return cls(
            1,
            identifier,
            revision,
            created_at,
            request,
            orchestration,
            previous,
            integrity,
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class StudySummary:
    study_id: str
    latest_revision: int
    latest_created_at: str
    request: str
    integrity_sha256: str


class StudyStore:
    """Persistance locale versionnée ; aucune révision existante n'est écrasée."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _study_dir(self, study_id: str) -> Path:
        identifier = _study_id(study_id)
        path = (self.root / identifier).resolve()
        if path.parent != self.root:
            raise ValueError("study path escapes the configured root")
        return path

    @staticmethod
    def _revision_path(directory: Path, revision: int) -> Path:
        return directory / f"revision-{revision:06d}.json"

    def _new_id(self) -> str:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dt%H%M%S")
        return f"study-{stamp}-{uuid4().hex[:12]}"

    def revisions(self, study_id: str) -> tuple[StudySnapshot, ...]:
        directory = self._study_dir(study_id)
        if not directory.is_dir():
            raise KeyError(f"unknown study: {study_id}")
        snapshots = tuple(
            StudySnapshot.from_dict(json.loads(path.read_text(encoding="utf-8")))
            for path in sorted(directory.glob("revision-*.json"))
        )
        if not snapshots:
            raise ValueError(f"study has no revision: {study_id}")
        previous = ""
        for expected_revision, snapshot in enumerate(snapshots, start=1):
            if snapshot.revision != expected_revision:
                raise ValueError(f"study revision sequence is broken: {study_id}")
            if snapshot.previous_sha256 != previous:
                raise ValueError(f"study integrity chain is broken: {study_id}")
            previous = snapshot.integrity_sha256
        return snapshots

    def save(
        self,
        request: str,
        orchestration: dict[str, Any],
        *,
        study_id: str | None = None,
    ) -> StudyReference:
        request = require_text("study request", request)
        if not isinstance(orchestration, dict):
            raise TypeError("study orchestration must be an object")
        identifier = _study_id(study_id or self._new_id())
        directory = self._study_dir(identifier)
        directory.mkdir(parents=True, exist_ok=True)
        existing = (
            self.revisions(identifier)
            if any(directory.glob("revision-*.json"))
            else ()
        )
        revision = len(existing) + 1
        previous = existing[-1].integrity_sha256 if existing else ""
        payload: dict[str, object] = {
            "schema_version": 1,
            "study_id": identifier,
            "revision": revision,
            "created_at": _now(),
            "request": request,
            "orchestration": orchestration,
            "previous_sha256": previous,
        }
        integrity = _canonical_hash(payload)
        snapshot = StudySnapshot.from_dict(
            {**payload, "integrity_sha256": integrity}
        )
        path = self._revision_path(directory, revision)
        if path.exists():
            raise FileExistsError(f"study revision already exists: {path}")
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return StudyReference(identifier, revision, integrity)

    def load(self, study_id: str, revision: int | None = None) -> StudySnapshot:
        snapshots = self.revisions(study_id)
        if revision is None:
            return snapshots[-1]
        if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
            raise ValueError("study revision must be a positive integer")
        if revision > len(snapshots):
            raise KeyError(f"unknown study revision: {study_id}@{revision}")
        return snapshots[revision - 1]

    def list_studies(self) -> tuple[StudySummary, ...]:
        summaries = []
        for directory in sorted(path for path in self.root.iterdir() if path.is_dir()):
            if not STUDY_ID_PATTERN.fullmatch(directory.name):
                continue
            snapshots = self.revisions(directory.name)
            latest = snapshots[-1]
            summaries.append(
                StudySummary(
                    latest.study_id,
                    latest.revision,
                    latest.created_at,
                    latest.request,
                    latest.integrity_sha256,
                )
            )
        return tuple(summaries)
