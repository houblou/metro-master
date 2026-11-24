"""Chargement et composition des instructions d'agents."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files

from .token_budget import TokenBudgetPolicy


AGENT_ORDER = (
    "METRO-MASTER",
    "PDF-EXTRACTOR",
    "WEB-RESEARCHER",
    "THEORIA",
    "PHYS-METRO",
    "METRO-COMPARE",
    "CALIB-EXPERT",
    "DATA-METRO",
    "UNCERTAINTY-ANALYST",
    "GUM-EXPERT",
    "MODEL-COMPILER",
    "NORM-EXPERT",
    "MODULE-BUILDER",
    "METRO-AUDIT",
)


@dataclass(frozen=True, slots=True)
class AgentSpec:
    name: str
    description: str
    prompt_file: str


AGENTS = {
    "METRO-MASTER": AgentSpec(
        "METRO-MASTER", "Coordinateur, cadrage, routage et synthèse", "metro-master.md"
    ),
    "PDF-EXTRACTOR": AgentSpec(
        "PDF-EXTRACTOR",
        "Extraction intégrale, paginée et traçable des PDF métrologiques",
        "pdf-extractor.md",
    ),
    "WEB-RESEARCHER": AgentSpec(
        "WEB-RESEARCHER",
        "Recherche Internet approfondie, itérative et traçable",
        "web-researcher.md",
    ),
    "THEORIA": AgentSpec(
        "THEORIA", "Fondements, définition du mesurande et validité du modèle", "theoria.md"
    ),
    "GUM-EXPERT": AgentSpec(
        "GUM-EXPERT", "Budgets, propagation, distributions et corrélations", "gum-expert.md"
    ),
    "METRO-COMPARE": AgentSpec(
        "METRO-COMPARE", "Comparaisons, transferts et séparation banc/référence", "metro-compare.md"
    ),
    "CALIB-EXPERT": AgentSpec(
        "CALIB-EXPERT", "Étalonnage, corrections, traçabilité et périodicité", "calib-expert.md"
    ),
    "DATA-METRO": AgentSpec(
        "DATA-METRO", "Statistiques, plans d'expérience et diagnostics", "data-metro.md"
    ),
    "UNCERTAINTY-ANALYST": AgentSpec(
        "UNCERTAINTY-ANALYST",
        "Parcours Ishikawa, modèle, Type A/B et composition traçable",
        "uncertainty-analyst.md",
    ),
    "MODEL-COMPILER": AgentSpec(
        "MODEL-COMPILER",
        "Compilation traçable d'un texte libre vers un modèle de calcul",
        "model-compiler.md",
    ),
    "PHYS-METRO": AgentSpec(
        "PHYS-METRO", "Physique de la chaîne et grandeurs d'influence", "phys-metro.md"
    ),
    "NORM-EXPERT": AgentSpec(
        "NORM-EXPERT", "Applicabilité normative et provenance documentaire", "norm-expert.md"
    ),
    "MODULE-BUILDER": AgentSpec(
        "MODULE-BUILDER",
        "Proposition gouvernée de nouvelles capacités de calcul déclaratives",
        "module-builder.md",
    ),
    "METRO-AUDIT": AgentSpec(
        "METRO-AUDIT", "Revue indépendante scientifique, numérique et documentaire", "metro-audit.md"
    ),
}


def list_agents() -> tuple[AgentSpec, ...]:
    return tuple(AGENTS[name] for name in AGENT_ORDER)


def _read_prompt(name: str) -> str:
    resource = files("metro_master").joinpath(f"resources/prompts/{name}")
    return resource.read_text(encoding="utf-8").strip()


def compose_prompt(
    agent_name: str,
    token_policy: TokenBudgetPolicy | None = None,
) -> str:
    normalized = agent_name.upper()
    if normalized not in AGENTS:
        raise KeyError(f"unknown agent: {agent_name}")
    policy = token_policy or TokenBudgetPolicy.load()
    common = _read_prompt("common.md")
    token_contract = _read_prompt("token-budget.md")
    role = _read_prompt(AGENTS[normalized].prompt_file)
    return (
        f"{common}\n\n---\n\n{token_contract}\n\n"
        f"{policy.prompt_block()}\n\n---\n\n{role}\n"
    )

