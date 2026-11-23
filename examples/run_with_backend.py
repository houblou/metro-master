"""Exemple de branchement : remplacer DemoBackend par votre fournisseur autorisé."""

import _bootstrap  # noqa: F401

from metro_master.orchestrator import MetroOrchestrator


class DemoBackend:
    """Démonstrateur local : il montre le contrat sans appeler de service."""

    def complete(
        self,
        *,
        agent: str,
        system_prompt: str,
        user_request: str,
        shared_context: str,
    ) -> str:
        return (
            f"DÉMONSTRATION — {agent}\n"
            f"La requête contient {len(user_request)} caractères, le contexte "
            f"{len(shared_context)} et les instructions {len(system_prompt)}. "
            "Remplacez ce corps par un appel à un modèle autorisé."
        )


if __name__ == "__main__":
    result = MetroOrchestrator().execute(
        "Caractériser un banc de pression par comparaison avec une référence corrélée.",
        DemoBackend(),
    )
    for turn in result.turns:
        print(f"[{turn.sequence}] {turn.agent}: {turn.response}")

