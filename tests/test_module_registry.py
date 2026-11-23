import json
from pathlib import Path
import tempfile
import unittest

from metro_master.execution import (
    BUILTIN_OPERATIONS,
    CalculationRequest,
    DeterministicEngine,
)
from metro_master.module_registry import (
    FormulaCalculationModule,
    FormulaModuleDefinition,
    ModuleStore,
    parse_unit_expression,
)


class ModuleRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).parents[1] / "modules" / "examples" / "linear-scale.json"
        cls.definition_value = json.loads(path.read_text(encoding="utf-8"))

    def test_formula_module_calculates_with_units_and_hash(self):
        definition = FormulaModuleDefinition.from_dict(self.definition_value)
        module = FormulaCalculationModule(definition)
        result = module.calculate(
            {
                "inputs": {
                    "x": {"value": 100.0, "unit": "kPa"},
                    "gain": {"value": 1.001, "unit": ""},
                    "offset": {"value": -0.05, "unit": "kPa"},
                }
            }
        )
        self.assertAlmostEqual(result["output"]["value"], 100.05)
        self.assertEqual(result["output"]["unit"], "kPa")
        self.assertEqual(result["definition_sha256"], definition.integrity_sha256())

    def test_formula_registry_uses_the_core_dimensional_algebra(self):
        self.assertEqual(parse_unit_expression("kPa"), parse_unit_expression("Pa"))
        self.assertEqual(
            parse_unit_expression("kPa/K"),
            {"L": -1, "M": 1, "T": -2, "Theta": -1},
        )

    def test_formula_rejects_python_and_attribute_access(self):
        for expression in (
            "__import__('os').system('dir')",
            "x.__class__",
            "[x][0]",
            "(x for x in [1])",
        ):
            value = dict(self.definition_value)
            value["expression"] = expression
            with self.subTest(expression=expression):
                with self.assertRaises(ValueError):
                    FormulaModuleDefinition.from_dict(value)

    def test_formula_enforces_units_domain_and_unknown_inputs(self):
        module = FormulaCalculationModule(
            FormulaModuleDefinition.from_dict(self.definition_value)
        )
        invalid_payloads = (
            {
                "inputs": {
                    "x": {"value": 1.0, "unit": "Pa"},
                    "gain": {"value": 1.0, "unit": ""},
                    "offset": {"value": 0.0, "unit": "kPa"},
                }
            },
            {
                "inputs": {
                    "x": {"value": 1001.0, "unit": "kPa"},
                    "gain": {"value": 1.0, "unit": ""},
                    "offset": {"value": 0.0, "unit": "kPa"},
                }
            },
            {
                "inputs": {
                    "x": {"value": 1.0, "unit": "kPa"},
                    "gain": {"value": 1.0, "unit": ""},
                    "offset": {"value": 0.0, "unit": "kPa"},
                    "surprise": {"value": 0.0, "unit": ""},
                }
            },
        )
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    module.calculate(payload)

    def test_dimensional_analysis_rejects_incoherent_addition(self):
        value = json.loads(json.dumps(self.definition_value))
        value["expression"] = "x + gain"
        with self.assertRaises(ValueError):
            FormulaModuleDefinition.from_dict(value)

    def test_dimensional_analysis_accepts_derived_unit(self):
        value = {
            "schema_version": 1,
            "id": "average-speed",
            "version": "1.0.0",
            "title": "Average speed",
            "description": "Distance divided by duration.",
            "kind": "formula",
            "inputs": [
                {"name": "distance", "unit": "m", "description": "Distance"},
                {"name": "duration", "unit": "s", "description": "Duration", "minimum": 0.001},
            ],
            "expression": "distance / duration",
            "output": {"name": "speed", "unit": "m/s", "description": "Average speed"},
            "references": [],
            "validation_cases": [
                {
                    "name": "one",
                    "source": "independent hand calculation",
                    "inputs": {
                        "distance": {"value": 10.0, "unit": "m"},
                        "duration": {"value": 2.0, "unit": "s"},
                    },
                    "expected_value": 5.0,
                    "expected_unit": "m/s",
                    "absolute_tolerance": 1e-12,
                }
            ],
        }
        module = FormulaCalculationModule(FormulaModuleDefinition.from_dict(value))
        result = module.calculate(
            {
                "inputs": {
                    "distance": {"value": 12.0, "unit": "m"},
                    "duration": {"value": 3.0, "unit": "s"},
                }
            }
        )
        self.assertEqual(result["output"], {"name": "speed", "value": 4.0, "unit": "m/s"})

    def test_candidate_promotion_execution_deprecation(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            store = ModuleStore(directory, reserved_ids=BUILTIN_OPERATIONS)
            candidate = store.submit(self.definition_value, created_by="test-agent")
            self.assertEqual(candidate.status, "candidate")
            self.assertTrue(store.test("linear-scale", "1.0.0").passed)
            promoted = store.promote(
                "linear-scale", "1.0.0", approved_by="human-reviewer"
            )
            self.assertEqual(promoted.status, "validated")
            engine = DeterministicEngine.from_store(store)
            result = engine.calculate(
                CalculationRequest(
                    "run-1",
                    "linear-scale",
                    {
                        "inputs": {
                            "x": {"value": 10.0, "unit": "kPa"},
                            "gain": {"value": 1.02, "unit": ""},
                            "offset": {"value": -0.1, "unit": "kPa"},
                        }
                    },
                )
            )
            self.assertAlmostEqual(result["output"]["value"], 10.1)
            deprecated = store.deprecate(
                "linear-scale",
                "1.0.0",
                approved_by="human-reviewer",
                reason="superseded",
            )
            self.assertEqual(deprecated.status, "deprecated")
            self.assertEqual(store.active_records(), ())

    def test_rollback_selects_prior_validated_version(self):
        second = json.loads(json.dumps(self.definition_value))
        second["version"] = "1.1.0"
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            store = ModuleStore(directory, reserved_ids=BUILTIN_OPERATIONS)
            for definition in (self.definition_value, second):
                store.submit(definition, created_by="agent")
                store.promote(
                    definition["id"],
                    definition["version"],
                    approved_by="reviewer",
                )
            self.assertEqual(store.active_records()[0].definition.version, "1.1.0")
            store.rollback("linear-scale", "1.0.0", approved_by="reviewer")
            self.assertEqual(store.active_records()[0].definition.version, "1.0.0")

    def test_reserved_core_id_cannot_be_submitted(self):
        value = json.loads(json.dumps(self.definition_value))
        value["id"] = "budget"
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            store = ModuleStore(directory, reserved_ids=BUILTIN_OPERATIONS)
            with self.assertRaises(ValueError):
                store.submit(value, created_by="agent")


if __name__ == "__main__":
    unittest.main()
