import json
from pathlib import Path
import tempfile
import unittest

from metro_master.knowledge import KnowledgeRecord, KnowledgeStore
from metro_master.orchestrator import MetroOrchestrator
from metro_master.research import (
    ResearchRequest,
    ResearchSource,
    execute_research,
)


class OfficialProvider:
    def __init__(self):
        self.queries = []

    def search(self, request):
        self.queries.append(request.query)
        return (
            ResearchSource(
                title="Official GUM publication page",
                url="https://www.bipm.org/en/committees/jc/jcgm/publications",
                summary="Official publication metadata for the JCGM guides.",
                publisher="BIPM/JCGM",
                source_type="official",
                published_at="2025-01-01T00:00:00Z",
            ),
        )


class ResearchBackend:
    def __init__(self, *, repeat_query=False):
        self.repeat_query = repeat_query
        self.research_phases = []
        self.audit_context = ""

    @staticmethod
    def _request():
        return {
            "id": "gum-status",
            "query": "JCGM GUM current official publication",
            "purpose": "Verify the current official publication status",
            "allowed_domains": ["bipm.org"],
            "primary_sources_only": True,
            "max_results": 3,
        }

    def complete(self, *, agent, system_prompt, user_request, shared_context):
        context = json.loads(shared_context)
        if agent == "WEB-RESEARCHER":
            phase = context["task_phase"]
            self.research_phases.append(phase)
            if phase == "plan_research":
                return json.dumps(
                    {
                        "message": "Initial official-source search.",
                        "research_requests": [self._request()],
                    }
                )
            if phase == "refine_research" and self.repeat_query:
                return json.dumps(
                    {
                        "message": "Accidental duplicate.",
                        "research_requests": [self._request()],
                    }
                )
            if phase == "refine_research":
                return "No additional gap found."
            return "Synthesis based on the recorded BIPM source."
        if agent == "METRO-AUDIT":
            self.audit_context = shared_context
        return f"{agent}: ok"


