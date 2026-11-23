import math
import unittest

from metro_master.comparison import (
    IdentifiabilityError,
    compare_results,
    normalized_error,
    paired_statistics,
    separate_bench_uncertainty,
)


class ComparisonTests(unittest.TestCase):
    def test_correlated_difference(self):
        result = compare_results(
            11.0,
            10.0,
            3.0,
            4.0,
            correlation=0.5,
            correlation_justification="shared reference",
        )
        self.assertAlmostEqual(result.difference, 1.0)
        self.assertAlmostEqual(result.correction_to_apply_to_bench, -1.0)
        self.assertAlmostEqual(result.covariance, 6.0)
        self.assertAlmostEqual(result.difference_standard_uncertainty, math.sqrt(13.0))

    def test_normalized_error(self):
        value = normalized_error(1.0, 2.0, 1.0)
        self.assertAlmostEqual(value, 1 / math.sqrt(5.0))

    def test_paired_statistics(self):
        result = paired_statistics([10.2, 10.4, 10.3], [10.0, 10.1, 10.2])
        self.assertEqual(result.count, 3)
        self.assertAlmostEqual(result.mean_difference, 0.2)
        self.assertAlmostEqual(result.correction_to_apply_to_bench, -0.2)
        self.assertGreater(result.standard_deviation_of_differences, 0)

    def test_separation_requires_explicit_identifiability(self):
        with self.assertRaises(IdentifiabilityError):
            separate_bench_uncertainty(math.sqrt(13.0), 4.0, covariance=6.0)

    def test_separation_recovers_bench_when_model_is_confirmed(self):
        result = separate_bench_uncertainty(
            math.sqrt(13.0),
            4.0,
            covariance=6.0,
            identifiability_confirmed=True,
            identifiability_justification="same complete scalar model",
        )
        self.assertAlmostEqual(result.bench_standard_uncertainty, 3.0)

    def test_inconsistent_separation_is_rejected(self):
        with self.assertRaises(IdentifiabilityError):
            separate_bench_uncertainty(
                1.0,
                4.0,
                covariance=0.0,
                identifiability_confirmed=True,
                identifiability_justification="same complete scalar model",
            )


if __name__ == "__main__":
    unittest.main()

