"""Contrats sûrs et traçables pour la recherche Internet approfondie."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from ipaddress import ip_address
import re
from typing import Any, Callable, Protocol, Sequence
from urllib.parse import urlsplit

from .validation import require_text


MAX_RESEARCH_REQUESTS_PER_TURN = 8
MAX_RESULTS_PER_REQUEST = 10
MAX_QUERY_LENGTH = 500
MAX_SUMMARY_LENGTH = 6_000
RESEARCH_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
DOMAIN_PATTERN = re.compile(
    r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)*"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
)
SOURCE_TYPES = frozenset({"official", "primary", "secondary", "unknown"})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def _validate_timestamp(label: str, value: object) -> str:
    text = require_text(label, value)
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{label} must be an ISO-8601 timestamp") from error
    return text


def _validate_domain(value: object) -> str:
    domain = require_text("research domain", value).casefold().rstrip(".")
    if len(domain) > 253 or not DOMAIN_PATTERN.fullmatch(domain):
        raise ValueError(f"invalid research domain: {value!r}")
    if domain == "localhost" or domain.endswith(".local"):
        raise ValueError("local research domains are not allowed")
    try:
        address = ip_address(domain)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError("private or non-global research addresses are not allowed")
    return domain


def _validate_url(value: object) -> str:
    url = require_text("research source URL", value)
    if len(url) > 2_048:
        raise ValueError("research source URL is too long")
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("research source URL must use http or https")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("research source URL must not contain credentials")
    hostname = parsed.hostname.casefold().rstrip(".")
    if hostname == "localhost" or hostname.endswith(".local"):
        raise ValueError("local research source URLs are not allowed")
    try:
        address = ip_address(hostname)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError("private or non-global research source URLs are not allowed")
    return url


@dataclass(frozen=True, slots=True)
class ResearchRequest:
    id: str
    query: str
    purpose: str
    allowed_domains: tuple[str, ...] = ()
    primary_sources_only: bool = True
    max_results: int = 5

    def __post_init__(self) -> None:
        identifier = require_text("research request id", self.id)
        if not RESEARCH_ID_PATTERN.fullmatch(identifier):
            raise ValueError(
                "research request id may contain only letters, digits, dot, underscore or hyphen"
            )
        query = require_text("research query", self.query)
        if len(query) > MAX_QUERY_LENGTH:
            raise ValueError(f"research query exceeds {MAX_QUERY_LENGTH} characters")
        require_text("research purpose", self.purpose)
        if not isinstance(self.primary_sources_only, bool):
            raise TypeError("primary_sources_only must be a boolean")
        if isinstance(self.max_results, bool) or not isinstance(self.max_results, int):
            raise TypeError("max_results must be an integer")
        if not 1 <= self.max_results <= MAX_RESULTS_PER_REQUEST:
            raise ValueError(
                f"max_results must be between 1 and {MAX_RESULTS_PER_REQUEST}"
            )
        normalized_domains = tuple(_validate_domain(item) for item in self.allowed_domains)
        if len(normalized_domains) > 12:
            raise ValueError("at most 12 allowed research domains may be supplied")
        if len(normalized_domains) != len(set(normalized_domains)):
            raise ValueError("allowed research domains must be unique")
        object.__setattr__(self, "allowed_domains", normalized_domains)

    @classmethod
    def from_dict(cls, value: object) -> "ResearchRequest":
        data = _strict_object(
            value,
            required={"id", "query", "purpose"},
            optional={"allowed_domains", "primary_sources_only", "max_results"},
            label="research request",
        )
        domains = data.get("allowed_domains", [])
        if not isinstance(domains, list) or not all(
            isinstance(item, str) for item in domains
        ):
            raise TypeError("allowed_domains must be an array of strings")
        return cls(
            id=data["id"],
            query=data["query"],
            purpose=data["purpose"],
            allowed_domains=tuple(domains),
            primary_sources_only=data.get("primary_sources_only", True),
            max_results=data.get("max_results", 5),
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def signature(self) -> str:
        return "|".join(
            (
                self.query.casefold().strip(),
                ",".join(self.allowed_domains),
                str(self.primary_sources_only),
            )
        )


@dataclass(frozen=True, slots=True)
class ResearchSource:
    title: str
    url: str
    summary: str
    publisher: str = ""
    source_type: str = "unknown"
    published_at: str | None = None
    retrieved_at: str = ""

    def __post_init__(self) -> None:
        require_text("research source title", self.title)
        _validate_url(self.url)
        summary = require_text("research source summary", self.summary)
        if len(summary) > MAX_SUMMARY_LENGTH:
            raise ValueError(
                f"research source summary exceeds {MAX_SUMMARY_LENGTH} characters"
            )
        require_text("research source publisher", self.publisher, allow_empty=True)
        source_type = require_text("research source type", self.source_type)
        if source_type not in SOURCE_TYPES:
            raise ValueError(f"invalid research source type: {source_type}")
        object.__setattr__(self, "source_type", source_type)
        if self.published_at is not None:
            _validate_timestamp("published_at", self.published_at)
        retrieved_at = self.retrieved_at or _now()
        _validate_timestamp("retrieved_at", retrieved_at)
        object.__setattr__(self, "retrieved_at", retrieved_at)

    @classmethod
    def from_dict(cls, value: object) -> "ResearchSource":
        data = _strict_object(
            value,
            required={"title", "url", "summary"},
            optional={
                "publisher",
                "source_type",
                "published_at",
                "retrieved_at",
            },
            label="research source",
        )
        return cls(
            title=data["title"],
            url=data["url"],
            summary=data["summary"],
            publisher=data.get("publisher", ""),
            source_type=data.get("source_type", "unknown"),
            published_at=data.get("published_at"),
            retrieved_at=data.get("retrieved_at", ""),
        )

    @property
    def content_sha256(self) -> str:
        payload = f"{self.url}\n{self.title}\n{self.summary}".encode("utf-8")
        return sha256(payload).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {**asdict(self), "content_sha256": self.content_sha256}


@dataclass(frozen=True, slots=True)
class ResearchRecord:
    request: ResearchRequest
    status: str
    sources: tuple[ResearchSource, ...] = ()
    error_type: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self) | {
            "sources": [source.to_dict() for source in self.sources]
        }


class ResearchProvider(Protocol):
    """Adaptateur d'un moteur de recherche réel, fourni par l'intégrateur."""

    def search(
        self, request: ResearchRequest
    ) -> Sequence[ResearchSource | dict[str, object]]: ...


class CallableResearchProvider:
    """Petit adaptateur pour brancher un SDK ou un service de recherche existant."""

    def __init__(
        self,
        handler: Callable[
            [ResearchRequest], Sequence[ResearchSource | dict[str, object]]
        ],
    ) -> None:
        self._handler = handler

    def search(
        self, request: ResearchRequest
    ) -> Sequence[ResearchSource | dict[str, object]]:
        return self._handler(request)


def _domain_allowed(url: str, allowed_domains: tuple[str, ...]) -> bool:
    if not allowed_domains:
        return True
    hostname = (urlsplit(url).hostname or "").casefold().rstrip(".")
    return any(
        hostname == domain or hostname.endswith(f".{domain}")
        for domain in allowed_domains
    )


def execute_research(
    provider: ResearchProvider | None, request: ResearchRequest
) -> ResearchRecord:
    """Exécute une requête et refuse les résultats non conformes au contrat."""

    if provider is None:
        return ResearchRecord(
            request,
            "rejected",
            error_type="ResearchProviderUnavailable",
            error="no Internet research provider is configured",
        )
    try:
        raw_sources = provider.search(request)
        if isinstance(raw_sources, (str, bytes)) or not isinstance(
            raw_sources, Sequence
        ):
            raise TypeError("research provider must return a sequence of sources")
        sources: list[ResearchSource] = []
        seen_urls: set[str] = set()
        excluded = 0
        for item in raw_sources:
            source = (
                item
                if isinstance(item, ResearchSource)
                else ResearchSource.from_dict(item)
            )
            if source.url in seen_urls:
                continue
            seen_urls.add(source.url)
            if not _domain_allowed(source.url, request.allowed_domains):
                excluded += 1
                continue
            if request.primary_sources_only and source.source_type not in {
                "official",
                "primary",
            }:
                excluded += 1
                continue
            sources.append(source)
            if len(sources) >= request.max_results:
                break
        if not sources:
            return ResearchRecord(
                request,
                "rejected",
                error_type="NoAdmissibleSources",
                error="the provider returned no source matching the request policy",
            )
        return ResearchRecord(
            request,
            "partial" if excluded else "ok",
            tuple(sources),
            error=(
                f"{excluded} source(s) excluded by domain or primary-source policy"
                if excluded
                else None
            ),
        )
    except Exception as error:
        return ResearchRecord(
            request,
            "rejected",
            error_type=type(error).__name__,
            error=str(error),
        )
