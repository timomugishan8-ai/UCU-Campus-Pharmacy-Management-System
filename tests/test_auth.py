"""Tests for staff accounts: domain, password security, service and screens.

Covers the admin-plus-sub-users feature: first-administrator bootstrap,
sign-in (including the identical-failure-message rule), role-based
authorisation, the safety rules (cannot disable yourself or the last
administrator), salted password hashing, and the two tkinter screens
with mocked message boxes.
"""

import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import tkinter as tk

from database.connection import Database
from database.repositories.user_repository import UserRepository
from domain.user import (
    ROLE_ADMIN,
    ROLE_STAFF,
    AuthenticationError,
    AuthorizationError,
    DuplicateUserError,
    InvalidUserError,
    StaffUser,
    UserError,
)
from gui.login import LoginScreen, ask_for_login
from gui.user_admin import UserAdminScreen
from services.auth_service import (
    AuthService,
    _hash_password,
    _verify_password,
)


class StaffUserDomainTests(unittest.TestCase):
    """Object-level rules of the StaffUser entity."""

    def test_construction_and_properties(self):
        user = StaffUser("alice", ROLE_ADMIN, user_id=1, created_by="bootstrap")
        self.assertEqual(user.username, "alice")
        self.assertEqual(user.role, ROLE_ADMIN)
        self.assertTrue(user.active)
        self.assertTrue(user.is_admin)
        self.assertEqual(user.user_id, 1)
        self.assertEqual(user.created_by, "bootstrap")

    def test_staff_role_is_not_admin(self):
        user = StaffUser("bob", ROLE_STAFF)
        self.assertFalse(user.is_admin)

    def test_username_is_stripped_and_must_be_non_blank(self):
        self.assertEqual(StaffUser("  alice ", ROLE_STAFF).username, "alice")
        for bad in ("", "   ", None, 42):
            with self.subTest(username=bad):
                with self.assertRaises(InvalidUserError):
                    StaffUser(bad, ROLE_STAFF)

    def test_invalid_role_is_rejected(self):
        for bad in ("root", "", None, 1, "Admin"):
            with self.subTest(role=bad):
                with self.assertRaises(InvalidUserError):
                    StaffUser("alice", bad)

    def test_invalid_active_flag_and_user_id_are_rejected(self):
        with self.assertRaises(InvalidUserError):
            StaffUser("alice", ROLE_STAFF, active="yes")
        for bad_id in (0, -1, "1", True):
            with self.subTest(user_id=bad_id):
                with self.assertRaises(InvalidUserError):
                    StaffUser("alice", ROLE_STAFF, user_id=bad_id)

    def test_all_user_errors_are_value_errors_for_the_gui_boundary(self):
        for error_class in (
            UserError,
            InvalidUserError,
            DuplicateUserError,
            AuthenticationError,
            AuthorizationError,
        ):
            with self.subTest(error=error_class.__name__):
                self.assertTrue(issubclass(error_class, ValueError))

    def test_attributes_are_read_only(self):
        user = StaffUser("alice", ROLE_STAFF, user_id=1)
        for attribute, value in (
            ("username", "bob"),
            ("role", ROLE_ADMIN),
            ("active", False),
            ("user_id", 2),
            ("created_by", "someone"),
            ("is_admin", True),
        ):
            with self.subTest(attribute=attribute):
                with self.assertRaises(AttributeError):
                    setattr(user, attribute, value)

    def test_to_dict_and_from_dict_round_trip(self):
        user = StaffUser("alice", ROLE_ADMIN, active=False, user_id=3,
                         created_by="bootstrap")
        restored = StaffUser.from_dict(user.to_dict())
        self.assertEqual(restored, user)
        self.assertEqual(restored.user_id, 3)

    def test_repository_row_active_flag_maps_to_bool(self):
        user = StaffUser.from_dict(
            {"username": "bob", "role": "staff", "active": 0}
        )
        self.assertIs(user.active, False)
        user = StaffUser.from_dict(
            {"username": "bob", "role": "staff", "active": 1}
        )
        self.assertIs(user.active, True)


