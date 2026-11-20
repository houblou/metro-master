"""Mémoire locale gouvernée, recherchable et distincte de l'entraînement du modèle."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Iterable

from .research import ResearchSource
from .validation import require_text


KNOWLEDGE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{2,95}$")
TOKEN_PATTERN = re.compile(r"[\wµ°%-]+", re.UNICODE)
STOP_WORDS = frozenset(
    {
        "and",
        "avec",
        "dans",
        "des",
        "for",
        "les",
        "pour",
        "sur",
        "the",
        "une",
    }
)
VALID_ORIGINS = frozenset(
    {
        "web_source",
        "local_document",
        "calculation",
        "module",
        "human_note",
        "agent_inference",
    }
)
VALID_STATUSES = frozenset({"candidate", "validated", "superseded"})
MAX_KNOWLEDGE_BODY_LENGTH = 100_000


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(
        token
        for token in (item.casefold() for item in TOKEN_PATTERN.findall(text))
        if len(token) >= 3 and token not in STOP_WORDS
    )


def _strict_object(
    value: object,
    *,
    required: set[str],
    optional: set[str] = frozenset(),
    label: str,
) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError(f"{label} must be an object")
    missing = required - set(value)
    unknown = set(value) - required - optional
    if missing:
        raise ValueError(f"{label} is missing fields: {', '.join(sorted(missing))}")
    if unknown:
        raise ValueError(f"{label} has unknown fields: {', '.join(sorted(unknown))}")
    return value


def _knowledge_id(value: object) -> str:
    identifier = require_text("knowledge id", value)
    if not KNOWLEDGE_ID_PATTERN.fullmatch(identifier):
        raise ValueError(
            "knowledge id must start with a lowercase letter and contain 3 to 96 "
            "lowercase letters, digits, underscores or hyphens"
        )
    return identifier


@dataclass(frozen=True, slots=True)
class KnowledgeEvent:
    action: str
    actor: str
    at: str
    reason: str = ""


@dataclass(frozen=True, slots=True)
class KnowledgeRecord:
    schema_version: int
    id: str
    title: str
    body: str
    origin: str
    source_ref: str
    source_sha256: str
    tags: tuple[str, ...]
    content_sha256: str
    status: str
    events: tuple[KnowledgeEvent, ...]
    record_sha256: str

    @staticmethod
    def compute_integrity(
        *,
        title: str,
        body: str,
        origin: str,
        source_ref: str,
        source_sha256: str,
        tags: Iterable[str],
    ) -> str:
        canonical = json.dumps(
            {
                "title": title,
                "body": body,
                "origin": origin,
                "source_ref": source_ref,
                "source_sha256": source_sha256,
                "tags": list(tags),
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return sha256(canonical).hexdigest()

    @staticmethod
    def compute_record_integrity(
        *,
        content_sha256: str,
        status: str,
        events: Iterable[KnowledgeEvent],
    ) -> str:
        canonical = json.dumps(
            {
                "content_sha256": content_sha256,
                "status": status,
                "events": [asdict(event) for event in events],
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return sha256(canonical).hexdigest()

    @classmethod
    def from_dict(cls, value: object) -> "KnowledgeRecord":
        data = _strict_object(
            value,
            required={
                "schema_version",
                "id",
                "title",
                "body",
                "origin",
                "source_ref",
                "source_sha256",
                "tags",
                "content_sha256",
                "status",
                "events",
                "record_sha256",
            },
            label="knowledge record",
        )
        if data["schema_version"] != 1:
            raise ValueError("only knowledge schema_version 1 is supported")
        identifier = _knowledge_id(data["id"])
        title = require_text("knowledge title", data["title"])
        body = require_text("knowledge body", data["body"])
        if len(body) > MAX_KNOWLEDGE_BODY_LENGTH:
            raise ValueError(
                f"knowledge body exceeds {MAX_KNOWLEDGE_BODY_LENGTH} characters"
            )
        origin = require_text("knowledge origin", data["origin"])
        if origin not in VALID_ORIGINS:
            raise ValueError(f"invalid knowledge origin: {origin}")
        source_ref = require_text("knowledge source_ref", data["source_ref"])
        source_sha256 = require_text(
            "knowledge source_sha256", data["source_sha256"], allow_empty=True
        )
        if source_sha256 and not re.fullmatch(r"[a-f0-9]{64}", source_sha256):
            raise ValueError("knowledge source_sha256 must be empty or 64 lowercase hex digits")
        raw_tags = data["tags"]
        if not isinstance(raw_tags, (list, tuple)) or not all(
            isinstance(item, str) and item.strip() for item in raw_tags
        ):
            raise TypeError("knowledge tags must be an array of non-empty strings")
        tags = tuple(dict.fromkeys(item.casefold().strip() for item in raw_tags))
        content_sha256 = require_text(
            "knowledge content_sha256", data["content_sha256"]
        )
        expected = cls.compute_integrity(
            title=title,
            body=body,
            origin=origin,
            source_ref=source_ref,
            source_sha256=source_sha256,
            tags=tags,
        )
        if content_sha256 != expected:
            raise ValueError(f"{identifier}: knowledge integrity mismatch")
        status = require_text("knowledge status", data["status"])
        if status not in VALID_STATUSES:
            raise ValueError(f"invalid knowledge status: {status}")
        raw_events = data["events"]
        if not isinstance(raw_events, (list, tuple)) or not raw_events:
            raise ValueError("knowledge events must be a non-empty array")
        events = []
        for item in raw_events:
            event = _strict_object(
                item,
                required={"action", "actor", "at", "reason"},
                label="knowledge event",
            )
            events.append(
                KnowledgeEvent(
                    require_text("knowledge event action", event["action"]),
                    require_text("knowledge event actor", event["actor"]),
                    require_text("knowledge event timestamp", event["at"]),
                    require_text(
                        "knowledge event reason", event["reason"], allow_empty=True
                    ),
                )
            )
        if events[0].action != "submitted":
            raise ValueError("knowledge lifecycle must start with a submitted event")
        allowed_actions = {"submitted", "promoted", "superseded"}
        if any(event.action not in allowed_actions for event in events):
            raise ValueError("knowledge lifecycle contains an unknown action")
        expected_last_action = {
            "candidate": "submitted",
            "validated": "promoted",
            "superseded": "superseded",
        }[status]
        if events[-1].action != expected_last_action:
            raise ValueError(
                f"knowledge status {status} is inconsistent with its last event"
            )
        record_sha256 = require_text(
            "knowledge record_sha256", data["record_sha256"]
        )
        expected_record_sha256 = cls.compute_record_integrity(
            content_sha256=content_sha256,
            status=status,
            events=events,
        )
        if record_sha256 != expected_record_sha256:
            raise ValueError(f"{identifier}: knowledge lifecycle integrity mismatch")
        return cls(
            1,
            identifier,
            title,
            body,
            origin,
            source_ref,
            source_sha256,
            tags,
            content_sha256,
            status,
            tuple(events),
            record_sha256,
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class KnowledgeHit:
    record: KnowledgeRecord
    score: float
    matched_terms: tuple[str, ...]

    def to_dict(self, *, body_limit: int | None = None) -> dict[str, object]:
        record = self.record.to_dict()
        truncated = False
        if body_limit is not None and len(self.record.body) > body_limit:
            record["body"] = self.record.body[:body_limit] + "… [truncated]"
            truncated = True
        return {
            "score": self.score,
            "matched_terms": list(self.matched_terms),
            "body_truncated": truncated,
            "body_original_length": len(self.record.body),
            "record": record,
        }


class KnowledgeStore:
    """Registre local intègre. Les ajouts automatiques restent candidats."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, identifier: str) -> Path:
        identifier = _knowledge_id(identifier)
        path = (self.root / f"{identifier}.json").resolve()
        if path.parent != self.root:
            raise ValueError("knowledge path escapes the configured root")
        return path

    def _write(self, record: KnowledgeRecord) -> None:
        path = self._path(record.id)
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(record.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    def load(self, identifier: str) -> KnowledgeRecord:
        path = self._path(identifier)
        if not path.is_file():
            raise KeyError(f"unknown knowledge record: {identifier}")
        return KnowledgeRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list_records(self) -> tuple[KnowledgeRecord, ...]:
        records = []
        for path in sorted(self.root.glob("*.json")):
            records.append(
                KnowledgeRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))
            )
        return tuple(records)

    def add(
        self,
        *,
        title: str,
        body: str,
        origin: str,
        source_ref: str,
        source_sha256: str = "",
        tags: Iterable[str] = (),
        created_by: str,
        identifier: str | None = None,
    ) -> KnowledgeRecord:
        title = require_text("knowledge title", title)
        body = require_text("knowledge body", body)
        if len(body) > MAX_KNOWLEDGE_BODY_LENGTH:
            raise ValueError(
                f"knowledge body exceeds {MAX_KNOWLEDGE_BODY_LENGTH} characters"
            )
        origin = require_text("knowledge origin", origin)
        if origin not in VALID_ORIGINS:
            raise ValueError(f"invalid knowledge origin: {origin}")
        source_ref = require_text("knowledge source_ref", source_ref)
        if source_sha256 and not re.fullmatch(r"[a-f0-9]{64}", source_sha256):
            raise ValueError("knowledge source_sha256 must be empty or 64 lowercase hex digits")
        if isinstance(tags, (str, bytes)):
            raise TypeError("knowledge tags must be an iterable of strings")
        normalized_tags = tuple(
            dict.fromkeys(require_text("knowledge tag", item).casefold() for item in tags)
        )
        integrity = KnowledgeRecord.compute_integrity(
            title=title,
            body=body,
            origin=origin,
            source_ref=source_ref,
            source_sha256=source_sha256,
            tags=normalized_tags,
        )
        identifier = identifier or f"{origin.replace('_', '-')}-{integrity[:16]}"
        identifier = _knowledge_id(identifier)
        path = self._path(identifier)
        if path.exists():
            existing = self.load(identifier)
            if existing.content_sha256 != integrity:
                raise ValueError(f"knowledge id already exists with different content: {identifier}")
            return existing
        for existing in self.list_records():
            if existing.content_sha256 == integrity:
                return existing
        events = (
            KnowledgeEvent(
                "submitted", require_text("created_by", created_by), _now()
            ),
        )
        status = "candidate"
        record = KnowledgeRecord(
            1,
            identifier,
            title,
            body,
            origin,
            source_ref,
            source_sha256,
            normalized_tags,
            integrity,
            status,
            events,
            KnowledgeRecord.compute_record_integrity(
                content_sha256=integrity,
                status=status,
                events=events,
            ),
        )
        self._write(record)
        return record

    def add_research_source(
        self,
        source: ResearchSource,
        *,
        request_id: str,
    ) -> KnowledgeRecord:
        return self.add(
            title=source.title,
            body=source.summary,
            origin="web_source",
            source_ref=source.url,
            source_sha256=source.content_sha256,
            tags=(
                source.publisher or "unknown-publisher",
                source.source_type,
                "web-research",
            ),
            created_by=f"research-provider:{request_id}",
        )

    def promote(
        self, identifier: str, *, approved_by: str, reason: str
    ) -> KnowledgeRecord:
        record = self.load(identifier)
        if record.status == "superseded":
            raise ValueError("a superseded knowledge record cannot be promoted")
        if record.status == "validated":
            raise ValueError("knowledge record is already validated")
        event = KnowledgeEvent(
            "promoted",
            require_text("approved_by", approved_by),
            _now(),
            require_text("promotion reason", reason),
        )
        events = (*record.events, event)
        updated = replace(
            record,
            status="validated",
            events=events,
            record_sha256=KnowledgeRecord.compute_record_integrity(
                content_sha256=record.content_sha256,
                status="validated",
                events=events,
            ),
        )
        self._write(updated)
        return updated

    def supersede(
        self, identifier: str, *, approved_by: str, reason: str
    ) -> KnowledgeRecord:
        record = self.load(identifier)
        if record.status == "superseded":
            raise ValueError("knowledge record is already superseded")
        event = KnowledgeEvent(
            "superseded",
            require_text("approved_by", approved_by),
            _now(),
            require_text("supersession reason", reason),
        )
        events = (*record.events, event)
        updated = replace(
            record,
            status="superseded",
            events=events,
            record_sha256=KnowledgeRecord.compute_record_integrity(
                content_sha256=record.content_sha256,
                status="superseded",
                events=events,
            ),
        )
        self._write(updated)
        return updated

    def search(
        self,
        query: str,
        *,
        include_candidates: bool = False,
        limit: int = 5,
    ) -> tuple[KnowledgeHit, ...]:
        query = require_text("knowledge query", query)
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 50:
            raise ValueError("knowledge search limit must be between 1 and 50")
        query_terms = tuple(dict.fromkeys(_tokens(query)))
        hits = []
        for record in self.list_records():
            if record.status == "superseded":
                continue
            if record.status != "validated" and not include_candidates:
                continue
            title_tokens = _tokens(record.title)
            tag_tokens = _tokens(" ".join(record.tags))
            source_tokens = _tokens(record.source_ref)
            body_tokens = _tokens(record.body)
            matched = tuple(
                term
                for term in query_terms
                if term in title_tokens
                or term in tag_tokens
                or term in source_tokens
                or term in body_tokens
            )
            if not matched:
                continue
            score = sum(
                4.0 * title_tokens.count(term)
                + 3.0 * tag_tokens.count(term)
                + 2.0 * source_tokens.count(term)
                + min(3, body_tokens.count(term))
                for term in matched
            )
            score += 2.0 * len(matched) / len(query_terms)
            if query.casefold() in record.title.casefold():
                score += 5.0
            hits.append(KnowledgeHit(record, round(score, 6), matched))
        hits.sort(key=lambda item: (-item.score, item.record.id))
        return tuple(hits[:limit])
