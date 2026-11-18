"""Tkinter screen for creating multi-line prescriptions.

This screen follows the agreed ``Screen(parent, services)`` pattern. It only
collects input, calls ``services.prescription_service`` and displays results;
it contains no SQL and no database connection.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from domain.prescription import PrescriptionError


class CreatePrescriptionScreen(ttk.Frame):
    """Form for a fictional patient, branch, prescriber and medicine lines."""

    def __init__(self, parent: Any, services: Any) -> None:
        super().__init__(parent)
        self.parent = parent
        self.services = services
        self._lines: list[tuple[str, int]] = []
        self._build_widgets()

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

        ttk.Label(form, text="Branch ID:").grid(row=1, column=0, sticky="w")
        self.branch_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.branch_var, width=24).grid(
            row=1, column=1, sticky="ew", padx=(6, 12)
        )

        ttk.Label(form, text="Prescriber code (if controlled):").grid(
            row=2, column=0, sticky="w"
        )
        self.prescriber_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.prescriber_var, width=24).grid(
            row=2, column=1, sticky="ew", padx=(6, 12)
        )

        # Line entry area
        line_box = ttk.LabelFrame(self, text="Medicine lines", padding=10)
        line_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        ttk.Label(line_box, text="Medicine code:").grid(row=0, column=0, sticky="w")
        self.medicine_var = tk.StringVar()
        ttk.Entry(line_box, textvariable=self.medicine_var, width=18).grid(
            row=0, column=1, sticky="w", padx=(6, 12)
        )

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
        medicine_code = self.medicine_var.get().strip()
        if not medicine_code:
            messagebox.showwarning("Missing medicine", "Enter a medicine code.")
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
        try:
            branch_id = int(self.branch_var.get().strip())
        except ValueError:
            messagebox.showerror("Invalid branch", "Branch ID must be a whole number.")
            return

        prescriber_code = self.prescriber_var.get().strip() or None
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
    def _refresh_lines(self) -> None:
        for item in self.line_tree.get_children():
            self.line_tree.delete(item)
        for medicine_code, quantity in self._lines:
            self.line_tree.insert("", "end", values=(medicine_code, quantity))