class ResearchAndKnowledgeTests(unittest.TestCase):
    def test_private_research_source_url_is_rejected(self):
        with self.assertRaises(ValueError):
            ResearchSource(
                title="Local service",
                url="http://127.0.0.1/internal",
                summary="Must never be accepted as an Internet source.",
            )

    def test_domain_and_primary_source_policy_are_enforced(self):
        class BadProvider:
            def search(self, request):
                return [
                    {
                        "title": "Blog mirror",
                        "url": "https://example.com/gum",
                        "summary": "Unverified secondary summary.",
                        "source_type": "secondary",
                    }
                ]

        request = ResearchRequest(
            "official-only",
            "GUM status",
            "Find official status",
            allowed_domains=("bipm.org",),
            primary_sources_only=True,
        )
        record = execute_research(BadProvider(), request)
        self.assertEqual(record.status, "rejected")
        self.assertEqual(record.error_type, "NoAdmissibleSources")

    def test_orchestrator_runs_iterative_research_and_exposes_sources_to_audit(self):
        provider = OfficialProvider()
        backend = ResearchBackend()
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            store = KnowledgeStore(directory)
            result = MetroOrchestrator(
                research_provider=provider,
                knowledge_store=store,
            ).execute(
                "Faire une recherche approfondie Internet sur le statut du GUM",
                backend,
            )
            web_turns = [
                turn for turn in result.turns if turn.agent == "WEB-RESEARCHER"
            ]
            self.assertEqual(
                backend.research_phases,
                ["plan_research", "refine_research", "synthesize_research"],
            )
            self.assertEqual([turn.internal for turn in web_turns], [True, True, False])
            self.assertEqual(len(provider.queries), 1)
            self.assertEqual(web_turns[-1].research_records[0].status, "ok")
            self.assertTrue(
                any(
                    item.origin == "web_source" and item.status == "candidate"
                    for item in web_turns[-1].knowledge_submissions
                )
            )
            audit = json.loads(backend.audit_context)
            visible = [
                turn for turn in audit["turns"] if turn["agent"] == "WEB-RESEARCHER"
            ]
            self.assertEqual(len(visible), 1)
            self.assertEqual(
                visible[0]["internet_research"][0]["sources"][0]["publisher"],
                "BIPM/JCGM",
            )
            self.assertEqual(store.search("GUM"), ())
            self.assertGreaterEqual(
                len(store.search("GUM", include_candidates=True)), 1
            )

    def test_duplicate_query_is_rejected_and_not_reexecuted(self):
        provider = OfficialProvider()
        backend = ResearchBackend(repeat_query=True)
        result = MetroOrchestrator(research_provider=provider).execute(
            "Faire une recherche approfondie Internet sur le GUM",
            backend,
        )
        final_web_turn = [
            turn for turn in result.turns if turn.agent == "WEB-RESEARCHER"
        ][-1]
        self.assertEqual(len(provider.queries), 1)
        self.assertEqual(
            [record.status for record in final_web_turn.research_records],
            ["ok", "rejected"],
        )
        self.assertEqual(
            final_web_turn.research_records[1].error_type,
            "DuplicateResearchRequest",
        )

    def test_missing_provider_is_a_visible_rejection(self):
        backend = ResearchBackend()
        result = MetroOrchestrator().execute(
            "Faire une recherche approfondie Internet sur le GUM",
            backend,
        )
        final_web_turn = [
            turn for turn in result.turns if turn.agent == "WEB-RESEARCHER"
        ][-1]
        self.assertEqual(final_web_turn.research_records[0].status, "rejected")
        self.assertEqual(
            final_web_turn.research_records[0].error_type,
            "ResearchProviderUnavailable",
        )

    def test_candidate_memory_requires_human_promotion_before_reuse(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            store = KnowledgeStore(directory)
            record = store.add(
                title="Validated pressure note",
                body="The pressure comparison uses paired observations.",
                origin="human_note",
                source_ref="lab-method:42",
                tags=("pressure", "comparison"),
                created_by="tester",
            )
            self.assertEqual(store.search("pressure"), ())
            candidate_hits = store.search("pressure", include_candidates=True)
            self.assertEqual(candidate_hits[0].record.status, "candidate")
            promoted = store.promote(
                record.id,
                approved_by="Metrology manager",
                reason="Checked against laboratory method 42",
            )
            self.assertEqual(promoted.status, "validated")
            self.assertEqual(store.search("pressure")[0].record.id, record.id)

    def test_only_validated_memory_is_injected_into_agent_context(self):
        class ContextBackend:
            def __init__(self):
                self.first_context = None

            def complete(
                self, *, agent, system_prompt, user_request, shared_context
            ):
                if self.first_context is None:
                    self.first_context = json.loads(shared_context)
                return f"{agent}: ok"

        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            store = KnowledgeStore(directory)
            candidate = store.add(
                title="Pressure comparison method",
                body="Use paired pressure readings under stable conditions.",
                origin="human_note",
                source_ref="lab-method:pressure",
                tags=("pressure", "pression", "comparaison"),
                created_by="tester",
            )
            backend = ContextBackend()
            MetroOrchestrator(knowledge_store=store).execute(
                "Analyser la comparaison de pression", backend
            )
            self.assertEqual(backend.first_context["knowledge_hits"], [])

            store.promote(
                candidate.id,
                approved_by="Metrology manager",
                reason="Method reviewed",
            )
            backend = ContextBackend()
            MetroOrchestrator(knowledge_store=store).execute(
                "Analyser la comparaison de pression", backend
            )
            self.assertEqual(
                backend.first_context["knowledge_hits"][0]["record"]["id"],
                candidate.id,
            )

    def test_knowledge_integrity_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            store = KnowledgeStore(directory)
            record = store.add(
                title="Note",
                body="Original content",
                origin="human_note",
                source_ref="note:1",
                created_by="tester",
            )
            payload = record.to_dict()
            payload["body"] = "Tampered content"
            with self.assertRaises(ValueError):
                KnowledgeRecord.from_dict(payload)


if __name__ == "__main__":
    unittest.main()
