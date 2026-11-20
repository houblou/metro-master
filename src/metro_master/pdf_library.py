"""Accès gouverné aux PDF locaux et extraction paginée vérifiable."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Protocol

from .validation import require_text


MAX_PAGES_PER_CHUNK = 20


class PdfExtractionUnavailableError(RuntimeError):
    """Le moteur PDF optionnel n'est pas installé."""


class PdfPageLike(Protocol):
    def extract_text(self) -> str | None: ...


class PdfReaderLike(Protocol):
    pages: list[PdfPageLike]


PdfReaderFactory = Callable[[str | Path], PdfReaderLike]


@dataclass(frozen=True, slots=True)
class PdfManifestRecord:
    id: str
    reference: str
    title: str
    relative_path: str
    source_url: str
    resolved_url: str
    status: str
    sha256: str
    rights: str
    message: str
    verified_at: str

    @classmethod
    def from_manifest_row(cls, row: dict[str, str]) -> "PdfManifestRecord":
        record = cls(
            id=row.get("id", ""),
            reference=row.get("reference", ""),
            title=row.get("titre", ""),
            relative_path=row.get("fichier", ""),
            source_url=row.get("source", ""),
            resolved_url=row.get("url_resolue", ""),
            status=row.get("statut", ""),
            sha256=row.get("sha256", ""),
            rights=row.get("droits", ""),
            message=row.get("message", ""),
            verified_at=row.get("verification", ""),
        )
        require_text("PDF record id", record.id)
        require_text("PDF relative path", record.relative_path)
        require_text("PDF sha256", record.sha256)
        if len(record.sha256) != 64 or any(
            character not in "0123456789abcdefABCDEF" for character in record.sha256
        ):
            raise ValueError(f"{record.id}: sha256 must contain 64 hexadecimal characters")
        return record

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ExtractedPdfPage:
    page_number: int
    text: str
    warning: str = ""


@dataclass(frozen=True, slots=True)
class PdfPageChunk:
    document_id: str
    reference: str
    title: str
    sha256: str
    rights: str
    total_pages: int
    start_page: int
    end_page: int
    pages: tuple[ExtractedPdfPage, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class GovernedPdfLibrary:
    def __init__(
        self,
        root: str | Path,
        records: Iterable[PdfManifestRecord],
        *,
        reader_factory: PdfReaderFactory | None = None,
    ) -> None:
        self.root = Path(root).resolve()
        self.records = tuple(records)
        self.reader_factory = reader_factory
        ids = [record.id for record in self.records]
        if len(ids) != len(set(ids)):
            raise ValueError("PDF manifest ids must be unique")

    @classmethod
    def from_source_roots(
        cls,
        source_roots_path: str | Path,
        *,
        source_id: str | None = None,
        reader_factory: PdfReaderFactory | None = None,
    ) -> "GovernedPdfLibrary":
        config_path = Path(source_roots_path)
        with config_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        sources = payload.get("sources")
        if not isinstance(sources, list) or not sources:
            raise ValueError("source-roots must contain a non-empty sources array")
        candidates = [
            item
            for item in sources
            if source_id is None or item.get("id") == source_id
        ]
        if len(candidates) != 1:
            raise ValueError("select exactly one governed PDF source")
        source = candidates[0]
        if source.get("access_mode") != "read_only":
            raise ValueError("PDF source must be registered as read_only")
        root = Path(require_text("root_path", source.get("root_path"))).resolve()
        manifest_relative = require_text("manifest_path", source.get("manifest_path"))
        manifest = (root / manifest_relative).resolve()
        cls._require_within_root(manifest, root, "manifest path")
        records = cls._load_manifest(manifest)
        return cls(root, records, reader_factory=reader_factory)

    @staticmethod
    def _load_manifest(path: Path) -> tuple[PdfManifestRecord, ...]:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=";")
            return tuple(PdfManifestRecord.from_manifest_row(row) for row in reader)

    @staticmethod
    def _require_within_root(path: Path, root: Path, label: str) -> None:
        if path != root and root not in path.parents:
            raise ValueError(f"{label} escapes governed source root")

    def search(self, query: str = "") -> tuple[PdfManifestRecord, ...]:
        tokens = query.casefold().split()
        matches = []
        for record in self.records:
            haystack = " ".join(
                [record.id, record.reference, record.title, record.status, record.message]
            ).casefold()
            if all(token in haystack for token in tokens):
                matches.append(record)
        return tuple(matches)

    def get(self, record_id: str) -> PdfManifestRecord:
        for record in self.records:
            if record.id == record_id:
                return record
        raise KeyError(f"unknown PDF record: {record_id}")

    def resolve_file(self, record: PdfManifestRecord) -> Path:
        relative = Path(*record.relative_path.replace("\\", "/").split("/"))
        if relative.is_absolute():
            candidate = relative.resolve()
        elif relative.parts and relative.parts[0].casefold() == self.root.name.casefold():
            candidate = (self.root.parent / relative).resolve()
        else:
            candidate = (self.root / relative).resolve()
        self._require_within_root(candidate, self.root, f"PDF path for {record.id}")
        return candidate

    def verify_file(self, record: PdfManifestRecord) -> bool:
        path = self.resolve_file(record)
        if not path.is_file():
            return False
        digest = sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest().casefold() == record.sha256.casefold()

    def iter_chunks(
        self,
        record_id: str,
        *,
        chunk_size: int = MAX_PAGES_PER_CHUNK,
    ) -> Iterator[PdfPageChunk]:
        if not 1 <= chunk_size <= MAX_PAGES_PER_CHUNK:
            raise ValueError(
                f"chunk_size must be between 1 and {MAX_PAGES_PER_CHUNK} pages"
            )
        record = self.get(record_id)
        path = self.resolve_file(record)
        if not path.is_file():
            raise FileNotFoundError(f"PDF file is unavailable: {record.relative_path}")
        if not self.verify_file(record):
            raise ValueError(f"{record.id}: local PDF sha256 does not match the manifest")
        reader_factory = self.reader_factory or self._default_reader_factory()
        reader = reader_factory(path)
        total_pages = len(reader.pages)
        for start_index in range(0, total_pages, chunk_size):
            page_items = []
            end_index = min(start_index + chunk_size, total_pages)
            for index in range(start_index, end_index):
                text = reader.pages[index].extract_text() or ""
                warning = "" if text.strip() else "No extractable text on this page."
                page_items.append(ExtractedPdfPage(index + 1, text, warning))
            yield PdfPageChunk(
                document_id=record.id,
                reference=record.reference,
                title=record.title,
                sha256=record.sha256,
                rights=record.rights,
                total_pages=total_pages,
                start_page=start_index + 1,
                end_page=end_index,
                pages=tuple(page_items),
            )

    @staticmethod
    def _default_reader_factory() -> PdfReaderFactory:
        try:
            from pypdf import PdfReader
        except ImportError as error:
            raise PdfExtractionUnavailableError(
                'PDF extraction requires the optional dependency: pip install "metro-master[pdf]"'
            ) from error
        return PdfReader
