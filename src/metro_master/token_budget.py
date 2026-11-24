"""Budgets de tokens conservateurs pour l'orchestration MetrologyLab AI.

Les valeurs sont des estimations independantes du fournisseur. Un adaptateur LLM
peut appliquer la limite de sortie exacte en acceptant ``max_output_tokens`` dans
sa methode ``complete``. Sans ce parametre, la limite reste injectee dans le
prompt et la consommation est suivie a posteriori.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib.resources import files
import json
from pathlib import Path
from typing import Any, Iterable


class TokenBudgetExceeded(RuntimeError):
    """Le prochain appel depasserait une limite de budget configuree."""


def estimate_tokens(value: str) -> int:
    """Estimer prudemment des tokens a partir des octets UTF-8.

    Ce n'est pas le tokenizer d'un fournisseur. Le ratio de quatre octets par
    token donne une estimation stable, reproductible et volontairement simple.
    """

    if not isinstance(value, str):
        raise TypeError("value must be a string")
    if not value:
        return 0
    return max(1, (len(value.encode("utf-8")) + 3) // 4)


@dataclass(frozen=True, slots=True)
class TokenBudgetPolicy:
    mode: str
    max_total_tokens: int
    max_input_tokens_per_call: int
    max_output_tokens_per_call: int
    final_audit_reserve_tokens: int
    max_agent_turns: int
    max_context_response_tokens: int
    max_knowledge_hit_tokens: int

    def __post_init__(self) -> None:
        if not self.mode.strip():
            raise ValueError("token budget mode must not be empty")
        integer_fields = (
            "max_total_tokens",
            "max_input_tokens_per_call",
            "max_output_tokens_per_call",
            "final_audit_reserve_tokens",
            "max_agent_turns",
            "max_context_response_tokens",
            "max_knowledge_hit_tokens",
        )
        for name in integer_fields:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        if self.final_audit_reserve_tokens >= self.max_total_tokens:
            raise ValueError("final audit reserve must be smaller than total budget")
        if self.max_input_tokens_per_call >= self.max_total_tokens:
            raise ValueError("per-call input limit must be smaller than total budget")
        if self.max_agent_turns < 2:
            raise ValueError("at least one specialist and METRO-AUDIT are required")

    @classmethod
    def load(
        cls,
        mode: str | None = None,
        path: str | Path | None = None,
    ) -> "TokenBudgetPolicy":
        if path is None:
            raw = files("metro_master").joinpath(
                "resources/token-budget.json"
            ).read_text(encoding="utf-8")
        else:
            raw = Path(path).read_text(encoding="utf-8")
        payload = json.loads(raw)
        selected_mode = mode or payload.get("default_mode")
        profiles = payload.get("profiles", {})
        if selected_mode not in profiles:
            allowed = ", ".join(sorted(profiles))
            raise ValueError(
                f"unknown token budget mode: {selected_mode}; expected one of: {allowed}"
            )
        profile = profiles[selected_mode]
        if not isinstance(profile, dict):
            raise TypeError(f"token profile {selected_mode} must be an object")
        return cls(mode=selected_mode, **profile)

    def prompt_block(self) -> str:
        return (
            "## Budget actif de ce tour\n\n"
            f"- mode : `{self.mode}` ;\n"
            f"- plafond estimé de l'étude : {self.max_total_tokens} tokens ;\n"
            f"- plafond d'entrée par appel : {self.max_input_tokens_per_call} tokens ;\n"
            f"- plafond de sortie par appel : {self.max_output_tokens_per_call} tokens ;\n"
            f"- réserve inviolable pour METRO-AUDIT : "
            f"{self.final_audit_reserve_tokens} tokens ;\n"
            f"- nombre maximal de tours d'agents : {self.max_agent_turns}.\n\n"
            "Respecter ce plafond comme une limite haute, pas comme un objectif à remplir."
        )

    def select_steps(self, steps: Iterable[Any]) -> tuple[tuple[Any, ...], tuple[str, ...]]:
        """Limiter les roles tout en conservant l'ordre et l'audit final."""

        ordered = tuple(steps)
        if len(ordered) <= self.max_agent_turns:
            return ordered, ()

        priority = {
            "METRO-AUDIT": 1_000,
            "METRO-MASTER": 950,
            "PDF-EXTRACTOR": 940,
            "WEB-RESEARCHER": 940,
            "THEORIA": 920,
            "UNCERTAINTY-ANALYST": 915,
            "MODEL-COMPILER": 910,
            "GUM-EXPERT": 900,
            "METRO-COMPARE": 890,
            "CALIB-EXPERT": 880,
            "DATA-METRO": 870,
            "PHYS-METRO": 860,
            "NORM-EXPERT": 850,
            "MODULE-BUILDER": 840,
        }
        ranked = sorted(
            enumerate(ordered),
            key=lambda item: (-priority.get(item[1].agent, 0), item[0]),
        )
        selected_indexes = {
            index for index, _ in ranked[: self.max_agent_turns]
        }
        selected = tuple(
            step for index, step in enumerate(ordered) if index in selected_indexes
        )
        skipped = tuple(
            step.agent for index, step in enumerate(ordered) if index not in selected_indexes
        )
        return selected, skipped


@dataclass(slots=True)
class TokenLedger:
    policy: TokenBudgetPolicy
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    call_count: int = 0
    skipped_steps: list[dict[str, str]] = field(default_factory=list)
    output_overrun_count: int = 0

    @property
    def estimated_consumed_tokens(self) -> int:
        return self.estimated_input_tokens + self.estimated_output_tokens

    @property
    def estimated_remaining_tokens(self) -> int:
        return max(0, self.policy.max_total_tokens - self.estimated_consumed_tokens)

    def output_allowance(self, input_tokens: int, *, final_audit: bool) -> int:
        reserve = 0 if final_audit else self.policy.final_audit_reserve_tokens
        available = (
            self.policy.max_total_tokens
            - self.estimated_consumed_tokens
            - input_tokens
            - reserve
        )
        return min(self.policy.max_output_tokens_per_call, max(0, available))

    def require_call(self, input_tokens: int, *, final_audit: bool) -> int:
        if input_tokens > self.policy.max_input_tokens_per_call:
            raise TokenBudgetExceeded(
                f"estimated input {input_tokens} exceeds per-call limit "
                f"{self.policy.max_input_tokens_per_call}"
            )
        allowance = self.output_allowance(input_tokens, final_audit=final_audit)
        if allowance < 128:
            reserve_label = "" if final_audit else " after preserving the final audit reserve"
            raise TokenBudgetExceeded(
                f"insufficient token budget for another call{reserve_label}"
            )
        return allowance

    def record(self, input_tokens: int, output_tokens: int, output_limit: int) -> None:
        self.estimated_input_tokens += input_tokens
        self.estimated_output_tokens += output_tokens
        self.call_count += 1
        if output_tokens > output_limit:
            self.output_overrun_count += 1

    def skip(self, agent: str, reason: str) -> None:
        self.skipped_steps.append({"agent": agent, "reason": reason})

    def snapshot(self) -> dict[str, object]:
        return {
            "mode": self.policy.mode,
            "estimates_only": True,
            "max_total_tokens": self.policy.max_total_tokens,
            "estimated_consumed_tokens": self.estimated_consumed_tokens,
            "estimated_remaining_tokens": self.estimated_remaining_tokens,
            "estimated_input_tokens": self.estimated_input_tokens,
            "estimated_output_tokens": self.estimated_output_tokens,
            "call_count": self.call_count,
            "final_audit_reserve_tokens": self.policy.final_audit_reserve_tokens,
            "skipped_steps": list(self.skipped_steps),
            "output_overrun_count": self.output_overrun_count,
        }

    def to_dict(self) -> dict[str, object]:
        return self.snapshot()
