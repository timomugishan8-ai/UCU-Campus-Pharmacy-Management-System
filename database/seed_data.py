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
    # Original demonstration set.
    ("MED-001", "Paracetamol 500mg", 2.50, 20, 0),
    ("MED-002", "Amoxicillin 250mg", 5.00, 15, 0),
    ("MED-003", "Ibuprofen 200mg", 3.25, 10, 0),
    ("MED-004", "Morphine 10mg", 12.00, 5, 1),
    ("MED-005", "Diazepam 5mg", 8.50, 5, 1),
    # Malaria - the leading outpatient diagnosis in Uganda.
    ("MED-006", "Coartem 20/120mg", 6.50, 25, 0),
    ("MED-007", "Fansidar tablets", 4.00, 15, 0),
    ("MED-008", "Quinine 300mg tablets", 5.50, 10, 0),
    # Common antibiotics.
    ("MED-009", "Metronidazole 400mg", 2.75, 20, 0),
    ("MED-010", "Cotrimoxazole 480mg", 3.50, 15, 0),
    ("MED-011", "Ciprofloxacin 500mg", 6.00, 12, 0),
    # Pain and inflammation.
    ("MED-012", "Diclofenac 50mg", 3.00, 15, 0),
    ("MED-013", "Tramadol 50mg", 7.50, 5, 1),
    # Gastro-intestinal.
    ("MED-014", "Omeprazole 20mg", 4.50, 12, 0),
    # Child health.
    ("MED-015", "ORS sachet", 1.25, 30, 0),
    ("MED-016", "Zinc 20mg dispersible", 1.75, 25, 0),
    ("MED-017", "Paracetamol syrup 120mg/5ml", 2.25, 20, 0),
    # Deworming and ante-natal care.
    ("MED-018", "Albendazole 400mg", 2.50, 15, 0),
    ("MED-019", "Ferrous sulphate + Folic acid", 2.00, 25, 0),
    # Chronic care.
    ("MED-020", "Amlodipine 5mg", 5.00, 12, 0),
    ("MED-021", "Metformin 500mg", 5.50, 12, 0),
    ("MED-022", "Prednisolone 5mg", 3.25, 10, 0),
    # Respiratory.
    ("MED-023", "Salbutamol inhaler 100mcg", 9.00, 8, 0),
    # TB and HIV programmes.
    ("MED-024", "Rifampicin/Isoniazid 150/75mg", 8.00, 10, 0),
    ("MED-025", "Tenofovir/Lamivudine/Dolutegravir", 14.00, 6, 0),
    # Codeine preparation - controlled like morphine and diazepam.
    ("MED-026", "Codeine cough syrup 15mg/5ml", 7.00, 5, 1),
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
    # Main Campus Pharmacy (branch 1): the rest of the catalogue.
    ("MED-006", 1, 45),
    ("MED-007", 1, 12),   # low stock: 12 <= reorder_level 15
    ("MED-008", 1, 14),
    ("MED-009", 1, 30),
    ("MED-010", 1, 22),
    ("MED-011", 1, 16),
    ("MED-012", 1, 24),
    ("MED-013", 1, 9),
    ("MED-014", 1, 18),
    ("MED-015", 1, 60),
    ("MED-016", 1, 38),
    ("MED-017", 1, 28),
    ("MED-018", 1, 21),
    ("MED-019", 1, 40),
    ("MED-020", 1, 17),
    ("MED-021", 1, 15),
    ("MED-022", 1, 14),
    ("MED-023", 1, 7),    # low stock: 7 <= reorder_level 8
    ("MED-024", 1, 13),
    ("MED-025", 1, 9),
    ("MED-026", 1, 4),    # low stock: 4 <= reorder_level 5
    # East Campus Pharmacy (branch 2): the faster-moving lines only.
    ("MED-006", 2, 40),
    ("MED-009", 2, 26),
    ("MED-015", 2, 45),
    ("MED-019", 2, 30),
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
