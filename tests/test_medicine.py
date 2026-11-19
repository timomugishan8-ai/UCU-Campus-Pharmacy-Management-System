"""Member 2 tests: medicine domain hierarchy and MedicineService.

Covers the exam's required OOP evidence (inheritance, method overriding,
polymorphism), the validation rules (positive price, non-negative reorder
level, unique code) and the service's registration/lookup contract.
"""

import os
import tempfile
import unittest

from database.connection import Database
from database.repositories.medicine_repository import MedicineRepository
from domain.medicine import (
    ControlledMedicine,
    DuplicateMedicineError,
    InvalidMedicineError,
    Medicine,
    OrdinaryMedicine,
)
from domain.prescription import Prescription, PrescriptionLine
from services.medicine_service import MedicineService


class MedicineDomainTests(unittest.TestCase):
    """Object-level rules of the Medicine hierarchy."""

    def test_ordinary_medicine_construction_and_properties(self):
        medicine = OrdinaryMedicine("MED-001", "Paracetamol 500mg", 2.50, 20)
        self.assertEqual(medicine.medicine_code, "MED-001")
        self.assertEqual(medicine.name, "Paracetamol 500mg")
        self.assertEqual(medicine.unit_price, 2.50)
        self.assertEqual(medicine.reorder_level, 20)
        self.assertFalse(medicine.is_controlled)

    def test_controlled_medicine_construction(self):
        medicine = ControlledMedicine("MED-004", "Morphine 10mg", 12.00, 5)
        self.assertTrue(medicine.is_controlled)

    def test_inheritance_from_medicine_base(self):
        self.assertTrue(issubclass(OrdinaryMedicine, Medicine))
        self.assertTrue(issubclass(ControlledMedicine, Medicine))
        self.assertTrue(isinstance(OrdinaryMedicine("M1", "Name", 1.0), Medicine))

    def test_medicine_base_cannot_be_instantiated(self):
        # The base class declares the polymorphic behaviour as abstract.
        with self.assertRaises(TypeError):
            Medicine("M1", "Name", 1.0)

    def test_method_overriding_requires_prescriber_code(self):
        ordinary = OrdinaryMedicine("M1", "Name", 1.0)
        controlled = ControlledMedicine("M2", "Name", 1.0)
        # Each subclass overrides the same inherited signature.
        self.assertIs(ordinary.requires_prescriber_code(), False)
        self.assertIs(controlled.requires_prescriber_code(), True)

    def test_polymorphic_call_through_base_references(self):
        # Dispensing logic only knows the base type; behaviour differs
        # by subclass without any isinstance check.
        collection: list[Medicine] = [
            OrdinaryMedicine("M1", "Name", 1.0),
            ControlledMedicine("M2", "Name", 1.0),
        ]
        self.assertEqual(
            [medicine.requires_prescriber_code() for medicine in collection],
            [False, True],
        )

    def test_invalid_price_is_rejected(self):
        for bad_price in (0, -1.0, "2.50", None, True):
            with self.subTest(price=bad_price):
                with self.assertRaises(InvalidMedicineError):
                    OrdinaryMedicine("M1", "Name", bad_price)

    def test_negative_or_non_integer_reorder_level_is_rejected(self):
        for bad_level in (-1, 2.5, "10", None, True):
            with self.subTest(reorder_level=bad_level):
                with self.assertRaises(InvalidMedicineError):
                    OrdinaryMedicine("M1", "Name", 1.0, bad_level)

    def test_blank_code_or_name_is_rejected(self):
        for bad_text in ("", "   ", None, 42):
            with self.subTest(text=bad_text):
                with self.assertRaises(InvalidMedicineError):
                    OrdinaryMedicine(bad_text, "Name", 1.0)
                with self.assertRaises(InvalidMedicineError):
                    OrdinaryMedicine("M1", bad_text, 1.0)

    def test_attributes_are_read_only(self):
        medicine = OrdinaryMedicine("M1", "Name", 1.0, 5)
        for attribute, value in (
            ("medicine_code", "M2"),
            ("name", "Other"),
            ("unit_price", 9.99),
            ("reorder_level", 99),
            ("is_controlled", True),
        ):
            with self.subTest(attribute=attribute):
                with self.assertRaises(AttributeError):
                    setattr(medicine, attribute, value)

    def test_to_dict_and_from_dict_round_trip_preserves_subtype(self):
        for medicine in (
            OrdinaryMedicine("M1", "Name", 1.5, 4),
            ControlledMedicine("M2", "Other", 2.5, 0),
        ):
            with self.subTest(medicine=medicine):
                restored = Medicine.from_dict(medicine.to_dict())
                self.assertEqual(restored, medicine)
                self.assertIs(type(restored), type(medicine))

    def test_from_dict_maps_controlled_flag_to_subtype(self):
        row = {
            "medicine_code": "MED-004",
            "name": "Morphine 10mg",
            "unit_price": 12.0,
            "reorder_level": 5,
            "is_controlled": 1,
        }
        self.assertIsInstance(Medicine.from_dict(row), ControlledMedicine)
        row["is_controlled"] = 0
        self.assertIsInstance(Medicine.from_dict(row), OrdinaryMedicine)

    def test_create_factory_selects_subtype_from_flag(self):
        self.assertIsInstance(
            Medicine.create("M1", "Name", 1.0, 0, is_controlled=False),
            OrdinaryMedicine,
        )
        self.assertIsInstance(
            Medicine.create("M2", "Name", 1.0, 0, is_controlled=True),
            ControlledMedicine,
        )

    def test_equality_distinguishes_subtype_and_fields(self):
        ordinary = OrdinaryMedicine("M1", "Name", 1.0, 5)
        self.assertEqual(ordinary, OrdinaryMedicine("M1", "Name", 1.0, 5))
        self.assertNotEqual(ordinary, OrdinaryMedicine("M1", "Name", 1.0, 6))
        # Same data, different subclass, different behaviour: not equal.
        self.assertNotEqual(ordinary, ControlledMedicine("M1", "Name", 1.0, 5))


