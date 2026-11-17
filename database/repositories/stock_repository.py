"""Repository for stock persistence.

SQL access only for the ``stock`` table. No business rules, no GUI code.
Every method accepts an optional ``conn`` so callers can join a transaction.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Optional

from database.connection import Database


class StockRepository:
    """Data access for branch-specific medicine stock."""

    def __init__(self, database: Any = None) -> None:
        if database is None:
            self.db = Database()
        elif isinstance(database, Database):
            self.db = database
        else:
            self.db = Database(database)

    # ------------------------------------------------------------------ #
    # Write operations
    # ------------------------------------------------------------------ #
    def set_quantity(
        self,
        medicine_code: str,
        branch_id: int,
        quantity: int,
        conn: Optional[sqlite3.Connection] = None,
    ) -> None:
        """Insert or update the stock row for (medicine, branch)."""
        sql = (
            "INSERT INTO stock (medicine_code, branch_id, quantity) VALUES (?, ?, ?) "
            "ON CONFLICT(medicine_code, branch_id) DO UPDATE SET "
            "quantity = excluded.quantity"
        )
        params = (medicine_code, branch_id, quantity)

        if conn is not None:
            conn.execute(sql, params)
            return

        with self.db.transaction() as own_conn:
            own_conn.execute(sql, params)

    def increase(
        self,
        medicine_code: str,
        branch_id: int,
        amount: int,
        conn: Optional[sqlite3.Connection] = None,
    ) -> None:
        """Add ``amount`` to existing stock (creates the row if missing)."""
        if amount <= 0:
            raise ValueError("Increase amount must be greater than zero.")

        sql = (
            "INSERT INTO stock (medicine_code, branch_id, quantity) VALUES (?, ?, ?) "
            "ON CONFLICT(medicine_code, branch_id) DO UPDATE SET "
            "quantity = quantity + excluded.quantity"
        )
        params = (medicine_code, branch_id, amount)

        if conn is not None:
            conn.execute(sql, params)
            return

        with self.db.transaction() as own_conn:
            own_conn.execute(sql, params)

    def decrease(
        self,
        medicine_code: str,
        branch_id: int,
        amount: int,
        conn: Optional[sqlite3.Connection] = None,
    ) -> None:
        """Subtract ``amount`` from stock.

        Uses a conditional update so stock can never become negative. If no
        row is updated (missing or insufficient stock), a ``ValueError`` is
        raised.
        """
        if amount <= 0:
            raise ValueError("Decrease amount must be greater than zero.")

        sql = (
            "UPDATE stock SET quantity = quantity - ? "
            "WHERE medicine_code = ? AND branch_id = ? AND quantity >= ?"
        )
        params = (amount, medicine_code, branch_id, amount)

        if conn is not None:
            cursor = conn.execute(sql, params)
            if cursor.rowcount == 0:
                raise ValueError(
                    "Insufficient or missing stock for medicine "
                    f"'{medicine_code}' at branch {branch_id}."
                )
            return

        with self.db.transaction() as own_conn:
            cursor = own_conn.execute(sql, params)
            if cursor.rowcount == 0:
                raise ValueError(
                    "Insufficient or missing stock for medicine "
                    f"'{medicine_code}' at branch {branch_id}."
                )

    def delete(
        self,
        medicine_code: str,
        branch_id: int,
        conn: Optional[sqlite3.Connection] = None,
    ) -> bool:
        """Delete a stock row. Returns True if a row was deleted."""
        sql = "DELETE FROM stock WHERE medicine_code = ? AND branch_id = ?"

        if conn is not None:
            cursor = conn.execute(sql, (medicine_code, branch_id))
            return cursor.rowcount > 0

        with self.db.transaction() as own_conn:
            cursor = own_conn.execute(sql, (medicine_code, branch_id))
            return cursor.rowcount > 0

    # ------------------------------------------------------------------ #
    # Read operations
    # ------------------------------------------------------------------ #
    def get_quantity(
        self,
        medicine_code: str,
        branch_id: int,
        conn: Optional[sqlite3.Connection] = None,
    ) -> int:
        """Return current quantity, or 0 if no stock row exists."""
        sql = "SELECT quantity FROM stock WHERE medicine_code = ? AND branch_id = ?"

        if conn is not None:
            row = conn.execute(sql, (medicine_code, branch_id)).fetchone()
            return int(row["quantity"]) if row is not None else 0

        with self.db.connection() as own_conn:
            row = own_conn.execute(sql, (medicine_code, branch_id)).fetchone()
            return int(row["quantity"]) if row is not None else 0

    def list_for_branch(
        self, branch_id: int, conn: Optional[sqlite3.Connection] = None
    ) -> list[dict]:
        sql = (
            "SELECT s.medicine_code, m.name AS medicine_name, s.branch_id, "
            "s.quantity, m.reorder_level, m.is_controlled "
            "FROM stock AS s JOIN medicines AS m "
            "ON m.medicine_code = s.medicine_code "
            "WHERE s.branch_id = ? ORDER BY s.medicine_code"
        )

        if conn is not None:
            rows = conn.execute(sql, (branch_id,)).fetchall()
            return [dict(row) for row in rows]

        with self.db.connection() as own_conn:
            rows = own_conn.execute(sql, (branch_id,)).fetchall()
            return [dict(row) for row in rows]

    def list_low_stock(
        self,
        branch_id: Optional[int] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> list[dict]:
        """Return stock rows where quantity <= reorder_level.

        If branch_id is given, restrict to that branch; otherwise return
        low-stock rows across all branches.
        """
        sql = (
            "SELECT s.medicine_code, m.name AS medicine_name, s.branch_id, "
            "b.branch_name, s.quantity, m.reorder_level, m.is_controlled "
            "FROM stock AS s "
            "JOIN medicines AS m ON m.medicine_code = s.medicine_code "
            "JOIN branches AS b ON b.branch_id = s.branch_id "
            "WHERE s.quantity <= m.reorder_level "
            "AND (? IS NULL OR s.branch_id = ?) "
            "ORDER BY s.branch_id, s.medicine_code"
        )
        params = (branch_id, branch_id)

        if conn is not None:
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

        with self.db.connection() as own_conn:
            rows = own_conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]