"""Cindy's StockService tests."""

import os
import tempfile
import unittest

from database.connection import Database
from database.repositories.branch_repository import BranchRepository
from database.repositories.medicine_repository import MedicineRepository
from database.repositories.stock_repository import StockRepository
from services.stock_service import StockService


class CindyStockServiceTests(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = Database(self.db_path)
        self.db.initialize_schema()

        self.medicine_repo = MedicineRepository(self.db)
        self.branch_repo = BranchRepository(self.db)
        self.stock_repo = StockRepository(self.db)
        self.service = StockService(
            self.stock_repo, self.medicine_repo, self.branch_repo
        )

        with self.db.transaction() as conn:
            self.medicine_repo.add("M1", "Medicine One", 2.5, 5, False, conn=conn)
            self.branch_id = self.branch_repo.add("Branch One", conn=conn)

    def tearDown(self):
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
        except OSError:
            pass

    def test_receive_stock_successfully(self):
        self.service.receive_stock("M1", self.branch_id, 10)
        self.assertEqual(self.stock_repo.get_quantity("M1", self.branch_id), 10)

    def test_increasing_existing_stock(self):
        self.service.receive_stock("M1", self.branch_id, 4)
        self.service.receive_stock("M1", self.branch_id, 6)
        self.assertEqual(self.stock_repo.get_quantity("M1", self.branch_id), 10)

    def test_unknown_medicine(self):
        with self.assertRaises(ValueError):
            self.service.receive_stock("NOPE", self.branch_id, 5)

    def test_unknown_branch(self):
        with self.assertRaises(ValueError):
            self.service.receive_stock("M1", 999, 5)

    def test_zero_quantity(self):
        with self.assertRaises(ValueError):
            self.service.receive_stock("M1", self.branch_id, 0)

    def test_negative_quantity(self):
        with self.assertRaises(ValueError):
            self.service.receive_stock("M1", self.branch_id, -1)

    def test_decimal_quantity(self):
        with self.assertRaises(ValueError):
            self.service.receive_stock("M1", self.branch_id, 1.5)

    def test_text_quantity(self):
        with self.assertRaises(ValueError):
            self.service.receive_stock("M1", self.branch_id, "5")

    def test_boolean_quantity(self):
        with self.assertRaises(ValueError):
            self.service.receive_stock("M1", self.branch_id, True)

    def test_get_branch_stock(self):
        self.service.receive_stock("M1", self.branch_id, 7)
        rows = self.service.get_branch_stock(self.branch_id)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["quantity"], 7)

    def test_get_branch_stock_unknown_branch(self):
        with self.assertRaises(ValueError):
            self.service.get_branch_stock(999)

    def test_get_low_stock_all_branches(self):
        self.service.receive_stock("M1", self.branch_id, 3)  # 3 <= reorder 5
        rows = self.service.get_low_stock()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["medicine_code"], "M1")

    def test_get_low_stock_filtered_branch(self):
        self.service.receive_stock("M1", self.branch_id, 3)
        rows = self.service.get_low_stock(self.branch_id)
        self.assertEqual(len(rows), 1)
        self.assertTrue(all(row["branch_id"] == self.branch_id for row in rows))

    def test_get_low_stock_unknown_branch(self):
        with self.assertRaises(ValueError):
            self.service.get_low_stock(999)

    def test_constructor_requires_medicine_and_branch_repositories(self):
        with self.assertRaises(TypeError):
            StockService(self.stock_repo)

    def test_constructor_accepts_required_dependencies(self):
        service = StockService(
            self.stock_repo, self.medicine_repo, self.branch_repo
        )
        self.assertIs(service.stock_repository, self.stock_repo)
        self.assertIs(service.medicine_repository, self.medicine_repo)
        self.assertIs(service.branch_repository, self.branch_repo)





if __name__ == "__main__":
    unittest.main()
