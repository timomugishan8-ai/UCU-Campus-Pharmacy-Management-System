"""Main application window for the UCU Pharmacy Management System.

Member 1 owns this file; Member 4 coordinates the GUI conventions used here.
The sidebar follows the UCU Pharmacy reference (dark navy, teal pill logo) and
one shared content area hosts every screen.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from app.services import ApplicationServices

from gui.dashboard import DashboardScreen
from gui.register_medicine import RegisterMedicineScreen
from gui.receive_stock import ReceiveStockScreen
from gui.create_prescription import CreatePrescriptionScreen
from gui.dispense import DispenseScreen
from gui.low_stock import LowStockScreen
from gui.user_admin import UserAdminScreen

NAVY = "#0F2A43"
NAVY_ACTIVE = "#1B3A57"
TEAL = "#16A085"
CONTENT_BG = "#F5F7FA"
MUTED = "#9FB3C8"
TEXT_DARK = "#1F2937"


class MainWindow(tk.Tk):
    """One main window, one navigation panel, one shared services object."""

    def __init__(self, services: ApplicationServices):
        super().__init__()
        self.services = services

        self.title("UCU Pharmacy Management System")
        self.geometry("1180x720")
        self.minsize(980, 620)
        self.configure(bg=CONTENT_BG)

        self.screens: dict[str, Any] = {}
        self.nav_buttons: dict[str, tk.Button] = {}

        self._configure_tree_style()
        self._build_layout()
        self._register_screens()

        # Dashboard is the landing screen.
        self.show_screen("Dashboard")

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    @staticmethod
    def _configure_tree_style() -> None:
        """One table style for the whole app (GUI coordinator convention)."""
        style = ttk.Style()
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 9, "bold"),
            background="#E8EDF2",
            foreground=TEXT_DARK,
        )
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=26)

    def _build_layout(self) -> None:
        self.main_container = tk.Frame(self, bg=CONTENT_BG)
        self.main_container.pack(fill="both", expand=True)

        self.navigation_frame = tk.Frame(
            self.main_container, bg=NAVY, width=250
        )
        self.navigation_frame.pack(side="left", fill="y")
        self.navigation_frame.pack_propagate(False)

        self._build_brand()

        tk.Label(
            self.navigation_frame,
            text="MAIN MENU",
            bg=NAVY,
            fg=MUTED,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", padx=22, pady=(18, 8))

        self.content_frame = tk.Frame(self.main_container, bg=CONTENT_BG)
        self.content_frame.pack(side="right", fill="both", expand=True)

    def _build_brand(self) -> None:
        """Teal pill logo and the UCU Pharmacy identity."""
        brand = tk.Frame(self.navigation_frame, bg=NAVY)
        brand.pack(fill="x", padx=18, pady=(24, 6))

        logo = tk.Canvas(
            brand, width=44, height=44, bg=NAVY, highlightthickness=0
        )
        logo.grid(row=0, column=0, rowspan=2, padx=(0, 10))

        # Rounded teal square built from rectangles and four corner ovals.
        logo.create_rectangle(0, 9, 44, 35, fill=TEAL, outline=TEAL)
        logo.create_rectangle(9, 0, 35, 44, fill=TEAL, outline=TEAL)
        for x0, y0 in ((0, 0), (28, 0), (0, 28), (28, 28)):
            logo.create_oval(
                x0, y0, x0 + 16, y0 + 16, fill=TEAL, outline=TEAL
            )
        # White capsule, split by a teal band.
        logo.create_line(12, 31, 32, 13, fill="white", width=10, capstyle=tk.ROUND)
        logo.create_line(20, 24, 26, 19, fill=TEAL, width=3)

        tk.Label(
            brand,
            text="UCU Pharmacy",
            bg=NAVY,
            fg="white",
            font=("Segoe UI", 13, "bold"),
            anchor="w",
        ).grid(row=0, column=1, sticky="sw")
        tk.Label(
            brand,
            text="Management System",
            bg=NAVY,
            fg=MUTED,
            font=("Segoe UI", 10),
            anchor="w",
        ).grid(row=1, column=1, sticky="nw")

        tk.Frame(self.navigation_frame, bg="#2A4763", height=1).pack(
            fill="x", padx=18, pady=(14, 0)
        )

    # ------------------------------------------------------------------
    # Screens and navigation
    # ------------------------------------------------------------------
    def _register_screens(self) -> None:
        """Create each screen once with the shared services object."""
        screen_definitions = {
            "Dashboard": DashboardScreen,
            "Register Medicine": RegisterMedicineScreen,
            "Receive Stock": ReceiveStockScreen,
            "Prescriptions": CreatePrescriptionScreen,
            "Dispense Medicine": DispenseScreen,
            "Low Stock": LowStockScreen,
            "Users": UserAdminScreen,
        }

        for name, screen_class in screen_definitions.items():
            button = tk.Button(
                self.navigation_frame,
                text=name,
                command=lambda screen_name=name: self.show_screen(screen_name),
                bg=NAVY,
                fg="#DCE6F0",
                activebackground=NAVY_ACTIVE,
                activeforeground="white",
                relief="flat",
                borderwidth=0,
                anchor="w",
                padx=22,
                pady=10,
                font=("Segoe UI", 11),
                cursor="hand2",
            )
            button.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[name] = button

            screen = screen_class(self.content_frame, self.services)
            self.screens[name] = screen
            screen.place(x=0, y=0, relwidth=1, relheight=1)

    def show_screen(self, screen_name: str) -> None:
        """Highlight the chosen menu item and bring its screen forward."""
        screen = self.screens.get(screen_name)
        if screen is None:
            raise ValueError(f"Screen '{screen_name}' has not been registered.")

        for name, button in self.nav_buttons.items():
            active = name == screen_name
            button.configure(
                bg=NAVY_ACTIVE if active else NAVY,
                fg="white" if active else "#DCE6F0",
            )

        screen.tkraise()
        refresh = getattr(screen, "refresh", None)
        if callable(refresh):
            refresh()

    def on_close(self) -> None:
        """Handle application shutdown."""
        self.destroy()
