import math
import unittest

from metro_master.models import Correlation, UncertaintyComponent
from metro_master.uncertainty import build_correlation_matrix, propagate_linear


class UncertaintyTests(unittest.TestCase):
    def test_independent_root_sum_square(self):
        result = propagate_linear(
            [
                UncertaintyComponent("a", 3.0, owner="bench"),
                UncertaintyComponent("b", 4.0, owner="reference"),
            ]
        )
        self.assertAlmostEqual(result.combined_variance, 25.0)
        self.assertAlmostEqual(result.combined_standard_uncertainty, 5.0)
        self.assertAlmostEqual(result.expanded_uncertainty, 10.0)
        self.assertEqual(result.effective_degrees_of_freedom, math.inf)

    def test_correlated_difference_has_correct_sign(self):
        result = propagate_linear(
            [
                UncertaintyComponent("bench", 3.0, 1.0, "bench"),
                UncertaintyComponent("reference", 4.0, -1.0, "reference"),
            ],
            [Correlation("bench", "reference", 0.5, "shared reference")],
        )
        self.assertAlmostEqual(result.combined_variance, 13.0)
        self.assertAlmostEqual(result.combined_standard_uncertainty, math.sqrt(13.0))
        self.assertEqual(result.effective_degrees_of_freedom, math.inf)
        self.assertEqual(
            result.effective_degrees_of_freedom_method,
            "welch_satterthwaite",
        )
        covariance_terms = [item for item in result.terms if item.kind == "covariance"]
        self.assertEqual(len(covariance_terms), 1)
        self.assertAlmostEqual(covariance_terms[0].value, -12.0)

    def test_finite_dof_correlation_requires_a_joint_sampling_model(self):
        result = propagate_linear(
            [
                UncertaintyComponent(
                    "bench", 3.0, 1.0, "bench", degrees_of_freedom=9
                ),
                UncertaintyComponent("reference", 4.0, -1.0, "reference"),
            ],
            [Correlation("bench", "reference", 0.5, "shared sampling")],
        )
        self.assertIsNone(result.effective_degrees_of_freedom)
        self.assertEqual(
            result.effective_degrees_of_freedom_method,
            "not_applicable_correlated_finite_dof",
        )
        self.assertTrue(any("joint sampling model" in item for item in result.warnings))

    def test_perfect_common_mode_can_cancel(self):
        result = propagate_linear(
            [
                UncertaintyComponent("left", 2.0, 1.0, "shared"),
                UncertaintyComponent("right", 2.0, -1.0, "shared"),
            ],
            [Correlation("left", "right", 1.0, "same realization")],
        )
        self.assertAlmostEqual(result.combined_standard_uncertainty, 0.0)

    def test_non_psd_correlation_is_rejected(self):
        components = [UncertaintyComponent(name, 1.0) for name in ("a", "b", "c")]
        correlations = [
            Correlation("a", "b", 1.0, "test"),
            Correlation("a", "c", 1.0, "test"),
            Correlation("b", "c", -1.0, "test"),
        ]
        with self.assertRaises(ValueError):
            build_correlation_matrix(components, correlations)

    def test_non_zero_correlation_requires_justification(self):
        with self.assertRaises(ValueError):
            Correlation("a", "b", 0.25)


if __name__ == "__main__":
    unittest.main()

