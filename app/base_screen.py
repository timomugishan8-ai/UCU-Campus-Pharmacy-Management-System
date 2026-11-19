
import tkinter as tk
from tkinter import ttk

from typing import Any


class BaseScreen(ttk.Frame):
    """
    Common foundation for all pharmacy application screens.

    Every feature screen inherits from this class to obtain
    a consistent parent window and shared application services.
    """

    def __init__(self, parent: Any, services: Any) -> None:
        # Initialize the Tkinter Frame.
        super().__init__(parent)

        # Store the parent window.
        self.parent = parent

        # Store the shared application services.
        self.services = services
