"""Medicine catalogue domain entities and their object-level rules.

This module is pure domain code: no tkinter imports and no database
connections. It models a catalogue entry shared by every branch and the
behavioural distinction between ordinary and controlled medicines.

Hierarchy (design document section 5.1, interface contract section 5):

- ``Medicine``        - abstract base class holding the shared data and
                        validation for every catalogue entry.
- ``OrdinaryMedicine``  - overrides ``requires_prescriber_code()`` with False.
- ``ControlledMedicine`` - overrides ``requires_prescriber_code()`` with True.

``requires_prescriber_code()`` is a behaviour, not a type label: dispensing
logic (``domain.prescription.Prescription.requires_authorised_prescriber``)
calls it polymorphically and never checks concrete subclass names.

Repository rows map to the correct subtype through ``Medicine.from_dict()``
(or ``Medicine.create()`` when the caller has the fields directly).
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import Any, Mapping


class MedicineError(ValueError):
    """Base class for medicine errors.

    Derives from ``ValueError`` so the GUI convention of catching
    ``ValueError`` at the screen boundary keeps working without every
    screen having to import this hierarchy.
    """


class InvalidMedicineError(MedicineError):
    """Raised when a medicine attribute breaks a domain rule."""


class DuplicateMedicineError(MedicineError):
    """Raised when a medicine code is already registered."""


def _require_non_blank_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidMedicineError(f"{label} must be a non-empty string.")
    return value.strip()


def _require_positive_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidMedicineError(f"{label} must be a positive number.")
    price = float(value)
    if not math.isfinite(price) or price <= 0:
        raise InvalidMedicineError(f"{label} must be a positive number.")
    return price


def _require_non_negative_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise InvalidMedicineError(f"{label} must be a non-negative integer.")
    return value


class Medicine(ABC):
    """Common base class for a catalogue entry.

    Attributes
    ----------
    medicine_code:
        Unique, non-blank identifier (uniqueness is enforced against the
        database by ``MedicineService.register_medicine``).
    name:
        Non-blank display name.
    unit_price:
        Strictly positive finite number.
    reorder_level:
        Non-negative integer; a branch stock quantity at or below this
        level is low stock.

    The attributes are read-only properties backed by private fields: the
    invariants are validated once on construction and cannot drift after
    that. Changes go through the application services.
    """

    def __init__(
        self,
        medicine_code: Any,
        name: Any,
        unit_price: Any,
        reorder_level: Any = 0,
    ) -> None:
        self._medicine_code = _require_non_blank_text(medicine_code, "Medicine code")
        self._name = _require_non_blank_text(name, "Medicine name")
        self._unit_price = _require_positive_number(unit_price, "Unit price")
        self._reorder_level = _require_non_negative_int(
            reorder_level, "Reorder level"
        )

    # ------------------------------------------------------------------ #
    # Encapsulated attributes
    # ------------------------------------------------------------------ #
    @property
    def medicine_code(self) -> str:
        """Unique medicine code."""
        return self._medicine_code

    @property
    def name(self) -> str:
        """Medicine display name."""
        return self._name

    @property
    def unit_price(self) -> float:
        """Unit price; always a positive finite float."""
        return self._unit_price

    @property
    def reorder_level(self) -> int:
        """Reorder level; always a non-negative integer."""
        return self._reorder_level

    @property
    def is_controlled(self) -> bool:
        """Persisted form of :meth:`requires_prescriber_code`.

        The ``medicines.is_controlled`` column stores exactly this
        behaviour, so the property derives from the polymorphic method
        instead of duplicating the answer.
        """
        return self.requires_prescriber_code()

    # ------------------------------------------------------------------ #
    # Polymorphic behaviour
    # ------------------------------------------------------------------ #
    @abstractmethod
    def requires_prescriber_code(self) -> bool:
        """Return True when dispensing this medicine needs an allow-listed prescriber.

        Implemented by :class:`OrdinaryMedicine` and
        :class:`ControlledMedicine`; callers rely on the common signature
        only.
        """

    # ------------------------------------------------------------------ #
    # Construction helpers
    # ------------------------------------------------------------------ #
    @classmethod
    def create(
        cls,
        medicine_code: str,
        name: str,
        unit_price: float,
        reorder_level: int = 0,
        is_controlled: bool = False,
    ) -> "Medicine":
        """Build the correct subtype from explicit fields.

        Used by GUI screens and services that hold raw form values; the
        ``is_controlled`` flag selects the concrete class.
        """
        if bool(is_controlled):
            return ControlledMedicine(medicine_code, name, unit_price, reorder_level)
        return OrdinaryMedicine(medicine_code, name, unit_price, reorder_level)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Medicine":
        """Map a ``medicines`` repository row to the correct subtype.

        The repository returns ``is_controlled`` as 0/1 (or a bool); any
        truthy value produces a :class:`ControlledMedicine`.
        """
        return cls.create(
            medicine_code=data["medicine_code"],
            name=data["name"],
            unit_price=data["unit_price"],
            reorder_level=data["reorder_level"],
            is_controlled=bool(data.get("is_controlled", False)),
        )

    # ------------------------------------------------------------------ #
    # Object identity
    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict[str, Any]:
        """Return a plain dictionary in repository-row shape."""
        return {
            "medicine_code": self._medicine_code,
            "name": self._name,
            "unit_price": self._unit_price,
            "reorder_level": self._reorder_level,
            "is_controlled": self.requires_prescriber_code(),
        }

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Medicine) or type(other) is not type(self):
            return NotImplemented
        return (
            self._medicine_code == other._medicine_code
            and self._name == other._name
            and self._unit_price == other._unit_price
            and self._reorder_level == other._reorder_level
        )

    def __hash__(self) -> int:
        return hash(
            (
                type(self).__name__,
                self._medicine_code,
                self._name,
                self._unit_price,
                self._reorder_level,
            )
        )

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}({self._medicine_code!r}, {self._name!r}, "
            f"{self._unit_price!r}, {self._reorder_level!r})"
        )


class OrdinaryMedicine(Medicine):
    """A medicine that may be dispensed without an allow-listed prescriber."""

    def requires_prescriber_code(self) -> bool:
        """Ordinary medicines never need prescriber authorisation."""
        return False


class ControlledMedicine(Medicine):
    """A medicine that may only be dispensed to an allow-listed prescriber."""

    def requires_prescriber_code(self) -> bool:
        """Controlled medicines always need prescriber authorisation."""
        return True