class PasswordSecurityTests(unittest.TestCase):
    """PBKDF2 hashing: salted, verifiable, never stored as plain text."""

    def test_hash_format_and_salt_uniqueness(self):
        first = _hash_password("secret123")
        second = _hash_password("secret123")
        self.assertTrue(first.startswith("pbkdf2_sha256$100000$"))
        # Same password, different random salts -> different hashes.
        self.assertNotEqual(first, second)

    def test_verify_accepts_correct_and_rejects_wrong_password(self):
        stored = _hash_password("correct-horse")
        self.assertTrue(_verify_password("correct-horse", stored))
        self.assertFalse(_verify_password("wrong-horse", stored))
        self.assertFalse(_verify_password("", stored))

    def test_verify_rejects_corrupted_storage(self):
        self.assertFalse(_verify_password("anything", "not-a-real-hash"))
        self.assertFalse(_verify_password("anything", "md5$1$abc$def"))


class AuthServiceTestCase(unittest.TestCase):
    """Shared setup: temporary database + auth service."""

    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = Database(self.db_path)
        self.db.initialize_schema()
        self.repository = UserRepository(self.db)
        self.service = AuthService(self.repository)

    def tearDown(self):
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
        except OSError:
            pass


class BootstrapAndLoginTests(AuthServiceTestCase):
    """First administrator bootstrap and the sign-in rules."""

    def test_fresh_database_has_no_users(self):
        self.assertFalse(self.service.has_users())

    def test_create_first_admin_returns_an_active_admin(self):
        admin = self.service.create_first_admin("chief", "secret123")
        self.assertTrue(admin.is_admin)
        self.assertTrue(admin.active)
        self.assertEqual(admin.created_by, "bootstrap")
        self.assertTrue(self.service.has_users())

    def test_bootstrap_is_only_possible_once(self):
        self.service.create_first_admin("chief", "secret123")
        with self.assertRaises(AuthorizationError):
            self.service.create_first_admin("second", "secret123")
        admin = self.service.login("chief", "secret123")
        self.assertEqual(len(self.service.list_users(admin)), 1)

    def test_login_round_trip(self):
        self.service.create_first_admin("chief", "secret123")
        user = self.service.login("chief", "secret123")
        self.assertEqual(user.username, "chief")
        self.assertTrue(user.is_admin)

    def test_unknown_user_and_wrong_password_give_the_identical_message(self):
        self.service.create_first_admin("chief", "secret123")
        with self.assertRaises(AuthenticationError) as unknown:
            self.service.login("ghost", "secret123")
        with self.assertRaises(AuthenticationError) as wrong:
            self.service.login("chief", "wrong-password")
        self.assertEqual(str(unknown.exception), str(wrong.exception))

    def test_blank_credentials_fail_authentication(self):
        for username, password in (("", "x"), ("chief", ""), ("  ", "x"),
                                   (None, "x"), ("chief", None)):
            with self.subTest(username=username, password=password):
                with self.assertRaises(AuthenticationError):
                    self.service.login(username, password)

    def test_disabled_account_cannot_sign_in(self):
        admin = self.service.create_first_admin("chief", "secret123")
        self.service.create_user("staffer", "secret123", ROLE_STAFF, admin)
        self.service.set_active("staffer", False, admin)
        with self.assertRaises(AuthenticationError) as caught:
            self.service.login("staffer", "secret123")
        self.assertIn("disabled", str(caught.exception))

    def test_short_password_is_rejected_on_creation(self):
        with self.assertRaises(InvalidUserError):
            self.service.create_first_admin("chief", "12345")
        self.assertFalse(self.service.has_users())


