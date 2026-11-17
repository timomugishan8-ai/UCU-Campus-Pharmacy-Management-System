"""Fictional seed data for development and testing.

This module inserts sample branches, medicines, stock rows and one
authorised prescriber. It is safe to run more than once: every insert uses
``INSERT OR IGNORE`` so existing rows are left untouched and no duplicates
are created.

No real patient information is used. No database file is committed to Git;
the caller decides where the database lives (use a temporary file for tests).
"""

from __future__ import annotations

from typing import Any

from database.connection import Database

# Fictional branches
BRANCHES = [
    (1, "Main Campus Pharmacy"),
    (2, "East Campus Pharmacy"),
]

# Fictional medicines: (code, name, unit_price, reorder_level, is_controlled)
MEDICINES = [
    ("MED-001", "Paracetamol 500mg", 2.50, 20, 0),
    ("MED-002", "Amoxicillin 250mg", 5.00, 15, 0),
    ("MED-003", "Ibuprofen 200mg", 3.25, 10, 0),
    ("MED-004", "Morphine 10mg", 12.00, 5, 1),
    ("MED-005", "Diazepam 5mg", 8.50, 5, 1),
]

# Fictional stock: (medicine_code, branch_id, quantity)
STOCK = [
    ("MED-001", 1, 15),   # low stock: 15 <= reorder_level 20
    ("MED-001", 2, 60),
    ("MED-002", 1, 40),
    ("MED-002", 2, 8),
    ("MED-003", 1, 25),
    ("MED-004", 1, 10),
    ("MED-004", 2, 3),
    ("MED-005", 1, 6),
]

# Fictional authorised prescriber (allow-list)
PRESCRIBERS = [
    ("DR-1001", "Dr. A. Example"),
]

# A fictional UNAUTHORISED prescriber code for testing (deliberately not
# inserted): "DR-9999". Tests can use it to verify rejection.


def seed(database: Any = None) -> None:
    """Insert fictional sample data.

    Parameters
    ----------
    database:
        A ``Database`` instance or a path to a database file. When ``None``
        the default project database is used.
    """
    if database is None:
        db = Database()
    elif isinstance(database, Database):
        db = database
    else:
        db = Database(database)

    with db.transaction() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO branches (branch_id, branch_name) VALUES (?, ?)",
            BRANCHES,
        )
        conn.executemany(
            "INSERT OR IGNORE INTO medicines "
            "(medicine_code, name, unit_price, reorder_level, is_controlled) "
            "VALUES (?, ?, ?, ?, ?)",
            MEDICINES,
        )
        conn.executemany(
            "INSERT OR IGNORE INTO stock (medicine_code, branch_id, quantity) "
            "VALUES (?, ?, ?)",
            STOCK,
        )
        conn.executemany(
            "INSERT OR IGNORE INTO authorised_prescribers "
            "(prescriber_code, prescriber_name) VALUES (?, ?)",
            PRESCRIBERS,
        )
if __name__ == "__main__":
    from database.connection import Database

    db = Database()
    db.initialize_schema()
    seed(db)
    print("Seed data inserted into the default database.")
