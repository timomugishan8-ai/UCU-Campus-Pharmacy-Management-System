"""Member 3 tests for prescription domain rules and creation.

Run with: py -m unittest tests.test_prescription -v
Tests use a temporary SQLite file, never the live demo database.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from database.connection import Database
from database.repositories.medicine_repository import MedicineRepository
from database.repositories.prescription_repository import PrescriptionRepository
from database.repositories.stock_repository import StockRepository
from domain.prescription import (
    InvalidPrescriptionStateError,
    Prescription,
    PrescriptionLine,
    UnknownMedicineError,
)
from services.prescription_service import PrescriptionService


class _BaseMedicine:
    """Test double mirroring the interface Member 2 will implement."""

    def __init__(self, controlled: bool = False) -> None:
        self.is_controlled = controlled

    def requires_prescriber_code(self) -> bool:
        return self.is_controlled


class _ControlledMedicine(_BaseMedicine):
    def __init__(self) -> None:
        super().__init__(True)

    def requires_prescriber_code(self) -> bool:
        return True  # meaningful override


class _OrdinaryMedicine(_BaseMedicine):
    def __init__(self) -> None:
        super().__init__(False)

    def requires_prescriber_code(self) -> bool:
        return False  # meaningful override


class PrescriptionLineTests(unittest.TestCase):
    def test_valid_line_and_dict_round_trip(self) -> None:
        line = PrescriptionLine("MED-001", 3, line_id=7, prescription_id=2)
        self.assertEqual(line.medicine_code, "MED-001")
        self.assertEqual(line.quantity, 3)
        restored = PrescriptionLine.from_dict(line.to_dict())
        self.assertEqual(restored.medicine_code, "MED-001")
        self.assertEqual(restored.line_id, 7)

    def test_rejects_invalid_codes_and_quantities(self) -> None:
        for bad_code in ("", "   ", None, 123):
            with self.subTest(code=bad_code):
                with self.assertRaises(ValueError):
                    PrescriptionLine(bad_code, 1)
        for bad_quantity in (0, -1, 1.5, True, "2"):
            with self.subTest(quantity=bad_quantity):
                with self.assertRaises(ValueError):
                    PrescriptionLine("MED-001", bad_quantity)


class PrescriptionDomainTests(unittest.TestCase):
    def test_single_and_multiple_lines(self) -> None:
        single = Prescription(
            branch_id=1,
            patient_identifier="PAT-1",
            lines=[PrescriptionLine("MED-001", 1)],
        )
        self.assertTrue(single.is_pending)
        self.assertEqual(len(single.lines), 1)

        multiple = Prescription(
            branch_id=1,
            patient_identifier="PAT-2",
            lines=[
                PrescriptionLine("MED-001", 2),
                PrescriptionLine("MED-004", 1),
            ],
        )
        self.assertEqual(len(multiple.lines), 2)

    def test_empty_lines_and_duplicates_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Prescription(branch_id=1, patient_identifier="PAT-1", lines=[])
        with self.assertRaises(ValueError):
            Prescription(
                branch_id=1,
                patient_identifier="PAT-1",
                lines=[PrescriptionLine("MED-001", 1), PrescriptionLine("MED-001", 2)],
            )

    def test_branch_patient_status_validation(self) -> None:
        line = PrescriptionLine("MED-001", 1)
        with self.assertRaises(ValueError):
            Prescription(branch_id=0, patient_identifier="PAT-1", lines=[line])
        with self.assertRaises(ValueError):
            Prescription(branch_id=1, patient_identifier="", lines=[line])
        with self.assertRaises(ValueError):
            Prescription(
                branch_id=1,
                patient_identifier="PAT-1",
                lines=[line],
                status="unknown",
            )

    def test_status_transitions(self) -> None:
        prescription = Prescription(
            branch_id=1,
            patient_identifier="PAT-1",
            lines=[PrescriptionLine("MED-001", 1)],
        )
        self.assertTrue(prescription.can_dispense())
        prescription.mark_dispensed("2026-11-18 10:00:00")
        self.assertTrue(prescription.is_dispensed)
        self.assertEqual(prescription.dispensed_at, "2026-11-18 10:00:00")
        with self.assertRaises(InvalidPrescriptionStateError):
            prescription.mark_dispensed()
        with self.assertRaises(InvalidPrescriptionStateError):
            prescription.mark_cancelled()

        cancelled = Prescription(
            branch_id=1,
            patient_identifier="PAT-2",
            lines=[PrescriptionLine("MED-001", 1)],
        )
        cancelled.mark_cancelled()
        self.assertTrue(cancelled.is_cancelled)
        self.assertFalse(cancelled.can_dispense())
        with self.assertRaises(InvalidPrescriptionStateError):
            cancelled.mark_dispensed()

    def test_authorisation_check_uses_common_medicine_behaviour(self) -> None:
        ordinary = _OrdinaryMedicine()
        controlled = _ControlledMedicine()
        prescription = Prescription(
            branch_id=1,
            patient_identifier="PAT-1",
            lines=[
                PrescriptionLine("ORD", 1),
                PrescriptionLine("CTL", 1),
            ],
        )
        self.assertFalse(
            prescription.requires_authorised_prescriber({"ORD": ordinary, "CTL": ordinary})
        )
        self.assertTrue(
            prescription.requires_authorised_prescriber(
                {"ORD": ordinary, "CTL": controlled}
            )
        )
        self.assertTrue(
            prescription.requires_authorised_prescriber({"ORD": ordinary})
        )  # missing medicine is treated as needing the check


class PrescriptionServiceCreationTests(unittest.TestCase):
    def setUp(self) -> None:
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.remove(self.db_path)
        self.db = Database(self.db_path)
        self.db.initialize_schema()
        with self.db.transaction() as conn:
            conn.execute(
                "INSERT INTO branches (branch_id, branch_name) VALUES (?, ?)",
                (1, "Main Campus"),
            )
            conn.executemany(
                "INSERT INTO medicines "
                "(medicine_code, name, unit_price, reorder_level, is_controlled) "
                "VALUES (?, ?, ?, ?, ?)",
                [
                    ("MED-001", "Paracetamol", 2.5, 5, 0),
                    ("MED-004", "Morphine", 12.0, 5, 1),
                ],
            )
        self.service = PrescriptionService(
            PrescriptionRepository(self.db),
            MedicineRepository(self.db),
            StockRepository(self.db),
        )

    def tearDown(self) -> None:
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_create_single_and_multiline_prescriptions(self) -> None:
        single = self.service.create_prescription("PAT-1", 1, None, [("MED-001", 2)])
        self.assertIsNotNone(single.prescription_id)
        self.assertEqual(single.status, "pending")
        self.assertEqual(len(single.lines), 1)

        multiple = self.service.create_prescription(
            "PAT-2", 1, "DR-1001", [("MED-001", 2), ("MED-004", 1)]
        )
        self.assertEqual(len(multiple.lines), 2)
        self.assertEqual(multiple.prescriber_code, "DR-1001")

    def test_empty_lines_unknown_medicine_and_unknown_branch_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.service.create_prescription("PAT-1", 1, None, [])
        with self.assertRaises(UnknownMedicineError):
            self.service.create_prescription("PAT-1", 1, None, [("NO-SUCH", 1)])
        with self.assertRaises(ValueError):
            self.service.create_prescription("PAT-1", 99, None, [("MED-001", 1)])

    def test_get_unknown_prescription_returns_none(self) -> None:
        self.assertIsNone(self.service.get_prescription(9999))

    def test_cancel_changes_status(self) -> None:
        created = self.service.create_prescription(
            "PAT-3", 1, None, [("MED-001", 1)]
        )
        cancelled = self.service.cancel_prescription(created.prescription_id)
        self.assertTrue(cancelled.is_cancelled)
        self.assertIsNone(cancelled.dispensed_at)


if __name__ == "__main__":
    unittest.main()
