"""Repository for prescription persistence.

SQL access only for ``prescriptions`` and ``prescription_lines``. No business
rules, no GUI code. Every method accepts an optional ``conn`` so callers can
participate in a larger transaction.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Optional

from database.connection import Database


class PrescriptionRepository:
    """Data access for prescriptions and their lines."""

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
    def create(
        self,
        branch_id: int,
        patient_identifier: str,
        prescriber_code: Optional[str],
        lines: list[tuple[str, int]],
        conn: Optional[sqlite3.Connection] = None,
    ) -> int:
        """Insert a prescription header plus its lines.

        Returns the generated prescription_id. Header and lines use the same
        connection. If any insert fails, the exception propagates so the
        caller (or the internal transaction) can roll back the whole unit.
        """
        header_sql = (
            "INSERT INTO prescriptions "
            "(branch_id, patient_identifier, prescriber_code) VALUES (?, ?, ?)"
        )
        line_sql = (
            "INSERT INTO prescription_lines "
            "(prescription_id, medicine_code, quantity) VALUES (?, ?, ?)"
        )

        if conn is not None:
            cursor = conn.execute(
                header_sql, (branch_id, patient_identifier, prescriber_code)
            )
            prescription_id = int(cursor.lastrowid)
            for medicine_code, quantity in lines:
                conn.execute(line_sql, (prescription_id, medicine_code, quantity))
            return prescription_id

        with self.db.transaction() as own_conn:
            cursor = own_conn.execute(
                header_sql, (branch_id, patient_identifier, prescriber_code)
            )
            prescription_id = int(cursor.lastrowid)
            for medicine_code, quantity in lines:
                own_conn.execute(line_sql, (prescription_id, medicine_code, quantity))
            return prescription_id

    def update_status(
        self,
        prescription_id: int,
        status: str,
        prescriber_code: Optional[str] = None,
        dispensed_at: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> int:
        """Update a prescription's status. Returns the affected row count.

        Dispensing is conditional: when ``status`` is 'dispensed' the update
        only applies to rows whose current status is 'pending'. The service
        can detect a repeated or invalid attempt via a return value of 0.
        """
        if status == "dispensed":
            sql = (
                "UPDATE prescriptions SET status = ?, "
                "prescriber_code = COALESCE(?, prescriber_code), "
                "dispensed_at = ? "
                "WHERE prescription_id = ? AND status = 'pending'"
            )
        else:
            sql = (
                "UPDATE prescriptions SET status = ?, "
                "prescriber_code = COALESCE(?, prescriber_code), "
                "dispensed_at = ? "
                "WHERE prescription_id = ?"
            )
        params = (status, prescriber_code, dispensed_at, prescription_id)

        if conn is not None:
            cursor = conn.execute(sql, params)
            return cursor.rowcount

        with self.db.transaction() as own_conn:
            cursor = own_conn.execute(sql, params)
            return cursor.rowcount

    def delete(
        self, prescription_id: int, conn: Optional[sqlite3.Connection] = None
    ) -> bool:
        """Delete a prescription (cascades to its lines). Returns True if deleted."""
        sql = "DELETE FROM prescriptions WHERE prescription_id = ?"

        if conn is not None:
            cursor = conn.execute(sql, (prescription_id,))
            return cursor.rowcount > 0

        with self.db.transaction() as own_conn:
            cursor = own_conn.execute(sql, (prescription_id,))
            return cursor.rowcount > 0

    # ------------------------------------------------------------------ #
    # Read operations
    # ------------------------------------------------------------------ #
    def get_by_id(
        self, prescription_id: int, conn: Optional[sqlite3.Connection] = None
    ) -> dict | None:
        """Return a prescription header plus its lines, or None if missing."""
        header_sql = (
            "SELECT prescription_id, branch_id, patient_identifier, status, "
            "prescriber_code, created_at, dispensed_at "
            "FROM prescriptions WHERE prescription_id = ?"
        )

        if conn is not None:
            header = conn.execute(header_sql, (prescription_id,)).fetchone()
            if header is None:
                return None
            lines = self.get_lines(prescription_id, conn=conn)
            result = dict(header)
            result["lines"] = lines
            return result

        with self.db.connection() as own_conn:
            header = own_conn.execute(header_sql, (prescription_id,)).fetchone()
            if header is None:
                return None
            lines = self.get_lines(prescription_id, conn=own_conn)
            result = dict(header)
            result["lines"] = lines
            return result

    def get_lines(
        self, prescription_id: int, conn: Optional[sqlite3.Connection] = None
    ) -> list[dict]:
        sql = (
            "SELECT line_id, prescription_id, medicine_code, quantity "
            "FROM prescription_lines WHERE prescription_id = ? "
            "ORDER BY line_id"
        )

        if conn is not None:
            rows = conn.execute(sql, (prescription_id,)).fetchall()
            return [dict(row) for row in rows]

        with self.db.connection() as own_conn:
            rows = own_conn.execute(sql, (prescription_id,)).fetchall()
            return [dict(row) for row in rows]

    def list_by_branch(
        self,
        branch_id: int,
        status: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> list[dict]:
        if status is None:
            sql = (
                "SELECT prescription_id, branch_id, patient_identifier, status, "
                "prescriber_code, created_at, dispensed_at "
                "FROM prescriptions WHERE branch_id = ? ORDER BY prescription_id"
            )
            params: tuple = (branch_id,)
        else:
            sql = (
                "SELECT prescription_id, branch_id, patient_identifier, status, "
                "prescriber_code, created_at, dispensed_at "
                "FROM prescriptions WHERE branch_id = ? AND status = ? "
                "ORDER BY prescription_id"
            )
            params = (branch_id, status)

        if conn is not None:
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

        with self.db.connection() as own_conn:
            rows = own_conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]