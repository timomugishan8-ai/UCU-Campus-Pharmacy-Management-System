"""Pharmacy branch domain entity and its object-level rules.

Pure domain code: no tkinter imports and no database connections. A branch
is a dispensing location (for example the Main Campus pharmacy or a
satellite clinic). Stock always belongs to one branch; there is no global
medicine quantity in this system.
"""

from __future__ import annotations

from typing import Any, Mapping


class BranchError(ValueError):
    """Base class for branch errors.

    Derives from ``ValueError`` so the GUI ``except ValueError`` boundary
    keeps catching branch validation problems.
    """


def _require_non_blank_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BranchError(f"{label} must be a non-empty string.")
    return value.strip()


class Branch:
    """One pharmacy location.

    Attributes
    ----------
    branch_id:
        Database identifier; ``None`` until the branch has been persisted.
        When present it must be a positive integer.
    branch_name:
        Unique, non-blank display name (uniqueness is enforced by the
        ``branches`` table).

    Both attributes are read-only: renaming happens through the
    repository/service layer so the database stays the source of truth.
    """

    def __init__(self, branch_name: Any, branch_id: Any = None) -> None:
        self._branch_name = _require_non_blank_text(branch_name, "Branch name")
        if branch_id is not None:
            if isinstance(branch_id, bool) or not isinstance(branch_id, int):
                raise BranchError("Branch ID must be a positive integer.")
            if branch_id <= 0:
                raise BranchError("Branch ID must be a positive integer.")
        self._branch_id = branch_id

    # ------------------------------------------------------------------ #
    # Encapsulated attributes
    # ------------------------------------------------------------------ #
    @property
    def branch_id(self) -> int | None:
        """Database identifier, or ``None`` before persistence."""
        return self._branch_id

    @property
    def branch_name(self) -> str:
        """Unique branch display name."""
        return self._branch_name

    # ------------------------------------------------------------------ #
    # Construction helpers
    # ------------------------------------------------------------------ #
    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Branch":
        """Map a ``branches`` repository row to a ``Branch``."""
        return cls(
            branch_name=data["branch_name"],
            branch_id=data.get("branch_id"),
        )

    # ------------------------------------------------------------------ #
    # Object identity
    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict[str, Any]:
        """Return a plain dictionary in repository-row shape."""
        return {
            "branch_id": self._branch_id,
            "branch_name": self._branch_name,
        }

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Branch):
            return NotImplemented
        return (
            self._branch_id == other._branch_id
            and self._branch_name == other._branch_name
        )

    def __hash__(self) -> int:
        return hash((self._branch_id, self._branch_name))

    def __repr__(self) -> str:
        return f"Branch({self._branch_name!r}, branch_id={self._branch_id!r})"
