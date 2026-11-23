"""Démonstration locale du chemin agent -> moteur -> audit."""

from __future__ import annotations

import json

import _bootstrap  # noqa: F401

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
        if agent == "MODEL-COMPILER":
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
                                        "sensitivity": 1.0,
                                        "sensitivity_unit": "1",
                                        "owner": "bench",
                                        "unit": "kPa",
                                        "distribution": "unspecified",
                                        "source": "illustrative example only",
                                        "degrees_of_freedom": None,
                                    },
                                    {
                                        "name": "reference",
                                        "standard_uncertainty": 4.0,
                                        "sensitivity": 1.0,
                                        "sensitivity_unit": "1",
                                        "owner": "reference",
                                        "unit": "kPa",
                                        "distribution": "unspecified",
                                        "source": "illustrative example only",
                                        "degrees_of_freedom": None,
                                    },
                                ],
                                "correlations": [],
                                "output_unit": "kPa",
                            },
                            "evidence": [
                                {"field_path": "/components/0/standard_uncertainty", "source_ref": "user_request", "excerpt": "banc = 3.0 kPa", "evidence_type": "provided"},
                                {"field_path": "/components/1/standard_uncertainty", "source_ref": "user_request", "excerpt": "référence = 4.0 kPa", "evidence_type": "provided"},
                                {"field_path": "/components/0/sensitivity", "source_ref": "declared:method", "excerpt": "sensibilité 1.0", "evidence_type": "method_choice"},
                                {"field_path": "/components/1/sensitivity", "source_ref": "declared:method", "excerpt": "sensibilité 1.0", "evidence_type": "method_choice"},
                                {"field_path": "/components/0/sensitivity_unit", "source_ref": "declared:method", "excerpt": "unité de sensibilité 1", "evidence_type": "method_choice"},
                                {"field_path": "/components/1/sensitivity_unit", "source_ref": "declared:method", "excerpt": "unité de sensibilité 1", "evidence_type": "method_choice"},
                                {"field_path": "/components/0/unit", "source_ref": "user_request", "excerpt": "banc = 3.0 kPa", "evidence_type": "provided"},
                                {"field_path": "/components/1/unit", "source_ref": "user_request", "excerpt": "référence = 4.0 kPa", "evidence_type": "provided"},
                                {"field_path": "/coverage_factor", "source_ref": "user_request", "excerpt": "k = 2.0", "evidence_type": "provided"},
                                {"field_path": "/output_unit", "source_ref": "declared:method", "excerpt": "unité de sortie kPa", "evidence_type": "method_choice"},
                            ],
                            "assumptions": [
                                "Les corrélations sont supposées nulles.",
                                "Les sensibilités unitaires sont des choix méthodologiques."
                            ]
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
            return json.dumps(
                {
                    "message": f"DÉMONSTRATION — audit reçu {len(records)} calcul déterministe ; incertitude-type composée 5.0 kPa.",
                    "conclusion_claims": [
                        {
                            "request_id": "demo-budget",
                            "result_pointer": "/combined_standard_uncertainty",
                            "stated_value": 5.0,
                            "unit": "kPa",
                            "statement": "Incertitude-type composée"
                        }
                    ]
                },
                ensure_ascii=False,
            )
        return f"DÉMONSTRATION — {agent} n'émet aucun calcul."


if __name__ == "__main__":
    result = MetroOrchestrator().execute(
        "Calculer le budget illustratif : banc = 3.0 kPa, référence = 4.0 kPa, k = 2.0.",
        StructuredDemoBackend(),
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
