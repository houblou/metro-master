from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from metro_master.execution import CalculationRequest, DeterministicEngine
from metro_master.orchestrator import MetroOrchestrator
from metro_master.source_registry import SourceRegistry
from metro_master.study_history import StudyStore
from metro_master.trace import canonical_sha256


ROOT = Path(__file__).resolve().parents[1]


class OneComponentBackend:
    def complete(self, *, agent, system_prompt, user_request, shared_context):
        if agent == "MODEL-COMPILER":
            return json.dumps(
                {
                    "message": "Compiled.",
                    "calculation_requests": [
                        {
                            "id": "one-component",
                            "operation": "budget",
                            "payload": {
                                "components": [
                                    {
                                        "name": "u",
                                        "standard_uncertainty": 1.0,
                                        "sensitivity": 1.0,
                                        "owner": "bench",
                                        "unit": "kPa",
                                        "distribution": "unspecified",
                                        "source": "user_request",
                                        "degrees_of_freedom": None,
                                    }
                                ],
                                "correlations": [],
                                "coverage_factor": 2.0,
                            },
                            "evidence": [
                                {"field_path": "/components/0/standard_uncertainty", "source_ref": "user_request", "excerpt": "u = 1.0 kPa", "evidence_type": "provided"},
                                {"field_path": "/components/0/sensitivity", "source_ref": "declared:method", "excerpt": "sensitivity 1.0", "evidence_type": "method_choice"},
                                {"field_path": "/components/0/unit", "source_ref": "user_request", "excerpt": "u = 1.0 kPa", "evidence_type": "provided"},
                                {"field_path": "/coverage_factor", "source_ref": "user_request", "excerpt": "k = 2.0", "evidence_type": "provided"},
                            ],
                            "assumptions": ["Correlations are assumed zero."],
                        }
                    ],
                }
            )
        if agent == "METRO-AUDIT":
            return json.dumps(
                {
                    "message": "u = 1.0 kPa",
                    "conclusion_claims": [
                        {
                            "request_id": "one-component",
                            "result_pointer": "/combined_standard_uncertainty",
                            "stated_value": 1.0,
                            "unit": "kPa",
                            "statement": "Combined standard uncertainty",
                        }
                    ],
                }
            )
        return f"{agent}: ok"


class TraceSourceCompletionTests(unittest.TestCase):
    def test_successful_and_rejected_calculations_are_traced(self):
        engine = DeterministicEngine()
        successful = engine.execute(
            CalculationRequest(
                "trace-ok",
                "budget",
                {
                    "components": [
                        {"name": "u", "standard_uncertainty": 1.0, "unit": "kPa"}
                    ]
                },
            ),
            execution_origin="test:structured_input",
        )
        self.assertEqual(successful.status, "ok")
        self.assertIsNotNone(successful.trace)
        successful.trace.verify()
        self.assertEqual(
            successful.trace.result_sha256,
            canonical_sha256(successful.result),
        )
        self.assertTrue(successful.trace.module["implementation_sha256"])
        self.assertTrue(successful.trace.module["validation_suite_sha256"])

        rejected = engine.execute(
            CalculationRequest("trace-rejected", "unknown-operation", {}),
            execution_origin="test:structured_input",
            previous_trace_sha256=successful.trace.trace_sha256,
        )
        self.assertEqual(rejected.status, "rejected")
        self.assertIsNotNone(rejected.trace)
        rejected.trace.verify()
        self.assertEqual(
            rejected.trace.previous_trace_sha256,
            successful.trace.trace_sha256,
        )

    def test_trace_tampering_is_detected(self):
        record = DeterministicEngine().execute(
            CalculationRequest(
                "trace-tamper",
                "budget",
                {
                    "components": [
                        {"name": "u", "standard_uncertainty": 1.0, "unit": "kPa"}
                    ]
                },
            )
        )
        tampered = replace(record.trace, result_sha256="0" * 64)
        with self.assertRaises(ValueError):
            tampered.verify()

    def test_four_frozen_sources_and_targets_are_valid(self):
        registry = SourceRegistry.load()
        self.assertEqual(len(registry.assets), 4)
        self.assertEqual(
            {item.source_id for item in registry.assets},
            {
                "kdense-uncertainty-and-units",
                "kdense-metrology-scientist",
                "nist-stat-handbook-pack",
                "mp-ai-20-metrology",
            },
        )
        registry.validate_local_targets(ROOT)

    def test_trace_output_refuses_to_overwrite(self):
        from metro_master.cli import _write_trace

        record = DeterministicEngine().execute(
            CalculationRequest(
                "trace-file",
                "budget",
                {
                    "components": [
                        {"name": "u", "standard_uncertainty": 1.0, "unit": "kPa"}
                    ]
                },
            )
        )
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "trace.json"
            _write_trace(str(path), record)
            self.assertTrue(path.is_file())
            with self.assertRaises(FileExistsError):
                _write_trace(str(path), record)

    def test_study_revisions_continue_the_trace_chain(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            orchestrator = MetroOrchestrator(study_store=StudyStore(directory))
            first = orchestrator.execute(
                "Calculer avec u = 1.0 kPa et k = 2.0",
                OneComponentBackend(),
            )
            first_trace = next(
                record.trace
                for turn in first.turns
                for record in turn.calculations
            )
            second = orchestrator.execute(
                "Recalculer avec u = 1.0 kPa et k = 2.0",
                OneComponentBackend(),
                study_id=first.study_reference.study_id,
            )
            second_trace = next(
                record.trace
                for turn in second.turns
                for record in turn.calculations
            )
            self.assertEqual(
                second_trace.previous_trace_sha256,
                first_trace.trace_sha256,
            )


if __name__ == "__main__":
    unittest.main()
