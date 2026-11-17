"""Repository for branch persistence.

SQL access only for the ``branches`` table. No business rules, no GUI code.
Every method accepts an optional ``conn`` so callers can join a transaction.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Optional

from database.connection import Database


class BranchRepository:
    """Data access for pharmacy branches."""

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
    def add(self, name: str, conn: Optional[sqlite3.Connection] = None) -> int:
        """Insert a branch and return its generated branch_id."""
        sql = "INSERT INTO branches (branch_name) VALUES (?)"

        if conn is not None:
            cursor = conn.execute(sql, (name,))
            return int(cursor.lastrowid)

        with self.db.transaction() as own_conn:
            cursor = own_conn.execute(sql, (name,))
            return int(cursor.lastrowid)

    def update(
        self, branch_id: int, name: str, conn: Optional[sqlite3.Connection] = None
    ) -> bool:
        """Update a branch name. Returns True if a row was changed."""
        sql = "UPDATE branches SET branch_name = ? WHERE branch_id = ?"
        params = (name, branch_id)

        if conn is not None:
            cursor = conn.execute(sql, params)
            return cursor.rowcount > 0

        with self.db.transaction() as own_conn:
            cursor = own_conn.execute(sql, params)
            return cursor.rowcount > 0

    def delete(
        self, branch_id: int, conn: Optional[sqlite3.Connection] = None
    ) -> bool:
        """Delete a branch. Returns True if a row was deleted."""
        sql = "DELETE FROM branches WHERE branch_id = ?"

        if conn is not None:
            cursor = conn.execute(sql, (branch_id,))
            return cursor.rowcount > 0

        with self.db.transaction() as own_conn:
            cursor = own_conn.execute(sql, (branch_id,))
            return cursor.rowcount > 0

    # ------------------------------------------------------------------ #
    # Read operations
    # ------------------------------------------------------------------ #
    def get_by_id(
        self, branch_id: int, conn: Optional[sqlite3.Connection] = None
    ) -> dict | None:
        sql = "SELECT branch_id, branch_name FROM branches WHERE branch_id = ?"

        if conn is not None:
            row = conn.execute(sql, (branch_id,)).fetchone()
            return dict(row) if row is not None else None

        with self.db.connection() as own_conn:
            row = own_conn.execute(sql, (branch_id,)).fetchone()
            return dict(row) if row is not None else None

    def get_by_name(
        self, name: str, conn: Optional[sqlite3.Connection] = None
    ) -> dict | None:
        sql = "SELECT branch_id, branch_name FROM branches WHERE branch_name = ?"

        if conn is not None:
            row = conn.execute(sql, (name,)).fetchone()
            return dict(row) if row is not None else None

        with self.db.connection() as own_conn:
            row = own_conn.execute(sql, (name,)).fetchone()
            return dict(row) if row is not None else None

    def list_all(self, conn: Optional[sqlite3.Connection] = None) -> list[dict]:
        sql = "SELECT branch_id, branch_name FROM branches ORDER BY branch_id"

        if conn is not None:
            rows = conn.execute(sql).fetchall()
            return [dict(row) for row in rows]

        with self.db.connection() as own_conn:
            rows = own_conn.execute(sql).fetchall()
            return [dict(row) for row in rows]