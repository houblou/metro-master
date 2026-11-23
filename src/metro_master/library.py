"""Catalogue documentaire avec états d'accès non ambigus."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
import json
from pathlib import Path
from typing import Any, Iterable


VALID_CONTENT_STATUS = {"metadata_only", "excerpt_provided", "full_text_provided"}


@dataclass(frozen=True, slots=True)
class DocumentRecord:
    id: str
    reference: str
    title: str
    publisher: str
    family: str
    edition: str
    publication_date: str
    status: str
    official_url: str
    topics: tuple[str, ...]
    agents: tuple[str, ...]
    content_status: str
    verified_at: str
    local_path: str | None
    sha256: str | None
    notes: str

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "DocumentRecord":
        data = dict(value)
        data["topics"] = tuple(data.get("topics", ()))
        data["agents"] = tuple(data.get("agents", ()))
        record = cls(**data)
        if record.content_status not in VALID_CONTENT_STATUS:
            raise ValueError(f"invalid content_status for {record.id}")
        if record.content_status != "metadata_only" and (
            not record.local_path or not record.sha256
        ):
            raise ValueError(f"{record.id}: provided content requires local_path and sha256")
        return record

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "reference": self.reference,
            "title": self.title,
            "publisher": self.publisher,
            "family": self.family,
            "edition": self.edition,
            "publication_date": self.publication_date,
            "status": self.status,
            "official_url": self.official_url,
            "topics": list(self.topics),
            "agents": list(self.agents),
            "content_status": self.content_status,
            "verified_at": self.verified_at,
            "local_path": self.local_path,
            "sha256": self.sha256,
            "notes": self.notes,
        }


class DocumentLibrary:
    def __init__(self, records: Iterable[DocumentRecord]) -> None:
        self.records = tuple(records)
        ids = [record.id for record in self.records]
        if len(ids) != len(set(ids)):
            raise ValueError("document ids must be unique")

    @classmethod
    def load_default(cls) -> "DocumentLibrary":
        resource = files("metro_master").joinpath("resources/library/catalog.json")
        with resource.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return cls(DocumentRecord.from_dict(item) for item in payload["documents"])

    @classmethod
    def load(cls, path: str | Path) -> "DocumentLibrary":
        with Path(path).open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return cls(DocumentRecord.from_dict(item) for item in payload["documents"])

    def search(self, query: str = "", publisher: str = "") -> tuple[DocumentRecord, ...]:
        query = query.casefold().strip()
        publisher = publisher.casefold().strip()
        matches = []
        for record in self.records:
            haystack = " ".join(
                [record.reference, record.title, record.family, *record.topics, record.notes]
            ).casefold()
            if query and query not in haystack:
                continue
            if publisher and publisher not in record.publisher.casefold():
                continue
            matches.append(record)
        return tuple(matches)

    @staticmethod
    def verify_local_file(record: DocumentRecord, project_root: str | Path) -> bool:
        if record.content_status == "metadata_only" or not record.local_path or not record.sha256:
            return False
        path = Path(project_root, record.local_path).resolve()
        root = Path(project_root).resolve()
        if root != path and root not in path.parents:
            raise ValueError("local document path escapes project root")
        if not path.is_file():
            return False
        digest = sha256(path.read_bytes()).hexdigest()
        return digest.casefold() == record.sha256.casefold()

