-- UCU Campus Pharmacy Management System
-- SQLite schema (agreed database contract)
-- Foreign keys must be enabled by the connection layer: PRAGMA foreign_keys = ON;

PRAGMA foreign_keys = ON;

-- Medicines catalogue
CREATE TABLE IF NOT EXISTS medicines (
    medicine_code   TEXT    PRIMARY KEY,
    name            TEXT    NOT NULL,
    unit_price      REAL    NOT NULL CHECK (unit_price > 0),
    reorder_level   INTEGER NOT NULL DEFAULT 0 CHECK (reorder_level >= 0),
    is_controlled   INTEGER NOT NULL DEFAULT 0 CHECK (is_controlled IN (0, 1))
);

-- Campus pharmacy branches
CREATE TABLE IF NOT EXISTS branches (
    branch_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_name TEXT    NOT NULL UNIQUE
);

-- Branch-specific stock (composite primary key)
CREATE TABLE IF NOT EXISTS stock (
    medicine_code TEXT    NOT NULL,
    branch_id     INTEGER NOT NULL,
    quantity      INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    PRIMARY KEY (medicine_code, branch_id),
    FOREIGN KEY (medicine_code)
        REFERENCES medicines (medicine_code)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (branch_id)
        REFERENCES branches (branch_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- Prescriptions
CREATE TABLE IF NOT EXISTS prescriptions (
    prescription_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id           INTEGER NOT NULL,
    patient_identifier  TEXT    NOT NULL,
    status              TEXT    NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'dispensed', 'cancelled')),
    prescriber_code     TEXT,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    dispensed_at        TEXT,
    FOREIGN KEY (branch_id)
        REFERENCES branches (branch_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- Prescription medicine lines
CREATE TABLE IF NOT EXISTS prescription_lines (
    line_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    prescription_id  INTEGER NOT NULL,
    medicine_code    TEXT    NOT NULL,
    quantity         INTEGER NOT NULL CHECK (quantity > 0),
    UNIQUE (prescription_id, medicine_code),
    FOREIGN KEY (prescription_id)
        REFERENCES prescriptions (prescription_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (medicine_code)
        REFERENCES medicines (medicine_code)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- Simulated authorised prescribers (allow-list)
CREATE TABLE IF NOT EXISTS authorised_prescribers (
    prescriber_code TEXT PRIMARY KEY,
    prescriber_name TEXT
);

-- Staff accounts: one administrator creates and manages sub-users.
-- Passwords are stored only as salted PBKDF2 hashes (never plain text).
-- NOTE: authentication was listed as out of scope in requirements 3.2;
-- this table is an additive proposal for group review (see PR).
CREATE TABLE IF NOT EXISTS staff_users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'staff')),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    created_by TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Useful indexes
CREATE INDEX IF NOT EXISTS idx_stock_branch
    ON stock (branch_id);

CREATE INDEX IF NOT EXISTS idx_prescriptions_branch
    ON prescriptions (branch_id);

CREATE INDEX IF NOT EXISTS idx_prescriptions_status
    ON prescriptions (status);

CREATE INDEX IF NOT EXISTS idx_prescription_lines_prescription
    ON prescription_lines (prescription_id);

CREATE INDEX IF NOT EXISTS idx_prescription_lines_medicine
    ON prescription_lines (medicine_code);