class MedicinePrescriptionIntegrationTests(unittest.TestCase):
    """The dispensing rule consumes the hierarchy polymorphically."""

    def _prescription(self) -> Prescription:
        return Prescription(
            branch_id=1,
            patient_identifier="PT-0001",
            lines=[PrescriptionLine("MED-001", 2)],
        )

    def test_controlled_medicine_triggers_authorisation_rule(self):
        prescription = self._prescription()
        medicines = {"MED-001": ControlledMedicine("MED-001", "Morphine", 12.0, 5)}
        self.assertTrue(prescription.requires_authorised_prescriber(medicines))

    def test_ordinary_medicine_does_not_trigger_authorisation_rule(self):
        prescription = self._prescription()
        medicines = {"MED-001": OrdinaryMedicine("MED-001", "Paracetamol", 2.5, 20)}
        self.assertFalse(prescription.requires_authorised_prescriber(medicines))

    def test_mixed_prescription_is_controlled_when_any_line_is(self):
        prescription = Prescription(
            branch_id=1,
            patient_identifier="PT-0002",
            lines=[
                PrescriptionLine("MED-001", 2),
                PrescriptionLine("MED-004", 1),
            ],
        )
        medicines = {
            "MED-001": OrdinaryMedicine("MED-001", "Paracetamol", 2.5, 20),
            "MED-004": ControlledMedicine("MED-004", "Morphine", 12.0, 5),
        }
        self.assertTrue(prescription.requires_authorised_prescriber(medicines))


class MedicineServiceTests(unittest.TestCase):
    """Registration and lookup against a real temporary database."""

    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = Database(self.db_path)
        self.db.initialize_schema()
        self.repository = MedicineRepository(self.db)
        self.service = MedicineService(self.repository)

    def tearDown(self):
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
        except OSError:
            pass

    def test_register_medicine_returns_stored_medicine(self):
        created = self.service.register_medicine(
            OrdinaryMedicine("MED-001", "Paracetamol 500mg", 2.50, 20)
        )
        self.assertEqual(created.medicine_code, "MED-001")
        self.assertEqual(created.unit_price, 2.50)

        fetched = self.service.get_medicine_by_code("MED-001")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched, created)

    def test_register_controlled_medicine_survives_round_trip(self):
        self.service.register_medicine(
            ControlledMedicine("MED-004", "Morphine 10mg", 12.00, 5)
        )
        fetched = self.service.get_medicine_by_code("MED-004")
        self.assertIsInstance(fetched, ControlledMedicine)
        self.assertTrue(fetched.requires_prescriber_code())

    def test_data_survives_service_restart(self):
        self.service.register_medicine(OrdinaryMedicine("MED-001", "Name", 1.0))
        # A fresh service over the same file simulates an application restart.
        restarted = MedicineService(MedicineRepository(Database(self.db_path)))
        fetched = restarted.get_medicine_by_code("MED-001")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.name, "Name")

    def test_duplicate_code_is_rejected(self):
        self.service.register_medicine(OrdinaryMedicine("MED-001", "Name", 1.0))
        with self.assertRaises(DuplicateMedicineError):
            self.service.register_medicine(
                ControlledMedicine("MED-001", "Other name", 2.0)
            )
        # The first registration is untouched.
        self.assertEqual(len(self.service.get_all_medicines()), 1)

    def test_invalid_price_cannot_be_registered(self):
        # The domain object refuses to exist, so nothing reaches the database.
        with self.assertRaises(InvalidMedicineError):
            OrdinaryMedicine("MED-009", "Bad price", 0)
        self.assertEqual(self.service.get_all_medicines(), [])

    def test_register_rejects_non_medicine_input(self):
        with self.assertRaises(TypeError):
            self.service.register_medicine(
                {"medicine_code": "M1", "name": "Name", "unit_price": 1.0}
            )

    def test_get_all_medicines_returns_objects_ordered_by_code(self):
        self.service.register_medicine(OrdinaryMedicine("MED-002", "B", 2.0))
        self.service.register_medicine(OrdinaryMedicine("MED-001", "A", 1.0))
        medicines = self.service.get_all_medicines()
        self.assertEqual(
            [medicine.medicine_code for medicine in medicines],
            ["MED-001", "MED-002"],
        )
        self.assertTrue(all(isinstance(m, Medicine) for m in medicines))

    def test_get_medicine_by_code_returns_none_for_unknown_code(self):
        self.assertIsNone(self.service.get_medicine_by_code("MED-404"))

    def test_get_medicine_by_code_rejects_blank_input(self):
        with self.assertRaises(ValueError):
            self.service.get_medicine_by_code("   ")


if __name__ == "__main__":
    unittest.main()
