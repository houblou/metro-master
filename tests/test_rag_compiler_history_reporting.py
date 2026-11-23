import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from metro_master.execution import (
    CalculationRequest,
    DeterministicEngine,
    InputEvidence,
)
from metro_master.cli import main
from metro_master.knowledge import KnowledgeStore
from metro_master.orchestrator import MetroOrchestrator
from metro_master.rag import (
    CallableEmbeddingProvider,
    HybridRagRetriever,
    VectorKnowledgeIndex,
)
from metro_master.reporting import render_study_report
from metro_master.study_history import StudyStore


class SemanticFixtureProvider:
    id = "semantic-fixture-v1"
    dimensions = 8

    def embed(self, texts):
        vectors = []
        for text in texts:
            lowered = text.casefold()
            if "thermal" in lowered or "temperature" in lowered:
                vectors.append([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
            elif "pressure" in lowered or "pression" in lowered:
                vectors.append([0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
            else:
                vectors.append([0.0] * 8)
        return vectors


class CompilerAndAuditBackend:
    def __init__(self, *, stated_value=5.0, unit="kPa"):
        self.stated_value = stated_value
        self.unit = unit

    def complete(self, *, agent, system_prompt, user_request, shared_context):
        if agent == "MODEL-COMPILER":
            return json.dumps(
                {
                    "message": "Compiled only from the supplied text.",
                    "calculation_requests": [
                        {
                            "id": "text-budget",
                            "operation": "budget",
                            "payload": {
                                "components": [
                                    {
                                        "name": "u1",
                                        "standard_uncertainty": 3.0,
                                        "sensitivity": 1.0,
                                        "owner": "bench",
                                        "unit": "kPa",
                                        "distribution": "unspecified",
                                        "source": "user_request",
                                        "degrees_of_freedom": None,
                                    },
                                    {
                                        "name": "u2",
                                        "standard_uncertainty": 4.0,
                                        "sensitivity": 1.0,
                                        "owner": "bench",
                                        "unit": "kPa",
                                        "distribution": "unspecified",
                                        "source": "user_request",
                                        "degrees_of_freedom": None,
                                    },
                                ],
                                "correlations": [],
                                "coverage_factor": 2.0,
                            },
                            "evidence": [
                                {
                                    "field_path": "/components/0/standard_uncertainty",
                                    "source_ref": "user_request",
                                    "excerpt": "u1 = 3.0 kPa",
                                    "evidence_type": "provided",
                                },
                                {
                                    "field_path": "/components/1/standard_uncertainty",
                                    "source_ref": "user_request",
                                    "excerpt": "u2 = 4.0 kPa",
                                    "evidence_type": "provided",
                                },
                                {
                                    "field_path": "/components/0/sensitivity",
                                    "source_ref": "declared:method",
                                    "excerpt": "sensitivity 1.0",
                                    "evidence_type": "method_choice",
                                },
                                {
                                    "field_path": "/components/1/sensitivity",
                                    "source_ref": "declared:method",
                                    "excerpt": "sensitivity 1.0",
                                    "evidence_type": "method_choice",
                                },
                                {
                                    "field_path": "/components/0/unit",
                                    "source_ref": "user_request",
                                    "excerpt": "u1 = 3.0 kPa",
                                    "evidence_type": "provided",
                                },
                                {
                                    "field_path": "/components/1/unit",
                                    "source_ref": "user_request",
                                    "excerpt": "u2 = 4.0 kPa",
                                    "evidence_type": "provided",
                                },
                                {
                                    "field_path": "/coverage_factor",
                                    "source_ref": "declared:method",
                                    "excerpt": "coverage factor 2.0",
                                    "evidence_type": "method_choice",
                                },
                            ],
                            "assumptions": [
                                "Correlation coefficients are assumed zero.",
                                "Sensitivity coefficients are set to 1.0.",
                                "Coverage factor 2.0 is a declared method choice."
                            ],
                        }
                    ],
                }
            )
        if agent == "METRO-AUDIT":
            return json.dumps(
                {
                    "message": f"Combined standard uncertainty is {self.stated_value} kPa.",
                    "conclusion_claims": [
                        {
                            "request_id": "text-budget",
                            "result_pointer": "/combined_standard_uncertainty",
                            "stated_value": self.stated_value,
                            "unit": self.unit,
                            "statement": "Combined standard uncertainty",
                        }
                    ],
                }
            )
        return f"{agent}: ok"


class PlainBackend:
    def complete(self, *, agent, system_prompt, user_request, shared_context):
        return f"{agent}: ok"


class RagCompilerHistoryReportingTests(unittest.TestCase):
    def test_persistent_vector_index_finds_semantic_synonym(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            store = KnowledgeStore(Path(directory) / "knowledge")
            thermal = store.add(
                title="Temperature compensation",
                body="Compensation of sensor temperature drift.",
                origin="human_note",
                source_ref="method:temperature",
                tags=("temperature",),
                created_by="tester",
            )
            pressure = store.add(
                title="Pressure comparison",
                body="Paired readings for pressure.",
                origin="human_note",
                source_ref="method:pressure",
                tags=("pressure",),
                created_by="tester",
            )
            for record in (thermal, pressure):
                store.promote(
                    record.id,
                    approved_by="manager",
                    reason="fixture reviewed",
                )
            index_root = Path(directory) / "vectors"
            index = VectorKnowledgeIndex(index_root, SemanticFixtureProvider())
            retriever = HybridRagRetriever(store, index)
            hits = retriever.search("thermal effects", limit=1)
            self.assertEqual(hits[0].record.id, thermal.id)
            self.assertTrue((index_root / "index.json").is_file())

            reloaded = VectorKnowledgeIndex(index_root, SemanticFixtureProvider())
            self.assertEqual(
                reloaded.search("thermal", store, limit=1)[0].record.id,
                thermal.id,
            )

    def test_callable_embedding_provider_validates_dimensions(self):
        provider = CallableEmbeddingProvider(
            "fixture", 8, lambda texts: [[1.0] * 8 for _ in texts]
        )
        self.assertEqual(len(provider.embed(["text"])[0]), 8)

    def test_provenance_checked_compilation_succeeds(self):
        request = CalculationRequest(
            "budget-from-text",
            "budget",
            {
                "components": [
                    {
                        "name": "u1",
                        "standard_uncertainty": 3.0,
                        "sensitivity": 1.0,
                        "owner": "bench",
                        "unit": "kPa",
                        "distribution": "unspecified",
                        "source": "user_request",
                        "degrees_of_freedom": None,
                    },
                    {
                        "name": "u2",
                        "standard_uncertainty": 4.0,
                        "sensitivity": 1.0,
                        "owner": "bench",
                        "unit": "kPa",
                        "distribution": "unspecified",
                        "source": "user_request",
                        "degrees_of_freedom": None,
                    },
                ],
                "correlations": [],
                "coverage_factor": 2.0,
            },
            evidence=(
                InputEvidence(
                    "/components/0/standard_uncertainty",
                    "user_request",
                    "u1 = 3.0 kPa",
                    "provided",
                ),
                InputEvidence(
                    "/components/1/standard_uncertainty",
                    "user_request",
                    "u2 = 4.0 kPa",
                    "provided",
                ),
                InputEvidence(
                    "/components/0/sensitivity",
                    "declared:method",
                    "sensitivity 1.0",
                    "method_choice",
                ),
                InputEvidence(
                    "/components/1/sensitivity",
                    "declared:method",
                    "sensitivity 1.0",
                    "method_choice",
                ),
                InputEvidence(
                    "/components/0/unit",
                    "user_request",
                    "u1 = 3.0 kPa",
                    "provided",
                ),
                InputEvidence(
                    "/components/1/unit",
                    "user_request",
                    "u2 = 4.0 kPa",
                    "provided",
                ),
                InputEvidence(
                    "/coverage_factor",
                    "declared:method",
                    "coverage factor 2.0",
                    "method_choice",
                ),
            ),
            assumptions=(
                "Correlation coefficients are assumed zero.",
                "Sensitivity coefficients are set to 1.0.",
                "Coverage factor 2.0 is a declared method choice.",
            ),
        )
        record = DeterministicEngine().execute(
            request,
            require_provenance=True,
            evidence_text="Given u1 = 3.0 kPa and u2 = 4.0 kPa.",
        )
        self.assertEqual(record.status, "ok")
        self.assertEqual(record.provenance_status, "conditional")
        self.assertAlmostEqual(record.result["combined_standard_uncertainty"], 5.0)

    def test_compilation_without_complete_evidence_is_rejected(self):
        request = CalculationRequest(
            "bad-model",
            "compare",
            {
                "bench_value": 10.0,
                "reference_value": 9.0,
                "bench_standard_uncertainty": 0.2,
                "reference_standard_uncertainty": 0.1,
            },
            evidence=(
                InputEvidence(
                    "/bench_value", "user_request", "bench 10.0", "provided"
                ),
            ),
        )
        record = DeterministicEngine().execute(
            request,
            require_provenance=True,
            evidence_text="bench 10.0",
        )
        self.assertEqual(record.status, "rejected")
        self.assertEqual(record.error_type, "ProvenanceValidationError")

    def test_evidence_excerpt_must_contain_the_compiled_value(self):
        request = CalculationRequest(
            "wrong-excerpt",
            "budget",
            {
                "components": [
                    {
                        "name": "u1",
                        "standard_uncertainty": 3.0,
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
            evidence=(
                InputEvidence(
                    "/components/0/standard_uncertainty",
                    "user_request",
                    "u1 = 30.0 kPa",
                    "provided",
                ),
                InputEvidence(
                    "/components/0/sensitivity",
                    "declared:method",
                    "sensitivity 1.0",
                    "method_choice",
                ),
                InputEvidence(
                    "/components/0/unit",
                    "user_request",
                    "u1 = 30.0 kPa",
                    "provided",
                ),
                InputEvidence(
                    "/coverage_factor",
                    "declared:method",
                    "coverage factor 2.0",
                    "method_choice",
                ),
            ),
            assumptions=(
                "Correlation coefficients are assumed zero.",
                "Sensitivity coefficient is set to 1.0.",
                "Coverage factor 2.0 is a declared method choice.",
            ),
        )
        record = DeterministicEngine().execute(
            request,
            require_provenance=True,
            evidence_text="u1 = 30.0 kPa",
        )
        self.assertEqual(record.status, "rejected")
        self.assertIn("does not contain its declared value", record.error)

    def test_prior_agent_prose_is_not_a_trusted_evidence_source(self):
        context = json.dumps(
            {
                "knowledge_hits": [],
                "document_chunk": None,
                "turns": [
                    {
                        "untrusted_agent_response": "invented value u1 = 3.0 kPa",
                        "deterministic_calculations": [],
                        "internet_research": [],
                    }
                ],
            }
        )
        sources = MetroOrchestrator._trusted_evidence_sources(
            "request without a value", context
        )
        self.assertEqual(sources, {"user_request": "request without a value"})

    def test_final_numeric_claim_is_automatically_verified(self):
        result = MetroOrchestrator().execute(
            "Calculer le budget avec u1 = 3.0 kPa et u2 = 4.0 kPa",
            CompilerAndAuditBackend(),
        )
        compiler = next(
            turn for turn in result.turns if turn.agent == "MODEL-COMPILER"
        )
        self.assertEqual(compiler.calculations[0].provenance_status, "conditional")
        self.assertEqual(result.conclusion_verification.status, "verified")

    def test_wrong_final_numeric_claim_is_rejected(self):
        result = MetroOrchestrator().execute(
            "Calculer le budget avec u1 = 3.0 kPa et u2 = 4.0 kPa",
            CompilerAndAuditBackend(stated_value=6.0),
        )
        self.assertEqual(result.conclusion_verification.status, "failed")
        self.assertEqual(
            result.conclusion_verification.claims[0].error,
            "stated value differs from deterministic result",
        )

    def test_wrong_final_unit_is_rejected(self):
        result = MetroOrchestrator().execute(
            "Calculer le budget avec u1 = 3.0 kPa et u2 = 4.0 kPa",
            CompilerAndAuditBackend(unit="Pa"),
        )
        self.assertEqual(result.conclusion_verification.status, "failed")
        self.assertIn(
            "differs from deterministic unit",
            result.conclusion_verification.claims[0].error,
        )

    def test_study_history_is_append_only_and_chained(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            store = StudyStore(directory)
            orchestrator = MetroOrchestrator(study_store=store)
            first = orchestrator.execute("Définir le mesurande", PlainBackend())
            second = orchestrator.execute(
                "Affiner le mesurande",
                PlainBackend(),
                study_id=first.study_reference.study_id,
            )
            self.assertEqual(first.study_reference.revision, 1)
            self.assertEqual(second.study_reference.revision, 2)
            revisions = store.revisions(first.study_reference.study_id)
            self.assertEqual(len(revisions), 2)
            self.assertEqual(
                revisions[1].previous_sha256,
                revisions[0].integrity_sha256,
            )

    def test_study_tampering_is_detected(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            store = StudyStore(directory)
            reference = store.save(
                "request",
                {"turns": [], "conclusion_verification": None},
                study_id="study-test-integrity-0001",
            )
            path = (
                Path(directory)
                / reference.study_id
                / "revision-000001.json"
            )
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["request"] = "tampered"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ValueError):
                store.load(reference.study_id)

    def test_reports_never_claim_certificate_or_accreditation_authority(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            store = StudyStore(directory)
            reference = store.save(
                "request",
                {
                    "turns": [],
                    "conclusion_verification": {"status": "not_applicable"},
                },
                study_id="study-report-fixture-0001",
            )
            snapshot = store.load(reference.study_id)
            draft = render_study_report(snapshot, "draft-certificate")
            assessment = render_study_report(
                snapshot, "accreditation-assessment"
            )
            self.assertIn("NE CONSTITUE PAS UN CERTIFICAT", draft)
            self.assertIn("N'ACCORDE", assessment)

    def test_study_cli_lists_and_exports_persisted_revision(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory) / "studies"
            store = StudyStore(root)
            reference = store.save(
                "request",
                {
                    "turns": [],
                    "conclusion_verification": {"status": "not_applicable"},
                },
                study_id="study-cli-fixture-0001",
            )
            output = Path(directory) / "report.md"
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(
                    main(["study-list", "--root", str(root)]),
                    0,
                )
                self.assertEqual(
                    main(
                        [
                            "study-export",
                            reference.study_id,
                            "--kind",
                            "technical-report",
                            "--output",
                            str(output),
                            "--root",
                            str(root),
                        ]
                    ),
                    0,
                )
            self.assertTrue(output.is_file())
            self.assertIn("Rapport technique", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
