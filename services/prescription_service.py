"""Prescription creation, cancellation and atomic dispensing operations.

Public methods agreed by the group (do not rename):
    create_prescription(patient_identifier, branch_id, prescriber_code, lines)
    dispense_prescription(prescription_id)
    cancel_prescription(prescription_id)
    get_prescription(prescription_id)

Return format: the first three return a ``domain.prescription.Prescription``
object; ``get_prescription`` returns that object or ``None`` when the id is
unknown. Expected failures raise ``ValueError`` or one of the prescription
exceptions defined in ``domain.prescription``.

The service owns the dispensing transaction boundary. It never opens tkinter
widgets and never writes SQL itself: all data access goes through the injected
repositories using one shared connection.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Sequence

from database.repositories.branch_repository import BranchRepository
from database.repositories.prescriber_repository import PrescriberRepository
from domain.prescription import (
    STATUS_CANCELLED,
    STATUS_DISPENSED,
    InsufficientStockError,
    InvalidPrescriptionStateError,
    Prescription,
    PrescriptionLine,
    UnauthorisedPrescriberError,
    UnknownMedicineError,
)


def _utc_now() -> str:
    """Timestamp in the same format as SQLite's ``datetime('now')``."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


class PrescriptionService:
    """Coordinate prescription use cases and the dispensing transaction.

    Constructor
    ----------
    prescription_repository, medicine_repository, stock_repository:
        Member 5 repositories. The first three positional arguments are the
        normal application wiring.
    prescriber_repository / branch_repository:
        Optional overrides for tests. When omitted they are built from the
        shared ``Database`` found on the repositories.
    """

    def __init__(
        self,
        prescription_repository: Any,
        medicine_repository: Any,
        stock_repository: Any,
        prescriber_repository: Optional[Any] = None,
        branch_repository: Optional[Any] = None,
    ) -> None:
        self.prescription_repository = prescription_repository
        self.medicine_repository = medicine_repository
        self.stock_repository = stock_repository

        self.db = getattr(prescription_repository, "db", None)
        self.prescriber_repository = prescriber_repository or PrescriberRepository(
            self.db
        )
        self.branch_repository = branch_repository or BranchRepository(self.db)

    # ------------------------------------------------------------------ #
    # Input validation helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _require_positive_int(value: Any, label: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{label} must be a positive integer.")
        return value

    @staticmethod
    def _require_non_blank_text(value: Any, label: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{label} must be a non-empty string.")
        return value.strip()

    @classmethod
    def _normalise_prescriber_code(cls, value: Any) -> Optional[str]:
        """Ordinary prescriptions may have no prescriber code."""
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return cls._require_non_blank_text(value, "Prescriber code")

    @classmethod
    def _normalise_lines(cls, lines: Sequence[Any]) -> list[tuple[str, int]]:
        """Accept PrescriptionLine, dict or ``(code, quantity)`` tuples."""
        if isinstance(lines, (str, bytes)) or lines is None:
            raise ValueError("lines must be a collection of medicine lines.")

        try:
            items = list(lines)
        except TypeError as exc:
            raise ValueError("lines must be a collection of medicine lines.") from exc

        if not items:
            raise ValueError("A prescription must contain at least one medicine line.")

        result: list[tuple[str, int]] = []
        seen: set[str] = set()
        for item in items:
            if isinstance(item, PrescriptionLine):
                code, quantity = item.medicine_code, item.quantity
            elif isinstance(item, Mapping):
                code, quantity = item.get("medicine_code"), item.get("quantity")
            else:
                try:
                    code, quantity = item
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        "Each line must be (medicine_code, quantity), a dict or "
                        "a PrescriptionLine."
                    ) from exc

            code = cls._require_non_blank_text(code, "Medicine code")
            quantity = cls._require_positive_int(quantity, "Line quantity")
            if code in seen:
                raise ValueError(f"Medicine {code} appears more than once.")
            seen.add(code)
            result.append((code, quantity))
        return result

    def _validate_references(
        self, branch_id: int, lines: list[tuple[str, int]], conn: Any
    ) -> None:
        """Check the branch and every medicine before inserting anything."""
        branch = self.branch_repository.get_by_id(branch_id, conn=conn)
        if branch is None:
            raise ValueError(f"Unknown branch ID: {branch_id}.")

        for medicine_code, _ in lines:
            medicine = self.medicine_repository.get_by_code(medicine_code, conn=conn)
            if medicine is None:
                raise UnknownMedicineError(
                    f"Unknown medicine code: {medicine_code}."
                )

    # ------------------------------------------------------------------ #
    # Agreed public methods
    # ------------------------------------------------------------------ #
    def create_prescription(
        self,
        patient_identifier: str,
        branch_id: int,
        prescriber_code: Optional[str],
        lines: Sequence[Any],
    ) -> Prescription:
        """Create a multi-line prescription for a fictional patient.

        The prescriber code is captured at creation but is only required to
        be on the allow-list when a controlled medicine is dispensed.
        """
        patient = self._require_non_blank_text(
            patient_identifier, "Patient identifier"
        )
        branch = self._require_positive_int(branch_id, "Branch ID")
        code = self._normalise_prescriber_code(prescriber_code)
        normalised_lines = self._normalise_lines(lines)

        if self.db is not None:
            with self.db.transaction() as conn:
                self._validate_references(branch, normalised_lines, conn)
                try:
                    prescription_id = self.prescription_repository.create(
                        branch, patient, code, normalised_lines, conn=conn
                    )
                except sqlite3.IntegrityError as exc:
                    raise ValueError(
                        "Could not create prescription: the branch or a medicine "
                        "does not exist, or a line was duplicated."
                    ) from exc
        else:  # pragma: no cover - used only with lightweight test doubles
            prescription_id = self.prescription_repository.create(
                branch, patient, code, normalised_lines
            )

        created = self.get_prescription(prescription_id)
        if created is None:  # pragma: no cover - defensive check
            raise RuntimeError("The newly created prescription could not be read back.")
        return created

    def get_authorised_prescribers(self) -> list[dict[str, Any]]:
        """Return the simulated allow-list for GUI dropdowns.

        Each row has ``prescriber_code`` and ``prescriber_name``. This is a
        read-only pass-through to the repository; authorisation decisions
        still use the same repository inside the dispensing transaction.
        """
        return self.prescriber_repository.list_all()

    def get_prescription(self, prescription_id: int) -> Optional[Prescription]:
        """Return a prescription (with lines) or ``None`` when it is unknown."""
        pid = self._require_positive_int(prescription_id, "Prescription ID")
        if self.db is not None:
            with self.db.connection() as conn:
                data = self.prescription_repository.get_by_id(pid, conn=conn)
        else:  # pragma: no cover - used only with lightweight test doubles
            data = self.prescription_repository.get_by_id(pid)
        return Prescription.from_dict(data) if data is not None else None

    def cancel_prescription(self, prescription_id: int) -> Prescription:
        """Cancel a pending prescription. Dispensed/cancelled ones are final."""
        pid = self._require_positive_int(prescription_id, "Prescription ID")
        if self.db is None:  # pragma: no cover - defensive check
            raise RuntimeError("A Database instance is required to cancel.")

        with self.db.transaction() as conn:
            data = self.prescription_repository.get_by_id(pid, conn=conn)
            if data is None:
                raise ValueError(f"Prescription {pid} does not exist.")
            prescription = Prescription.from_dict(data)
            if not prescription.is_pending:
                raise InvalidPrescriptionStateError(
                    f"A {prescription.status} prescription cannot be cancelled."
                )
            updated = self.prescription_repository.update_status(
                pid, STATUS_CANCELLED, conn=conn
            )
            if updated != 1:
                raise InvalidPrescriptionStateError(
                    "Prescription changed concurrently and could not be cancelled."
                )

        cancelled = self.get_prescription(pid)
        if cancelled is None:  # pragma: no cover - defensive check
            raise RuntimeError("The cancelled prescription could not be read back.")
        return cancelled

    def dispense_prescription(self, prescription_id: int) -> Prescription:
        """Dispense a pending prescription in ONE atomic transaction.

        All checks and writes below share the same connection:
        status, medicines, controlled-prescriber allow-list, stock levels,
        conditional stock reductions and the conditional status change. If
        anything fails, ``Database.transaction()`` rolls everything back, so
        no stock is deducted and the prescription stays pending.
        """
        pid = self._require_positive_int(prescription_id, "Prescription ID")
        if self.db is None:  # pragma: no cover - defensive check
            raise RuntimeError("A Database instance is required for dispensing.")

        with self.db.transaction() as conn:
            data = self.prescription_repository.get_by_id(pid, conn=conn)
            if data is None:
                raise ValueError(f"Prescription {pid} does not exist.")

            prescription = Prescription.from_dict(data)
            if not prescription.can_dispense():
                if prescription.is_dispensed:
                    reason = "It has already been dispensed."
                elif prescription.is_cancelled:
                    reason = "It has been cancelled."
                else:
                    reason = "It has no medicine lines."
                raise InvalidPrescriptionStateError(
                    f"Prescription {pid} cannot be dispensed. {reason}"
                )

            branch_id = prescription.branch_id
            medicines: dict[str, Any] = {}
            for line in prescription.lines:
                medicine = self.medicine_repository.get_by_code(
                    line.medicine_code, conn=conn
                )
                if medicine is None:
                    raise UnknownMedicineError(
                        f"Unknown medicine code: {line.medicine_code}."
                    )
                medicines[line.medicine_code] = medicine

            if prescription.requires_authorised_prescriber(medicines):
                code = prescription.prescriber_code
                if not code or not self.prescriber_repository.is_authorised(
                    code, conn=conn
                ):
                    raise UnauthorisedPrescriberError(
                        "A controlled medicine needs an authorised prescriber code."
                    )

            # Check every line before changing anything so the error message
            # is useful. The conditional UPDATE below is the real safeguard.
            for line in prescription.lines:
                available = self.stock_repository.get_quantity(
                    line.medicine_code, branch_id, conn=conn
                )
                if available < line.quantity:
                    raise InsufficientStockError(
                        f"Insufficient stock for '{line.medicine_code}' at branch "
                        f"{branch_id}: needed {line.quantity}, available {available}."
                    )

            for line in prescription.lines:
                try:
                    self.stock_repository.decrease(
                        line.medicine_code, branch_id, line.quantity, conn=conn
                    )
                except ValueError as exc:
                    raise InsufficientStockError(str(exc)) from exc

            updated = self.prescription_repository.update_status(
                pid,
                STATUS_DISPENSED,
                dispensed_at=_utc_now(),
                conn=conn,
            )
            if updated != 1:
                raise InvalidPrescriptionStateError(
                    "The prescription was changed concurrently and could not be "
                    "dispensed. No stock was deducted."
                )

        dispensed = self.get_prescription(pid)
        if dispensed is None:  # pragma: no cover - defensive check
            raise RuntimeError("The dispensed prescription could not be read back.")
        return dispensed
