"""Member 3 tests for atomic dispensing and rollback.

Run with: py -m unittest tests.test_dispensing -v
Every test uses a fresh temporary SQLite database.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from typing import Any, Optional

from database.connection import Database
from database.repositories.medicine_repository import MedicineRepository
from database.repositories.prescription_repository import PrescriptionRepository
from database.repositories.stock_repository import StockRepository
from domain.prescription import (
    InsufficientStockError,
    InvalidPrescriptionStateError,
    UnauthorisedPrescriberError,
    UnknownMedicineError,
)
from services.prescription_service import PrescriptionService


class _MedicineRepositoryMissingOne:
    """Test double: hides one medicine to simulate a broken prescription line."""

    def __init__(self, wrapped: Any, missing_code: str) -> None:
        self.wrapped = wrapped
        self.missing_code = missing_code

    def get_by_code(self, code: str, conn: Any = None) -> Optional[dict]:
        if code == self.missing_code:
            return None
        return self.wrapped.get_by_code(code, conn=conn)


class DispensingTests(unittest.TestCase):
    def setUp(self) -> None:
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.remove(self.db_path)

        self.db = Database(self.db_path)
        self.db.initialize_schema()
        with self.db.transaction() as conn:
            conn.executemany(
                "INSERT INTO branches (branch_id, branch_name) VALUES (?, ?)",
                [(1, "Main Campus"), (2, "East Campus")],
            )
            conn.executemany(
                "INSERT INTO medicines "
                "(medicine_code, name, unit_price, reorder_level, is_controlled) "
                "VALUES (?, ?, ?, ?, ?)",
                [
                    ("MED-001", "Paracetamol", 2.5, 5, 0),
                    ("MED-002", "Amoxicillin", 5.0, 5, 0),
                    ("MED-004", "Morphine", 12.0, 5, 1),
                ],
            )
            conn.executemany(
                "INSERT INTO stock (medicine_code, branch_id, quantity) "
                "VALUES (?, ?, ?)",
                [
                    ("MED-001", 1, 10),
                    ("MED-002", 1, 10),
                    ("MED-004", 1, 10),
                    ("MED-001", 2, 50),
                ],
            )
            conn.execute(
                "INSERT INTO authorised_prescribers (prescriber_code, prescriber_name) "
                "VALUES (?, ?)",
                ("DR-1001", "Dr. A. Example"),
            )

        self.medicine_repository = MedicineRepository(self.db)
        self.stock_repository = StockRepository(self.db)
        self.service = PrescriptionService(
            PrescriptionRepository(self.db),
            self.medicine_repository,
            self.stock_repository,
        )

    def tearDown(self) -> None:
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _quantity(self, code: str, branch_id: int = 1) -> int:
        return self.stock_repository.get_quantity(code, branch_id)

    def _status(self, prescription_id: int) -> str:
        data = self.service.get_prescription(prescription_id)
        assert data is not None
        return data.status

    # ------------------------------------------------------------------ #
    # Success cases
    # ------------------------------------------------------------------ #
    def test_successful_multi_line_dispense(self) -> None:
        prescription = self.service.create_prescription(
            "PAT-1", 1, None, [("MED-001", 2), ("MED-002", 3)]
        )
        result = self.service.dispense_prescription(prescription.prescription_id)

        self.assertTrue(result.is_dispensed)
        self.assertIsNotNone(result.dispensed_at)
        self.assertEqual(self._quantity("MED-001"), 8)
        self.assertEqual(self._quantity("MED-002"), 7)

    def test_controlled_medicine_with_authorised_prescriber(self) -> None:
        prescription = self.service.create_prescription(
            "PAT-2", 1, "DR-1001", [("MED-004", 2)]
        )
        result = self.service.dispense_prescription(prescription.prescription_id)
        self.assertTrue(result.is_dispensed)
        self.assertEqual(self._quantity("MED-004"), 8)

    def test_ordinary_medicine_is_not_blocked_by_allow_list(self) -> None:
        prescription = self.service.create_prescription(
            "PAT-3", 1, None, [("MED-001", 1)]
        )
        result = self.service.dispense_prescription(prescription.prescription_id)
        self.assertTrue(result.is_dispensed)
        self.assertEqual(self._quantity("MED-001"), 9)

    # ------------------------------------------------------------------ #
    # Failure cases: every one must leave stock and status unchanged
    # ------------------------------------------------------------------ #
    def test_insufficient_stock_rolls_back_every_line(self) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE stock SET quantity = 2 WHERE medicine_code = ? AND branch_id = ?",
                ("MED-002", 1),
            )
        prescription = self.service.create_prescription(
            "PAT-4", 1, None, [("MED-001", 3), ("MED-002", 5)]
        )

        with self.assertRaises(InsufficientStockError):
            self.service.dispense_prescription(prescription.prescription_id)

        self.assertEqual(self._quantity("MED-001"), 10)
        self.assertEqual(self._quantity("MED-002"), 2)
        self.assertEqual(self._status(prescription.prescription_id), "pending")

    def test_unauthorised_prescriber_is_rejected(self) -> None:
        prescription = self.service.create_prescription(
            "PAT-5", 1, "DR-9999", [("MED-001", 1), ("MED-004", 2)]
        )

        with self.assertRaises(UnauthorisedPrescriberError):
            self.service.dispense_prescription(prescription.prescription_id)

        self.assertEqual(self._quantity("MED-001"), 10)
        self.assertEqual(self._quantity("MED-004"), 10)
        self.assertEqual(self._status(prescription.prescription_id), "pending")

    def test_missing_prescriber_code_for_controlled_medicine_is_rejected(self) -> None:
        prescription = self.service.create_prescription(
            "PAT-6", 1, None, [("MED-004", 1)]
        )
        with self.assertRaises(UnauthorisedPrescriberError):
            self.service.dispense_prescription(prescription.prescription_id)
        self.assertEqual(self._quantity("MED-004"), 10)
        self.assertEqual(self._status(prescription.prescription_id), "pending")

    def test_repeat_dispense_is_rejected(self) -> None:
        prescription = self.service.create_prescription(
            "PAT-7", 1, None, [("MED-001", 4)]
        )
        first = self.service.dispense_prescription(prescription.prescription_id)
        self.assertTrue(first.is_dispensed)

        with self.assertRaises(InvalidPrescriptionStateError):
            self.service.dispense_prescription(prescription.prescription_id)
        self.assertEqual(self._quantity("MED-001"), 6)

    def test_cancelled_prescription_cannot_be_dispensed(self) -> None:
        prescription = self.service.create_prescription(
            "PAT-8", 1, None, [("MED-002", 2)]
        )
        self.service.cancel_prescription(prescription.prescription_id)

        with self.assertRaises(InvalidPrescriptionStateError):
            self.service.dispense_prescription(prescription.prescription_id)
        self.assertEqual(self._quantity("MED-002"), 10)

    def test_unknown_medicine_line_is_rejected_without_stock_change(self) -> None:
        prescription = self.service.create_prescription(
            "PAT-9", 1, None, [("MED-001", 1), ("MED-002", 2)]
        )
        original_repository = self.service.medicine_repository
        self.service.medicine_repository = _MedicineRepositoryMissingOne(
            original_repository, "MED-002"
        )
        try:
            with self.assertRaises(UnknownMedicineError):
                self.service.dispense_prescription(prescription.prescription_id)
        finally:
            self.service.medicine_repository = original_repository

        self.assertEqual(self._quantity("MED-001"), 10)
        self.assertEqual(self._quantity("MED-002"), 10)
        self.assertEqual(self._status(prescription.prescription_id), "pending")

    def test_branch_specific_stock_is_used(self) -> None:
        # Branch 1 has 10, branch 2 has 50. Asking for 12 at branch 1 must fail.
        prescription = self.service.create_prescription(
            "PAT-10", 1, None, [("MED-001", 12)]
        )
        with self.assertRaises(InsufficientStockError):
            self.service.dispense_prescription(prescription.prescription_id)

        self.assertEqual(self._quantity("MED-001", 1), 10)
        self.assertEqual(self._quantity("MED-001", 2), 50)

    def test_competing_dispense_attempts_do_not_oversell(self) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE stock SET quantity = 5 WHERE medicine_code = ? AND branch_id = ?",
                ("MED-001", 1),
            )
        prescription = self.service.create_prescription(
            "PAT-11", 1, None, [("MED-001", 5)]
        )

        self.assertTrue(
            self.service.dispense_prescription(prescription.prescription_id).is_dispensed
        )
        with self.assertRaises(InvalidPrescriptionStateError):
            self.service.dispense_prescription(prescription.prescription_id)

        self.assertEqual(self._quantity("MED-001"), 0)
        self.assertEqual(self._status(prescription.prescription_id), "dispensed")

    def test_stock_never_becomes_negative(self) -> None:
        prescription = self.service.create_prescription(
            "PAT-12", 1, None, [("MED-002", 11)]
        )
        with self.assertRaises(InsufficientStockError):
            self.service.dispense_prescription(prescription.prescription_id)
        self.assertGreaterEqual(self._quantity("MED-002"), 0)


if __name__ == "__main__":
    unittest.main()
