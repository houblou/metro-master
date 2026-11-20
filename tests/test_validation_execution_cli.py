import contextlib
import io
import math
import unittest
from unittest import mock

from metro_master.cli import _configure_utf8_streams, main
from metro_master.comparison import compare_results, separate_bench_uncertainty
from metro_master.execution import CalculationRequest, DeterministicEngine
from metro_master.models import UncertaintyComponent
from metro_master.uncertainty import propagate_linear


class ScientificValidationTests(unittest.TestCase):
    def test_nonfinite_measurement_is_rejected(self):
        with self.assertRaises(ValueError):
            compare_results(math.nan, 1.0, 0.1, 0.1)

    def test_nonfinite_coverage_factor_is_rejected(self):
        with self.assertRaises(ValueError):
            propagate_linear(
                [UncertaintyComponent("x", 1.0)], coverage_factor=math.nan
            )

    def test_incompatible_units_are_rejected(self):
        with self.assertRaises(ValueError):
            propagate_linear(
                [
                    UncertaintyComponent("pressure", 1.0, unit="kPa"),
                    UncertaintyComponent("temperature", 1.0, unit="degC"),
                ]
            )

    def test_scalar_correlation_requires_justification(self):
        with self.assertRaises(ValueError):
            compare_results(1.0, 0.0, 0.2, 0.1, correlation=0.5)

    def test_separation_requires_written_identifiability_evidence(self):
        with self.assertRaises(ValueError):
            separate_bench_uncertainty(
                math.sqrt(13.0),
                4.0,
                covariance=6.0,
                identifiability_confirmed=True,
            )

    def test_impossible_covariance_is_rejected(self):
        with self.assertRaises(ValueError):
            separate_bench_uncertainty(
                1.0,
                1.0,
                covariance=100.0,
                identifiability_confirmed=True,
                identifiability_justification="same complete scalar model",
            )


class ExecutionAndCliTests(unittest.TestCase):
    def test_redirected_cli_streams_are_utf8(self):
        stdout = mock.Mock()
        stderr = mock.Mock()
        stdout.isatty.return_value = False
        stderr.isatty.return_value = False
        with mock.patch("metro_master.cli.sys.stdout", stdout), mock.patch(
            "metro_master.cli.sys.stderr", stderr
        ):
            _configure_utf8_streams()
        stdout.reconfigure.assert_called_once_with(encoding="utf-8")
        stderr.reconfigure.assert_called_once_with(encoding="utf-8")

    def test_calculation_request_constructor_enforces_identifier(self):
        with self.assertRaises(ValueError):
            CalculationRequest("", "budget", {"components": []})

    def test_builtin_payload_rejects_unknown_fields(self):
        with self.assertRaises(ValueError):
            DeterministicEngine().calculate(
                CalculationRequest(
                    "typo",
                    "budget",
                    {
                        "components": [
                            {"name": "x", "standard_uncertainty": 1.0}
                        ],
                        "coverge_factor": 9.0,
                    },
                )
            )

    def test_invalid_structured_calculation_is_recorded_as_rejected(self):
        record = DeterministicEngine().execute(
            CalculationRequest(
                "bad-units",
                "budget",
                {
                    "components": [
                        {"name": "a", "standard_uncertainty": 1.0, "unit": "kPa"},
                        {"name": "b", "standard_uncertainty": 1.0, "unit": "degC"},
                    ]
                },
            )
        )
        self.assertEqual(record.status, "rejected")
        self.assertEqual(record.error_type, "ScientificValidationError")

    def test_cli_reports_zero_denominator_without_traceback(self):
        payload = {
            "bench_value": 2.0,
            "reference_value": 1.0,
            "bench_standard_uncertainty": 0.0,
            "reference_standard_uncertainty": 0.0,
            "bench_expanded_uncertainty": 0.0,
            "reference_expanded_uncertainty": 0.0,
        }
        stderr = io.StringIO()
        with mock.patch("metro_master.cli._load_json", return_value=payload):
            with contextlib.redirect_stderr(stderr):
                exit_code = main(["compare", "unused.json"])
        self.assertEqual(exit_code, 2)
        self.assertIn("zero denominator", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
