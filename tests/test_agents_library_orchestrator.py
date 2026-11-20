import json
from pathlib import Path
import tempfile
import unittest

from metro_master.agents import compose_prompt, list_agents
from metro_master.library import DocumentLibrary
from metro_master.orchestrator import (
    MetroOrchestrator,
    RoutingPlan,
    RoutingStep,
)
from metro_master.module_registry import ModuleStore
from metro_master.pdf_library import ExtractedPdfPage, PdfPageChunk


class FakeBackend:
    def complete(self, *, agent, system_prompt, user_request, shared_context):
        return f"{agent}: reviewed {len(shared_context)}"


class NoAuditRouter:
    def plan(self, request):
        return RoutingPlan(
            request,
            (RoutingStep("THEORIA", "probe"),),
            mandatory_final_audit=True,
        )


class StructuredBackend:
    def __init__(self):
        self.audit_context = ""

    def complete(self, *, agent, system_prompt, user_request, shared_context):
        if agent == "GUM-EXPERT":
            return json.dumps(
                {
                    "message": "Budget proposé pour exécution déterministe.",
                    "calculation_requests": [
                        {
                            "id": "budget-1",
                            "operation": "budget",
                            "payload": {
                                "components": [
                                    {
                                        "name": "a",
                                        "standard_uncertainty": 3.0,
                                        "unit": "kPa",
                                    },
                                    {
                                        "name": "b",
                                        "standard_uncertainty": 4.0,
                                        "unit": "kPa",
                                    },
                                ]
                            },
                        }
                    ],
                }
            )
        if agent == "METRO-AUDIT":
            self.audit_context = shared_context
        return f"{agent}: ok"


class PdfBackend:
    def __init__(self):
        self.pdf_phases = []
        self.audit_context = ""

    def complete(self, *, agent, system_prompt, user_request, shared_context):
        context = json.loads(shared_context)
        if agent == "PDF-EXTRACTOR":
            phase = context["task_phase"]
            self.pdf_phases.append(phase)
            if phase == "extract_chunk":
                chunk = context["document_chunk"]
                return f"Extraction pages {chunk['start_page']}-{chunk['end_page']}"
            return "Rapport documentaire final paginé"
        if agent == "METRO-AUDIT":
            self.audit_context = shared_context
        return f"{agent}: ok"


class ModuleProposalBackend:
    def __init__(self, proposal):
        self.proposal = proposal
        self.audit_context = ""

    def complete(self, *, agent, system_prompt, user_request, shared_context):
        if agent == "MODULE-BUILDER":
            return json.dumps(
                {
                    "message": "Proposition candidate.",
                    "calculation_requests": [],
                    "module_proposals": [self.proposal],
                }
            )
        if agent == "METRO-AUDIT":
            self.audit_context = shared_context
        return f"{agent}: ok"


