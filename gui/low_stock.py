"""Low-stock report screen for the campus pharmacy system.

Member 4 - Tkinter GUI coordination.

This screen follows the agreed ``Screen(parent, services)`` pattern. It talks
only to ``services.report_service``; it never imports sqlite3 and never opens
its own database connection.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Optional

from app.base_screen import BaseScreen


class LowStockScreen(BaseScreen):
    """Display medicines whose stock is at or below their reorder level.

    Constructor: ``LowStockScreen(parent, services)``.
    Inherits ``BaseScreen`` so it shares the agreed parent/services handling
    with every other screen. ``services`` is the single shared
    ApplicationServices object - we receive it, we never build it.
    """

    # (key, heading, width) - one place to describe the table columns.
    # Keys and headings follow the GUI convention used by the other screens
    # (Register Medicine, Receive Stock, Create Prescription, Dispense) so
    # the same data is labelled consistently across the application.
    COLUMNS = (
        ("medicine", "Medicine code", 120),
        ("name", "Name", 200),
        ("branch", "Branch", 180),
        ("quantity", "Quantity", 90),
        ("reorder", "Reorder level", 110),
        ("controlled", "Controlled", 95),
    )

    ALL_BRANCHES = "All branches"

    def __init__(self, parent: tk.Widget, services: Any) -> None:
        super().__init__(parent, services)
        self._branch_ids: dict[str, int] = {}   # branch name -> branch id
        self.status_var = tk.StringVar(value="")
        self._build_widgets()
        self.refresh()

    # ------------------------------------------------------------------
    # Widget setup
    # ------------------------------------------------------------------
    def _build_widgets(self) -> None:
        """Create the filter controls, the results table and the status line."""
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill="x", padx=10, pady=(10, 5))

        ttk.Label(filter_frame, text="Branch:").pack(side="left", padx=(0, 6))

        self.branch_combo = ttk.Combobox(
            filter_frame, state="readonly", width=28, values=(self.ALL_BRANCHES,)
        )
        self.branch_combo.set(self.ALL_BRANCHES)
        self.branch_combo.pack(side="left")

        refresh_button = ttk.Button(
            filter_frame, text="Refresh", command=self.refresh
        )
        refresh_button.pack(side="left", padx=(8, 0))

        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(
            table_frame,
            columns=[key for key, _heading, _width in self.COLUMNS],
            show="headings",
            height=15,
        )
        for key, heading, width in self.COLUMNS:
            self.tree.heading(key, text=heading)
            self.tree.column(key, width=width, anchor="w")

        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ttk.Label(self, textvariable=self.status_var).pack(
            fill="x", padx=10, pady=(0, 10)
        )

        self._load_branch_options()

    def _load_branch_options(self) -> None:
        """Fill the branch dropdown from the branch stock summary.

        We use get_branch_stock_summary() rather than the low-stock rows so
        that branches with no low-stock items (or no stock at all) still
        appear in the filter. Only branch_id and branch_name are read here.
        """
        try:
            rows = self.services.report_service.get_branch_stock_summary()
        except Exception as exc:
            messagebox.showerror(
                "Low stock", f"Could not load branches: {exc}", parent=self
            )
            return

        self._branch_ids = {
            row["branch_name"]: row["branch_id"] for row in rows
        }
        names = sorted(self._branch_ids)
        self.branch_combo["values"] = (self.ALL_BRANCHES, *names)
        self.branch_combo.set(self.ALL_BRANCHES)

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def _selected_branch_id(self) -> Optional[int]:
        """Return None for 'All branches', otherwise the chosen branch id."""
        name = self.branch_combo.get()
        if name == self.ALL_BRANCHES or not name:
            return None
        return self._branch_ids.get(name)

    def refresh(self) -> None:
        """Reload the table from ReportService and update the status line."""
        branch_id = self._selected_branch_id()
        try:
            rows = self.services.report_service.get_low_stock_report(
                branch_id=branch_id
            )
        except Exception as exc:
            # Show a readable message, never a raw SQL traceback.
            messagebox.showerror(
                "Low stock", f"Could not load the report: {exc}", parent=self
            )
            self.status_var.set("Report could not be loaded.")
            return

        self._clear_rows()
        for row in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    row["medicine_code"],
                    row["medicine_name"],
                    row["branch_name"],
                    row["quantity"],
                    row["reorder_level"],
                    "Yes" if row["is_controlled"] else "No",
                ),
            )

        where = "all branches" if branch_id is None else self.branch_combo.get()
        self.status_var.set(f"{len(rows)} low-stock item(s) - {where}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _clear_rows(self) -> None:
        """Remove every row before displaying fresh data (prevents duplicates)."""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def show(self) -> None:
        """Bring this screen forward and refresh it (called by navigation)."""
        self.tkraise()
        self.refresh()
