"""Prescription domain entities and their object-level rules.

This module is pure domain code: it has no tkinter imports and no database
connections. It models a prescription header, its medicine lines and the
permitted status changes. Application services coordinate persistence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

# Prescription statuses agreed by the group.
STATUS_PENDING = "pending"
STATUS_DISPENSED = "dispensed"
STATUS_CANCELLED = "cancelled"
VALID_STATUSES = frozenset({STATUS_PENDING, STATUS_DISPENSED, STATUS_CANCELLED})

# Only pending prescriptions may move to another state. A dispensed or
# cancelled prescription is final.
ALLOWED_TRANSITIONS: Mapping[str, frozenset[str]] = {
    STATUS_PENDING: frozenset({STATUS_DISPENSED, STATUS_CANCELLED}),
    STATUS_DISPENSED: frozenset(),
    STATUS_CANCELLED: frozenset(),
}


class PrescriptionError(Exception):
    """Base class for prescription application errors."""


class InvalidPrescriptionStateError(PrescriptionError):
    """Raised when a status change is not allowed from the current state."""


class InsufficientStockError(PrescriptionError):
    """Raised when a prescription cannot be supplied from its branch."""


class UnauthorisedPrescriberError(PrescriptionError):
    """Raised when a controlled medicine lacks an authorised prescriber."""


class UnknownMedicineError(PrescriptionError):
    """Raised when a prescription line references a missing medicine."""


def _require_non_blank_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string.")
    return value.strip()


def _require_positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} must be a positive integer.")
    return value


@dataclass
class PrescriptionLine:
    """One medicine line on a prescription.

    Attributes
    ----------
    medicine_code:
        Code of an existing medicine.
    quantity:
        Strictly positive integer number of units requested.
    line_id / prescription_id:
        Database identifiers, ``None`` until the line has been persisted.
    medicine_name / is_controlled:
        Optional display/authorisation information copied from the medicine
        catalogue when the line is loaded.
    """

    medicine_code: str
    quantity: int
    line_id: int | None = None
    prescription_id: int | None = None
    medicine_name: str | None = None
    is_controlled: bool = False

    def __post_init__(self) -> None:
        self.medicine_code = _require_non_blank_text(
            self.medicine_code, "Medicine code"
        )
        self.quantity = _require_positive_int(self.quantity, "Line quantity")
        self.is_controlled = bool(self.is_controlled)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PrescriptionLine":
        """Build a line from a repository row (``dict`` or ``sqlite3.Row``)."""
        return cls(
            line_id=data.get("line_id"),
            prescription_id=data.get("prescription_id"),
            medicine_code=data["medicine_code"],
            quantity=data["quantity"],
            medicine_name=data.get("medicine_name"),
            is_controlled=bool(data.get("is_controlled", 0)),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dictionary representation of the line."""
        return {
            "line_id": self.line_id,
            "prescription_id": self.prescription_id,
            "medicine_code": self.medicine_code,
            "quantity": self.quantity,
            "medicine_name": self.medicine_name,
            "is_controlled": self.is_controlled,
        }


