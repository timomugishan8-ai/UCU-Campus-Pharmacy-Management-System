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

Visual design (2026-11-21): inspired by the UCU Alpha portal log-in page —
dark university-branded background, a centred white card with a crest and
the UCU tagline, and a bright pink action button. Drawn entirely with
standard tkinter widgets: no image files and no third-party libraries.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Any, Optional

from app.base_screen import BaseScreen
from domain.user import StaffUser

NAVY = "#0F2A43"
NAVY_DARK = "#0A1E30"
NAVY_MID = "#153451"
TEAL = "#16A085"
PINK = "#E91E63"
PINK_DARK = "#C2185B"
WHITE = "#FFFFFF"
LIGHT = "#F1F5F9"
BORDER = "#CBD5E1"
MUTED = "#64748B"
TEXT = "#1F2937"
GOLD = "#F5C518"


class BrandedButton(tk.Button):
    """A tk.Button with a ttk-compatible ``state()`` method.

    Custom colours need a tk.Button, but the existing auth tests (and the
    rest of the GUI contract) call ``state([...])`` like a ttk button. This
    small adapter keeps that API so the redesign changes only appearance.
    """

    def state(self, *args: Any) -> list[str]:
        if args:
            states = args[0] if isinstance(args[0], (list, tuple)) else args
            if "disabled" in states:
                self.configure(state="disabled")
            elif "!disabled" in states:
                self.configure(state="normal")
            return []
        return ["disabled"] if str(self.cget("state")) == "disabled" else ["!disabled"]


