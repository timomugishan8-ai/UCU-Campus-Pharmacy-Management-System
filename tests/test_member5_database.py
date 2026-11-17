"""Member 5 database and repository tests (unittest)."""

import os
import sqlite3
import tempfile
import unittest

from database.connection import Database
from database.repositories.medicine_repository import MedicineRepository
from database.repositories.branch_repository import BranchRepository
from database.repositories.stock_repository import StockRepository
from database.repositories.prescription_repository import PrescriptionRepository
from database.seed_data import seed


class Member5DatabaseTests(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = Database(self.db_path)
        self.db.initialize_schema()

    def tearDown(self):
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
        except OSError:
            pass

    def test_medicine_and_branch_creation(self):
        med_repo = MedicineRepository(self.db)
        branch_repo = BranchRepository(self.db)

        med_repo.add("M1", "Medicine One", 2.5, 5, False)
        medicine = med_repo.get_by_code("M1")
        self.assertIsNotNone(medicine)
        self.assertEqual(medicine["name"], "Medicine One")

        branch_id = branch_repo.add("Branch One")
        branch = branch_repo.get_by_id(branch_id)
        self.assertIsNotNone(branch)
        self.assertEqual(branch["branch_name"], "Branch One")

    def test_branch_specific_stock(self):
        med_repo = MedicineRepository(self.db)
        branch_repo = BranchRepository(self.db)
        stock_repo = StockRepository(self.db)

        med_repo.add("M1", "Medicine One", 2.5, 5, False)
        b1 = branch_repo.add("Branch One")
        b2 = branch_repo.add("Branch Two")

        stock_repo.set_quantity("M1", b1, 10)
        stock_repo.set_quantity("M1", b2, 20)
        stock_repo.increase("M1", b1, 5)
        stock_repo.decrease("M1", b2, 3)

        self.assertEqual(stock_repo.get_quantity("M1", b1), 15)
        self.assertEqual(stock_repo.get_quantity("M1", b2), 17)

    def test_stock_increase_decrease_and_low_stock(self):
        med_repo = MedicineRepository(self.db)
        branch_repo = BranchRepository(self.db)
        stock_repo = StockRepository(self.db)

        med_repo.add("M1", "Medicine One", 2.5, 5, False)
        med_repo.add("M2", "Medicine Two", 3.0, 10, False)
        branch_id = branch_repo.add("Branch One")

        stock_repo.set_quantity("M1", branch_id, 3)   # below reorder level 5
        stock_repo.set_quantity("M2", branch_id, 10)  # equal to reorder level 10

        stock_repo.increase("M1", branch_id, 2)
        self.assertEqual(stock_repo.get_quantity("M1", branch_id), 5)

        stock_repo.decrease("M1", branch_id, 1)
        self.assertEqual(stock_repo.get_quantity("M1", branch_id), 4)

        low = stock_repo.list_low_stock(branch_id)
        codes = {row["medicine_code"] for row in low}
        self.assertIn("M1", codes)
        self.assertIn("M2", codes)

        low_all = stock_repo.list_low_stock()
        self.assertGreaterEqual(len(low_all), 2)

    def test_prescription_creation_and_retrieval(self):
        med_repo = MedicineRepository(self.db)
        branch_repo = BranchRepository(self.db)
        prescription_repo = PrescriptionRepository(self.db)

        med_repo.add("M1", "Medicine One", 2.5, 5, False)
        med_repo.add("M2", "Medicine Two", 3.0, 10, True)
        branch_id = branch_repo.add("Branch One")

        prescription_id = prescription_repo.create(
            branch_id, "PAT-1", "DR-1", [("M1", 2), ("M2", 1)]
        )
        prescription = prescription_repo.get_by_id(prescription_id)

        self.assertIsNotNone(prescription)
        self.assertEqual(prescription["branch_id"], branch_id)
        self.assertEqual(prescription["status"], "pending")
        self.assertEqual(len(prescription["lines"]), 2)

        lines = prescription_repo.get_lines(prescription_id)
        self.assertEqual(len(lines), 2)

    def test_failed_shared_transaction_rollback(self):
        med_repo = MedicineRepository(self.db)
        branch_repo = BranchRepository(self.db)
        stock_repo = StockRepository(self.db)
        prescription_repo = PrescriptionRepository(self.db)

        med_repo.add("M1", "Medicine One", 2.5, 5, False)
        med_repo.add("M2", "Medicine Two", 3.0, 10, False)
        branch_id = branch_repo.add("Branch One")
        stock_repo.set_quantity("M1", branch_id, 10)
        stock_repo.set_quantity("M2", branch_id, 2)

        prescription_id = prescription_repo.create(
            branch_id, "PAT-2", None, [("M1", 3), ("M2", 5)]
        )

        with self.assertRaises(ValueError):
            with self.db.transaction() as conn:
                stock_repo.decrease("M1", branch_id, 3, conn=conn)
                stock_repo.decrease("M2", branch_id, 5, conn=conn)

        self.assertEqual(stock_repo.get_quantity("M1", branch_id), 10)
        self.assertEqual(stock_repo.get_quantity("M2", branch_id), 2)
        prescription = prescription_repo.get_by_id(prescription_id)
        self.assertEqual(prescription["status"], "pending")

    def test_successful_shared_transaction_commit(self):
        med_repo = MedicineRepository(self.db)
        branch_repo = BranchRepository(self.db)
        stock_repo = StockRepository(self.db)
        prescription_repo = PrescriptionRepository(self.db)

        med_repo.add("M1", "Medicine One", 2.5, 5, False)
        med_repo.add("M2", "Medicine Two", 3.0, 10, False)
        branch_id = branch_repo.add("Branch One")
        stock_repo.set_quantity("M1", branch_id, 10)
        stock_repo.set_quantity("M2", branch_id, 10)

        prescription_id = prescription_repo.create(
            branch_id, "PAT-3", None, [("M1", 3), ("M2", 4)]
        )

        with self.db.transaction() as conn:
            stock_repo.decrease("M1", branch_id, 3, conn=conn)
            stock_repo.decrease("M2", branch_id, 4, conn=conn)
            row_count = prescription_repo.update_status(
                prescription_id, "dispensed", conn=conn
            )
            self.assertEqual(row_count, 1)

        self.assertEqual(stock_repo.get_quantity("M1", branch_id), 7)
        self.assertEqual(stock_repo.get_quantity("M2", branch_id), 6)
        prescription = prescription_repo.get_by_id(prescription_id)
        self.assertEqual(prescription["status"], "dispensed")

    def test_repeated_conditional_dispensing_update(self):
        med_repo = MedicineRepository(self.db)
        branch_repo = BranchRepository(self.db)
        prescription_repo = PrescriptionRepository(self.db)

        med_repo.add("M1", "Medicine One", 2.5, 5, False)
        branch_id = branch_repo.add("Branch One")
        prescription_id = prescription_repo.create(
            branch_id, "PAT-4", None, [("M1", 1)]
        )

        first = prescription_repo.update_status(prescription_id, "dispensed")
        second = prescription_repo.update_status(prescription_id, "dispensed")
        self.assertEqual(first, 1)
        self.assertEqual(second, 0)

    def test_seed_idempotency(self):
        seed(self.db)
        seed(self.db)

        with self.db.connection() as conn:
            branches = conn.execute("SELECT COUNT(*) FROM branches").fetchone()[0]
            medicines = conn.execute("SELECT COUNT(*) FROM medicines").fetchone()[0]
            stock = conn.execute("SELECT COUNT(*) FROM stock").fetchone()[0]
            prescribers = conn.execute(
                "SELECT COUNT(*) FROM authorised_prescribers"
            ).fetchone()[0]

        self.assertEqual(branches, 2)
        self.assertEqual(medicines, 5)
        self.assertEqual(stock, 8)
        self.assertEqual(prescribers, 1)


if __name__ == "__main__":
    unittest.main()