class UserManagementTests(AuthServiceTestCase):
    """Sub-user creation, authorisation guards and safety rules."""

    def setUp(self):
        super().setUp()
        self.admin = self.service.create_first_admin("chief", "secret123")

    def test_admin_creates_a_sub_user_attributed_to_themself(self):
        created = self.service.create_user(
            "staffer", "secret123", ROLE_STAFF, self.admin
        )
        self.assertEqual(created.username, "staffer")
        self.assertFalse(created.is_admin)
        self.assertEqual(created.created_by, "chief")

    def test_admin_can_create_another_administrator(self):
        created = self.service.create_user(
            "second-admin", "secret123", ROLE_ADMIN, self.admin
        )
        self.assertTrue(created.is_admin)

    def test_staff_actor_is_rejected(self):
        staffer = self.service.create_user(
            "staffer", "secret123", ROLE_STAFF, self.admin
        )
        with self.assertRaises(AuthorizationError):
            self.service.create_user("intruder", "secret123", ROLE_STAFF, staffer)
        with self.assertRaises(AuthorizationError):
            self.service.set_active("staffer", False, staffer)
        with self.assertRaises(AuthorizationError):
            self.service.list_users(staffer)

    def test_missing_or_inactive_actor_is_rejected(self):
        with self.assertRaises(AuthorizationError):
            self.service.create_user("x-user", "secret123", ROLE_STAFF, None)
        disabled = self.service.create_user(
            "disabled-admin", "secret123", ROLE_ADMIN, self.admin
        )
        # Use the object returned by set_active: it reflects active=False.
        disabled = self.service.set_active("disabled-admin", False, self.admin)
        with self.assertRaises(AuthorizationError):
            self.service.create_user("y-user", "secret123", ROLE_STAFF, disabled)

    def test_duplicate_username_is_rejected(self):
        self.service.create_user("staffer", "secret123", ROLE_STAFF, self.admin)
        with self.assertRaises(DuplicateUserError):
            self.service.create_user("staffer", "other-pass1", ROLE_STAFF, self.admin)
        # Exactly one row with that name survives.
        matches = [
            u for u in self.service.list_users(self.admin)
            if u.username == "staffer"
        ]
        self.assertEqual(len(matches), 1)

    def test_invalid_role_is_rejected_by_the_service(self):
        with self.assertRaises(InvalidUserError):
            self.service.create_user("someone", "secret123", "superuser", self.admin)

    def test_password_is_never_stored_in_plain_text(self):
        self.service.create_user("staffer", "secret123", ROLE_STAFF, self.admin)
        row = self.repository.get_by_username("staffer")
        self.assertNotIn("secret123", row["password_hash"])
        self.assertTrue(row["password_hash"].startswith("pbkdf2_sha256$"))
        self.assertFalse(_verify_password("secret123-not-it", row["password_hash"]))

    def test_admin_can_disable_and_re_enable_a_sub_user(self):
        self.service.create_user("staffer", "secret123", ROLE_STAFF, self.admin)
        disabled = self.service.set_active("staffer", False, self.admin)
        self.assertFalse(disabled.active)
        re_enabled = self.service.set_active("staffer", True, self.admin)
        self.assertTrue(re_enabled.active)
        # Re-enabled accounts can sign in again.
        self.assertTrue(self.service.login("staffer", "secret123").active)

    def test_admin_cannot_disable_their_own_account(self):
        with self.assertRaises(AuthorizationError) as caught:
            self.service.set_active("chief", False, self.admin)
        self.assertIn("own account", str(caught.exception))

    def test_last_active_administrator_cannot_be_disabled(self):
        self.service.create_user(
            "helper-admin", "secret123", ROLE_ADMIN, self.admin
        )
        # Two active admins: chief may step helper down (and back up).
        self.service.set_active("helper-admin", False, self.admin)
        self.service.set_active("helper-admin", True, self.admin)

        # Meanwhile chief's own row is disabled elsewhere, while this
        # session still holds a stale 'active' chief object. helper-admin
        # is then the ONLY active administrator left in the database, and
        # the guard must refuse to take out the final one.
        self.repository.set_active(self.admin.user_id, False)
        with self.assertRaises(AuthorizationError) as caught:
            self.service.set_active("helper-admin", False, self.admin)
        self.assertIn("administrator must remain", str(caught.exception))

    def test_set_active_on_unknown_user_is_rejected(self):
        with self.assertRaises(InvalidUserError):
            self.service.set_active("ghost", False, self.admin)

    def test_list_users_requires_an_administrator(self):
        self.service.create_user("staffer", "secret123", ROLE_STAFF, self.admin)
        users = self.service.list_users(self.admin)
        self.assertEqual(
            sorted(u.username for u in users), ["chief", "staffer"]
        )
        with self.assertRaises(AuthorizationError):
            self.service.list_users(None)


