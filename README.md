# UCU Campus Pharmacy Management System

**Multi-Branch Campus Pharmacy Inventory, Dispensing and Reporting System**

- **Course:** CSC2105 - Object-Oriented Programming Using Python
- **Institution:** Uganda Christian University
- **Language:** Python 3.13
- **GUI:** Tkinter (desktop)
- **Database:** SQLite

> Status: This project is under active development. The database foundation, repositories, prescription domain/service and some GUI screens are implemented. The application entry point, several domain classes, services and GUI screens are still incomplete.

---

## 1. Project overview

This system is a desktop application for managing pharmacy operations across multiple campus branches. It tracks medicines, branch-specific stock levels, prescriptions, dispensing transactions and low-stock reports. The goal is to support accurate inventory control and safe dispensing of medicines, including controlled medicines that require an authorised simulated prescriber code, while keeping each branch's stock consistent.

The project follows a layered architecture:

- **Domain classes** hold core business entities and rules.
- **Services** coordinate business logic and orchestrate operations.
- **Repositories** handle all SQL and persistence against SQLite.
- **GUI (Tkinter)** communicates only with application services, never directly with SQL.

## 2. Project objectives and main features

### Objectives

- Manage medicines, branches and branch-specific stock.
- Create and dispense prescriptions safely.
- Prevent partial stock deduction when a prescription cannot be fully supplied.
- Enforce authorised simulated prescriber codes for controlled medicines.
- Identify low-stock items per branch.
- Persist data in SQLite between application sessions.

### Main features

Implemented or partially implemented:
- Database schema, connection management and seed data.
- Repositories for medicines, branches, stock, prescriptions and authorised prescribers.
- Prescription creation and atomic dispensing.
- Low-stock report screen (on `origin/member-4-gui`).

Planned or incomplete:
- Medicine, branch and stock domain classes.
- MedicineService, StockService and ReportService.
- ApplicationServices facade and application entry point.
- Main window and several feature screens.

## 3. Technologies used

- Python 3.13
- Tkinter (standard library, desktop GUI)
- SQLite (standard library, file-based database)
- unittest (Python standard library, testing)
- Git and GitHub (version control and collaboration)

No third-party dependencies are required at this stage; `requirements.txt` is currently empty.

## 4. Group members and responsibilities

1. **Timothy** - Architecture and integration.
2. **Mulisa** - Medicine, branch and stock domain classes, MedicineService, medicine registration and stock receiving.
3. **Conrad** - Prescription and dispensing, including PrescriptionService.
4. **Matilda** - Tkinter GUI coordination.
5. **Cindy** - Database, repositories, StockService, ReportService, database integration, testing and documentation.

## 5. Project folder structure

```text
UCU-Campus-Pharmacy-Management-System/
|-- app/            # Application entry points and shared screen services
|   |-- base_screen.py   # currently empty placeholder
|   +-- services.py      # ApplicationServices facade, currently empty placeholder
|-- data/            # SQLite database file(s), generated at runtime, not committed
|-- database/        # Connection, schema, seed data and repositories
|   |-- connection.py
|   |-- schema.sql
|   |-- seed_data.py
|   +-- repositories/
|       |-- branch_repository.py
|       |-- medicine_repository.py
|       |-- prescriber_repository.py
|       |-- prescription_repository.py
|       +-- stock_repository.py
|-- domain/          # Core pharmacy domain models
|   |-- branch.py         # currently empty placeholder
|   |-- medicine.py       # currently empty placeholder
|   |-- prescription.py   # implemented
|   +-- stock.py          # currently empty placeholder
|-- gui/             # Tkinter screens
|   |-- create_prescription.py   # implemented
|   |-- dispense.py              # implemented
|   |-- low_stock.py             # implemented on origin/member-4-gui
|   |-- main_window.py           # currently empty placeholder
|   |-- receive_stock.py         # currently empty placeholder
|   +-- register_medicine.py     # currently empty placeholder
|-- services/        # Business services
|   |-- medicine_service.py      # currently empty placeholder
|   |-- prescription_service.py  # implemented
|   |-- report_service.py        # currently empty placeholder
|   +-- stock_service.py         # currently empty placeholder
|-- tests/           # Unit and integration tests
|   |-- test_dispensing.py
|   |-- test_medicine.py
|   |-- test_member5_database.py
|   |-- test_prescription.py
|   +-- test_stock.py
|-- docs/            # Design, requirements and database design
|   |-- database_design.md       # implemented
|   |-- design.md                # empty on main; full version on origin/member-1-architecture
|   |-- requirements.md          # empty on main; full version on origin/member-1-architecture
|   +-- test_report.md           # empty
|-- main.py          # Application entry point, currently empty placeholder
|-- README.md
|-- requirements.txt
+-- task_log.md
```