class AgentsLibraryOrchestratorTests(unittest.TestCase):
    def test_thirteen_complete_agent_prompts(self):
        agents = list_agents()
        self.assertEqual(len(agents), 13)
        for agent in agents:
            prompt = compose_prompt(agent.name)
            self.assertIn("Contrat scientifique commun", prompt)
            self.assertIn(f"Rôle — {agent.name}", prompt)

    def test_catalog_is_metadata_honest(self):
        library = DocumentLibrary.load_default()
        self.assertGreaterEqual(len(library.records), 27)
        self.assertTrue(all(item.content_status == "metadata_only" for item in library.records))
        self.assertTrue(all(item.local_path is None for item in library.records))
        references = {item.reference for item in library.records}
        for pending_reference in ("R140", "R113", "R280", "R353", "R560", "R603"):
            self.assertTrue(any(pending_reference in item for item in references))

    def test_theoria_includes_imported_skill_invariants(self):
        prompt = compose_prompt("THEORIA")
        self.assertIn("h(Y, X_1", prompt)
        self.assertIn("Type A et type B", prompt)
        self.assertIn("R140, R113, R280, R353, R560 et R603", prompt)

    def test_comparison_route_contains_mandatory_specialists(self):
        plan = MetroOrchestrator().plan(
            "Caractériser un banc de pression par comparaison interlaboratoires"
        )
        agents = [step.agent for step in plan.steps]
        for expected in (
            "METRO-MASTER",
            "THEORIA",
            "PHYS-METRO",
            "METRO-COMPARE",
            "DATA-METRO",
            "GUM-EXPERT",
            "NORM-EXPERT",
            "METRO-AUDIT",
        ):
            self.assertIn(expected, agents)
        self.assertEqual(agents[-1], "METRO-AUDIT")

    def test_pdf_route_contains_extractor_before_theoria(self):
        plan = MetroOrchestrator().plan("Lire intégralement ce PDF de métrologie")
        agents = [step.agent for step in plan.steps]
        self.assertIn("PDF-EXTRACTOR", agents)
        self.assertLess(agents.index("PDF-EXTRACTOR"), agents.index("THEORIA"))

    def test_new_calculation_route_contains_module_builder(self):
        plan = MetroOrchestrator().plan(
            "Ajouter un nouveau module de calcul déclaratif"
        )
        agents = [step.agent for step in plan.steps]
        self.assertIn("MODULE-BUILDER", agents)
        self.assertEqual(agents[-1], "METRO-AUDIT")

    def test_free_text_calculation_route_contains_model_compiler(self):
        plan = MetroOrchestrator().plan(
            "Calculer un budget d'incertitude depuis ce texte libre"
        )
        agents = [step.agent for step in plan.steps]
        self.assertIn("MODEL-COMPILER", agents)
        self.assertEqual(agents[-1], "METRO-AUDIT")

    def test_deep_web_research_route_contains_researcher(self):
        plan = MetroOrchestrator().plan(
            "Faire une recherche approfondie Internet sur le statut du GUM"
        )
        agents = [step.agent for step in plan.steps]
        self.assertIn("WEB-RESEARCHER", agents)
        self.assertLess(agents.index("WEB-RESEARCHER"), agents.index("THEORIA"))

    def test_orchestrator_passes_context_sequentially(self):
        result = MetroOrchestrator().execute("Calculer une incertitude", FakeBackend())
        self.assertGreaterEqual(len(result.turns), 4)
        self.assertEqual(result.turns[-1].agent, "METRO-AUDIT")

    def test_mandatory_audit_is_enforced_for_custom_router(self):
        result = MetroOrchestrator(NoAuditRouter()).execute("probe", FakeBackend())
        self.assertEqual([turn.agent for turn in result.turns], ["THEORIA", "METRO-AUDIT"])

    def test_structured_calculation_is_executed_and_passed_to_audit(self):
        backend = StructuredBackend()
        result = MetroOrchestrator().execute("Calculer une incertitude", backend)
        gum_turn = next(turn for turn in result.turns if turn.agent == "GUM-EXPERT")
        self.assertEqual(len(gum_turn.calculations), 1)
        record = gum_turn.calculations[0]
        self.assertEqual(record.status, "ok")
        self.assertAlmostEqual(record.result["combined_standard_uncertainty"], 5.0)
        audit_context = json.loads(backend.audit_context)
        calculations = [
            calculation
            for turn in audit_context["turns"]
            for calculation in turn["deterministic_calculations"]
        ]
        self.assertEqual(calculations[0]["status"], "ok")
        self.assertAlmostEqual(
            calculations[0]["result"]["combined_standard_uncertainty"], 5.0
        )

    def test_pdf_chunks_are_extracted_then_synthesized_before_audit(self):
        chunks = (
            PdfPageChunk(
                "DOC-1",
                "REF-1",
                "Document",
                "a" * 64,
                "private",
                22,
                1,
                20,
                (ExtractedPdfPage(1, "page one"),),
            ),
            PdfPageChunk(
                "DOC-1",
                "REF-1",
                "Document",
                "a" * 64,
                "private",
                22,
                21,
                22,
                (ExtractedPdfPage(21, "page twenty-one"),),
            ),
        )
        backend = PdfBackend()
        result = MetroOrchestrator().execute(
            "Analyser le document",
            backend,
            document_chunks=chunks,
        )
        pdf_turns = [turn for turn in result.turns if turn.agent == "PDF-EXTRACTOR"]
        self.assertEqual(backend.pdf_phases, ["extract_chunk", "extract_chunk", "synthesize_document"])
        self.assertEqual([turn.internal for turn in pdf_turns], [True, True, False])
        self.assertEqual(result.turns[-1].agent, "METRO-AUDIT")
        audit_context = json.loads(backend.audit_context)
        visible_pdf_turns = [
            turn for turn in audit_context["turns"] if turn["agent"] == "PDF-EXTRACTOR"
        ]
        self.assertEqual(len(visible_pdf_turns), 1)
        self.assertEqual(
            visible_pdf_turns[0]["untrusted_agent_response"],
            "Rapport documentaire final paginé",
        )

    def test_module_builder_can_submit_candidate_but_not_activate_it(self):
        proposal_path = (
            Path(__file__).parents[1] / "modules" / "examples" / "linear-scale.json"
        )
        proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            store = ModuleStore(directory, reserved_ids={"budget", "compare", "paired", "separate"})
            backend = ModuleProposalBackend(proposal)
            result = MetroOrchestrator(module_store=store).execute(
                "Ajouter un nouveau module de calcul",
                backend,
            )
            builder_turn = next(
                turn for turn in result.turns if turn.agent == "MODULE-BUILDER"
            )
            self.assertEqual(builder_turn.module_submissions[0].status, "candidate")
            self.assertEqual(store.load("linear-scale", "1.0.0").status, "candidate")
            self.assertEqual(store.active_records(), ())
            audit_context = json.loads(backend.audit_context)
            submissions = [
                submission
                for turn in audit_context["turns"]
                for submission in turn["module_submissions"]
            ]
            self.assertEqual(submissions[0]["status"], "candidate")


if __name__ == "__main__":
    unittest.main()