class UserRepositorySchemaTests(AuthServiceTestCase):
    """The table itself: constraints enforced at the database level."""

    def test_count_and_active_admin_guards(self):
        admin = self.service.create_first_admin("chief", "secret123")
        self.assertEqual(self.repository.count(), 1)
        self.assertEqual(self.repository.count_active_admins(), 1)
        self.service.create_user("staffer", "secret123", ROLE_STAFF, admin)
        self.assertEqual(self.repository.count(), 2)
        self.assertEqual(self.repository.count_active_admins(), 1)

    def test_unique_username_constraint_is_the_race_backstop(self):
        self.service.create_first_admin("chief", "secret123")
        with self.assertRaises(sqlite3.IntegrityError):
            self.repository.add("chief", "some-hash", ROLE_STAFF, "chief")

    def test_role_check_constraint_rejects_unknown_roles(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.repository.add("someone", "some-hash", "superuser", None)

    def test_list_all_is_ordered_by_username(self):
        self.service.create_first_admin("chief", "secret123")
        rows = self.repository.list_all()
        self.assertEqual([row["username"] for row in rows], ["chief"])


class _StubAuthServices:
    """Minimal stand-in for the ApplicationServices facade (Member 1)."""

    def __init__(self, database: Database) -> None:
        self.auth_service = AuthService(UserRepository(database))
        self.current_user = None


class ScreenTestCase(unittest.TestCase):
    """Shared tkinter setup: one hidden root, one temporary database."""

    screen_class = None

    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = Database(self.db_path)
        self.db.initialize_schema()
        self.services = _StubAuthServices(self.db)
        # Each screen gets its own withdraw-able container: on success the
        # login screen destroys its toplevel, which must never be the
        # shared test root.
        self.container = tk.Toplevel(self.root)
        self.container.withdraw()
        self.screen = self.screen_class(self.container, self.services)

    def tearDown(self):
        try:
            self.container.destroy()
        except tk.TclError:
            pass
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
        except OSError:
            pass


class LoginScreenTests(ScreenTestCase):
    screen_class = LoginScreen

    @patch("gui.login.messagebox.showinfo")
    @patch("gui.login.messagebox.showerror")
    def test_fresh_install_offers_first_admin_and_finishes(
        self, error, info
    ):
        # Bootstrap mode: sign-in is disabled, the create button is live.
        self.assertIn("disabled", self.screen.sign_in_button.state())
        self.screen.username_var.set("chief")
        self.screen.password_var.set("secret123")
        self.screen.confirm_var.set("secret123")
        self.screen.on_create_first_admin_clicked()

        info.assert_called_once()
        error.assert_not_called()
        self.assertIsInstance(self.services.current_user, StaffUser)
        self.assertTrue(self.services.current_user.is_admin)
        # The gate window closed itself so MainWindow can open next.
        self.assertFalse(self.container.winfo_exists())

    @patch("gui.login.messagebox.showinfo")
    @patch("gui.login.messagebox.showerror")
    def test_mismatched_passwords_do_not_create_anything(
        self, error, info
    ):
        self.screen.username_var.set("chief")
        self.screen.password_var.set("secret123")
        self.screen.confirm_var.set("different")
        self.screen.on_create_first_admin_clicked()

        error.assert_called_once()
        info.assert_not_called()
        self.assertIsNone(self.services.current_user)
        self.assertFalse(self.services.auth_service.has_users())

    @patch("gui.login.messagebox.showinfo")
    @patch("gui.login.messagebox.showerror")
    def test_sign_in_success_sets_current_user(self, error, info):
        self.services.auth_service.create_first_admin("chief", "secret123")
        # Rebuild: the screen chose bootstrap mode for the empty table.
        self.screen.destroy()
        self.screen = LoginScreen(self.container, self.services)

        self.screen.username_var.set("chief")
        self.screen.password_var.set("secret123")
        self.screen.on_sign_in_clicked()

        error.assert_not_called()
        self.assertEqual(self.services.current_user.username, "chief")

    @patch("gui.login.messagebox.showinfo")
    @patch("gui.login.messagebox.showerror")
    def test_failed_sign_in_shows_dialog_and_keeps_gate_open(
        self, error, info
    ):
        self.services.auth_service.create_first_admin("chief", "secret123")
        self.screen.destroy()
        self.screen = LoginScreen(self.container, self.services)

        self.screen.username_var.set("chief")
        self.screen.password_var.set("wrong-password")
        self.screen.on_sign_in_clicked()

        error.assert_called_once()
        info.assert_not_called()
        self.assertIsNone(self.services.current_user)
        self.assertTrue(self.container.winfo_exists())  # gate stays open

    @patch("gui.login.messagebox.showinfo")
    @patch("gui.login.messagebox.showerror")
    def test_blank_credentials_show_a_dialog(self, error, info):
        self.services.auth_service.create_first_admin("chief", "secret123")
        self.screen.destroy()
        self.screen = LoginScreen(self.container, self.services)

        self.screen.username_var.set("")
        self.screen.password_var.set("")
        self.screen.on_sign_in_clicked()

        error.assert_called_once()
        info.assert_not_called()
        self.assertIsNone(self.services.current_user)


class AskForLoginRunnerTests(unittest.TestCase):
    """``ask_for_login`` must mount the screen, or the window is blank."""

    def test_screen_is_packed_into_the_gate_window(self):
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        if os.path.exists(db_path):
            os.remove(db_path)
        try:
            db = Database(db_path)
            db.initialize_schema()
            services = _StubAuthServices(db)

            observed = {}

            def fake_mainloop(root):
                # Runs instead of the real event loop: inspect how the
                # window mounted its screen, then clean the window up.
                children = root.winfo_children()
                observed["child_count"] = len(children)
                observed["pack"] = children[0].pack_info() if children else {}
                root.destroy()

            with patch.object(tk.Tk, "mainloop", fake_mainloop):
                result = ask_for_login(services)

            # Nobody signed in during the fake loop, so no session.
            self.assertIsNone(result)
            # Regression: the screen used to be created but never packed,
            # which rendered a completely blank login window.
            self.assertEqual(observed["child_count"], 1)
            self.assertEqual(observed["pack"].get("fill"), "both")
            self.assertIn(observed["pack"].get("expand"), (1, "1"))
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)


