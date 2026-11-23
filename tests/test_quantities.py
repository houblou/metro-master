import math
import unittest

from metro_master.models import UncertaintyComponent
from metro_master.quantities import (
    compatible_units,
    convert_standard_uncertainty,
    convert_value,
    parse_unit,
)
from metro_master.uncertainty import propagate_linear


class QuantityTests(unittest.TestCase):
    def test_pressure_and_length_conversions(self):
        self.assertEqual(convert_value(1.0, "bar", "kPa"), 100.0)
        self.assertEqual(convert_value(1000.0, "µm", "mm"), 1.0)
        self.assertTrue(compatible_units("m/s", "mm/s"))
        self.assertFalse(compatible_units("kPa", "mm"))

    def test_affine_temperature_and_uncertainty_are_distinct(self):
        self.assertAlmostEqual(convert_value(20.0, "°C", "K"), 293.15)
        self.assertAlmostEqual(
            convert_standard_uncertainty(1.0, "°C", "K"),
            1.0,
        )

    def test_unknown_and_affine_compound_units_are_rejected(self):
        with self.assertRaises(ValueError):
            parse_unit("psi")
        with self.assertRaises(ValueError):
            parse_unit("°C/s")

    def test_budget_is_invariant_under_coherent_unit_conversion(self):
        in_kpa = propagate_linear(
            [
                UncertaintyComponent("a", 1.0, unit="kPa"),
                UncertaintyComponent("b", 500.0, unit="Pa"),
            ]
        )
        all_kpa = propagate_linear(
            [
                UncertaintyComponent("a", 1.0, unit="kPa"),
                UncertaintyComponent("b", 0.5, unit="kPa"),
            ]
        )
        self.assertAlmostEqual(
            in_kpa.combined_standard_uncertainty,
            all_kpa.combined_standard_uncertainty,
        )
        self.assertAlmostEqual(in_kpa.combined_standard_uncertainty, math.sqrt(1.25))


if __name__ == "__main__":
    unittest.main()
