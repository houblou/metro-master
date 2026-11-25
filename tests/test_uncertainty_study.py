from __future__ import annotations

import contextlib
import copy
import io
import json
from math import sqrt
from pathlib import Path
import tempfile
import unittest

from metro_master.cli import main
from metro_master.execution import CalculationRequest, DeterministicEngine
from metro_master.uncertainty_oracles import verify_with_external_oracles
from metro_master.uncertainty_study import build_uncertainty_study, evaluate_type_b


ROOT = Path(__file__).resolve().parents[1]


def fixture() -> dict[str, object]:
    return json.loads(
        (ROOT / "examples" / "uncertainty_study.json").read_text(encoding="utf-8")
    )


class UncertaintyStudyTests(unittest.TestCase):
    def test_four_stage_study_is_deterministic_and_explicit(self) -> None:
        result = build_uncertainty_study(fixture())
        repeatability, resolution = result.components
        self.assertAlmostEqual(repeatability.standard_uncertainty, 0.1 / sqrt(3))
        self.assertEqual(repeatability.degrees_of_freedom, 2.0)
        self.assertEqual(repeatability.observations, (9.9, 10.0, 10.1))
        self.assertAlmostEqual(resolution.standard_uncertainty, 0.02 / sqrt(12))
        expected = sqrt((0.1 / sqrt(3)) ** 2 + (0.02 / sqrt(12)) ** 2)
        self.assertAlmostEqual(result.budget.combined_standard_uncertainty, expected)
        self.assertTrue(result.independent_verification.matches_engine)
        self.assertEqual(result.budget.unit, "mm")
        self.assertIn("## 2. Registre structuré des sources d’incertitude", result.latex_note)
        self.assertIn("## 3. Équation de mesure", result.latex_note)
        self.assertIn("## 4. Évaluation des composantes et contributions", result.latex_note)
        self.assertIn("## 5. Composition et corrélations", result.latex_note)
        self.assertIn("$$\nL = x + c_{res}\n$$", result.latex_note)
        self.assertIn("x = (9.9,\\;10,\\;10.1)", result.latex_note)
        self.assertIn("Validité de la propagation linéaire", result.latex_note)

    def test_every_component_must_be_connected_to_influence_register(self) -> None:
        payload = fixture()
        payload["influences"] = payload["influences"][:1]
        with self.assertRaisesRegex(ValueError, "without a direct influence-register"):
            build_uncertainty_study(payload)

    def test_bank_budget_rejects_reference_or_transfer_components(self) -> None:
        for owner in ("reference", "transfer", "comparison"):
            with self.subTest(owner=owner):
                payload = fixture()
                payload["type_b"][0]["owner"] = owner
                with self.assertRaisesRegex(
                    ValueError,
                    "budget_scope 'bench' cannot include component owners",
                ):
                    build_uncertainty_study(payload)

    def test_transfer_source_can_be_marked_as_covered_without_double_counting(self) -> None:
        payload = fixture()
        payload["influences"].append(
            {
                "id": "transfer-certificate",
                "category": "method",
                "description": "incertitude de la référence de transfert utilisée pour calibrer la correction",
                "treatment": "covered",
                "component_name": "resolution",
                "justification": "la composante de correction porte déjà cette provenance",
                "source_ref": "certificat de transfert",
            }
        )
        result = build_uncertainty_study(payload)
        self.assertEqual(result.budget_scope, "bench")
        self.assertEqual(len(result.components), 2)
        self.assertIn("**Périmètre du budget :** `bench`", result.latex_note)

    def test_legacy_payload_without_scope_is_warned_but_remains_compatible(self) -> None:
        payload = fixture()
        del payload["budget_scope"]
        result = build_uncertainty_study(payload)
        self.assertEqual(result.budget_scope, "unspecified")
        self.assertTrue(any("scope is not declared" in item for item in result.warnings))

    def test_temperature_input_remains_distinct_from_its_contribution(self) -> None:
        payload = {
            "model": {
                "measurand": "longueur corrigée",
                "symbol": "L",
                "output_unit": "nm",
                "equation_latex": "L = L_0 - 575\\,\\delta\\theta",
                "decision": "évaluer la contribution thermique",
                "conditions": "comparaison de deux cales à 20 degrés Celsius",
                "variables": [
                    {
                        "symbol": "\\delta\\theta",
                        "name": "différence de température entre les cales",
                        "unit": "K",
                        "description": "écart thermique entre cale testée et référence",
                        "estimate": 0.0,
                    }
                ],
            },
            "influences": [
                {
                    "id": "environment-temperature-difference",
                    "category": "environment",
                    "description": "différence de température entre les cales",
                    "treatment": "component",
                    "component_name": "temperature_difference",
                    "justification": "intervalle thermique documenté",
                    "source_ref": "JCGM 100:2008 H.1.3.6",
                }
            ],
            "type_a": [],
            "type_b": [
                {
                    "name": "temperature_difference",
                    "value": 0.05,
                    "value_kind": "half_width",
                    "distribution": "rectangular",
                    "distribution_justification": "écart équiprobable entre -0,05 K et +0,05 K",
                    "estimate": 0.0,
                    "unit": "K",
                    "sensitivity": -575.0,
                    "sensitivity_unit": "nm/K",
                    "owner": "comparison",
                    "source": "JCGM 100:2008 H.1.3.6",
                    "degrees_of_freedom": 2.0,
                    "sensitivity_justification": "c = -l_S alpha_S",
                }
            ],
            "correlations": [],
            "correlation_justification": "une seule composante dans ce contrôle ciblé",
            "propagation_justification": "modèle linéaire local pour delta theta",
            "coverage_factor": 1.0,
            "coverage_justification": "incertitude-type uniquement",
        }
        result = build_uncertainty_study(payload)
        component = result.components[0]
        self.assertEqual(component.input_estimate, 0.0)
        self.assertEqual(component.unit, "K")
        self.assertEqual(component.sensitivity_unit, "nm/K")
        self.assertAlmostEqual(component.standard_uncertainty, 0.05 / sqrt(3.0))
        self.assertAlmostEqual(component.output_contribution, -575.0 * 0.05 / sqrt(3.0))
        self.assertAlmostEqual(
            result.budget.combined_standard_uncertainty,
            abs(component.output_contribution),
        )
        self.assertIn("Une ligne individuelle décrit une composante", result.latex_note)
        self.assertIn("-575\\;\\mathrm{nm/K}", result.latex_note)
        self.assertIn("influence_register", result.to_dict())
        self.assertIn("ishikawa", result.to_dict())

    def test_resolution_step_requires_rectangular_distribution(self) -> None:
        payload = fixture()
        payload["type_b"][0]["distribution"] = "triangular"
        with self.assertRaisesRegex(ValueError, "requires a rectangular"):
            build_uncertainty_study(payload)

    def test_type_b_conversions_cover_the_supported_gum_cases(self) -> None:
        base = {
            "name": "type-b",
            "value": 12.0,
            "distribution_justification": "cas de référence du test",
            "unit": "mm",
            "sensitivity": 1.0,
            "sensitivity_unit": "1",
            "sensitivity_justification": "modèle additif",
            "owner": "bench",
            "source": "cas de test",
            "degrees_of_freedom": None,
        }
        cases = (
            ("standard_uncertainty", "normal", {}, 12.0),
            ("expanded_uncertainty", "normal", {"coverage_factor": 3.0}, 4.0),
            ("half_width", "rectangular", {}, 12.0 / sqrt(3.0)),
            ("half_width", "triangular", {}, 12.0 / sqrt(6.0)),
            ("half_width", "arcsine", {}, 12.0 / sqrt(2.0)),
            ("resolution_step", "rectangular", {}, 12.0 / sqrt(12.0)),
        )
        for value_kind, distribution, extra, expected in cases:
            with self.subTest(value_kind=value_kind, distribution=distribution):
                payload = {
                    **base,
                    "value_kind": value_kind,
                    "distribution": distribution,
                    **extra,
                }
                self.assertAlmostEqual(
                    evaluate_type_b(payload).standard_uncertainty,
                    expected,
                )

    def test_native_engine_emits_a_canonical_trace(self) -> None:
        record = DeterministicEngine().execute(
            CalculationRequest("study-1", "uncertainty-study", fixture()),
            execution_origin="test",
        )
        self.assertEqual(record.status, "ok")
        self.assertEqual(record.result["schema_version"], "uncertainty-study-v1")
        self.assertEqual(record.trace.module["id"], "uncertainty-study")
        self.assertTrue(record.trace.trace_sha256)

    def test_cli_writes_note_and_trace_without_overwriting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            note = Path(directory) / "note.md"
            trace = Path(directory) / "trace.json"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = main(
                    [
                        "uncertainty-study",
                        str(ROOT / "examples" / "uncertainty_study.json"),
                        "--note-out",
                        str(note),
                        "--trace-out",
                        str(trace),
                    ]
                )
            self.assertEqual(status, 0)
            self.assertIn("# Bilan d’incertitude", note.read_text(encoding="utf-8"))
            self.assertTrue(json.loads(trace.read_text(encoding="utf-8"))["trace_sha256"])
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(
                    main(
                        [
                            "uncertainty-study",
                            str(ROOT / "examples" / "uncertainty_study.json"),
                            "--note-out",
                            str(note),
                        ]
                    ),
                    2,
                )

    def test_optional_oracles_never_replace_the_native_result(self) -> None:
        study = build_uncertainty_study(fixture())
        checks = verify_with_external_oracles(study)
        self.assertEqual({item.oracle for item in checks}, {"GTC", "uncertainties"})
        self.assertTrue(all(item.status in {"match", "unavailable"} for item in checks))

    def test_external_oracles_preserve_signed_correlations(self) -> None:
        payload = fixture()
        payload["type_b"][0]["sensitivity"] = -1.0
        payload["type_b"][0]["sensitivity_justification"] = (
            "la correction de résolution est soustraite dans ce scénario de contrôle"
        )
        payload["correlations"] = [
            {
                "left": "repeatability",
                "right": "resolution",
                "coefficient": 0.25,
                "justification": "corrélation non nulle imposée pour le cas de contrôle",
            }
        ]
        payload["correlation_justification"] = (
            "cas de contrôle avec coefficient positif et sensibilité négative"
        )
        checks = verify_with_external_oracles(build_uncertainty_study(payload))
        self.assertTrue(all(item.status in {"match", "unavailable"} for item in checks))


if __name__ == "__main__":
    unittest.main()
