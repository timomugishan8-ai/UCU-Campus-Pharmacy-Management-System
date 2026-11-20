"""Tkinter screen for managing staff accounts (administrator only).

This screen follows the agreed ``Screen(parent, services)`` pattern and
inherits ``BaseScreen``. It collects input, calls
``services.auth_service`` and displays results; it contains no SQL and
no repository construction.

Access control happens twice on purpose: the screen disables its form
for non-administrators (friendly), and ``AuthService`` re-checks the
actor on every call (authoritative) - so even a modified screen cannot
create or disable accounts without an administrator session.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Optional

from app.base_screen import BaseScreen
from domain.user import ROLE_STAFF, ROLES, StaffUser


class UserAdminScreen(BaseScreen):
    """List accounts, create sub-users, enable/disable them."""

    def __init__(self, parent: Any, services: Any) -> None:
        super().__init__(parent, services)
        self._build_widgets()
        self.refresh()

    # ------------------------------------------------------------------ #
    # Widget construction
    # ------------------------------------------------------------------ #
    def _build_widgets(self) -> None:
        header = ttk.Frame(self, padding=(10, 10, 10, 0))
        header.pack(fill="x")
        self.session_label = ttk.Label(header, text="")
        self.session_label.pack(side="left")

        form = ttk.LabelFrame(self, text="Create sub-user", padding=10)
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="Username:").grid(row=0, column=0, sticky="w")
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(form, textvariable=self.username_var, width=24)
        self.username_entry.grid(row=0, column=1, sticky="ew", padx=(6, 12))

        ttk.Label(form, text="Password:").grid(row=1, column=0, sticky="w")
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(
            form, textvariable=self.password_var, show="*", width=24
        )
        self.password_entry.grid(row=1, column=1, sticky="ew", padx=(6, 12))

        ttk.Label(form, text="Role:").grid(row=2, column=0, sticky="w")
        self.role_combo = ttk.Combobox(
            form, state="readonly", width=22, values=list(ROLES)
        )
        self.role_combo.grid(row=2, column=1, sticky="ew", padx=(6, 12))
        self.role_combo.set(ROLE_STAFF)

        form.columnconfigure(1, weight=1)

        buttons = ttk.Frame(self, padding=(10, 0, 10, 10))
        buttons.pack(fill="x")
        self.create_button = ttk.Button(
            buttons, text="Create user", command=self.on_create_clicked
        )
        self.create_button.pack(side="left")
        self.disable_button = ttk.Button(
            buttons, text="Disable selected", command=self.on_disable_clicked
        )
        self.disable_button.pack(side="left", padx=8)
        self.enable_button = ttk.Button(
            buttons, text="Enable selected", command=self.on_enable_clicked
        )
        self.enable_button.pack(side="left")
        ttk.Button(buttons, text="Refresh", command=self.refresh).pack(
            side="left", padx=8
        )

        listing = ttk.LabelFrame(self, text="Accounts", padding=10)
        listing.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.user_tree = ttk.Treeview(
            listing,
            columns=("username", "role", "status", "created_by"),
            show="headings",
            height=10,
        )
        self.user_tree.heading("username", text="Username")
        self.user_tree.heading("role", text="Role")
        self.user_tree.heading("status", text="Status")
        self.user_tree.heading("created_by", text="Created by")
        self.user_tree.column("username", width=180)
        self.user_tree.column("role", width=90, anchor="center")
        self.user_tree.column("status", width=90, anchor="center")
        self.user_tree.column("created_by", width=160)
        self.user_tree.pack(fill="both", expand=True)

        self.status_label = ttk.Label(
            listing, text="", foreground="#5B6B7C", padding=(0, 6, 0, 0)
        )
        self.status_label.pack(fill="x")

    # ------------------------------------------------------------------ #
    # Access control and display helpers
    # ------------------------------------------------------------------ #
    @property
    def _actor(self) -> Optional[StaffUser]:
        user = getattr(self.services, "current_user", None)
        return user if isinstance(user, StaffUser) else None

    def _apply_access(self, admin_allowed: bool, message: str) -> None:
        """Grey the form out for non-administrators (service still re-checks)."""
        state = ["!disabled"] if admin_allowed else ["disabled"]
        for widget in (
            self.username_entry,
            self.password_entry,
            self.role_combo,
            self.create_button,
            self.disable_button,
            self.enable_button,
        ):
            widget.state(state)
        self.session_label.configure(text=message)

    def refresh(self) -> None:
        """Reload accounts and re-apply the administrator gate.

        Called by ``MainWindow.show_screen()`` on navigation.
        """
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)

        actor = self._actor
        if actor is None:
            self._apply_access(False, "No active session.")
            self.status_label.configure(
                text="Sign in to manage accounts."
            )
            return

        header = f"Signed in as {actor.username} ({actor.role})"
        try:
            users = self.services.auth_service.list_users(actor)
        except ValueError as error:
            # AuthorizationError: a staff member opened this screen.
            self._apply_access(False, header)
            self.status_label.configure(text=str(error))
            return

        self._apply_access(True, header)
        for user in users:
            self.user_tree.insert(
                "",
                "end",
                values=(
                    user.username,
                    user.role,
                    "Active" if user.active else "Disabled",
                    user.created_by or "-",
                ),
            )
        self.status_label.configure(
            text=f"{len(users)} account(s). Only administrators can create "
            "or disable accounts."
        )

    def _selected_username(self) -> Optional[str]:
        selection = self.user_tree.selection()
        if not selection:
            messagebox.showwarning(
                "Nothing selected", "Select an account first."
            )
            return None
        return str(self.user_tree.item(selection[0])["values"][0])

    def _clear_form(self) -> None:
        self.username_var.set("")
        self.password_var.set("")
        self.role_combo.set(ROLE_STAFF)

    # ------------------------------------------------------------------ #
    # Event handlers
    # ------------------------------------------------------------------ #
    def on_create_clicked(self) -> None:
        """Create a sub-user through the service (actor = signed-in user)."""
        actor = self._actor
        if actor is None:
            messagebox.showerror("No session", "Sign in to manage accounts.")
            return

        username = self.username_var.get().strip()
        password = self.password_var.get()
        role = self.role_combo.get() or "staff"
        if not username:
            messagebox.showwarning("Missing username", "Enter a username.")
            return
        if not password:
            messagebox.showwarning("Missing password", "Enter a password.")
            return

        try:
            created = self.services.auth_service.create_user(
                username, password, role, actor
            )
        except ValueError as error:
            messagebox.showerror("User not created", str(error))
            return

        messagebox.showinfo(
            "User created",
            f"'{created.username}' was created as {created.role}.",
        )
        self._clear_form()
        self.refresh()

    def on_disable_clicked(self) -> None:
        self._set_active(False)

    def on_enable_clicked(self) -> None:
        self._set_active(True)

    def _set_active(self, active: bool) -> None:
        actor = self._actor
        if actor is None:
            messagebox.showerror("No session", "Sign in to manage accounts.")
            return
        username = self._selected_username()
        if username is None:
            return

        try:
            updated = self.services.auth_service.set_active(
                username, active, actor
            )
        except ValueError as error:
            messagebox.showerror("Account not updated", str(error))
            return

        state = "enabled" if updated.active else "disabled"
        messagebox.showinfo("Account updated", f"'{updated.username}' {state}.")
        self.refresh()