class UserAdminScreenTests(ScreenTestCase):
    screen_class = UserAdminScreen

    def setUp(self):
        super().setUp()
        self.admin = self.services.auth_service.create_first_admin(
            "chief", "secret123"
        )
        self.services.current_user = self.admin
        self.screen.refresh()

    @patch("gui.user_admin.messagebox.showinfo")
    @patch("gui.user_admin.messagebox.showerror")
    @patch("gui.user_admin.messagebox.showwarning")
    def test_admin_sees_the_list_and_creates_sub_users(
        self, warning, error, info
    ):
        current = [
            str(self.screen.user_tree.item(i)["values"][0])
            for i in self.screen.user_tree.get_children()
        ]
        self.assertIn("chief", current)

        self.screen.username_var.set("staffer")
        self.screen.password_var.set("secret123")
        self.screen.role_combo.set(ROLE_STAFF)
        self.screen.on_create_clicked()

        info.assert_called_once()
        error.assert_not_called()
        usernames = [
            str(self.screen.user_tree.item(i)["values"][0])
            for i in self.screen.user_tree.get_children()
        ]
        self.assertIn("staffer", usernames)
        # Form clears after success.
        self.assertEqual(self.screen.username_var.get(), "")

    @patch("gui.user_admin.messagebox.showinfo")
    @patch("gui.user_admin.messagebox.showerror")
    @patch("gui.user_admin.messagebox.showwarning")
    def test_duplicate_creation_shows_the_domain_error(
        self, warning, error, info
    ):
        self.services.auth_service.create_user(
            "staffer", "secret123", ROLE_STAFF, self.admin
        )
        self.screen.refresh()

        self.screen.username_var.set("staffer")
        self.screen.password_var.set("other-pass1")
        self.screen.on_create_clicked()

        error.assert_called_once()
        self.assertIn("already taken", error.call_args[0][1])
        info.assert_not_called()

    @patch("gui.user_admin.messagebox.showinfo")
    @patch("gui.user_admin.messagebox.showerror")
    @patch("gui.user_admin.messagebox.showwarning")
    def test_disable_and_enable_through_the_screen(self, warning, error, info):
        self.services.auth_service.create_user(
            "staffer", "secret123", ROLE_STAFF, self.admin
        )
        self.screen.refresh()
        staffer_row = next(
            i for i in self.screen.user_tree.get_children()
            if str(self.screen.user_tree.item(i)["values"][0]) == "staffer"
        )
        self.screen.user_tree.selection_set(staffer_row)

        self.screen.on_disable_clicked()
        info.assert_called_once()
        error.assert_not_called()
        row = self.services.auth_service.user_repository.get_by_username("staffer")
        self.assertEqual(row["active"], 0)

        # Refresh rebuilt the tree, so re-select the row before enabling.
        staffer_row = next(
            i for i in self.screen.user_tree.get_children()
            if str(self.screen.user_tree.item(i)["values"][0]) == "staffer"
        )
        self.screen.user_tree.selection_set(staffer_row)
        self.screen.on_enable_clicked()
        row = self.services.auth_service.user_repository.get_by_username("staffer")
        self.assertEqual(row["active"], 1)

    @patch("gui.user_admin.messagebox.showinfo")
    @patch("gui.user_admin.messagebox.showerror")
    @patch("gui.user_admin.messagebox.showwarning")
    def test_disabling_yourself_shows_the_safety_error(
        self, warning, error, info
    ):
        chief_row = next(
            i for i in self.screen.user_tree.get_children()
            if str(self.screen.user_tree.item(i)["values"][0]) == "chief"
        )
        self.screen.user_tree.selection_set(chief_row)

        self.screen.on_disable_clicked()

        error.assert_called_once()
        self.assertIn("own account", error.call_args[0][1])
        info.assert_not_called()

    def test_staff_member_gets_a_disabled_form_and_explanation(self):
        staffer = self.services.auth_service.create_user(
            "staffer", "secret123", ROLE_STAFF, self.admin
        )
        self.services.current_user = staffer
        self.screen.refresh()

        # The service refused the listing; the explanation is visible and
        # the account-management form is greyed out.
        self.assertIn("Administrator access required",
                      self.screen.session_label.cget("text")
                      + self.screen.status_label.cget("text"))
        self.assertIn("disabled", self.screen.create_button.state())
        self.assertEqual(self.screen.user_tree.get_children(), ())

    def test_no_session_gets_a_disabled_form(self):
        self.services.current_user = None
        self.screen.refresh()
        self.assertIn("disabled", self.screen.create_button.state())
        self.assertIn("Sign in",
                      self.screen.status_label.cget("text"))


if __name__ == "__main__":
    unittest.main()
