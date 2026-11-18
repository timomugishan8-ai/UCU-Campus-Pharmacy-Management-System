"""Repository for the simulated authorised-prescriber allow-list.

This file contains SQL only. There are no business rules and no GUI code.
Every read accepts an optional ``conn`` so a prescription service can check
authorisation inside the same transaction as the stock deduction.

Note for the team: the shared agreement did not name a repository for
``authorised_prescribers``. This new file was added by the prescription
owner so the controlled-medicine rule can be enforced through the repository
layer rather than by putting SQL in a service. Member 5 owns the database
folder and should review/confirm this addition during integration.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Optional

from database.connection import Database


class PrescriberRepository:
    """Data access for the simulated prescriber allow-list."""

    def __init__(self, database: Any = None) -> None:
        if database is None:
            self.db = Database()
        elif isinstance(database, Database):
            self.db = database
        else:
            self.db = Database(database)

    def is_authorised(
        self, prescriber_code: str, conn: Optional[sqlite3.Connection] = None
    ) -> bool:
        """Return True when ``prescriber_code`` is on the allow-list.

        A blank or non-string code is never authorised. The lookup is
        parameterised, matching the repository convention in this project.
        """
        if not isinstance(prescriber_code, str) or not prescriber_code.strip():
            return False

        sql = (
            "SELECT 1 FROM authorised_prescribers "
            "WHERE prescriber_code = ? LIMIT 1"
        )
        params = (prescriber_code.strip(),)

        if conn is not None:
            return conn.execute(sql, params).fetchone() is not None

        with self.db.connection() as own_conn:
            return own_conn.execute(sql, params).fetchone() is not None
