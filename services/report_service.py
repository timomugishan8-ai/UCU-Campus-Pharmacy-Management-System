"""Pharmacy inventory and activity reporting operations.

This service contains no SQL. It delegates to repositories and returns the
data structures already produced by the repository layer.
"""

from __future__ import annotations

from typing import Any, Optional


class ReportService:
    """Reporting operations for stock and low-stock items."""

    def __init__(self, stock_repository: Any, database: Any = None) -> None:
        self.stock_repository = stock_repository
        self.db = database or getattr(stock_repository, "db", None)

    def get_low_stock_report(
        self, branch_id: Optional[int] = None
    ) -> list[dict[str, Any]]:
        """Return low-stock rows for one branch or all branches.

        Low stock means ``quantity <= reorder_level``. The repository already
        returns the agreed dictionary keys, so this method only delegates.
        """
        return self.stock_repository.list_low_stock(branch_id=branch_id)

    def get_branch_stock_summary(self) -> list[dict[str, Any]]:
        """Return one summary row per branch.

        Branches without stock are included with zero values.
        """
        return self.stock_repository.get_branch_stock_summary()