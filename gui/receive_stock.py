"""Tkinter screen for receiving stock into a branch.

This screen follows the agreed ``Screen(parent, services)`` pattern
(interface contract section 6). It only collects input, calls
``services.stock_service`` and displays results; it contains no SQL and no
database connection.

The branch dropdown is filled from
``services.report_service.get_branch_stock_summary()`` rather than from
low-stock rows, so branches with no low-stock items (or no stock at all)
still appear - the group agreement recorded on 2026-11-19.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any


class ReceiveStockScreen(ttk.Frame):
    """Form for receiving a positive quantity of a medicine at a branch."""

    def __init__(self, parent: Any, services: Any) -> None:
        super().__init__(parent)
        self.parent = parent
        self.services = services
        self._branch_ids: dict[str, int] = {}   # branch name -> branch id
        self._medicine_codes: list[str] = []
        self._build_widgets()
        self.refresh_options()
        self.refresh_stock()

    # ------------------------------------------------------------------ #
    # Widget construction
    # ------------------------------------------------------------------ #
    def _build_widgets(self) -> None:
        form = ttk.LabelFrame(self, text="Receive stock", padding=10)
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="Medicine:").grid(row=0, column=0, sticky="w")
        self.medicine_combo = ttk.Combobox(
            form, state="readonly", width=30, values=()
        )
        self.medicine_combo.grid(row=0, column=1, sticky="ew", padx=(6, 12))

        ttk.Label(form, text="Branch:").grid(row=1, column=0, sticky="w")
        self.branch_combo = ttk.Combobox(
            form, state="readonly", width=30, values=()
        )
        self.branch_combo.grid(row=1, column=1, sticky="ew", padx=(6, 12))

        ttk.Label(form, text="Quantity received:").grid(row=2, column=0, sticky="w")
        self.quantity_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.quantity_var, width=32).grid(
            row=2, column=1, sticky="ew", padx=(6, 12)
        )

        form.columnconfigure(1, weight=1)

        buttons = ttk.Frame(self, padding=(10, 0, 10, 10))
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Receive stock", command=self.on_receive_clicked).pack(
            side="left"
        )
        ttk.Button(buttons, text="Clear quantity", command=self.on_clear_clicked).pack(
            side="left", padx=8
        )
        ttk.Button(buttons, text="Refresh", command=self.refresh_options).pack(
            side="left"
        )

        stock_box = ttk.LabelFrame(self, text="Branch stock", padding=10)
        stock_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.stock_tree = ttk.Treeview(
            stock_box,
            columns=("medicine", "name", "quantity", "reorder"),
            show="headings",
            height=10,
        )
        self.stock_tree.heading("medicine", text="Medicine code")
        self.stock_tree.heading("name", text="Name")
        self.stock_tree.heading("quantity", text="Quantity")
        self.stock_tree.heading("reorder", text="Reorder level")
        self.stock_tree.column("medicine", width=110)
        self.stock_tree.column("name", width=240)
        self.stock_tree.column("quantity", width=90, anchor="center")
        self.stock_tree.column("reorder", width=100, anchor="center")
        self.stock_tree.pack(fill="both", expand=True)

        self.branch_combo.bind("<<ComboboxSelected>>", self._on_branch_selected)

    # ------------------------------------------------------------------ #
    # Event handlers
    # ------------------------------------------------------------------ #
    def on_receive_clicked(self) -> None:
        """Read the form, call the service and refresh the stock view."""
        medicine_code = self.medicine_combo.get().strip()
        if not medicine_code:
            messagebox.showwarning("Missing medicine", "Select a medicine.")
            return
        branch_name = self.branch_combo.get().strip()
        if not branch_name or branch_name not in self._branch_ids:
            messagebox.showwarning("Missing branch", "Select a branch.")
            return
        branch_id = self._branch_ids[branch_name]

        try:
            quantity = int(self.quantity_var.get().strip())
        except ValueError:
            messagebox.showerror(
                "Invalid quantity", "Quantity must be a whole number."
            )
            return
        if quantity <= 0:
            messagebox.showerror(
                "Invalid quantity", "Quantity must be greater than zero."
            )
            return

        try:
            self.services.stock_service.receive_stock(
                medicine_code, branch_id, quantity
            )
        except ValueError as error:
            messagebox.showerror("Stock not received", str(error))
            return

        messagebox.showinfo(
            "Stock received",
            f"{quantity} unit(s) of {medicine_code} were added at {branch_name}.",
        )
        self.on_clear_clicked()
        self.refresh_stock()

    def on_clear_clicked(self) -> None:
        """Reset only the quantity field; medicine and branch stay selected."""
        self.quantity_var.set("")

    def _on_branch_selected(self, _event: Any) -> None:
        """Show the selected branch's stock as soon as it is chosen."""
        self.refresh_stock()

    # ------------------------------------------------------------------ #
    # Display helpers
    # ------------------------------------------------------------------ #
    def refresh_options(self) -> None:
        """Reload the medicine and branch dropdowns from the services."""
        medicines = self.services.medicine_service.get_all_medicines()
        self._medicine_codes = [m.medicine_code for m in medicines]
        self.medicine_combo.configure(values=self._medicine_codes)

        # Branches come from the summary so empty branches still appear.
        self._branch_ids = {}
        branch_names: list[str] = []
        for row in self.services.report_service.get_branch_stock_summary():
            name = row["branch_name"]
            branch_names.append(name)
            self._branch_ids[name] = row["branch_id"]
        self.branch_combo.configure(values=branch_names)

    def refresh_stock(self) -> None:
        """Reload the stock listing for the selected branch."""
        for item in self.stock_tree.get_children():
            self.stock_tree.delete(item)

        branch_name = self.branch_combo.get().strip()
        if branch_name not in self._branch_ids:
            return
        for row in self.services.stock_service.get_branch_stock(
            self._branch_ids[branch_name]
        ):
            self.stock_tree.insert(
                "",
                "end",
                values=(
                    row["medicine_code"],
                    row.get("medicine_name", ""),
                    row["quantity"],
                    row.get("reorder_level", ""),
                ),
            )
