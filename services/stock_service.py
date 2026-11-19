"""StockService implementation for Cindy's service responsibilities."""

from __future__ import annotations

from typing import Any, Optional

from database.repositories.stock_repository import StockRepository


class StockService:
    """Coordinate stock receipt and stock availability use cases."""

    def __init__(
        self,
        stock_repository: StockRepository,
        medicine_repository: Any = None,
        branch_repository: Any = None,
        database: Any = None,
    ) -> None:
        self.stock_repository = stock_repository
        self.medicine_repository = medicine_repository
        self.branch_repository = branch_repository
        self.db = database or getattr(stock_repository, "db", None)

    @staticmethod
    def _require_positive_int(value: Any, label: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{label} must be a positive integer.")
        return value

    def receive_stock(
        self, medicine_code: str, branch_id: int, quantity: Any
    ) -> None:
        """Receive a positive quantity of stock for a medicine at a branch."""
        quantity = self._require_positive_int(quantity, "Quantity")

        if self.medicine_repository is not None:
            medicine = self.medicine_repository.get_by_code(medicine_code)
            if medicine is None:
                raise ValueError(f"Unknown medicine code: {medicine_code}.")

        if self.branch_repository is not None:
            branch = self.branch_repository.get_by_id(branch_id)
            if branch is None:
                raise ValueError(f"Unknown branch ID: {branch_id}.")

        self.stock_repository.increase(medicine_code, branch_id, quantity)

    def get_branch_stock(self, branch_id: int) -> list[dict[str, Any]]:
        """Return stock rows for one branch."""
        if self.branch_repository is not None:
            branch = self.branch_repository.get_by_id(branch_id)
            if branch is None:
                raise ValueError(f"Unknown branch ID: {branch_id}.")

        return self.stock_repository.list_for_branch(branch_id)

    def get_low_stock(
        self, branch_id: Optional[int] = None
    ) -> list[dict[str, Any]]:
        """Return low-stock rows for one branch or all branches."""
        if branch_id is not None and self.branch_repository is not None:
            branch = self.branch_repository.get_by_id(branch_id)
            if branch is None:
                raise ValueError(f"Unknown branch ID: {branch_id}.")

        return self.stock_repository.list_low_stock(branch_id=branch_id)