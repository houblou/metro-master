import math
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from metro_master.models import UncertaintyComponent
from metro_master.quantities import (
    DependencyUnavailable,
    PintQuantityAdapter,
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

    def test_typed_sensitivity_converts_contributions_to_output_unit(self):
        result = propagate_linear(
            [
                UncertaintyComponent(
                    "temperature effect",
                    2.0,
                    sensitivity=3.0,
                    unit="°C",
                    sensitivity_unit="kPa/K",
                ),
                UncertaintyComponent(
                    "pressure effect",
                    500.0,
                    unit="Pa",
                    sensitivity_unit="1",
                ),
            ],
            output_unit="kPa",
        )
        self.assertEqual(result.unit, "kPa")
        self.assertAlmostEqual(
            result.combined_standard_uncertainty,
            math.sqrt(6.0**2 + 0.5**2),
        )

    def test_typed_sensitivity_rejects_incoherent_output_unit(self):
        with self.assertRaisesRegex(ValueError, "incompatible contribution units"):
            propagate_linear(
                [
                    UncertaintyComponent(
                        "temperature effect",
                        2.0,
                        unit="K",
                        sensitivity_unit="kPa/K",
                    )
                ],
                output_unit="mm",
            )

    def test_contribution_overflow_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "contribution must be finite"):
            propagate_linear(
                [
                    UncertaintyComponent(
                        "overflow",
                        1e308,
                        sensitivity=2.0,
                        unit="kPa",
                    )
                ],
                output_unit="kPa",
            )

    def test_pint_adapter_is_explicitly_optional(self):
        with patch(
            "metro_master.quantities.importlib.import_module",
            side_effect=ImportError("not installed"),
        ):
            with self.assertRaisesRegex(DependencyUnavailable, "units.*extra"):
                PintQuantityAdapter()

    def test_pint_adapter_uses_supported_temperature_difference_units(self):
        calls = []

        class FakeQuantity:
            def __init__(self, value, unit):
                self.magnitude = value
                calls.append(("from", unit))

            def to(self, unit):
                calls.append(("to", unit))
                return self

        fake_pint = SimpleNamespace(
            UnitRegistry=lambda: SimpleNamespace(Quantity=FakeQuantity)
        )
        with patch(
            "metro_master.quantities.importlib.import_module",
            return_value=fake_pint,
        ):
            adapter = PintQuantityAdapter()
            adapter.convert_value(1.0, "°C", "K", difference=True)
        self.assertEqual(calls, [("from", "delta_degC"), ("to", "kelvin")])


if __name__ == "__main__":
    unittest.main()
