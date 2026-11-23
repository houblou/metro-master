"""Exemple de branchement d'un fournisseur Web et d'une mémoire locale.

Le service de recherche réel et le backend LLM restent à fournir par l'intégrateur.
"""

from metro_master import CallableResearchProvider, KnowledgeStore, ResearchSource
from metro_master.orchestrator import MetroOrchestrator


def search_with_your_service(request):
    """Remplacer ce corps par le SDK Web autorisé dans votre environnement."""

    # Transformer chaque résultat lu en ResearchSource. Ne pas reprendre un extrait
    # moteur comme preuve si la page correspondante n'a pas été effectivement lue.
    return [
        ResearchSource(
            title="Exemple à remplacer par le titre réellement consulté",
            url="https://www.bipm.org/",
            summary="Exemple de structure, pas une conclusion métrologique.",
            publisher="BIPM",
            source_type="official",
        )
    ]


class YourLlmBackend:
    def complete(self, *, agent, system_prompt, user_request, shared_context):
        raise NotImplementedError("Brancher ici votre fournisseur de modèle")


provider = CallableResearchProvider(search_with_your_service)
memory = KnowledgeStore("knowledge/registry")
orchestrator = MetroOrchestrator(
    research_provider=provider,
    knowledge_store=memory,
    max_research_rounds=3,
)

# result = orchestrator.execute(
#     "Faire une recherche approfondie Internet sur l'édition applicable du GUM",
#     YourLlmBackend(),
# )
