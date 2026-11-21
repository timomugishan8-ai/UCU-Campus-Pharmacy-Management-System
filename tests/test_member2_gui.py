"""Member 2 GUI smoke tests: register-medicine and receive-stock screens.

These tests build the real tkinter screens against a stub ``services``
facade wired to a temporary database, then drive the event handlers the
way a user would. Message boxes are replaced with recorders so no dialog
ever blocks the test run.

They follow the agreed screen contract: ``Screen(parent, services)``, no
SQL in the GUI, errors surfaced through ``messagebox``.
"""

import os
import tempfile
import unittest
from unittest.mock import patch

import tkinter as tk

from database.connection import Database
from database.repositories.branch_repository import BranchRepository
from database.repositories.medicine_repository import MedicineRepository
from database.repositories.stock_repository import StockRepository
from domain.medicine import ControlledMedicine, OrdinaryMedicine
from gui.receive_stock import ReceiveStockScreen
from gui.register_medicine import RegisterMedicineScreen
from services.medicine_service import MedicineService
from services.report_service import ReportService
from services.stock_service import StockService


class _StubServices:
    """Minimal stand-in for the ApplicationServices facade (Member 1)."""

    def __init__(self, database: Database) -> None:
        medicine_repository = MedicineRepository(database)
        stock_repository = StockRepository(database)
        self.medicine_service = MedicineService(medicine_repository)
        self.stock_service = StockService(
            stock_repository,
            medicine_repository=medicine_repository,
            branch_repository=BranchRepository(database),
            database=database,
        )
        self.report_service = ReportService(stock_repository, database=database)


class ScreenTestCase(unittest.TestCase):
    """Shared tkinter setup: one hidden root, one temporary database."""

    screen_class = None

    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()  # never show a window during tests

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = Database(self.db_path)
        self.db.initialize_schema()
        self.services = _StubServices(self.db)
        self.screen = self.screen_class(self.root, self.services)

    def tearDown(self):
        self.screen.destroy()
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
        except OSError:
            pass


