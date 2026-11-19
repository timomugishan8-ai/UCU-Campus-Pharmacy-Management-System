"""Cindy's StockRepository reporting and ReportService tests."""

import os
import sqlite3
import tempfile
import unittest

from database.connection import Database
from database.repositories.branch_repository import BranchRepository
from database.repositories.medicine_repository import MedicineRepository
from database.repositories.stock_repository import StockRepository
from services.report_service import ReportService


class CindyStockReportTests(unittest.TestCase):
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
        self.report_service = ReportService(self.stock_repo)

        with self.db.transaction() as conn:
            self.medicine_repo.add("M1", "Medicine One", 2.5, 5, False, conn=conn)
            self.medicine_repo.add("M2", "Medicine Two", 3.0, 10, False, conn=conn)
            self.medicine_repo.add("M3", "Medicine Three", 4.0, 2, False, conn=conn)

            self.branch_one = self.branch_repo.add("Branch One", conn=conn)
            self.branch_two = self.branch_repo.add("Branch Two", conn=conn)
            self.branch_empty = self.branch_repo.add("Empty Branch", conn=conn)

            # Branch one: three medicines, one low, one equal to reorder level.
            self.stock_repo.set_quantity("M1", self.branch_one, 3, conn=conn)   # low: 3 <= 5
            self.stock_repo.set_quantity("M2", self.branch_one, 10, conn=conn)  # equal: 10 <= 10
            self.stock_repo.set_quantity("M3", self.branch_one, 5, conn=conn)   # not low: 5 > 2

            # Branch two: one medicine, not low.
            self.stock_repo.set_quantity("M1", self.branch_two, 20, conn=conn)  # 20 > 5

    def tearDown(self):
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
        except OSError:
            pass

    def test_branch_stock_summary_counts(self):
        summary = self.stock_repo.get_branch_stock_summary()
        branch_one = next(row for row in summary if row["branch_id"] == self.branch_one)

        self.assertEqual(branch_one["branch_name"], "Branch One")
        self.assertEqual(branch_one["medicine_count"], 3)
        self.assertEqual(branch_one["total_quantity"], 18)
        self.assertEqual(branch_one["low_stock_count"], 2)

    def test_branch_with_no_stock_has_zero_values(self):
        summary = self.stock_repo.get_branch_stock_summary()
        empty = next(row for row in summary if row["branch_id"] == self.branch_empty)

        self.assertEqual(empty["medicine_count"], 0)
        self.assertEqual(empty["total_quantity"], 0)
        self.assertEqual(empty["low_stock_count"], 0)

    def test_multiple_branches_are_included(self):
        summary = self.stock_repo.get_branch_stock_summary()
        branch_ids = {row["branch_id"] for row in summary}

        self.assertIn(self.branch_one, branch_ids)
        self.assertIn(self.branch_two, branch_ids)
        self.assertIn(self.branch_empty, branch_ids)
        self.assertEqual(len(summary), 3)

    def test_branch_summary_delegates_through_report_service(self):
        summary = self.report_service.get_branch_stock_summary()
        self.assertEqual(len(summary), 3)
        self.assertTrue(all("branch_name" in row for row in summary))

    def test_low_stock_report_no_filter(self):
        rows = self.report_service.get_low_stock_report()
        codes = {(row["medicine_code"], row["branch_id"]) for row in rows}

        self.assertIn(("M1", self.branch_one), codes)
        self.assertIn(("M2", self.branch_one), codes)
        self.assertNotIn(("M3", self.branch_one), codes)
        self.assertNotIn(("M1", self.branch_two), codes)

    def test_low_stock_report_filtered_by_branch(self):
        rows = self.report_service.get_low_stock_report(branch_id=self.branch_one)
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row["branch_id"] == self.branch_one for row in rows))

    def test_low_stock_report_row_keys(self):
        rows = self.report_service.get_low_stock_report(branch_id=self.branch_one)
        expected_keys = {
            "medicine_code",
            "medicine_name",
            "branch_id",
            "branch_name",
            "quantity",
            "reorder_level",
            "is_controlled",
        }
        self.assertTrue(all(set(row.keys()) == expected_keys for row in rows))

    def test_quantity_equal_to_reorder_level_is_low(self):
        rows = self.report_service.get_low_stock_report(branch_id=self.branch_one)
        equal_row = next(row for row in rows if row["medicine_code"] == "M2")
        self.assertEqual(equal_row["quantity"], 10)
        self.assertEqual(equal_row["reorder_level"], 10)

    def test_branch_stock_summary_shared_connection(self):
        with self.db.transaction() as conn:
            self.stock_repo.set_quantity("M1", self.branch_one, 50, conn=conn)
            summary = self.stock_repo.get_branch_stock_summary(conn=conn)
            branch_one = next(row for row in summary if row["branch_id"] == self.branch_one)
            self.assertEqual(branch_one["total_quantity"], 65)  # 50 + 10 + 5

        # Rolled back by raising? This block commits normally; verify persisted.
        self.assertEqual(self.stock_repo.get_quantity("M1", self.branch_one), 50)

    def test_report_service_shared_connection_rollback(self):
        try:
            with self.db.transaction() as conn:
                self.stock_repo.set_quantity("M1", self.branch_one, 999, conn=conn)
                self.report_service.get_branch_stock_summary()  # uses own connection, not shared
                raise RuntimeError("boom")
        except RuntimeError:
            pass
        self.assertEqual(self.stock_repo.get_quantity("M1", self.branch_one), 3)


if __name__ == "__main__":
    unittest.main()