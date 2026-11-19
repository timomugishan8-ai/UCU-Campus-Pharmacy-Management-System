"""Medicine registration and lookup operations.

This service is the application-layer owner of the medicine catalogue
(interface contract section 4, owner: Member 2). It contains no SQL and
no tkinter: every operation goes through the injected
``MedicineRepository``, and results are domain ``Medicine`` objects.

Public methods agreed by the group (do not rename):
    register_medicine(medicine) -> Medicine
    get_all_medicines() -> list[Medicine]
    get_medicine_by_code(medicine_code) -> Medicine | None

Return format (confirmed by Member 2): all three methods return domain
``Medicine`` objects (``OrdinaryMedicine`` or ``ControlledMedicine``),
mapped from repository rows with ``Medicine.from_dict``. Expected failures
raise ``ValueError`` or one of the medicine exceptions defined in
``domain.medicine`` (all derive from ``ValueError``).
"""

from __future__ import annotations

import sqlite3
from typing import Any, Optional

from database.repositories.medicine_repository import MedicineRepository
from domain.medicine import (
    DuplicateMedicineError,
    InvalidMedicineError,
    Medicine,
)


class MedicineService:
    """Coordinate medicine registration and lookup use cases.

    Constructor
    ----------
    medicine_repository:
        Member 5's ``MedicineRepository``. It must be built from the
        shared ``Database`` instance provided by the application facade so
        every service talks to the same database manager.
    """

    def __init__(self, medicine_repository: MedicineRepository) -> None:
        self.medicine_repository = medicine_repository
        self.db = getattr(medicine_repository, "db", None)

    # ------------------------------------------------------------------ #
    # Input validation helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _require_non_blank_text(value: Any, label: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{label} must be a non-empty string.")
        return value.strip()

    # ------------------------------------------------------------------ #
    # Agreed public methods
    # ------------------------------------------------------------------ #
    def register_medicine(self, medicine: Medicine) -> Medicine:
        """Register a new catalogue entry and return the stored medicine.

        ``medicine`` must be a domain ``Medicine`` (build it with
        ``Medicine.create(...)`` when the caller only has form values).
        Duplicate codes are rejected with ``DuplicateMedicineError`` both
        pre-emptively and, as a backstop, when the database unique
        constraint fires.
        """
        if not isinstance(medicine, Medicine):
            raise TypeError(
                "register_medicine() expects a Medicine instance; "
                "use Medicine.create(...) to build one from raw fields."
            )

        code = medicine.medicine_code
        if self.medicine_repository.exists(code):
            raise DuplicateMedicineError(
                f"Medicine code '{code}' is already registered."
            )

        try:
            self.medicine_repository.add(
                code,
                medicine.name,
                medicine.unit_price,
                medicine.reorder_level,
                medicine.is_controlled,
            )
        except sqlite3.IntegrityError as exc:
            # Race backstop: the unique constraint is the authority.
            raise DuplicateMedicineError(
                f"Medicine code '{code}' is already registered."
            ) from exc

        stored = self.get_medicine_by_code(code)
        if stored is None:  # pragma: no cover - defensive check
            raise RuntimeError(
                "The newly registered medicine could not be read back."
            )
        return stored

    def get_all_medicines(self) -> list[Medicine]:
        """Return every catalogue entry as a ``Medicine`` object.

        Rows arrive ordered by medicine code (repository contract).
        """
        return [
            Medicine.from_dict(row)
            for row in self.medicine_repository.list_all()
        ]

    def get_medicine_by_code(self, medicine_code: Any) -> Optional[Medicine]:
        """Return the medicine for ``medicine_code`` or ``None`` if unknown."""
        code = self._require_non_blank_text(medicine_code, "Medicine code")
        row = self.medicine_repository.get_by_code(code)
        if row is None:
            return None
        return Medicine.from_dict(row)
