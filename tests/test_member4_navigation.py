"""Member 4 GUI navigation tests for the prescription screens.

Conrad's two screens were the last ones still inheriting ``ttk.Frame``
without a ``refresh()`` hook, so MainWindow.show_screen() could not reload
their data. These tests prove they now follow the shared pattern:

- they inherit ``app.base_screen.BaseScreen``;
- they expose a callable ``refresh()`` that the navigation code can call;
- the hook keeps in-progress form state and reloads saved status quietly.
"""

import os
import tempfile
import unittest
from unittest.mock import patch

import tkinter as tk

from app.base_screen import BaseScreen
from app.services import ApplicationServices
from database.seed_data import seed
from gui.create_prescription import CreatePrescriptionScreen
from gui.dispense import DispenseScreen


class NavigationTestCase(unittest.TestCase):
    """One hidden Tk root and a seeded temporary database per test."""

    screen_class = None

    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.services = ApplicationServices(self.db_path)
        self.services.database.initialize_schema()
        seed(self.services.database)
        self.screen = self.screen_class(self.root, self.services)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)


class CreatePrescriptionNavigationTests(NavigationTestCase):
    screen_class = CreatePrescriptionScreen

    def test_screen_uses_base_screen_and_exposes_refresh(self):
        self.assertIsInstance(self.screen, BaseScreen)
        self.assertTrue(callable(self.screen.refresh))

    def test_refresh_keeps_in_progress_lines(self):
        self.screen._lines.append(("MED-001", 3))
        self.screen.refresh()
        self.assertEqual(self.screen._lines, [("MED-001", 3)])
        codes = [
            str(self.screen.line_tree.item(item)["values"][0])
            for item in self.screen.line_tree.get_children()
        ]
        self.assertIn("MED-001", codes)


class DispenseNavigationTests(NavigationTestCase):
    screen_class = DispenseScreen

    def test_screen_uses_base_screen_and_exposes_refresh(self):
        self.assertIsInstance(self.screen, BaseScreen)
        self.assertTrue(callable(self.screen.refresh))

    @patch("gui.dispense.messagebox.showerror")
    def test_refresh_reloads_status_without_dialog(self, error):
        prescription = self.services.prescription_service.create_prescription(
            "PAT-NAV", 1, None, [("MED-001", 1)]
        )
        self.screen.current = prescription
        self.screen._refresh_display()
        self.assertEqual(self.screen.status_var.get(), "pending")

        self.services.prescription_service.cancel_prescription(
            prescription.prescription_id
        )
        self.screen.refresh()

        self.assertEqual(self.screen.status_var.get(), "cancelled")
        error.assert_not_called()

    @patch("gui.dispense.messagebox.showerror")
    def test_refresh_is_silent_with_no_prescription_loaded(self, error):
        self.screen.refresh()
        self.assertEqual(self.screen.status_var.get(), "-")
        error.assert_not_called()


if __name__ == "__main__":
    unittest.main()
