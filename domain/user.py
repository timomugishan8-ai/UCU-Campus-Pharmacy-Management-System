"""Staff account domain entity (admin + sub-users) and its object-level rules.

Pure domain code: no tkinter imports, no database connections, and **no
passwords**. A ``StaffUser`` is an identity (username, role, active flag);
the secret itself never enters this layer - it is hashed by
``services.auth_service`` before it reaches the database.

Hierarchy mirrors the project's exception convention: every error derives
from ``ValueError`` so the GUI's single ``except ValueError`` boundary
keeps working.

Roles
-----
``admin``  - may create, enable and disable accounts (the "admit account"
             that owns its sub-users).
``staff``  - may sign in and use the pharmacy screens, nothing more.
"""

from __future__ import annotations

from typing import Any, Mapping

ROLE_ADMIN = "admin"
ROLE_STAFF = "staff"
ROLES: tuple[str, ...] = (ROLE_ADMIN, ROLE_STAFF)


class UserError(ValueError):
    """Base class for staff-account errors (a ValueError for the GUI)."""


class InvalidUserError(UserError):
    """Raised when an account attribute breaks a domain rule."""


class DuplicateUserError(UserError):
    """Raised when a username is already taken."""


class AuthenticationError(UserError):
    """Raised when a sign-in attempt fails (unknown user, bad or disabled)."""


class AuthorizationError(UserError):
    """Raised when a signed-in user lacks the required role."""


def _require_non_blank_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidUserError(f"{label} must be a non-empty string.")
    return value.strip()


def _require_role(value: Any) -> str:
    if not isinstance(value, str) or value not in ROLES:
        raise InvalidUserError(f"Role must be one of: {', '.join(ROLES)}.")
    return value


class StaffUser:
    """One signed-in identity.

    Attributes
    ----------
    username:
        Unique, non-blank display name (uniqueness enforced by the
        ``staff_users`` table).
    role:
        ``admin`` or ``staff`` - validated at construction.
    active:
        Disabled accounts cannot sign in.
    user_id:
        Database identifier, ``None`` before persistence.
    created_by:
        Username of the administrator who created this account
        (``bootstrap`` for the first administrator).

    Passwords are deliberately absent: this object represents *who*, not
    *how to prove it*. All attributes are read-only.
    """

    def __init__(
        self,
        username: Any,
        role: Any,
        active: Any = True,
        user_id: Any = None,
        created_by: Any = None,
    ) -> None:
        self._username = _require_non_blank_text(username, "Username")
        self._role = _require_role(role)
        if not isinstance(active, bool):
            raise InvalidUserError("Active flag must be a boolean.")
        if user_id is not None:
            if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
                raise InvalidUserError("User ID must be a positive integer.")
        if created_by is not None:
            self._created_by = _require_non_blank_text(created_by, "Created by")
        else:
            self._created_by = None
        self._active = active
        self._user_id = user_id

    # ------------------------------------------------------------------ #
    # Encapsulated attributes
    # ------------------------------------------------------------------ #
    @property
    def username(self) -> str:
        """Unique sign-in name."""
        return self._username

    @property
    def role(self) -> str:
        """``admin`` or ``staff``."""
        return self._role

    @property
    def active(self) -> bool:
        """Whether the account may sign in."""
        return self._active

    @property
    def user_id(self) -> int | None:
        """Database identifier, or ``None`` before persistence."""
        return self._user_id

    @property
    def created_by(self) -> str | None:
        """Administrator who created this account, if any."""
        return self._created_by

    @property
    def is_admin(self) -> bool:
        """True when this account may manage other accounts."""
        return self._role == ROLE_ADMIN

    # ------------------------------------------------------------------ #
    # Construction helpers
    # ------------------------------------------------------------------ #
    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "StaffUser":
        """Map a ``staff_users`` repository row to a ``StaffUser``."""
        return cls(
            username=data["username"],
            role=data["role"],
            active=bool(data.get("active", 1)),
            user_id=data.get("user_id"),
            created_by=data.get("created_by"),
        )

    # ------------------------------------------------------------------ #
    # Object identity
    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict[str, Any]:
        """Return a plain dictionary in repository-row shape (no secret)."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "role": self._role,
            "active": self._active,
            "created_by": self._created_by,
        }

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StaffUser):
            return NotImplemented
        return (
            self._username == other._username
            and self._role == other._role
            and self._active == other._active
            and self._user_id == other._user_id
        )

    def __hash__(self) -> int:
        return hash((self._username, self._role, self._active, self._user_id))

    def __repr__(self) -> str:
        state = "active" if self._active else "disabled"
        return f"StaffUser({self._username!r}, role={self._role!r}, {state})"
