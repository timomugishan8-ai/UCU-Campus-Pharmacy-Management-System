"""Pharmacy inventory and activity reporting operations.

This service contains no SQL. It delegates to repositories and returns the
data structures already produced by the repository layer.
"""

from __future__ import annotations

from typing import Any, Optional

from database.repositories.branch_repository import BranchRepository


class ReportService:
    """Reporting operations for stock and low-stock items."""

    def __init__(
        self,
        stock_repository: Any,
        database: Any = None,
        branch_repository: Any = None,
    ) -> None:
        self.stock_repository = stock_repository
        self.db = database or getattr(stock_repository, "db", None)
        # Keep branch validation inside the service layer. If the caller does
        # not inject a branch repository, build one from the shared database
        # manager so production wiring cannot silently skip the check.
        self.branch_repository = (
            branch_repository
            if branch_repository is not None
            else (BranchRepository(self.db) if self.db is not None else None)
        )

    def get_low_stock_report(
        self, branch_id: Optional[int] = None
    ) -> list[dict[str, Any]]:
        """Return low-stock rows for one branch or all branches.

        Low stock means ``quantity <= reorder_level``. The repository already
        returns the agreed dictionary keys, so this method only delegates.
        A supplied branch ID is validated explicitly before querying.
        """
        if branch_id is not None:
            if self.branch_repository is None:
                raise RuntimeError("A BranchRepository is required to validate branch IDs.")
            branch = self.branch_repository.get_by_id(branch_id)
            if branch is None:
                raise ValueError(f"Unknown branch ID: {branch_id}.")

        return self.stock_repository.list_low_stock(branch_id=branch_id)

    def get_branch_stock_summary(self) -> list[dict[str, Any]]:
        """Return one summary row per branch.

        Branches without stock are included with zero values.
        """
        return self.stock_repository.get_branch_stock_summary()