class RegisterMedicineScreenTests(ScreenTestCase):
    screen_class = RegisterMedicineScreen

    def _fill_form(self, code="MED-101", name="Ibuprofen 400mg",
                   price="3.25", reorder="10", controlled=False):
        self.screen.code_var.set(code)
        self.screen.name_var.set(name)
        self.screen.price_var.set(price)
        self.screen.reorder_var.set(reorder)
        self.screen.controlled_var.set(controlled)

    def test_screen_shows_empty_catalogue_on_open(self):
        self.assertEqual(self.screen.medicine_tree.get_children(), ())

    @patch("gui.register_medicine.messagebox.showinfo")
    @patch("gui.register_medicine.messagebox.showerror")
    @patch("gui.register_medicine.messagebox.showwarning")
    def test_register_ordinary_medicine(self, _warning, _error, info):
        self._fill_form()
        self.screen.on_register_clicked()

        medicine = self.services.medicine_service.get_medicine_by_code("MED-101")
        self.assertIsNotNone(medicine)
        self.assertEqual(medicine.name, "Ibuprofen 400mg")
        self.assertFalse(medicine.requires_prescriber_code())
        info.assert_called_once()
        _error.assert_not_called()
        # The listing refreshes and the form clears.
        self.assertEqual(len(self.screen.medicine_tree.get_children()), 1)
        self.assertEqual(self.screen.code_var.get(), "")

    @patch("gui.register_medicine.messagebox.showinfo")
    @patch("gui.register_medicine.messagebox.showerror")
    @patch("gui.register_medicine.messagebox.showwarning")
    def test_register_controlled_medicine(self, _warning, error, info):
        self._fill_form(code="MED-102", name="Diazepam 5mg",
                        price="8.50", reorder="5", controlled=True)
        self.screen.on_register_clicked()

        medicine = self.services.medicine_service.get_medicine_by_code("MED-102")
        self.assertIsInstance(medicine, ControlledMedicine)
        self.assertTrue(medicine.requires_prescriber_code())
        info.assert_called_once()
        error.assert_not_called()

    @patch("gui.register_medicine.messagebox.showinfo")
    @patch("gui.register_medicine.messagebox.showerror")
    @patch("gui.register_medicine.messagebox.showwarning")
    def test_rejects_invalid_price(self, _warning, error, info):
        # MVP rejection path: a zero price must not reach the database.
        self._fill_form(price="0")
        self.screen.on_register_clicked()

        error.assert_called_once()
        self.assertIn("positive", error.call_args[0][1].lower())
        info.assert_not_called()
        self.assertIsNone(
            self.services.medicine_service.get_medicine_by_code("MED-101")
        )

    @patch("gui.register_medicine.messagebox.showinfo")
    @patch("gui.register_medicine.messagebox.showerror")
    @patch("gui.register_medicine.messagebox.showwarning")
    def test_rejects_non_numeric_price(self, _warning, error, info):
        self._fill_form(price="cheap")
        self.screen.on_register_clicked()
        error.assert_called_once()
        info.assert_not_called()

    @patch("gui.register_medicine.messagebox.showinfo")
    @patch("gui.register_medicine.messagebox.showerror")
    @patch("gui.register_medicine.messagebox.showwarning")
    def test_rejects_duplicate_code(self, _warning, error, info):
        self._fill_form()
        self.screen.on_register_clicked()
        info.reset_mock()

        self._fill_form(name="Another brand")
        self.screen.on_register_clicked()

        error.assert_called_once()
        self.assertIn("already registered", error.call_args[0][1])
        info.assert_not_called()
        self.assertEqual(len(self.services.medicine_service.get_all_medicines()), 1)

    @patch("gui.register_medicine.messagebox.showinfo")
    @patch("gui.register_medicine.messagebox.showerror")
    @patch("gui.register_medicine.messagebox.showwarning")
    def test_rejects_blank_fields(self, warning, error, info):
        self._fill_form(code="   ")
        self.screen.on_register_clicked()
        warning.assert_called_once()
        error.assert_not_called()
        info.assert_not_called()

    @patch("gui.register_medicine.messagebox.showinfo")
    @patch("gui.register_medicine.messagebox.showerror")
    @patch("gui.register_medicine.messagebox.showwarning")
    def test_negative_reorder_level_is_rejected(self, _warning, error, info):
        self._fill_form(reorder="-3")
        self.screen.on_register_clicked()
        error.assert_called_once()
        info.assert_not_called()
        self.assertIsNone(
            self.services.medicine_service.get_medicine_by_code("MED-101")
        )

    @patch("gui.register_medicine.messagebox.showinfo")
    @patch("gui.register_medicine.messagebox.showerror")
    @patch("gui.register_medicine.messagebox.showwarning")
    def test_navigation_refresh_hook_reloads_catalogue(
        self, _warning, _error, _info
    ):
        # MainWindow.show_screen() calls an optional refresh() hook, so the
        # screen must expose it. Medicine registered outside the screen
        # must appear after the hook runs.
        self.assertTrue(callable(self.screen.refresh))
        self.services.medicine_service.register_medicine(
            OrdinaryMedicine("MED-901", "Late addition", 1.0)
        )
        self.screen.refresh()
        codes = [
            str(self.screen.medicine_tree.item(item)["values"][0])
            for item in self.screen.medicine_tree.get_children()
        ]
        self.assertIn("MED-901", codes)