## 6. System architecture

The system uses four layers:

1. **GUI (`gui/`)** - Tkinter screens, input collection, navigation, messages and display refresh. No SQL.
2. **Application services (`app/services.py`)** - intended composition point for repositories and services. Not yet implemented.
3. **Services and domain (`services/`, `domain/`)** - services coordinate use cases; domain objects enforce object-level rules. No tkinter imports.
4. **Repositories and database (`database/`)** - parameterised SQLite access, row mapping, connection management and transaction boundaries.

Communication flow:

```text
User -> Tkinter screen -> ApplicationServices -> service -> domain/repository -> SQLite
```

Repository methods that accept `conn` must use the supplied connection and must not start a separate transaction. This allows a service to keep related reads and writes in one transaction.

## 7. Database tables and their purpose

The SQLite schema is defined in `database/schema.sql`.

- `medicines` - medicine catalogue: code, name, unit price, reorder level, controlled flag.
- `branches` - pharmacy branches with unique IDs and names.
- `stock` - branch-specific medicine quantities using a composite primary key `(medicine_code, branch_id)`.
- `prescriptions` - prescription header: branch, fictional patient identifier, status, prescriber code, timestamps.
- `prescription_lines` - medicine lines for a prescription.
- `authorised_prescribers` - simulated allow-list for controlled-medicine prescriber codes.

Important rules:
- Stock quantity must never be negative.
- Prescription status is restricted to `pending`, `dispensed` and `cancelled`.
- Prescription line quantities must be positive.
- Duplicate medicine lines in one prescription are prevented.
- Low stock means quantity is less than or equal to the medicine's reorder level, per branch.

## 8. Installation and environment setup

Prerequisites:
- Python 3.13 installed with Tkinter and SQLite support.
- Git installed.
- Visual Studio Code (recommended) with the Python extension.

Create and activate a virtual environment on Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If script execution is restricted:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Install dependencies (currently none beyond the standard library):

```powershell
pip install -r requirements.txt
```

Deactivate when finished:

```powershell
deactivate
```

## 9. Database initialization and sample data

The schema is implemented in `database/schema.sql` and is created automatically when a database is initialised.

Seed fictional development data with:

```powershell
python -m database.seed_data
```

This creates fictional branches, medicines, stock rows and one authorised prescriber. It does not use real patient information.

Do not commit generated `.db`, `.sqlite` or `.sqlite3` files.

## 10. How to run the application

The application is not yet fully runnable. `main.py`, `app/services.py`, `gui/main_window.py` and several feature screens are still placeholders.

Prescription screens exist in `gui/create_prescription.py` and `gui/dispense.py`, but they require the shared application services and main window integration that are not yet implemented.

Do not run `python main.py` expecting a complete application.

## 11. How to run the available tests

Run all tests:

```powershell
python -m unittest discover -s tests -v
```

Implemented tests:
- Cindy's database/repository tests: `tests/test_member5_database.py`
- Conrad's prescription and dispensing tests: `tests/test_prescription.py` and `tests/test_dispensing.py`

Other test files are currently empty placeholders.

Tests use temporary databases and do not modify the live demonstration database.

## 12. Current implementation status

Completed:
- Database schema, connection management and seed data.
- Repositories for medicines, branches, stock, prescriptions and authorised prescribers.
- Prescription domain and PrescriptionService.
- Create-prescription and dispense GUI screens.
- Low-stock GUI screen on `origin/member-4-gui`.
- Database design documentation.

Incomplete:
- Medicine, branch and stock domain classes.
- MedicineService, StockService and ReportService.
- ApplicationServices facade.
- Main window and remaining GUI screens.
- Medicine registration and stock receiving screens.
- Application entry point.

## 13. GitHub repository and contribution workflow

- Work on a dedicated feature branch per member.
- Pull the latest `main` before starting work.
- Make small, focused commits with clear messages.
- Do not commit generated files (`.venv/`, `__pycache__/`, `*.db`, `.env`).
- Open a pull request to `main` and request review before merging.
- Resolve conflicts locally and re-run tests before pushing.
- Never force-push to `main`.

Historical branch names such as `member-5-database-tests` remain part of the project history.

## 14. Academic integrity and fictional data note

This project is submitted for academic assessment (CSC2105). All members are responsible for understanding and being able to explain every part of the submitted code. AI tools may be used to assist with drafting, refactoring and documentation, but the final submission must reflect the group's own understanding. Any AI-assisted content must be reviewed, tested and owned by the group. Plagiarism or uncredited copying is not permitted.

The system uses fictional patient identifiers and simulated prescriber codes only. No real patient or prescriber information is stored.

---

Last updated: 19 November 2026.