import json
import tempfile
from pathlib import Path
import unittest

from metro_master.agents import compose_prompt
from metro_master.orchestrator import MetroOrchestrator
from metro_master.token_budget import (
    TokenBudgetPolicy,
    TokenLedger,
    estimate_tokens,
)


class BudgetAwareBackend:
    def __init__(self):
        self.calls = []
        self.audit_context = None

    def complete(
        self,
        *,
        agent,
        system_prompt,
        user_request,
        shared_context,
        max_output_tokens,
    ):
        self.calls.append((agent, max_output_tokens))
        if agent == "METRO-AUDIT":
            self.audit_context = json.loads(shared_context)
        return f"{agent}: ok"


class TokenBudgetTests(unittest.TestCase):
    def test_default_profiles_load_and_are_ordered(self):
        eco = TokenBudgetPolicy.load("eco")
        standard = TokenBudgetPolicy.load("standard")
        deep = TokenBudgetPolicy.load("deep")
        self.assertLess(eco.max_total_tokens, standard.max_total_tokens)
        self.assertLess(standard.max_total_tokens, deep.max_total_tokens)
        self.assertEqual(TokenBudgetPolicy.load().mode, "standard")

    def test_custom_configuration_is_editable_json(self):
        payload = {
            "default_mode": "custom",
            "profiles": {
                "custom": {
                    "max_total_tokens": 10000,
                    "max_input_tokens_per_call": 4000,
                    "max_output_tokens_per_call": 800,
                    "final_audit_reserve_tokens": 2000,
                    "max_agent_turns": 4,
                    "max_context_response_tokens": 300,
                    "max_knowledge_hit_tokens": 200,
                }
            },
        }
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            path = Path(directory) / "tokens.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            policy = TokenBudgetPolicy.load(path=path)
        self.assertEqual(policy.mode, "custom")
        self.assertEqual(policy.max_agent_turns, 4)

    def test_prompt_contains_budget_contract_and_master_document(self):
        prompt = compose_prompt("METRO-MASTER", TokenBudgetPolicy.load("eco"))
        self.assertIn("Contrat de sobriété contextuelle", prompt)
        self.assertIn("prompt maître éditable", prompt)
        self.assertIn("mode : `eco`", prompt)

    def test_eco_execution_passes_hard_output_limit_when_supported(self):
        backend = BudgetAwareBackend()
        result = MetroOrchestrator(
            token_policy=TokenBudgetPolicy.load("eco")
        ).execute("Calculer une incertitude", backend)
        self.assertEqual(result.turns[-1].agent, "METRO-AUDIT")
        self.assertTrue(backend.calls)
        self.assertTrue(all(limit <= 1000 for _, limit in backend.calls))
        self.assertEqual(result.token_budget["mode"], "eco")
        self.assertEqual(result.token_budget["call_count"], len(backend.calls))
        self.assertIn("token_budget", backend.audit_context)

    def test_eco_plan_keeps_audit_and_reports_omitted_agents(self):
        policy = TokenBudgetPolicy.load("eco")
        full = MetroOrchestrator(token_policy=policy).plan(
            "Caractériser un banc de pression par comparaison avec une référence"
        )
        selected, skipped = policy.select_steps(full.steps)
        self.assertLessEqual(len(selected), policy.max_agent_turns)
        self.assertEqual(selected[-1].agent, "METRO-AUDIT")
        self.assertTrue(skipped)

    def test_ledger_preserves_audit_reserve(self):
        policy = TokenBudgetPolicy.load("eco")
        ledger = TokenLedger(policy)
        allowance = ledger.require_call(5000, final_audit=False)
        self.assertLessEqual(allowance, policy.max_output_tokens_per_call)
        ledger.record(5000, 500, allowance)
        self.assertGreaterEqual(
            ledger.estimated_remaining_tokens,
            policy.final_audit_reserve_tokens,
        )

    def test_estimator_handles_utf8_and_empty_text(self):
        self.assertEqual(estimate_tokens(""), 0)
        self.assertGreater(estimate_tokens("métrologie"), 0)


if __name__ == "__main__":
    unittest.main()
