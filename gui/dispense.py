"""Tkinter screen for viewing, dispensing and cancelling prescriptions.

Uses only ``services.prescription_service``. All business rules (status,
controlled-medicine authorisation and atomic stock deduction) live in the
service and domain layers, never in this widget.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Optional

from app.base_screen import BaseScreen
from domain.prescription import Prescription, PrescriptionError


class DispenseScreen(BaseScreen):
    """Look up a prescription and act on it through the agreed service."""

    def __init__(self, parent: Any, services: Any) -> None:
        super().__init__(parent, services)
        self.current: Optional[Prescription] = None
        self._build_widgets()

    # ------------------------------------------------------------------ #
    # Widget construction
    # ------------------------------------------------------------------ #
    def _build_widgets(self) -> None:
        search = ttk.LabelFrame(self, text="Find prescription", padding=10)
        search.pack(fill="x", padx=10, pady=10)

        ttk.Label(search, text="Prescription ID:").grid(row=0, column=0, sticky="w")
        self.prescription_var = tk.StringVar()
        ttk.Entry(search, textvariable=self.prescription_var, width=14).grid(
            row=0, column=1, sticky="w", padx=(6, 10)
        )
        ttk.Button(search, text="Find", command=self.on_find_clicked).grid(
            row=0, column=2, sticky="w"
        )

        details = ttk.LabelFrame(self, text="Prescription details", padding=10)
        details.pack(fill="x", padx=10, pady=(0, 10))

        self.patient_var = tk.StringVar(value="-")
        self.branch_var = tk.StringVar(value="-")
        self.status_var = tk.StringVar(value="-")
        self.prescriber_var = tk.StringVar(value="-")

        rows = (
            ("Patient identifier:", self.patient_var),
            ("Branch ID:", self.branch_var),
            ("Status:", self.status_var),
            ("Prescriber code:", self.prescriber_var),
        )
        for row, (label, variable) in enumerate(rows):
            ttk.Label(details, text=label).grid(row=row, column=0, sticky="w")
            ttk.Label(details, textvariable=variable).grid(
                row=row, column=1, sticky="w", padx=(8, 0)
            )

        line_box = ttk.LabelFrame(self, text="Medicine lines", padding=10)
        line_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.line_tree = ttk.Treeview(
            line_box,
            columns=("medicine", "quantity", "controlled"),
            show="headings",
            height=8,
        )
        self.line_tree.heading("medicine", text="Medicine code")
        self.line_tree.heading("quantity", text="Quantity")
        self.line_tree.heading("controlled", text="Controlled")
        self.line_tree.column("medicine", width=180)
        self.line_tree.column("quantity", width=90, anchor="center")
        self.line_tree.column("controlled", width=100, anchor="center")
        self.line_tree.pack(fill="both", expand=True)

        buttons = ttk.Frame(self, padding=(10, 0, 10, 10))
        buttons.pack(fill="x")
        self.dispense_button = ttk.Button(
            buttons, text="Dispense", command=self.on_dispense_clicked
        )
        self.dispense_button.pack(side="left")
        ttk.Button(buttons, text="Cancel prescription", command=self.on_cancel_clicked).pack(
            side="left", padx=8
        )
        ttk.Button(buttons, text="Refresh", command=self.on_find_clicked).pack(
            side="left"
        )

    # ------------------------------------------------------------------ #
    # Event handlers
    # ------------------------------------------------------------------ #
    def on_find_clicked(self) -> None:
        """Load the prescription through the service and refresh the display."""
        prescription_id = self._read_id()
        if prescription_id is None:
            return
        try:
            prescription = self.services.prescription_service.get_prescription(
                prescription_id
            )
        except ValueError as error:
            messagebox.showerror("Invalid ID", str(error))
            return
        if prescription is None:
            messagebox.showerror(
                "Not found", f"No prescription with ID {prescription_id}."
            )
            self.current = None
        else:
            self.current = prescription
        self._refresh_display()

    def on_dispense_clicked(self) -> None:
        """Dispense atomically and report success or a clear failure reason."""
        prescription_id = self._read_id()
        if prescription_id is None:
            return
        try:
            prescription = self.services.prescription_service.dispense_prescription(
                prescription_id
            )
        except (ValueError, PrescriptionError) as error:
            messagebox.showerror("Dispensing failed", str(error))
            self.on_find_clicked()
            return

        self.current = prescription
        self._refresh_display()
        messagebox.showinfo(
            "Dispensed",
            f"Prescription #{prescription.prescription_id} was dispensed successfully.",
        )

    def on_cancel_clicked(self) -> None:
        """Cancel a pending prescription through the agreed service method."""
        prescription_id = self._read_id()
        if prescription_id is None:
            return
        try:
            prescription = self.services.prescription_service.cancel_prescription(
                prescription_id
            )
        except (ValueError, PrescriptionError) as error:
            messagebox.showerror("Cancellation failed", str(error))
            self.on_find_clicked()
            return

        self.current = prescription
        self._refresh_display()
        messagebox.showinfo(
            "Cancelled",
            f"Prescription #{prescription.prescription_id} was cancelled.",
        )

    # ------------------------------------------------------------------ #
    # Navigation hook
    # ------------------------------------------------------------------ #
    def refresh(self) -> None:
        """Re-fetch the displayed prescription quietly on navigation.

        Unlike ``on_find_clicked()`` this does not validate the text field or
        show an error dialog, so switching to this screen with an empty form
        stays silent. If a prescription is currently displayed, its status
        is reloaded from the service in case it changed elsewhere.
        """
        if self.current is None:
            return
        try:
            prescription = self.services.prescription_service.get_prescription(
                self.current.prescription_id
            )
        except (ValueError, PrescriptionError):
            return
        self.current = prescription
        self._refresh_display()

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _read_id(self) -> Optional[int]:
        try:
            prescription_id = int(self.prescription_var.get().strip())
        except ValueError:
            messagebox.showerror("Invalid ID", "Prescription ID must be a whole number.")
            return None
        if prescription_id <= 0:
            messagebox.showerror("Invalid ID", "Prescription ID must be positive.")
            return None
        return prescription_id

    def _refresh_display(self) -> None:
        prescription = self.current
        self.patient_var.set(
            prescription.patient_identifier if prescription else "-"
        )
        self.branch_var.set(str(prescription.branch_id) if prescription else "-")
        self.status_var.set(prescription.status if prescription else "-")
        self.prescriber_var.set(
            prescription.prescriber_code or "-" if prescription else "-"
        )

        for item in self.line_tree.get_children():
            self.line_tree.delete(item)
        if prescription is not None:
            for line in prescription.lines:
                self.line_tree.insert(
                    "",
                    "end",
                    values=(
                        line.medicine_code,
                        line.quantity,
                        "Yes" if line.is_controlled else "No",
                    ),
                )
