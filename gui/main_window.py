
import tkinter as tk
from tkinter import ttk

from app.services import ApplicationServices

from gui.create_prescription import CreatePrescriptionScreen
from gui.dispense import DispenseScreen
from gui.register_medicine import RegisterMedicineScreen
from gui.receive_stock import ReceiveStockScreen
from gui.low_stock import LowStockScreen


class MainWindow(tk.Tk):
    """
    Main application window.

    Responsible for creating the main interface,
    managing navigation and displaying feature screens.
    """

    def __init__(self, services: ApplicationServices):
        super().__init__()

        self.services = services

        # Main window configuration.
        self.title("UCU Campus Pharmacy Management System")
        self.geometry("1100x700")
        self.minsize(850, 550)

        # Store registered screens.
        self.screens = {}

        # Build the main interface.
        self._build_layout()

        # Register available feature screens.
        self._register_screens()

        # Display the default screen.
        self.show_screen("Create Prescription")

    def _build_layout(self):
        """Create the navigation area and screen display area."""

        # Main container.
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill="both", expand=True)

        # Navigation panel.
        self.navigation_frame = ttk.Frame(
            self.main_container,
            padding=10
        )
        self.navigation_frame.pack(side="left", fill="y")

        ttk.Label(
            self.navigation_frame,
            text="PHARMACY MENU",
            font=("Arial", 12, "bold")
        ).pack(pady=(10, 20))

        # Screen content area.
        self.content_frame = ttk.Frame(
            self.main_container,
            padding=10
        )
        self.content_frame.pack(
            side="right",
            fill="both",
            expand=True
        )

        # Application heading.
        ttk.Label(
            self.content_frame,
            text="UCU Campus Pharmacy Management System",
            font=("Arial", 17, "bold")
        ).pack(anchor="w", pady=(5, 15))

    def _register_screens(self):
        """Create feature screens and register them for navigation."""

        screen_definitions = {
            "Register Medicine": RegisterMedicineScreen,
            "Receive Stock": ReceiveStockScreen,
            "Create Prescription": CreatePrescriptionScreen,
            "Dispense": DispenseScreen,
            "Low Stock": LowStockScreen,
        }

        for name, screen_class in screen_definitions.items():

            # Create the screen using shared application services.
            screen = screen_class(
                self.content_frame,
                self.services
            )

            # Store the screen for later navigation.
            self.screens[name] = screen

            # Place it in the same content area.
            screen.place(
                x=0,
                y=45,
                relwidth=1,
                relheight=1
            )

            # Create its navigation button.
            ttk.Button(
                self.navigation_frame,
                text=name,
                command=lambda screen_name=name:
                    self.show_screen(screen_name)
            ).pack(fill="x", pady=5)

    def show_screen(self, screen_name):
        """Display the selected feature screen."""

        screen = self.screens.get(screen_name)

        if screen is None:
            raise ValueError(
                f"Screen '{screen_name}' has not been registered."
            )

        # Bring the selected screen to the front.
        screen.tkraise()

        # Refresh the screen if it supports a refresh method.
        refresh = getattr(screen, "refresh", None)

        if callable(refresh):
            refresh()

    def on_close(self):
        """Handle application shutdown."""
        self.destroy()
