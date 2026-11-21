"""Repository for staff-account persistence.

SQL access only for the ``staff_users`` table. No business rules, no GUI
code, and this layer never sees a plain-text password - only the
pre-hashed ``password_hash`` produced by the auth service. Every method
accepts an optional ``conn`` so callers can join a transaction.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Optional

from database.connection import Database


class UserRepository:
    """Data access for staff accounts."""

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
        username: str,
        password_hash: str,
        role: str,
        created_by: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> int:
        """Insert an account and return its generated user_id.

        Raises ``sqlite3.IntegrityError`` on a duplicate username; the
        service converts it to the domain's ``DuplicateUserError``.
        """
        sql = (
            "INSERT INTO staff_users (username, password_hash, role, created_by) "
            "VALUES (?, ?, ?, ?)"
        )
        params = (username, password_hash, role, created_by)

        if conn is not None:
            cursor = conn.execute(sql, params)
            return int(cursor.lastrowid)

        with self.db.transaction() as own_conn:
            cursor = own_conn.execute(sql, params)
            return int(cursor.lastrowid)

    def set_active(
        self, user_id: int, active: bool, conn: Optional[sqlite3.Connection] = None
    ) -> bool:
        """Enable or disable an account. Returns True if a row was changed."""
        sql = "UPDATE staff_users SET active = ? WHERE user_id = ?"
        params = (1 if active else 0, user_id)

        if conn is not None:
            cursor = conn.execute(sql, params)
            return cursor.rowcount > 0

        with self.db.transaction() as own_conn:
            cursor = own_conn.execute(sql, params)
            return cursor.rowcount > 0

    # ------------------------------------------------------------------ #
    # Read operations
    # ------------------------------------------------------------------ #
    def get_by_username(
        self, username: str, conn: Optional[sqlite3.Connection] = None
    ) -> dict | None:
        """Fetch one account *including* its stored hash (login only).

        ``list_all()`` deliberately omits ``password_hash`` so account
        listings never carry secrets around.
        """
        sql = (
            "SELECT user_id, username, password_hash, role, active, created_by "
            "FROM staff_users WHERE username = ?"
        )

        if conn is not None:
            row = conn.execute(sql, (username,)).fetchone()
            return dict(row) if row is not None else None

        with self.db.connection() as own_conn:
            row = own_conn.execute(sql, (username,)).fetchone()
            return dict(row) if row is not None else None

    def list_all(self, conn: Optional[sqlite3.Connection] = None) -> list[dict]:
        sql = (
            "SELECT user_id, username, role, active, created_by "
            "FROM staff_users ORDER BY username"
        )

        if conn is not None:
            rows = conn.execute(sql).fetchall()
            return [dict(row) for row in rows]

        with self.db.connection() as own_conn:
            rows = own_conn.execute(sql).fetchall()
            return [dict(row) for row in rows]

    def count(self, conn: Optional[sqlite3.Connection] = None) -> int:
        """Total number of accounts, active or not."""
        sql = "SELECT COUNT(*) AS n FROM staff_users"

        if conn is not None:
            row = conn.execute(sql).fetchone()
            return int(row["n"])

        with self.db.connection() as own_conn:
            row = own_conn.execute(sql).fetchone()
            return int(row["n"])

    def count_active_admins(self, conn: Optional[sqlite3.Connection] = None) -> int:
        """Active administrator accounts (guards the last-admin rule)."""
        sql = (
            "SELECT COUNT(*) AS n FROM staff_users "
            "WHERE role = 'admin' AND active = 1"
        )

        if conn is not None:
            row = conn.execute(sql).fetchone()
            return int(row["n"])

        with self.db.connection() as own_conn:
            row = own_conn.execute(sql).fetchone()
            return int(row["n"])
