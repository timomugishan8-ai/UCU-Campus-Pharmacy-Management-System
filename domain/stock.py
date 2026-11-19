"""Stock domain entity: one medicine's quantity at one branch.

Pure domain code: no tkinter imports and no database connections. Stock is
identified by the ``(medicine_code, branch_id)`` pair, matching the
composite primary key of the ``stock`` table. Quantity is branch-specific
and can never become negative.

Rules enforced here (design document section 5.3 and the exam domain
rules):
- quantity is a non-negative integer;
- receiving adds a strictly positive integer;
- a decrease only happens when enough quantity is available;
- low stock means ``quantity <= reorder_level``.
"""

from __future__ import annotations

from typing import Any, Mapping


class StockError(ValueError):
    """Base class for stock errors.

    Derives from ``ValueError`` so the GUI ``except ValueError`` boundary
    keeps catching stock validation problems.
    """


class InsufficientStockError(StockError):
    """Raised when a decrease would drive a branch quantity below zero."""


def _require_non_blank_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StockError(f"{label} must be a non-empty string.")
    return value.strip()


def _require_positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise StockError(f"{label} must be a positive integer.")
    return value


def _require_non_negative_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise StockError(f"{label} must be a non-negative integer.")
    return value


class Stock:
    """Quantity of a single medicine at a single branch.

    Attributes
    ----------
    medicine_code:
        Code of the stocked medicine.
    branch_id:
        Positive integer branch identifier; stock is never global.
    quantity:
        Non-negative integer held at the branch.

    Quantity is read-only from the outside: it changes only through
    :meth:`receive` and :meth:`decrease`, which uphold the invariants.
    """

    def __init__(
        self,
        medicine_code: Any,
        branch_id: Any,
        quantity: Any = 0,
    ) -> None:
        self._medicine_code = _require_non_blank_text(medicine_code, "Medicine code")
        self._branch_id = _require_positive_int(branch_id, "Branch ID")
        self._quantity = _require_non_negative_int(quantity, "Quantity")

    # ------------------------------------------------------------------ #
    # Encapsulated attributes
    # ------------------------------------------------------------------ #
    @property
    def medicine_code(self) -> str:
        """Code of the stocked medicine."""
        return self._medicine_code

    @property
    def branch_id(self) -> int:
        """Branch holding this stock row."""
        return self._branch_id

    @property
    def quantity(self) -> int:
        """Current non-negative quantity at the branch."""
        return self._quantity

    # ------------------------------------------------------------------ #
    # Behaviour
    # ------------------------------------------------------------------ #
    def receive(self, amount: Any) -> None:
        """Add a strictly positive integer quantity to this branch's stock."""
        self._quantity += _require_positive_int(amount, "Received quantity")

    def can_fulfil(self, amount: Any) -> bool:
        """Return True when this branch can supply ``amount`` units."""
        return _require_positive_int(amount, "Requested quantity") <= self._quantity

    def decrease(self, amount: Any) -> None:
        """Remove ``amount`` units, or raise without changing anything.

        Raises ``InsufficientStockError`` when the branch holds less than
        ``amount``; the quantity is left untouched so it can never go
        negative.
        """
        requested = _require_positive_int(amount, "Requested quantity")
        if requested > self._quantity:
            raise InsufficientStockError(
                f"Insufficient stock for '{self._medicine_code}' at branch "
                f"{self._branch_id}: requested {requested}, "
                f"available {self._quantity}."
            )
        self._quantity -= requested

    def is_low_stock(self, reorder_level: Any) -> bool:
        """Return True when quantity is at or below ``reorder_level``."""
        level = _require_non_negative_int(reorder_level, "Reorder level")
        return self._quantity <= level

    # ------------------------------------------------------------------ #
    # Construction helpers
    # ------------------------------------------------------------------ #
    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Stock":
        """Map a ``stock`` repository row to a ``Stock``."""
        return cls(
            medicine_code=data["medicine_code"],
            branch_id=data["branch_id"],
            quantity=data.get("quantity", 0),
        )

    # ------------------------------------------------------------------ #
    # Object identity
    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict[str, Any]:
        """Return a plain dictionary in repository-row shape."""
        return {
            "medicine_code": self._medicine_code,
            "branch_id": self._branch_id,
            "quantity": self._quantity,
        }

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Stock):
            return NotImplemented
        return (
            self._medicine_code == other._medicine_code
            and self._branch_id == other._branch_id
            and self._quantity == other._quantity
        )

    def __hash__(self) -> int:
        return hash((self._medicine_code, self._branch_id, self._quantity))

    def __repr__(self) -> str:
        return (
            f"Stock({self._medicine_code!r}, branch {self._branch_id}, "
            f"quantity={self._quantity})"
        )
