"""Member 4 tests: database-backed dropdowns on the prescription form.

The recorder should select medicines, branches and authorised prescribers
from lists rather than typing codes. These tests prove the lists come from
the services (and therefore the database), and that a prescription created
through the form reaches the service with the codes it expects.
"""

import os
import tempfile
import unittest
from unittest.mock import patch

import tkinter as tk

from app.services import ApplicationServices
from database.seed_data import seed
from gui.create_prescription import CreatePrescriptionScreen


class PrescriptionDropdownTests(unittest.TestCase):
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
        self.screen = CreatePrescriptionScreen(self.root, self.services)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_prescriber_allow_list_is_available_through_the_service(self):
        prescribers = self.services.prescription_service.get_authorised_prescribers()
        self.assertIn("DR-1001", [row["prescriber_code"] for row in prescribers])

    def test_dropdowns_are_populated_from_the_database(self):
        self.assertIn("Main Campus Pharmacy", self.screen.branch_combo["values"])
        self.assertEqual(self.screen._branch_ids["Main Campus Pharmacy"], 1)

        prescribers = self.screen.prescriber_combo["values"]
        self.assertIn(self.screen.NO_PRESCRIBER, prescribers)
        self.assertTrue(any("DR-1001" in label for label in prescribers))
        self.assertIsNone(
            self.screen._prescriber_codes[self.screen.NO_PRESCRIBER]
        )

        medicines = self.screen.medicine_combo["values"]
        self.assertTrue(any("MED-001" in label for label in medicines))
        controlled = [label for label in medicines if "controlled" in label]
        self.assertTrue(controlled)
        self.assertEqual(self.screen._medicine_codes[controlled[0]], "MED-004")

    @patch("gui.create_prescription.messagebox.showinfo")
    def test_prescription_created_from_dropdown_selections(self, info):
        self.screen.patient_var.set("PAT-DROPDOWN")
        self.screen.branch_combo.set("East Campus Pharmacy")
        self.screen.medicine_combo.set("MED-002 - Amoxicillin 250mg")
        self.screen.quantity_var.set("3")
        self.screen.on_add_line_clicked()

        self.screen.prescriber_combo.set(self.screen.NO_PRESCRIBER)
        self.screen.on_create_clicked()

        prescription = self.services.prescription_service.get_prescription(1)
        self.assertIsNotNone(prescription)
        self.assertEqual(prescription.branch_id, 2)
        self.assertEqual(prescription.patient_identifier, "PAT-DROPDOWN")
        self.assertEqual(prescription.lines[0].medicine_code, "MED-002")
        self.assertEqual(prescription.lines[0].quantity, 3)
        info.assert_called_once()


if __name__ == "__main__":
    unittest.main()
