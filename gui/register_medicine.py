"""Tkinter screen for registering medicines in the catalogue.

This screen follows the agreed ``Screen(parent, services)`` pattern
(interface contract section 6). It only collects input, builds a domain
``Medicine`` with ``Medicine.create(...)``, calls
``services.medicine_service`` and displays results; it contains no SQL and
no database connection.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from domain.medicine import Medicine


class RegisterMedicineScreen(ttk.Frame):
    """Form for adding a medicine plus a read-only catalogue listing."""

    def __init__(self, parent: Any, services: Any) -> None:
        super().__init__(parent)
        self.parent = parent
        self.services = services
        self._build_widgets()
        self.refresh_medicines()

    # ------------------------------------------------------------------ #
    # Widget construction
    # ------------------------------------------------------------------ #
    def _build_widgets(self) -> None:
        form = ttk.LabelFrame(self, text="Register medicine", padding=10)
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="Medicine code:").grid(row=0, column=0, sticky="w")
        self.code_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.code_var, width=24).grid(
            row=0, column=1, sticky="ew", padx=(6, 12)
        )

        ttk.Label(form, text="Medicine name:").grid(row=1, column=0, sticky="w")
        self.name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.name_var, width=34).grid(
            row=1, column=1, sticky="ew", padx=(6, 12)
        )

        ttk.Label(form, text="Unit price:").grid(row=2, column=0, sticky="w")
        self.price_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.price_var, width=24).grid(
            row=2, column=1, sticky="ew", padx=(6, 12)
        )

        ttk.Label(form, text="Reorder level:").grid(row=3, column=0, sticky="w")
        self.reorder_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.reorder_var, width=24).grid(
            row=3, column=1, sticky="ew", padx=(6, 12)
        )

        self.controlled_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            form,
            text="Controlled medicine (needs an authorised prescriber)",
            variable=self.controlled_var,
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 0))

        form.columnconfigure(1, weight=1)

        buttons = ttk.Frame(self, padding=(10, 0, 10, 10))
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Register medicine", command=self.on_register_clicked).pack(
            side="left"
        )
        ttk.Button(buttons, text="Clear form", command=self.on_clear_clicked).pack(
            side="left", padx=8
        )
        ttk.Button(buttons, text="Refresh list", command=self.refresh_medicines).pack(
            side="left"
        )

        catalogue = ttk.LabelFrame(self, text="Medicine catalogue", padding=10)
        catalogue.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.medicine_tree = ttk.Treeview(
            catalogue,
            columns=("code", "name", "price", "reorder", "controlled"),
            show="headings",
            height=10,
        )
        self.medicine_tree.heading("code", text="Code")
        self.medicine_tree.heading("name", text="Name")
        self.medicine_tree.heading("price", text="Unit price")
        self.medicine_tree.heading("reorder", text="Reorder level")
        self.medicine_tree.heading("controlled", text="Controlled")
        self.medicine_tree.column("code", width=110)
        self.medicine_tree.column("name", width=240)
        self.medicine_tree.column("price", width=90, anchor="e")
        self.medicine_tree.column("reorder", width=100, anchor="center")
        self.medicine_tree.column("controlled", width=90, anchor="center")
        self.medicine_tree.pack(fill="both", expand=True)

    # ------------------------------------------------------------------ #
    # Event handlers
    # ------------------------------------------------------------------ #
    def on_register_clicked(self) -> None:
        """Validate the form, build the domain object and register it."""
        code = self.code_var.get().strip()
        name = self.name_var.get().strip()
        if not code:
            messagebox.showwarning("Missing code", "Enter a medicine code.")
            return
        if not name:
            messagebox.showwarning("Missing name", "Enter a medicine name.")
            return

        try:
            unit_price = float(self.price_var.get().strip())
        except ValueError:
            messagebox.showerror(
                "Invalid price", "Unit price must be a number (for example 2.50)."
            )
            return

        reorder_text = self.reorder_var.get().strip() or "0"
        try:
            reorder_level = int(reorder_text)
        except ValueError:
            messagebox.showerror(
                "Invalid reorder level", "Reorder level must be a whole number."
            )
            return

        # The domain object enforces the remaining rules (positive price,
        # non-negative reorder level) and selects the correct subclass.
        # It is created inside the try block so its InvalidMedicineError
        # (a ValueError) reaches the same error dialog as service errors.
        try:
            medicine = Medicine.create(
                code,
                name,
                unit_price,
                reorder_level,
                is_controlled=self.controlled_var.get(),
            )
            stored = self.services.medicine_service.register_medicine(medicine)
        except ValueError as error:
            # MedicineError derives from ValueError, so duplicate codes and
            # domain-rule violations all arrive here with a clear message.
            messagebox.showerror("Medicine not registered", str(error))
            return

        kind = "controlled" if stored.requires_prescriber_code() else "ordinary"
        messagebox.showinfo(
            "Medicine registered",
            f"{stored.medicine_code} ({stored.name}) was registered as an "
            f"{kind} medicine.",
        )
        self.on_clear_clicked()
        self.refresh_medicines()

    def on_clear_clicked(self) -> None:
        """Reset the form after success or when the user starts again."""
        self.code_var.set("")
        self.name_var.set("")
        self.price_var.set("")
        self.reorder_var.set("")
        self.controlled_var.set(False)

    # ------------------------------------------------------------------ #
    # Display helpers
    # ------------------------------------------------------------------ #
    def refresh_medicines(self) -> None:
        """Reload the catalogue listing from the service."""
        for item in self.medicine_tree.get_children():
            self.medicine_tree.delete(item)
        for medicine in self.services.medicine_service.get_all_medicines():
            self.medicine_tree.insert(
                "",
                "end",
                values=(
                    medicine.medicine_code,
                    medicine.name,
                    f"{medicine.unit_price:.2f}",
                    medicine.reorder_level,
                    "Yes" if medicine.requires_prescriber_code() else "No",
                ),
            )
