"""RAG hybride avec index vectoriel persistant et fournisseur d'embeddings remplaçable."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite, sqrt
from pathlib import Path
import re
from typing import Callable, Protocol, Sequence

from .knowledge import KnowledgeRecord, KnowledgeStore


TOKEN_PATTERN = re.compile(r"[\wµ°%-]+", re.UNICODE)
DEFAULT_DIMENSIONS = 384


class EmbeddingProvider(Protocol):
    id: str
    dimensions: int

    def embed(self, texts: Sequence[str]) -> Sequence[Sequence[float]]: ...


class CallableEmbeddingProvider:
    """Adaptateur vers un modèle d'embedding local ou distant."""

    def __init__(
        self,
        identifier: str,
        dimensions: int,
        handler: Callable[[Sequence[str]], Sequence[Sequence[float]]],
    ) -> None:
        if not identifier.strip():
            raise ValueError("embedding provider id must not be empty")
        if not 8 <= dimensions <= 16_384:
            raise ValueError("embedding dimensions must be between 8 and 16384")
        self.id = identifier
        self.dimensions = dimensions
        self._handler = handler

    def embed(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        return self._handler(texts)


class HashingEmbeddingProvider:
    """Embedding vectoriel local reproductible, lexical et sans dépendance externe.

    Il sert de repli hors ligne. Pour une proximité réellement sémantique, injecter un
    modèle d'embedding via ``CallableEmbeddingProvider``.
    """

    id = "hashing-word-bigram-v1"

    def __init__(self, dimensions: int = DEFAULT_DIMENSIONS) -> None:
        if not 64 <= dimensions <= 4_096:
            raise ValueError("hashing embedding dimensions must be between 64 and 4096")
        self.dimensions = dimensions

    @staticmethod
    def _features(text: str) -> tuple[str, ...]:
        tokens = [
            token.casefold()
            for token in TOKEN_PATTERN.findall(text)
            if len(token) >= 2
        ]
        bigrams = [f"{left}::{right}" for left, right in zip(tokens, tokens[1:])]
        return tuple([*tokens, *bigrams])

    def embed(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        vectors = []
        for text in texts:
            vector = [0.0] * self.dimensions
            for feature in self._features(text):
                digest = sha256(feature.encode("utf-8")).digest()
                index = int.from_bytes(digest[:8], "big") % self.dimensions
                sign = 1.0 if digest[8] & 1 else -1.0
                vector[index] += sign
            vectors.append(_normalize(vector))
        return vectors


def _normalize(vector: Sequence[float]) -> tuple[float, ...]:
    values = []
    for item in vector:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise TypeError("embedding values must be numbers")
        value = float(item)
        if not isfinite(value):
            raise ValueError("embedding values must be finite")
        values.append(value)
    norm = sqrt(sum(item * item for item in values))
    if norm == 0.0:
        return tuple(0.0 for _ in values)
    return tuple(item / norm for item in values)


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("embedding dimensions do not match")
    return sum(a * b for a, b in zip(left, right))


def _record_text(record: KnowledgeRecord) -> str:
    return "\n".join(
        (
            record.title,
            " ".join(record.tags),
            record.source_ref,
            record.body,
        )
    )


@dataclass(frozen=True, slots=True)
class VectorEntry:
    knowledge_id: str
    content_sha256: str
    vector: tuple[float, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class VectorHit:
    record: KnowledgeRecord
    vector_score: float


@dataclass(frozen=True, slots=True)
class RagHit:
    record: KnowledgeRecord
    score: float
    vector_score: float
    lexical_score: float
    matched_terms: tuple[str, ...]

    def to_dict(self, *, body_limit: int | None = None) -> dict[str, object]:
        record = self.record.to_dict()
        truncated = False
        if body_limit is not None and len(self.record.body) > body_limit:
            record["body"] = self.record.body[:body_limit] + "… [truncated]"
            truncated = True
        return {
            "retrieval_mode": "hybrid_vector_lexical",
            "score": self.score,
            "vector_score": self.vector_score,
            "lexical_score": self.lexical_score,
            "matched_terms": list(self.matched_terms),
            "body_truncated": truncated,
            "body_original_length": len(self.record.body),
            "record": record,
        }


class VectorKnowledgeIndex:
    """Index vectoriel JSON persistant, reconstruit si modèle ou contenu change."""

    def __init__(
        self,
        root: str | Path,
        provider: EmbeddingProvider | None = None,
    ) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "index.json"
        self.provider = provider or HashingEmbeddingProvider()

    @staticmethod
    def _integrity_payload(
        provider_id: str,
        dimensions: int,
        entries: Sequence[VectorEntry],
    ) -> str:
        canonical = json.dumps(
            {
                "provider_id": provider_id,
                "dimensions": dimensions,
                "entries": [entry.to_dict() for entry in entries],
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return sha256(canonical).hexdigest()

    def _load(self) -> tuple[VectorEntry, ...]:
        if not self.path.is_file():
            return ()
        value = json.loads(self.path.read_text(encoding="utf-8"))
        required = {
            "schema_version",
            "provider_id",
            "dimensions",
            "entries",
            "integrity_sha256",
        }
        if not isinstance(value, dict) or set(value) != required:
            raise ValueError("invalid vector index structure")
        if value["schema_version"] != 1:
            raise ValueError("unsupported vector index schema")
        if value["provider_id"] != self.provider.id:
            return ()
        if value["dimensions"] != self.provider.dimensions:
            return ()
        if not isinstance(value["entries"], list):
            raise TypeError("vector index entries must be an array")
        entries = []
        for item in value["entries"]:
            if not isinstance(item, dict) or set(item) != {
                "knowledge_id",
                "content_sha256",
                "vector",
            }:
                raise ValueError("invalid vector index entry")
            vector = _normalize(item["vector"])
            if len(vector) != self.provider.dimensions:
                raise ValueError("vector index entry has wrong dimensions")
            entries.append(
                VectorEntry(
                    str(item["knowledge_id"]),
                    str(item["content_sha256"]),
                    vector,
                )
            )
        expected = self._integrity_payload(
            self.provider.id, self.provider.dimensions, entries
        )
        if value["integrity_sha256"] != expected:
            raise ValueError("vector index integrity mismatch")
        return tuple(entries)

    def _write(self, entries: Sequence[VectorEntry]) -> None:
        payload = {
            "schema_version": 1,
            "provider_id": self.provider.id,
            "dimensions": self.provider.dimensions,
            "entries": [entry.to_dict() for entry in entries],
            "integrity_sha256": self._integrity_payload(
                self.provider.id, self.provider.dimensions, entries
            ),
        }
        temporary = self.path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.path)

    def refresh(self, store: KnowledgeStore) -> tuple[VectorEntry, ...]:
        records = tuple(
            record for record in store.list_records() if record.status == "validated"
        )
        existing = {entry.knowledge_id: entry for entry in self._load()}
        current_ids = {record.id for record in records}
        changed = set(existing) != current_ids
        entries = []
        missing = []
        for record in records:
            entry = existing.get(record.id)
            if entry is None or entry.content_sha256 != record.content_sha256:
                missing.append(record)
                changed = True
            else:
                entries.append(entry)
        if missing:
            vectors = self.provider.embed([_record_text(record) for record in missing])
            if len(vectors) != len(missing):
                raise ValueError("embedding provider returned the wrong number of vectors")
            for record, raw_vector in zip(missing, vectors):
                vector = _normalize(raw_vector)
                if len(vector) != self.provider.dimensions:
                    raise ValueError("embedding provider returned wrong dimensions")
                entries.append(VectorEntry(record.id, record.content_sha256, vector))
        entries.sort(key=lambda item: item.knowledge_id)
        if changed or (records and not self.path.exists()):
            self._write(entries)
        elif not records and self.path.exists():
            self._write(())
        return tuple(entries)

    def search(
        self,
        query: str,
        store: KnowledgeStore,
        *,
        limit: int = 5,
        minimum_score: float = 0.0,
    ) -> tuple[VectorHit, ...]:
        if not query.strip():
            raise ValueError("vector query must not be empty")
        if not 1 <= limit <= 50:
            raise ValueError("vector search limit must be between 1 and 50")
        entries = self.refresh(store)
        query_vectors = self.provider.embed([query])
        if len(query_vectors) != 1:
            raise ValueError("embedding provider must return one query vector")
        query_vector = _normalize(query_vectors[0])
        if len(query_vector) != self.provider.dimensions:
            raise ValueError("embedding provider returned wrong query dimensions")
        records = {record.id: record for record in store.list_records()}
        hits = []
        for entry in entries:
            score = _dot(query_vector, entry.vector)
            record = records.get(entry.knowledge_id)
            if record is None or record.status != "validated" or score < minimum_score:
                continue
            hits.append(VectorHit(record, round(score, 8)))
        hits.sort(key=lambda item: (-item.vector_score, item.record.id))
        return tuple(hits[:limit])


class HybridRagRetriever:
    """Combine score lexical et similarité vectorielle sur les preuves validées."""

    def __init__(
        self,
        store: KnowledgeStore,
        index: VectorKnowledgeIndex | None = None,
        *,
        vector_weight: float = 0.65,
    ) -> None:
        if not 0.0 <= vector_weight <= 1.0:
            raise ValueError("vector_weight must be between 0 and 1")
        self.store = store
        self.index = index or VectorKnowledgeIndex(store.root / "_vector_index")
        self.vector_weight = vector_weight

    def search(self, query: str, *, limit: int = 5) -> tuple[RagHit, ...]:
        lexical = self.store.search(query, limit=max(limit * 4, 20))
        vector = self.index.search(
            query,
            self.store,
            limit=max(limit * 4, 20),
            minimum_score=0.05,
        )
        lexical_by_id = {hit.record.id: hit for hit in lexical}
        vector_by_id = {hit.record.id: hit for hit in vector}
        max_lexical = max((hit.score for hit in lexical), default=1.0)
        records = {record.id: record for record in self.store.list_records()}
        hits = []
        for identifier in set(lexical_by_id) | set(vector_by_id):
            lexical_hit = lexical_by_id.get(identifier)
            vector_hit = vector_by_id.get(identifier)
            lexical_score = (
                lexical_hit.score / max_lexical if lexical_hit is not None else 0.0
            )
            raw_vector_score = vector_hit.vector_score if vector_hit is not None else 0.0
            vector_score = max(0.0, raw_vector_score)
            score = self.vector_weight * vector_score + (
                1.0 - self.vector_weight
            ) * lexical_score
            hits.append(
                RagHit(
                    records[identifier],
                    round(score, 8),
                    round(raw_vector_score, 8),
                    round(lexical_score, 8),
                    lexical_hit.matched_terms if lexical_hit else (),
                )
            )
        hits.sort(key=lambda item: (-item.score, item.record.id))
        return tuple(hits[:limit])