@dataclass
class Prescription:
    """A prescription header plus its medicine lines.

    The class enforces the object-level rules: a prescription needs a fictional
    patient identifier, a valid branch, at least one line, unique medicine
    lines and one of the three agreed statuses. State changes go through
    ``mark_dispensed`` and ``mark_cancelled`` so invalid transitions are
    rejected in one place.
    """

    branch_id: int
    patient_identifier: str
    lines: list[PrescriptionLine] = field(default_factory=list)
    prescription_id: int | None = None
    prescriber_code: str | None = None
    status: str = STATUS_PENDING
    created_at: str | None = None
    dispensed_at: str | None = None

    def __post_init__(self) -> None:
        self.branch_id = _require_positive_int(self.branch_id, "Branch ID")
        self.patient_identifier = _require_non_blank_text(
            self.patient_identifier, "Patient identifier"
        )
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Invalid prescription status: {self.status!r}")

        self.lines = list(self.lines)
        if not self.lines:
            raise ValueError("A prescription must contain at least one medicine line.")
        if not all(isinstance(line, PrescriptionLine) for line in self.lines):
            raise TypeError("Every prescription line must be a PrescriptionLine.")

        codes = [line.medicine_code for line in self.lines]
        if len(codes) != len(set(codes)):
            raise ValueError("A medicine may appear only once on a prescription.")

        if self.prescriber_code is not None:
            self.prescriber_code = _require_non_blank_text(
                self.prescriber_code, "Prescriber code"
            )

    # ------------------------------------------------------------------ #
    # Status helpers
    # ------------------------------------------------------------------ #
    @property
    def is_pending(self) -> bool:
        return self.status == STATUS_PENDING

    @property
    def is_dispensed(self) -> bool:
        return self.status == STATUS_DISPENSED

    @property
    def is_cancelled(self) -> bool:
        return self.status == STATUS_CANCELLED

    def can_dispense(self) -> bool:
        """Return True only when dispensing is a valid next step."""
        return self.is_pending and bool(self.lines)

    def _require_transition(self, new_status: str) -> None:
        if new_status not in ALLOWED_TRANSITIONS[self.status]:
            raise InvalidPrescriptionStateError(
                f"Cannot change a {self.status} prescription to {new_status}."
            )

    def mark_dispensed(self, dispensed_at: str | None = None) -> None:
        """Move a pending prescription to dispensed."""
        self._require_transition(STATUS_DISPENSED)
        if not self.lines:
            raise InvalidPrescriptionStateError(
                "A prescription with no lines cannot be dispensed."
            )
        self.status = STATUS_DISPENSED
        self.dispensed_at = dispensed_at

    def mark_cancelled(self) -> None:
        """Move a pending prescription to cancelled."""
        self._require_transition(STATUS_CANCELLED)
        self.status = STATUS_CANCELLED

    def add_line(self, line: PrescriptionLine) -> None:
        """Add a line while the prescription is still pending."""
        if not self.is_pending:
            raise InvalidPrescriptionStateError(
                "Lines can only be added to a pending prescription."
            )
        if not isinstance(line, PrescriptionLine):
            raise TypeError("line must be a PrescriptionLine.")
        if any(item.medicine_code == line.medicine_code for item in self.lines):
            raise ValueError(f"Medicine {line.medicine_code} is already on this prescription.")
        self.lines.append(line)

    # ------------------------------------------------------------------ #
    # Authorisation and conversion helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _medicine_needs_authorisation(medicine: Any) -> bool:
        """Ask a medicine whether it needs a prescriber code.

        We call a common behaviour first instead of checking subclasses by
        name. This is polymorphism: Member 2's ``ControlledMedicine`` can
        override ``requires_prescriber_code()`` while ``OrdinaryMedicine``
        inherits the ordinary answer. Dictionary rows from the repository are
        also accepted so the rule works before the domain hierarchy lands.
        """
        behaviour = getattr(medicine, "requires_prescriber_code", None)
        if callable(behaviour):
            return bool(behaviour())
        if isinstance(medicine, Mapping):
            return bool(medicine.get("is_controlled", False))
        return bool(getattr(medicine, "is_controlled", False))

    def requires_authorised_prescriber(self, medicines: Mapping[str, Any]) -> bool:
        """Return True if any line contains a controlled medicine.

        ``medicines`` maps each line's medicine code to a medicine object or
        repository row. A missing mapping entry is treated as controlled so a
        caller cannot accidentally skip the allow-list check.
        """
        for line in self.lines:
            medicine = medicines.get(line.medicine_code)
            if medicine is None or self._medicine_needs_authorisation(medicine):
                return True
        return False

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Prescription":
        """Build a prescription from a repository row.

        The repository returns the header plus a ``lines`` key containing
        medicine-line dictionaries.
        """
        line_rows: Iterable[Mapping[str, Any]] = data.get("lines", [])
        lines = [PrescriptionLine.from_dict(row) for row in line_rows]
        return cls(
            prescription_id=data.get("prescription_id"),
            branch_id=data["branch_id"],
            patient_identifier=data["patient_identifier"],
            prescriber_code=data.get("prescriber_code"),
            status=data.get("status", STATUS_PENDING),
            created_at=data.get("created_at"),
            dispensed_at=data.get("dispensed_at"),
            lines=lines,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dictionary representation of the prescription."""
        return {
            "prescription_id": self.prescription_id,
            "branch_id": self.branch_id,
            "patient_identifier": self.patient_identifier,
            "prescriber_code": self.prescriber_code,
            "status": self.status,
            "created_at": self.created_at,
            "dispensed_at": self.dispensed_at,
            "lines": [line.to_dict() for line in self.lines],
        }
