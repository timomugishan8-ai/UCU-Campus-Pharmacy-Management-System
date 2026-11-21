"""Staff account operations: bootstrap, sign-in and sub-user management.

This service owns the account use cases (admit/administrator account with
sub-users). It contains no SQL and no tkinter: every operation goes
through the injected ``UserRepository``, and results are domain
``StaffUser`` objects.

Security notes
--------------
- Passwords are hashed with PBKDF2-HMAC-SHA256 (100k iterations) and a
  per-user random salt; only the hash reaches the database.
- Verification uses ``hmac.compare_digest`` (constant-time comparison).
- A failed sign-in raises the *same* message for "unknown username" and
  "wrong password" so attackers cannot enumerate accounts.

Public methods:
    has_users() -> bool
    create_first_admin(username, password) -> StaffUser
    login(username, password) -> StaffUser
    create_user(username, password, role, actor) -> StaffUser
    set_active(username, active, actor) -> StaffUser
    list_users(actor) -> list[StaffUser]

All failures raise ``ValueError`` subclasses from ``domain.user`` (the
GUI's ``except ValueError`` boundary catches them all).
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from typing import Any

from database.repositories.user_repository import UserRepository
from domain.user import (
    ROLE_ADMIN,
    ROLES,
    AuthenticationError,
    AuthorizationError,
    DuplicateUserError,
    InvalidUserError,
    StaffUser,
    UserError,
)

_PBKDF2_ITERATIONS = 100_000
_FAILED_SIGN_IN_MESSAGE = "Invalid username or password."


# ---------------------------------------------------------------------- #
# Password hashing helpers (module-private: never exported)
# ---------------------------------------------------------------------- #
def _hash_password(password: str) -> str:
    """Return ``algorithm$iterations$salt$hexdigest`` for storage."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), _PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    """Constant-time check of ``password`` against a stored hash string."""
    try:
        algorithm, iterations, salt, expected = stored.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        computed = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()
        return hmac.compare_digest(computed, expected)
    except (ValueError, TypeError):
        return False


class AuthService:
    """Coordinate sign-in and account-management use cases.

    Constructor
    ----------
    user_repository:
        ``UserRepository`` built from the shared ``Database`` instance
        (wired by the ``ApplicationServices`` facade).
    """

    MIN_PASSWORD_LENGTH = 6

    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository
        self.db = getattr(user_repository, "db", None)

    # ------------------------------------------------------------------ #
    # Input validation helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _require_username(value: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            raise InvalidUserError("Username must be a non-empty string.")
        return value.strip()

    @classmethod
    def _require_password(cls, value: Any) -> str:
        if not isinstance(value, str) or len(value) < cls.MIN_PASSWORD_LENGTH:
            raise InvalidUserError(
                f"Password must be at least {cls.MIN_PASSWORD_LENGTH} characters."
            )
        return value

    @staticmethod
    def _require_admin(actor: Any) -> StaffUser:
        """Authorisation guard shared by every privileged operation."""
        if not isinstance(actor, StaffUser) or not actor.active:
            raise AuthorizationError("Sign in to an active account first.")
        if not actor.is_admin:
            raise AuthorizationError("Administrator access required.")
        return actor

    # ------------------------------------------------------------------ #
    # Bootstrap and sign-in
    # ------------------------------------------------------------------ #
    def has_users(self) -> bool:
        """True when at least one account exists (disables bootstrap)."""
        return self.user_repository.count() > 0

    def create_first_admin(self, username: Any, password: Any) -> StaffUser:
        """Create the very first account (an administrator).

        Only possible while the table is empty - this replaces shipping a
        default admin/admin password. Afterwards, administrators create
        sub-users through :meth:`create_user`.
        """
        if self.has_users():
            raise AuthorizationError(
                "Accounts already exist. Sign in and ask an administrator "
                "to create users."
            )
        return self._create(username, password, ROLE_ADMIN, created_by="bootstrap")

    def login(self, username: Any, password: Any) -> StaffUser:
        """Authenticate and return the signed-in ``StaffUser``.

        Unknown username and wrong password raise the identical message;
        disabled accounts get their own clear message.
        """
        if not isinstance(username, str) or not username.strip():
            raise AuthenticationError(_FAILED_SIGN_IN_MESSAGE)
        if not isinstance(password, str) or not password:
            raise AuthenticationError(_FAILED_SIGN_IN_MESSAGE)

        row = self.user_repository.get_by_username(username.strip())
        if row is None:
            raise AuthenticationError(_FAILED_SIGN_IN_MESSAGE)
        if not _verify_password(password, row["password_hash"]):
            raise AuthenticationError(_FAILED_SIGN_IN_MESSAGE)

        user = StaffUser.from_dict(row)
        if not user.active:
            raise AuthenticationError("This account is disabled.")
        return user

    # ------------------------------------------------------------------ #
    # Sub-user management (administrator only)
    # ------------------------------------------------------------------ #
    def create_user(
        self, username: Any, password: Any, role: Any, actor: Any
    ) -> StaffUser:
        """Create a sub-user; ``actor`` must be an active administrator."""
        self._require_admin(actor)
        return self._create(
            username, password, role, created_by=actor.username
        )

    def _create(self, username: Any, password: Any, role: Any, created_by: str) -> StaffUser:
        clean_username = self._require_username(username)
        self._require_password(password)
        if not isinstance(role, str) or role not in ROLES:
            raise InvalidUserError(f"Role must be one of: {', '.join(ROLES)}.")

        if self.user_repository.get_by_username(clean_username) is not None:
            raise DuplicateUserError(
                f"Username '{clean_username}' is already taken."
            )

        try:
            self.user_repository.add(
                clean_username, _hash_password(password), role, created_by
            )
        except sqlite3.IntegrityError as exc:
            # Race backstop: the UNIQUE constraint is the authority.
            raise DuplicateUserError(
                f"Username '{clean_username}' is already taken."
            ) from exc

        stored = self.user_repository.get_by_username(clean_username)
        if stored is None:  # pragma: no cover - defensive check
            raise RuntimeError("The new account could not be read back.")
        return StaffUser.from_dict(stored)

    def set_active(self, username: Any, active: Any, actor: Any) -> StaffUser:
        """Enable or disable an account; ``actor`` must be an administrator.

        Two safety rules keep the system administrable:
        - an administrator cannot disable their own account;
        - at least one active administrator must always remain.
        """
        self._require_admin(actor)
        if not isinstance(active, bool):
            raise InvalidUserError("Active flag must be a boolean.")
        clean_username = self._require_username(username)

        row = self.user_repository.get_by_username(clean_username)
        if row is None:
            raise InvalidUserError(f"Unknown user '{clean_username}'.")
        target = StaffUser.from_dict(row)

        if not active:
            if target.username == actor.username:
                raise AuthorizationError(
                    "You cannot disable your own account."
                )
            if target.is_admin and target.active:
                if self.user_repository.count_active_admins() <= 1:
                    raise AuthorizationError(
                        "At least one active administrator must remain."
                    )

        self.user_repository.set_active(target.user_id, active)
        updated = self.user_repository.get_by_username(clean_username)
        return StaffUser.from_dict(updated)

    def list_users(self, actor: Any) -> list[StaffUser]:
        """Return every account; ``actor`` must be an administrator."""
        self._require_admin(actor)
        return [
            StaffUser.from_dict(row)
            for row in self.user_repository.list_all()
        ]
