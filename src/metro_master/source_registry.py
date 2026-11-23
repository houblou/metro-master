"""Registre local des sources tierces utilisées pour concevoir MetrologyLab AI."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any

from .validation import require_text


SHA_PATTERN = re.compile(r"^[a-f0-9]{40}$")
USAGE_MODES = frozenset({"copy", "adapt", "reimplement", "reference_only"})


@dataclass(frozen=True, slots=True)
class SourceAsset:
    source_id: str
    repository: str
    commit: str
    path: str
    blob_sha: str
    license: str
    usage_mode: str
    local_targets: tuple[str, ...]
    modifications: str
    review_status: str

    @classmethod
    def from_dict(cls, value: object) -> "SourceAsset":
        required = {
            "source_id", "repository", "commit", "path", "blob_sha", "license",
            "usage_mode", "local_targets", "modifications", "review_status",
        }
        if not isinstance(value, dict) or set(value) != required:
            raise ValueError("invalid source asset structure")
        commit = require_text("source commit", value["commit"])
        blob = require_text("source blob_sha", value["blob_sha"])
        if not SHA_PATTERN.fullmatch(commit) or not SHA_PATTERN.fullmatch(blob):
            raise ValueError("source commit and blob_sha must be full Git SHA-1 values")
        mode = require_text("source usage_mode", value["usage_mode"])
        if mode not in USAGE_MODES:
            raise ValueError(f"invalid source usage mode: {mode}")
        targets = value["local_targets"]
        if not isinstance(targets, list) or not all(
            isinstance(item, str) and item.strip() for item in targets
        ):
            raise TypeError("source local_targets must be non-empty path strings")
        return cls(
            require_text("source id", value["source_id"]),
            require_text("source repository", value["repository"]),
            commit,
            require_text("source path", value["path"]),
            blob,
            require_text("source license", value["license"]),
            mode,
            tuple(targets),
            require_text("source modifications", value["modifications"]),
            require_text("source review_status", value["review_status"]),
        )


class SourceRegistry:
    def __init__(self, assets: tuple[SourceAsset, ...]) -> None:
        identifiers = [item.source_id for item in assets]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("source ids must be unique")
        self.assets = assets

    @classmethod
    def load(cls, path: str | Path | None = None) -> "SourceRegistry":
        selected = Path(path) if path is not None else Path(__file__).parent / "resources" / "source-manifest.json"
        value: Any = json.loads(selected.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or set(value) != {"schema_version", "assets"}:
            raise ValueError("invalid source registry structure")
        if value["schema_version"] != 1 or not isinstance(value["assets"], list):
            raise ValueError("unsupported source registry schema")
        return cls(tuple(SourceAsset.from_dict(item) for item in value["assets"]))

    def validate_local_targets(self, root: str | Path) -> None:
        base = Path(root).resolve()
        for asset in self.assets:
            for target in asset.local_targets:
                path = (base / target).resolve()
                if base not in path.parents and path != base:
                    raise ValueError(f"source target escapes repository: {target}")
                if not path.exists():
                    raise FileNotFoundError(f"declared source target is missing: {target}")
