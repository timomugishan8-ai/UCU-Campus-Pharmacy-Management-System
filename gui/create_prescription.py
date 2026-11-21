"""Tkinter screen for creating multi-line prescriptions.

This screen follows the agreed ``Screen(parent, services)`` pattern. It only
collects input, calls ``services.prescription_service`` and displays results;
it contains no SQL and no database connection.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from app.base_screen import BaseScreen
from domain.prescription import PrescriptionError


class CreatePrescriptionScreen(BaseScreen):
    """Form for a fictional patient, branch, prescriber and medicine lines."""

    NO_PRESCRIBER = "(none - ordinary medicine)"

    def __init__(self, parent: Any, services: Any) -> None:
        super().__init__(parent, services)
        self._lines: list[tuple[str, int]] = []
        self._branch_ids: dict[str, int] = {}
        self._prescriber_codes: dict[str, Any] = {}
        self._medicine_codes: dict[str, str] = {}
        self._build_widgets()
        self._load_options()

    # ------------------------------------------------------------------ #
    # Widget construction
    # ------------------------------------------------------------------ #
    def _build_widgets(self) -> None:
        form = ttk.LabelFrame(self, text="New prescription", padding=10)
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="Patient identifier:").grid(row=0, column=0, sticky="w")
        self.patient_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.patient_var, width=24).grid(
            row=0, column=1, sticky="ew", padx=(6, 12)
        )

        ttk.Label(form, text="Branch:").grid(row=1, column=0, sticky="w")
        self.branch_var = tk.StringVar()
        self.branch_combo = ttk.Combobox(
            form, textvariable=self.branch_var, state="readonly", width=24
        )
        self.branch_combo.grid(row=1, column=1, sticky="ew", padx=(6, 12))

        ttk.Label(form, text="Prescriber code (if controlled):").grid(
            row=2, column=0, sticky="w"
        )
        self.prescriber_var = tk.StringVar()
        self.prescriber_combo = ttk.Combobox(
            form, textvariable=self.prescriber_var, state="readonly", width=24
        )
        self.prescriber_combo.grid(row=2, column=1, sticky="ew", padx=(6, 12))

        # Line entry area
        line_box = ttk.LabelFrame(self, text="Medicine lines", padding=10)
        line_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        ttk.Label(line_box, text="Medicine:").grid(row=0, column=0, sticky="w")
        self.medicine_var = tk.StringVar()
        self.medicine_combo = ttk.Combobox(
            line_box, textvariable=self.medicine_var, state="readonly", width=30
        )
        self.medicine_combo.grid(row=0, column=1, sticky="w", padx=(6, 12))

        ttk.Label(line_box, text="Quantity:").grid(row=0, column=2, sticky="w")
        self.quantity_var = tk.StringVar()
        ttk.Entry(line_box, textvariable=self.quantity_var, width=10).grid(
            row=0, column=3, sticky="w", padx=(6, 12)
        )

        ttk.Button(line_box, text="Add line", command=self.on_add_line_clicked).grid(
            row=0, column=4, sticky="w"
        )

        self.line_tree = ttk.Treeview(
            line_box,
            columns=("medicine", "quantity"),
            show="headings",
            height=8,
        )
        self.line_tree.heading("medicine", text="Medicine code")
        self.line_tree.heading("quantity", text="Quantity")
        self.line_tree.column("medicine", width=180)
        self.line_tree.column("quantity", width=90, anchor="center")
        self.line_tree.grid(row=1, column=0, columnspan=5, sticky="nsew", pady=(10, 0))

        line_box.rowconfigure(1, weight=1)
        line_box.columnconfigure(0, weight=1)

        buttons = ttk.Frame(self, padding=(10, 0, 10, 10))
        buttons.pack(fill="x")
        ttk.Button(
            buttons, text="Create prescription", command=self.on_create_clicked
        ).pack(side="left")
        ttk.Button(buttons, text="Clear form", command=self.on_clear_clicked).pack(
            side="left", padx=8
        )

    # ------------------------------------------------------------------ #
    # Event handlers
    # ------------------------------------------------------------------ #
    def on_add_line_clicked(self) -> None:
        """Read one medicine line, convert the quantity and add it locally."""
        selection = self.medicine_var.get().strip()
        medicine_code = self._medicine_codes.get(selection)
        if not medicine_code:
            messagebox.showwarning("Missing medicine", "Select a medicine from the list.")
            return
        try:
            quantity = int(self.quantity_var.get().strip())
        except ValueError:
            messagebox.showerror("Invalid quantity", "Quantity must be a whole number.")
            return
        if quantity <= 0:
            messagebox.showerror("Invalid quantity", "Quantity must be greater than zero.")
            return
        if any(code == medicine_code for code, _ in self._lines):
            messagebox.showerror(
                "Duplicate line", "That medicine is already on this prescription."
            )
            return

        self._lines.append((medicine_code, quantity))
        self.medicine_var.set("")
        self.quantity_var.set("")
        self._refresh_lines()

    def on_create_clicked(self) -> None:
        """Call the agreed service method and show a useful result."""
        if not self._lines:
            messagebox.showwarning("No lines", "Add at least one medicine line first.")
            return
        branch_id = self._branch_ids.get(self.branch_var.get().strip())
        if branch_id is None:
            messagebox.showerror("Invalid branch", "Select a branch from the list.")
            return

        # The "(none - ordinary medicine)" option maps to None, so ordinary
        # medicines are not blocked by the allow-list check.
        prescriber_code = self._prescriber_codes.get(self.prescriber_var.get().strip())
        patient_identifier = self.patient_var.get().strip()

        try:
            prescription = self.services.prescription_service.create_prescription(
                patient_identifier,
                branch_id,
                prescriber_code,
                list(self._lines),
            )
        except (ValueError, PrescriptionError) as error:
            messagebox.showerror("Prescription not created", str(error))
            return

        messagebox.showinfo(
            "Prescription created",
            f"Prescription #{prescription.prescription_id} was created with "
            f"{len(prescription.lines)} line(s). Status: {prescription.status}.",
        )
        self.on_clear_clicked()

    def on_clear_clicked(self) -> None:
        """Reset the form after success or when the user starts again."""
        self.patient_var.set("")
        self.branch_var.set("")
        self.prescriber_var.set("")
        self.medicine_var.set("")
        self.quantity_var.set("")
        self._lines.clear()
        self._refresh_lines()

    # ------------------------------------------------------------------ #
    # Display helpers
    # ------------------------------------------------------------------ #
    def refresh(self) -> None:
        """Navigation hook called by ``MainWindow.show_screen``.

        Reload the reference lists (a medicine or prescriber added elsewhere
        should appear) and redraw the in-progress lines. The form itself is
        never cleared, so switching screens cannot lose unfinished work.
        """
        self._load_options()
        self._refresh_lines()

    def _load_options(self) -> None:
        """Fill the branch, prescriber and medicine dropdowns from services.

        Each dropdown displays a friendly label; the mapping dictionaries
        translate the chosen label back to the ID/code the service expects.
        No SQL is used here - everything comes through the shared services.
        """
        branch_names: list[str] = []
        self._branch_ids = {}
        for row in self.services.report_service.get_branch_stock_summary():
            name = row["branch_name"]
            branch_names.append(name)
            self._branch_ids[name] = row["branch_id"]
        self.branch_combo.configure(values=branch_names)
        if self.branch_var.get() not in branch_names:
            self.branch_combo.set(branch_names[0] if branch_names else "")

        prescriber_labels = [self.NO_PRESCRIBER]
        self._prescriber_codes = {self.NO_PRESCRIBER: None}
        for row in self.services.prescription_service.get_authorised_prescribers():
            code = row["prescriber_code"]
            name = row.get("prescriber_name") or ""
            label = f"{code} - {name}" if name else code
            prescriber_labels.append(label)
            self._prescriber_codes[label] = code
        self.prescriber_combo.configure(values=prescriber_labels)
        if self.prescriber_var.get() not in prescriber_labels:
            self.prescriber_combo.set(self.NO_PRESCRIBER)

        medicine_labels: list[str] = []
        self._medicine_codes = {}
        for medicine in self.services.medicine_service.get_all_medicines():
            suffix = " (controlled)" if medicine.requires_prescriber_code() else ""
            label = f"{medicine.medicine_code} - {medicine.name}{suffix}"
            medicine_labels.append(label)
            self._medicine_codes[label] = medicine.medicine_code
        self.medicine_combo.configure(values=medicine_labels)
        if self.medicine_var.get() not in medicine_labels:
            self.medicine_combo.set(medicine_labels[0] if medicine_labels else "")

    def _refresh_lines(self) -> None:
        for item in self.line_tree.get_children():
            self.line_tree.delete(item)
        for medicine_code, quantity in self._lines:
            self.line_tree.insert("", "end", values=(medicine_code, quantity))
