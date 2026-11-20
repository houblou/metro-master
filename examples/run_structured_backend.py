"""Démonstration locale du chemin agent -> moteur -> audit."""

from __future__ import annotations

import json

from metro_master.orchestrator import MetroOrchestrator


class StructuredDemoBackend:
    def complete(
        self,
        *,
        agent: str,
        system_prompt: str,
        user_request: str,
        shared_context: str,
    ) -> str:
        if agent == "GUM-EXPERT":
            return json.dumps(
                {
                    "message": "Démonstration : budget transmis au moteur local.",
                    "calculation_requests": [
                        {
                            "id": "demo-budget",
                            "operation": "budget",
                            "payload": {
                                "coverage_factor": 2.0,
                                "components": [
                                    {
                                        "name": "bench",
                                        "standard_uncertainty": 3.0,
                                        "owner": "bench",
                                        "unit": "kPa",
                                        "source": "illustrative example only",
                                    },
                                    {
                                        "name": "reference",
                                        "standard_uncertainty": 4.0,
                                        "owner": "reference",
                                        "unit": "kPa",
                                        "source": "illustrative example only",
                                    },
                                ],
                            },
                        }
                    ],
                },
                ensure_ascii=False,
            )
        if agent == "METRO-AUDIT":
            context = json.loads(shared_context)
            records = [
                calculation
                for turn in context["turns"]
                for calculation in turn["deterministic_calculations"]
            ]
            return f"DÉMONSTRATION — audit reçu {len(records)} calcul déterministe."
        return f"DÉMONSTRATION — {agent} n'émet aucun calcul."


if __name__ == "__main__":
    result = MetroOrchestrator().execute(
        "Calculer un budget d'incertitude illustratif.",
        StructuredDemoBackend(),
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
