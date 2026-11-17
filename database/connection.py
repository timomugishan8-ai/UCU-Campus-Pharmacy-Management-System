"""Database connection management for the pharmacy system.

This module provides a small, reusable helper around Python's built-in
``sqlite3`` library. It is intentionally free of business logic: it only
opens connections, enables foreign keys and helps run the schema script.

Beginner notes:
- A ``Database`` object does not keep a connection open. Each operation
  opens a connection, does its work and closes it again. This avoids
  leaking connections and makes the class safe to share.
- ``PRAGMA foreign_keys = ON`` is executed on every connection because
  SQLite disables foreign-key enforcement by default.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Union

PathLike = Union[str, Path]


class Database:
    """Manage a SQLite database file.

    Parameters
    ----------
    db_path:
        Path to the SQLite file. When ``None`` (the default) the file is
        placed at ``<project_root>/data/pharmacy.db`` so that it works no
        matter which directory ``main.py`` is launched from. Pass a different
        path (for example a temporary file) for tests.
    """

    def __init__(self, db_path: PathLike | None = None) -> None:
        if db_path is None:
            db_path = Path(__file__).resolve().parent.parent / "data" / "pharmacy.db"

        # Special in-memory database: do not try to create a parent directory.
        if str(db_path) == ":memory:":
            self.db_path: PathLike = ":memory:"
            return

        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = path

    # ------------------------------------------------------------------ #
    # Connection helpers
    # ------------------------------------------------------------------ #
    def connect(self) -> sqlite3.Connection:
        """Open and return a new connection with foreign keys enabled."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        # SQLite disables foreign keys by default; enable them for this
        # connection. This setting is per-connection, not per-database.
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Context manager yielding a connection that is always closed."""
        conn = self.connect()
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Context manager that wraps work in BEGIN IMMEDIATE / commit.

        On any exception the transaction is rolled back and the exception
        is re-raised. The connection is closed in all cases.

        Usage::

            with db.transaction() as conn:
                conn.execute("INSERT INTO ...", (...))
                # commit happens automatically when the block exits
        """
        conn = self.connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------ #
    # Schema
    # ------------------------------------------------------------------ #
    def initialize_schema(self, schema_path: PathLike | None = None) -> None:
        """Create all tables from ``database/schema.sql``.

        ``executescript`` runs the whole SQL file in one go. It manages its
        own transaction, so we commit afterwards and always close.
        """
        if schema_path is None:
            schema_path = Path(__file__).resolve().parent / "schema.sql"

        with open(schema_path, "r", encoding="utf-8") as handle:
            script = handle.read()

        conn = self.connect()
        try:
            conn.executescript(script)
            conn.commit()
        finally:
            conn.close()

    # Convenience alias kept for callers that expect a close method.
    def close(self) -> None:  # pragma: no cover - nothing to close
        return None