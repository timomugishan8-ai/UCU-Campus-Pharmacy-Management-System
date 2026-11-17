"""Repository for medicine persistence.

This module contains only SQL access for the ``medicines`` table. It has no
business rules and no GUI code. Every method accepts an optional ``conn``
argument so callers can participate in a larger transaction.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Optional

from database.connection import Database


def _as_controlled_flag(value: bool | int) -> int:
    """Convert a boolean to 0/1 while leaving other ints untouched for CHECK validation."""
    if isinstance(value, bool):
        return 1 if value else 0
    return int(value)


class MedicineRepository:
    """Data access for medicines."""

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
    def add(
        self,
        code: str,
        name: str,
        unit_price: float,
        reorder_level: int,
        is_controlled: bool | int,
        conn: Optional[sqlite3.Connection] = None,
    ) -> None:
        """Insert a new medicine.

        Raises ``sqlite3.IntegrityError`` (or ``sqlite3.Error``) on failure.
        When ``conn`` is supplied the caller owns the transaction.
        """
        controlled = _as_controlled_flag(is_controlled)
        sql = (
            "INSERT INTO medicines "
            "(medicine_code, name, unit_price, reorder_level, is_controlled) "
            "VALUES (?, ?, ?, ?, ?)"
        )
        params = (code, name, unit_price, reorder_level, controlled)

        if conn is not None:
            conn.execute(sql, params)
            return

        with self.db.transaction() as own_conn:
            own_conn.execute(sql, params)

    def update(
        self,
        code: str,
        name: str,
        unit_price: float,
        reorder_level: int,
        is_controlled: bool | int,
        conn: Optional[sqlite3.Connection] = None,
    ) -> bool:
        """Update an existing medicine. Returns True if a row was changed."""
        controlled = _as_controlled_flag(is_controlled)
        sql = (
            "UPDATE medicines "
            "SET name = ?, unit_price = ?, reorder_level = ?, is_controlled = ? "
            "WHERE medicine_code = ?"
        )
        params = (name, unit_price, reorder_level, controlled, code)

        if conn is not None:
            cursor = conn.execute(sql, params)
            return cursor.rowcount > 0

        with self.db.transaction() as own_conn:
            cursor = own_conn.execute(sql, params)
            return cursor.rowcount > 0

    def delete(self, code: str, conn: Optional[sqlite3.Connection] = None) -> bool:
        """Delete a medicine. Returns True if a row was deleted."""
        sql = "DELETE FROM medicines WHERE medicine_code = ?"

        if conn is not None:
            cursor = conn.execute(sql, (code,))
            return cursor.rowcount > 0

        with self.db.transaction() as own_conn:
            cursor = own_conn.execute(sql, (code,))
            return cursor.rowcount > 0

    # ------------------------------------------------------------------ #
    # Read operations
    # ------------------------------------------------------------------ #
    def get_by_code(
        self, code: str, conn: Optional[sqlite3.Connection] = None
    ) -> dict | None:
        sql = (
            "SELECT medicine_code, name, unit_price, reorder_level, is_controlled "
            "FROM medicines WHERE medicine_code = ?"
        )

        if conn is not None:
            row = conn.execute(sql, (code,)).fetchone()
            return dict(row) if row is not None else None

        with self.db.connection() as own_conn:
            row = own_conn.execute(sql, (code,)).fetchone()
            return dict(row) if row is not None else None

    def list_all(self, conn: Optional[sqlite3.Connection] = None) -> list[dict]:
        sql = (
            "SELECT medicine_code, name, unit_price, reorder_level, is_controlled "
            "FROM medicines ORDER BY medicine_code"
        )

        if conn is not None:
            rows = conn.execute(sql).fetchall()
            return [dict(row) for row in rows]

        with self.db.connection() as own_conn:
            rows = own_conn.execute(sql).fetchall()
            return [dict(row) for row in rows]

    def exists(self, code: str, conn: Optional[sqlite3.Connection] = None) -> bool:
        sql = "SELECT 1 FROM medicines WHERE medicine_code = ?"

        if conn is not None:
            row = conn.execute(sql, (code,)).fetchone()
            return row is not None

        with self.db.connection() as own_conn:
            row = own_conn.execute(sql, (code,)).fetchone()
            return row is not None