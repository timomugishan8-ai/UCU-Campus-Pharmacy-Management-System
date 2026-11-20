"""Login gate shown before the main pharmacy window opens.

Two pieces:

- ``LoginScreen(parent, services)`` follows the agreed
  ``Screen(parent, services)`` pattern: it collects input, calls
  ``services.auth_service`` and displays results; no SQL, no repository
  construction.

- ``ask_for_login(services)`` is the small runner used by ``main.py``:
  it opens a standalone tkinter root with the login screen, runs the
  event loop, and returns the signed-in ``StaffUser`` (or ``None`` when
  the window was closed). On success the screen stores the user in
  ``services.current_user`` and destroys the gate window so ``main.py``
  can open the real ``MainWindow``.

First-run bootstrap: when the account table is empty the screen offers
"Create the first administrator" instead of shipping a default password.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Optional

from app.base_screen import BaseScreen
from domain.user import StaffUser


class LoginScreen(BaseScreen):
    """Sign-in form, with a first-administrator panel when no users exist."""

    def __init__(self, parent: Any, services: Any) -> None:
        super().__init__(parent, services)
        self._bootstrap_mode = not services.auth_service.has_users()
        self._build_widgets()
        self._apply_mode()

    # ------------------------------------------------------------------ #
    # Widget construction
    # ------------------------------------------------------------------ #
    def _build_widgets(self) -> None:
        self.configure(padding=40)

        card = ttk.Frame(self)
        card.pack(expand=True)

        ttk.Label(
            card,
            text="UCU Pharmacy Management System",
            font=("Segoe UI", 15, "bold"),
        ).grid(row=0, column=0, columnspan=2, pady=(0, 4))
        ttk.Label(
            card,
            text="Sign in to continue",
            foreground="#5B6B7C",
        ).grid(row=1, column=0, columnspan=2, pady=(0, 18))

        ttk.Label(card, text="Username:").grid(row=2, column=0, sticky="w", pady=4)
        self.username_var = tk.StringVar()
        ttk.Entry(card, textvariable=self.username_var, width=28).grid(
            row=2, column=1, sticky="ew", padx=(10, 0), pady=4
        )

        ttk.Label(card, text="Password:").grid(row=3, column=0, sticky="w", pady=4)
        self.password_var = tk.StringVar()
        ttk.Entry(card, textvariable=self.password_var, show="*", width=28).grid(
            row=3, column=1, sticky="ew", padx=(10, 0), pady=4
        )

        ttk.Label(card, text="Confirm password:").grid(
            row=4, column=0, sticky="w", pady=4
        )
        self.confirm_var = tk.StringVar()
        ttk.Entry(card, textvariable=self.confirm_var, show="*", width=28).grid(
            row=4, column=1, sticky="ew", padx=(10, 0), pady=4
        )

        buttons = ttk.Frame(card)
        buttons.grid(row=5, column=0, columnspan=2, pady=(18, 0))

        self.sign_in_button = ttk.Button(
            buttons, text="Sign in", command=self.on_sign_in_clicked
        )
        self.sign_in_button.pack(side="left", padx=(0, 8))
        self.bootstrap_button = ttk.Button(
            buttons,
            text="Create first administrator",
            command=self.on_create_first_admin_clicked,
        )
        self.bootstrap_button.pack(side="left")

        self.status_label = ttk.Label(
            card,
            text="",
            foreground="#B03A2E",
            font=("Segoe UI", 9),
        )
        self.status_label.grid(row=6, column=0, columnspan=2, pady=(12, 0))

    def _apply_mode(self) -> None:
        """Bootstrap mode shows the create button and hides sign-in."""
        if self._bootstrap_mode:
            self.sign_in_button.state(["disabled"])
            self.bootstrap_button.state(["!disabled"])
            self.status_label.configure(
                text="No accounts exist yet - create the first administrator.",
                foreground="#5B6B7C",
            )
        else:
            self.sign_in_button.state(["!disabled"])
            self.bootstrap_button.state(["disabled"])

    # ------------------------------------------------------------------ #
    # Event handlers
    # ------------------------------------------------------------------ #
    def on_sign_in_clicked(self) -> None:
        """Authenticate and close the gate on success."""
        username = self.username_var.get().strip()
        password = self.password_var.get()
        if not username or not password:
            messagebox.showerror(
                "Missing details", "Enter your username and password."
            )
            return

        try:
            user = self.services.auth_service.login(username, password)
        except ValueError as error:
            # AuthenticationError / AuthorizationError derive from ValueError.
            messagebox.showerror("Sign-in failed", str(error))
            return

        self._finish(user)

    def on_create_first_admin_clicked(self) -> None:
        """First-run bootstrap: create the initial administrator account."""
        username = self.username_var.get().strip()
        password = self.password_var.get()
        confirm = self.confirm_var.get()

        if not username or not password:
            messagebox.showerror(
                "Missing details", "Enter a username and password."
            )
            return
        if password != confirm:
            messagebox.showerror(
                "Mismatch", "The passwords do not match."
            )
            return

        try:
            user = self.services.auth_service.create_first_admin(username, password)
        except ValueError as error:
            messagebox.showerror("Account not created", str(error))
            return

        messagebox.showinfo(
            "Administrator created",
            f"Welcome, {user.username}. Your administrator account is ready.",
        )
        self._finish(user)

    def _finish(self, user: StaffUser) -> None:
        """Publish the session and close the login gate window."""
        self.services.current_user = user
        self.winfo_toplevel().destroy()

    # ------------------------------------------------------------------ #
    # Display helpers
    # ------------------------------------------------------------------ #
    def refresh(self) -> None:
        """Navigation hook (the gate is standalone; kept for contract parity)."""
        self._apply_mode()


def ask_for_login(services: Any) -> Optional[StaffUser]:
    """Run the login gate and return the signed-in user, or ``None``.

    ``main.py`` calls this *before* building ``MainWindow``: the gate is
    its own ``tk.Tk`` root, destroyed on success so the main window can
    be created afterwards.
    """
    root = tk.Tk()
    root.title("Sign in - UCU Pharmacy Management System")
    root.geometry("460x360")
    root.minsize(460, 360)
    LoginScreen(root, services)
    root.mainloop()
    return services.current_user
