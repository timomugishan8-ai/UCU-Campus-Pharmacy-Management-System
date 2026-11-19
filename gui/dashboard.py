"""Dashboard screen for the UCU Pharmacy Management System.

Member 4 - Tkinter GUI coordination.

Design references (WhatsApp reference images, 2026-11-19):
- UCU Pharmacy sidebar identity (dark navy, teal pill logo)
- Stat-card layout from the MediStock Pro reference

All figures come from the shared services. The screen contains no SQL, no
message boxes unless a service fails, and no invented/trend data.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from app.base_screen import BaseScreen

# Palette shared with gui/main_window.py so the whole app looks consistent.
CONTENT_BG = "#F5F7FA"
CARD_BG = "#FFFFFF"
BORDER = "#E5E7EB"
TEXT_DARK = "#1F2937"
TEXT_MUTED = "#6B7280"
BLUE = "#3B82F6"
AMBER = "#F59E0B"
TEAL = "#16A085"
NAVY = "#0F2A43"
RED = "#DC2626"


class DashboardScreen(BaseScreen):
    """Read-only overview: key figures, inventory status and branch summary.

    Constructor: ``DashboardScreen(parent, services)``. It uses only
    ``medicine_service``, ``stock_service`` and ``report_service``.
    """

    # (key, caption, glyph, colour)
    CARDS = (
        ("medicines", "Total Medicines", "M", BLUE),
        ("low", "Low Stock Items", "!", AMBER),
        ("units", "Total Stock Units", "U", TEAL),
        ("branches", "Branches", "B", NAVY),
    )

    INVENTORY_COLUMNS = (
        ("medicine", "Medicine code", 120, "w"),
        ("name", "Name", 200, "w"),
        ("branch", "Branch", 170, "w"),
        ("quantity", "Quantity", 85, "center"),
        ("reorder", "Reorder level", 100, "center"),
        ("status", "Status", 120, "center"),
    )

    BRANCH_COLUMNS = (
        ("branch", "Branch", 180, "w"),
        ("types", "Medicine types", 110, "center"),
        ("units", "Total units", 100, "center"),
        ("low", "Low stock", 90, "center"),
    )

    def __init__(self, parent: tk.Widget, services: Any) -> None:
        super().__init__(parent, services)
        self.card_labels: dict[str, tk.Label] = {}
        self._build_widgets()
        self.refresh()

    # ------------------------------------------------------------------
    # Widget construction
    # ------------------------------------------------------------------
    def _build_widgets(self) -> None:
        root = tk.Frame(self, bg=CONTENT_BG)
        root.pack(fill="both", expand=True)

        self._build_header(root)
        self._build_cards(root)
        self._build_panels(root)

    def _build_header(self, root: tk.Widget) -> None:
        header = tk.Frame(root, bg=CONTENT_BG)
        header.pack(fill="x", padx=26, pady=(22, 8))

        tk.Label(
            header,
            text="Dashboard",
            bg=CONTENT_BG,
            fg=TEXT_DARK,
            font=("Segoe UI", 21, "bold"),
        ).pack(anchor="w")

        tk.Label(
            header,
            text="UCU Pharmacy Management System  -  inventory overview",
            bg=CONTENT_BG,
            fg=TEXT_MUTED,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(2, 0))

        tk.Frame(header, bg=TEAL, height=3).pack(fill="x", pady=(10, 0))

    def _build_cards(self, root: tk.Widget) -> None:
        cards = tk.Frame(root, bg=CONTENT_BG)
        cards.pack(fill="x", padx=26, pady=(10, 6))

        for index, (key, caption, glyph, colour) in enumerate(self.CARDS):
            cards.columnconfigure(index, weight=1)
            card = tk.Frame(
                cards,
                bg=CARD_BG,
                highlightbackground=BORDER,
                highlightthickness=1,
            )
            card.grid(row=0, column=index, sticky="nsew", padx=(0, 12))

            icon = tk.Label(
                card,
                text=glyph,
                bg=colour,
                fg="white",
                font=("Segoe UI", 16, "bold"),
                width=3,
                height=2,
            )
            icon.grid(row=0, column=0, rowspan=2, padx=(14, 8), pady=14)

            value = tk.Label(
                card,
                text="0",
                bg=CARD_BG,
                fg=TEXT_DARK,
                font=("Segoe UI", 22, "bold"),
                anchor="sw",
            )
            value.grid(row=0, column=1, sticky="sw", pady=(14, 0))

            tk.Label(
                card,
                text=caption,
                bg=CARD_BG,
                fg=TEXT_MUTED,
                font=("Segoe UI", 10),
                anchor="nw",
            ).grid(row=1, column=1, sticky="nw", pady=(0, 14))

            self.card_labels[key] = value

    def _build_panels(self, root: tk.Widget) -> None:
        panels = tk.Frame(root, bg=CONTENT_BG)
        panels.pack(fill="both", expand=True, padx=26, pady=(6, 22))
        panels.columnconfigure(0, weight=3)
        panels.columnconfigure(1, weight=2)
        panels.rowconfigure(0, weight=1)

        left = tk.LabelFrame(
            panels,
            text="  Inventory Status  ",
            bg=CARD_BG,
            fg=TEXT_DARK,
            font=("Segoe UI", 11, "bold"),
            padx=8,
            pady=8,
        )
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.inventory_tree = self._make_tree(left, self.INVENTORY_COLUMNS)
        self.inventory_tree.tag_configure("OUT OF STOCK", foreground=RED)
        self.inventory_tree.tag_configure("LOW STOCK", foreground="#B45309")
        self.inventory_tree.tag_configure("IN STOCK", foreground="#15803D")

        right = tk.LabelFrame(
            panels,
            text="  Branch Overview  ",
            bg=CARD_BG,
            fg=TEXT_DARK,
            font=("Segoe UI", 11, "bold"),
            padx=8,
            pady=8,
        )
        right.grid(row=0, column=1, sticky="nsew")
        self.branch_tree = self._make_tree(right, self.BRANCH_COLUMNS)

    @staticmethod
    def _make_tree(
        parent: tk.Widget, columns: tuple[tuple[str, str, int, str], ...]
    ) -> ttk.Treeview:
        frame = tk.Frame(parent, bg=CARD_BG)
        frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(
            frame,
            columns=[key for key, _heading, _width, _anchor in columns],
            show="headings",
            height=10,
        )
        for key, heading, width, anchor in columns:
            tree.heading(key, text=heading)
            tree.column(key, width=width, anchor=anchor)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return tree

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        """Reload every figure and table from the shared services."""
        try:
            medicines = self.services.medicine_service.get_all_medicines()
            summaries = self.services.report_service.get_branch_stock_summary()
            low_stock = self.services.report_service.get_low_stock_report()
            inventory_rows = self._collect_inventory_rows(summaries)
        except Exception as exc:
            messagebox.showerror(
                "Dashboard", f"Could not load the dashboard: {exc}", parent=self
            )
            return

        self.card_labels["medicines"].config(text=str(len(medicines)))
        self.card_labels["low"].config(text=str(len(low_stock)))
        self.card_labels["units"].config(
            text=str(sum(int(row["total_quantity"]) for row in summaries))
        )
        self.card_labels["branches"].config(text=str(len(summaries)))

        self._fill_tree(self.inventory_tree, inventory_rows)
        self._fill_tree(
            self.branch_tree,
            [
                (
                    row["branch_name"],
                    row["medicine_count"],
                    row["total_quantity"],
                    row["low_stock_count"],
                )
                for row in summaries
            ],
        )

    def _collect_inventory_rows(self, summaries: list[dict[str, Any]]) -> list[tuple]:
        """Build one row per stock record across every branch."""
        rows: list[tuple] = []
        for branch in summaries:
            for item in self.services.stock_service.get_branch_stock(
                branch["branch_id"]
            ):
                quantity = int(item["quantity"])
                reorder = int(item["reorder_level"])
                if quantity == 0:
                    status = "OUT OF STOCK"
                elif quantity <= reorder:
                    status = "LOW STOCK"
                else:
                    status = "IN STOCK"
                rows.append(
                    (
                        item["medicine_code"],
                        item["medicine_name"],
                        branch["branch_name"],
                        quantity,
                        reorder,
                        status,
                    )
                )
        return rows

    @staticmethod
    def _fill_tree(tree: ttk.Treeview, rows: list[tuple]) -> None:
        for item in tree.get_children():
            tree.delete(item)
        for row in rows:
            tags = (row[-1],) if tree is not None and len(row) == 6 else ()
            tree.insert("", "end", values=row, tags=tags)

    def show(self) -> None:
        """Navigation hook: bring the dashboard forward and refresh it."""
        self.tkraise()
        self.refresh()