class LoginScreen(BaseScreen):
    """Sign-in form, with a first-administrator panel when no users exist."""

    def __init__(self, parent: Any, services: Any) -> None:
        super().__init__(parent, services)
        self._bootstrap_mode = not services.auth_service.has_users()
        self._build_widgets()
        self._apply_mode()

    # ------------------------------------------------------------------
    # Widget construction
    # ------------------------------------------------------------------
    def _build_widgets(self) -> None:
        background = tk.Frame(self, bg=NAVY_DARK)
        background.pack(fill="both", expand=True)

        self._build_top_bar(background)

        centre = tk.Frame(background, bg=NAVY_DARK)
        centre.pack(fill="both", expand=True)

        # pack_propagate(False) means the card needs BOTH dimensions; with
        # only a width it collapses to 1x1 and the whole form is clipped.
        card = tk.Frame(centre, bg=WHITE, width=540, height=540)
        card.pack(pady=(6, 18))
        card.pack_propagate(False)

        self._build_brand_header(card)
        # Pack the footer first (side=bottom) so the expanding form cannot
        # squeeze it out of the card.
        self._build_footer(card)
        self._build_form(card)

    def _build_top_bar(self, parent: tk.Widget) -> None:
        bar = tk.Frame(parent, bg=NAVY, height=46)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        tk.Label(
            bar,
            text="UCU PHARMACY   |   Management Information System",
            bg=NAVY,
            fg=WHITE,
            font=("Segoe UI", 11, "bold"),
        ).pack(side="left", padx=24)
        tk.Label(
            bar,
            text="Secure staff access",
            bg=NAVY,
            fg="#9FB3C8",
            font=("Segoe UI", 9),
        ).pack(side="right", padx=24)

    def _build_brand_header(self, card: tk.Widget) -> None:
        header = tk.Frame(card, bg=WHITE, height=118)
        header.pack(fill="x")
        header.pack_propagate(False)

        crest = tk.Canvas(
            header, width=74, height=74, bg=WHITE, highlightthickness=0
        )
        crest.pack(side="left", padx=(28, 14), pady=22)
        # A simple shield/cross emblem drawn with canvas primitives.
        crest.create_oval(6, 4, 68, 68, fill=TEAL, outline=NAVY, width=2)
        crest.create_rectangle(33, 16, 41, 56, fill=WHITE, outline="")
        crest.create_rectangle(18, 32, 56, 40, fill=WHITE, outline="")
        crest.create_text(
            37, 62, text="UCU", fill=GOLD,
            font=("Segoe UI", 7, "bold"),
        )

        names = tk.Frame(header, bg=WHITE)
        names.pack(side="left", pady=(22, 0))
        tk.Label(
            names,
            text="UGANDA CHRISTIAN UNIVERSITY",
            bg=WHITE,
            fg=NAVY,
            font=("Segoe UI", 15, "bold"),
        ).pack(anchor="w")
        tk.Label(
            names,
            text="A Centre of Excellence in the Heart of Africa",
            bg=WHITE,
            fg=PINK,
            font=("Segoe UI", 9, "italic"),
        ).pack(anchor="w", pady=(4, 0))

        tk.Frame(card, bg=TEAL, height=4).pack(fill="x")

    def _build_form(self, card: tk.Widget) -> None:
        form = tk.Frame(card, bg=WHITE)
        form.pack(fill="both", expand=True, padx=34, pady=(20, 12))

        self.title_label = tk.Label(
            form,
            text="Welcome back",
            bg=WHITE,
            fg=TEXT,
            font=("Segoe UI", 18, "bold"),
        )
        self.title_label.pack(anchor="w")
        self.subtitle_label = tk.Label(
            form,
            text="Sign in to continue to your pharmacy workspace",
            bg=WHITE,
            fg=MUTED,
            font=("Segoe UI", 10),
        )
        self.subtitle_label.pack(anchor="w", pady=(2, 18))

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.confirm_var = tk.StringVar()

        self._field(form, "Username", self.username_var, False, 0)
        self._field(form, "Password", self.password_var, True, 1)
        self.confirm_row = self._field(
            form, "Confirm password", self.confirm_var, True, 2
        )

        actions = tk.Frame(form, bg=WHITE)
        actions.pack(fill="x", pady=(22, 0))
        self.actions_row = actions
        self.sign_in_button = BrandedButton(
            actions,
            text="SIGN IN  >",
            command=self.on_sign_in_clicked,
            bg=PINK,
            fg=WHITE,
            activebackground=PINK_DARK,
            activeforeground=WHITE,
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 10, "bold"),
            padx=20,
            pady=9,
            cursor="hand2",
        )
        self.sign_in_button.pack(side="left")
        self.bootstrap_button = BrandedButton(
            actions,
            text="CREATE ADMINISTRATOR",
            command=self.on_create_first_admin_clicked,
            bg=TEAL,
            fg=WHITE,
            activebackground="#0E7C68",
            activeforeground=WHITE,
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=9,
            cursor="hand2",
        )
        self.bootstrap_button.pack(side="left", padx=(10, 0))

        self.status_label = tk.Label(
            form,
            text="",
            bg=WHITE,
            fg="#B03A2E",
            font=("Segoe UI", 9),
            wraplength=460,
            justify="left",
        )
        self.status_label.pack(anchor="w", pady=(12, 0))

        tk.Label(
            form,
            text="By signing in, I agree to the system usage terms and conditions.",
            bg=WHITE,
            fg=MUTED,
            font=("Segoe UI", 8),
        ).pack(anchor="w", pady=(10, 0))

        # Pressing Enter submits whichever action is currently enabled.
        self._bind_enter(self)

    def _field(
        self,
        parent: tk.Widget,
        label: str,
        variable: tk.StringVar,
        secret: bool,
        row: int,
    ) -> tk.Frame:
        wrapper = tk.Frame(parent, bg=WHITE)
        wrapper.pack(fill="x", pady=(0, 10))
        tk.Label(
            wrapper,
            text=label.upper(),
            bg=WHITE,
            fg=NAVY,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w")
        entry = tk.Entry(
            wrapper,
            textvariable=variable,
            show="*" if secret else "",
            bg=LIGHT,
            fg=TEXT,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=TEAL,
            font=("Segoe UI", 11),
            width=38,
        )
        entry.pack(fill="x", pady=(3, 0), ipady=6)
        return wrapper

    def _build_footer(self, card: tk.Widget) -> None:
        footer = tk.Frame(card, bg=NAVY)
        footer.pack(fill="x", side="bottom")
        tk.Label(
            footer,
            text="© 2026 Uganda Christian University   -   Pharmacy Management System",
            bg=NAVY,
            fg="#9FB3C8",
            font=("Segoe UI", 8),
        ).pack(pady=9)

    def _bind_enter(self, widget: tk.Widget) -> None:
        for child in widget.winfo_children():
            if isinstance(child, tk.Entry):
                child.bind(
                    "<Return>",
                    lambda _event: (
                        self.on_create_first_admin_clicked()
                        if self._bootstrap_mode
                        else self.on_sign_in_clicked()
                    ),
                )
            else:
                self._bind_enter(child)

    # ------------------------------------------------------------------
    # Mode
    # ------------------------------------------------------------------
    def _apply_mode(self) -> None:
        """Bootstrap mode shows the create button and hides sign-in."""
        if self._bootstrap_mode:
            self.sign_in_button.state(["disabled"])
            self.bootstrap_button.state(["!disabled"])
            self.confirm_row.pack(fill="x", pady=(0, 10), before=self.actions_row)
            self.title_label.configure(text="Create the first administrator")
            self.subtitle_label.configure(
                text="No accounts exist yet - set up the administrator account."
            )
            self.status_label.configure(
                text="First run: choose a username and a strong password.",
                fg=MUTED,
            )
        else:
            self.sign_in_button.state(["!disabled"])
            self.bootstrap_button.state(["disabled"])
            self.confirm_row.pack_forget()
            self.title_label.configure(text="Welcome back")
            self.subtitle_label.configure(
                text="Sign in to continue to your pharmacy workspace"
            )
            self.status_label.configure(text="")

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
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
            messagebox.showerror("Mismatch", "The passwords do not match.")
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

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------
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
    root.configure(bg=NAVY_DARK)
    root.geometry("900x620")
    root.minsize(820, 580)
    root.resizable(False, False)

    # Centre the gate on the screen.
    root.update_idletasks()
    width, height = 900, 620
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")

    screen = LoginScreen(root, services)
    # A frame must be given geometry explicitly: MainWindow uses place()
    # to mount its screens, but this gate is standalone, so pack the
    # screen so the form actually fills the window.
    screen.pack(fill="both", expand=True)

    # Bring the gate to the front. Without this it can open behind VS Code
    # or the browser and look as though the application did not start.
    root.attributes("-topmost", True)
    root.lift()
    root.focus_force()

    root.mainloop()
    return services.current_user
