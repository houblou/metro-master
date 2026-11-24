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
        self.assertIn("## 2. Inventaire Ishikawa", result.latex_note)
        self.assertIn("## 3. Équation de mesure", result.latex_note)
        self.assertIn("## 4. Évaluation des composantes", result.latex_note)
        self.assertIn("## 5. Composition et corrélations", result.latex_note)
        self.assertIn("$$\nL = x + c_{res}\n$$", result.latex_note)
        self.assertIn("x = (9.9,\\;10,\\;10.1)", result.latex_note)
        self.assertIn("Validité de la propagation linéaire", result.latex_note)

    def test_every_component_must_be_connected_to_ishikawa(self) -> None:
        payload = fixture()
        payload["influences"] = payload["influences"][:1]
        with self.assertRaisesRegex(ValueError, "without a direct Ishikawa"):
            build_uncertainty_study(payload)

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