class ReceiveStockScreenTests(ScreenTestCase):
    screen_class = ReceiveStockScreen

    def setUp(self):
        super().setUp()
        # Seed one medicine and one branch directly through the services.
        self.services.medicine_service.register_medicine(
            OrdinaryMedicine("MED-201", "Paracetamol 500mg", 2.50, 20)
        )
        branch_id = BranchRepository(self.db).add("Main Campus Pharmacy")
        self.branch_name = "Main Campus Pharmacy"
        self.branch_id = branch_id
        self.screen.refresh_options()
        self.screen.refresh_stock()

    def _select(self, medicine="MED-201", branch=None):
        self.screen.medicine_combo.set(medicine)
        self.screen.branch_combo.set(branch or self.branch_name)

    @patch("gui.receive_stock.messagebox.showinfo")
    @patch("gui.receive_stock.messagebox.showerror")
    @patch("gui.receive_stock.messagebox.showwarning")
    def test_receive_stock_increases_branch_quantity(self, _warning, error, info):
        self._select()
        self.screen.quantity_var.set("30")
        self.screen.on_receive_clicked()

        info.assert_called_once()
        error.assert_not_called()
        quantity = self.services.stock_service.get_branch_stock(self.branch_id)[0][
            "quantity"
        ]
        self.assertEqual(quantity, 30)
        # The on-screen listing refreshes too.
        self.assertEqual(len(self.screen.stock_tree.get_children()), 1)

    @patch("gui.receive_stock.messagebox.showinfo")
    @patch("gui.receive_stock.messagebox.showerror")
    @patch("gui.receive_stock.messagebox.showwarning")
    def test_rejects_non_positive_quantity(self, _warning, error, info):
        for bad_quantity in ("0", "-5", "abc"):
            with self.subTest(quantity=bad_quantity):
                error.reset_mock()
                self._select()
                self.screen.quantity_var.set(bad_quantity)
                self.screen.on_receive_clicked()
                error.assert_called_once()
                info.assert_not_called()
        self.assertEqual(self.services.stock_service.get_branch_stock(self.branch_id), [])

    @patch("gui.receive_stock.messagebox.showinfo")
    @patch("gui.receive_stock.messagebox.showerror")
    @patch("gui.receive_stock.messagebox.showwarning")
    def test_requires_medicine_and_branch_selection(self, warning, error, info):
        # No medicine selected.
        self.screen.branch_combo.set(self.branch_name)
        self.screen.quantity_var.set("5")
        self.screen.on_receive_clicked()
        warning.assert_called_once()

        # No branch selected.
        warning.reset_mock()
        self.screen.medicine_combo.set("MED-201")
        self.screen.branch_combo.set("")
        self.screen.on_receive_clicked()
        warning.assert_called_once()
        error.assert_not_called()
        info.assert_not_called()

    @patch("gui.receive_stock.messagebox.showinfo")
    @patch("gui.receive_stock.messagebox.showerror")
    @patch("gui.receive_stock.messagebox.showwarning")
    def test_rejects_unknown_medicine(self, _warning, error, info):
        self._select(medicine="MED-404")
        self.screen.quantity_var.set("5")
        self.screen.on_receive_clicked()
        error.assert_called_once()
        self.assertIn("Unknown medicine", error.call_args[0][1])
        info.assert_not_called()

    @patch("gui.receive_stock.messagebox.showinfo")
    @patch("gui.receive_stock.messagebox.showerror")
    @patch("gui.receive_stock.messagebox.showwarning")
    def test_branch_dropdown_lists_empty_branches_from_summary(
        self, _warning, _error, _info
    ):
        # A branch with no stock must still appear in the dropdown.
        BranchRepository(self.db).add("Satellite Clinic")
        self.screen.refresh_options()
        self.assertIn("Satellite Clinic", self.screen.branch_combo.cget("values"))
        self.assertIn(self.branch_name, self.screen.branch_combo.cget("values"))

    @patch("gui.receive_stock.messagebox.showinfo")
    @patch("gui.receive_stock.messagebox.showerror")
    @patch("gui.receive_stock.messagebox.showwarning")
    def test_navigation_refresh_hook_reloads_options_and_stock(
        self, _warning, _error, _info
    ):
        # MainWindow.show_screen() calls an optional refresh() hook, so the
        # screen must expose it and pick up data changed elsewhere.
        self.assertTrue(callable(self.screen.refresh))

        self._select()
        BranchRepository(self.db).add("New Branch")
        self.services.stock_service.receive_stock("MED-201", self.branch_id, 10)

        self.screen.refresh()

        self.assertIn("New Branch", self.screen.branch_combo.cget("values"))
        rows = self.screen.stock_tree.get_children()
        self.assertEqual(len(rows), 1)
        self.assertEqual(int(self.screen.stock_tree.item(rows[0])["values"][2]), 10)


if __name__ == "__main__":
    unittest.main()
