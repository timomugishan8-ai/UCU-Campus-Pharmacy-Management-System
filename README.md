# UCU Campus Pharmacy Management System

**Multi-Branch Campus Pharmacy Inventory, Dispensing and Reporting System**

- **Course:** CSC2105 - Object-Oriented Programming Using Python
- **Institution:** Uganda Christian University
- **Language:** Python 3.13
- **GUI:** Tkinter (desktop)
- **Database:** SQLite

> Status: Core application features are implemented. The Tkinter application can be launched with `python main.py`. Final integration testing and manual GUI walkthrough are still recommended.

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

Implemented:
- Database schema, connection management and seed data.
- Repositories for medicines, branches, stock, prescriptions and authorised prescribers.
- Medicine, branch, stock and prescription domain classes.
- MedicineService, StockService, ReportService and PrescriptionService.
- ApplicationServices facade and application entry point.
- Tkinter screens for dashboard, medicine registration, stock receiving, prescription creation, dispensing and low-stock reporting.
- Low-stock reporting with branch filtering.
- Atomic prescription dispensing with rollback.

## 3. Technologies used

- Python 3.13
- Tkinter (standard library, desktop GUI)
- SQLite (standard library, file-based database)
- unittest (Python standard library, testing)
- Git and GitHub (version control and collaboration)

No third-party dependencies are required; `requirements.txt` is currently empty.

## 4. Group members and responsibilities

1. **Timothy** - Architecture and integration.
2. **Mulisa** - Medicine, branch and stock domain classes, MedicineService, medicine registration and stock receiving.
3. **Conrad** - Prescription and dispensing, including PrescriptionService.
4. **Matilda** - Tkinter GUI coordination.
5. **Cindy** - Database, repositories, StockService, ReportService, database integration, testing and documentation.

### 5.1 Member 3 contribution - Prescription and dispensing (Conrad)

This section describes the prescription and dispensing part; Cindy owns the database and reporting parts of this README.

**Files owned by Conrad**

- domain/prescription.py - Prescription, PrescriptionLine, status constants, valid transitions and prescription exceptions.
- services/prescription_service.py - the agreed public service methods and the dispensing transaction.
- gui/create_prescription.py - CreatePrescriptionScreen(parent, services).
- gui/dispense.py - DispenseScreen(parent, services).
- 	ests/test_prescription.py and 	ests/test_dispensing.py - prescription and dispensing tests.
- database/repositories/prescriber_repository.py - allow-list lookup (reviewed by Cindy).

**What is implemented**

- Multi-line prescriptions tied to one branch and a fictional patient identifier.
- pending, dispensed and cancelled statuses; only pending prescriptions can dispense or cancel.
- Controlled medicines require an authorised simulated prescriber code; ordinary medicines do not.
- All-or-nothing dispensing: one SQLite transaction covers status checks, controlled-medicine authorisation, stock checks, conditional stock reductions and the conditional status update. If any step fails, everything rolls back and no stock is deducted.

**Agreed public methods**

`python
PrescriptionService(prescription_repository, medicine_repository, stock_repository)

create_prescription(patient_identifier, branch_id, prescriber_code, lines) -> Prescription
dispense_prescription(prescription_id) -> Prescription
cancel_prescription(prescription_id) -> Prescription
get_prescription(prescription_id) -> Prescription | None
`

**Tests**

`powershell
py -m unittest tests.test_prescription tests.test_dispensing -v
`

Tests use temporary databases, never the live data/pharmacy.db.

---

## 5. Project folder structure

```text
UCU-Campus-Pharmacy-Management-System/
|-- app/            # Application entry points and shared screen services
|   |-- base_screen.py
|   +-- services.py      # ApplicationServices facade
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
|   |-- branch.py
|   |-- medicine.py
|   |-- prescription.py
|   +-- stock.py
|-- gui/             # Tkinter screens
|   |-- create_prescription.py
|   |-- dashboard.py
|   |-- dispense.py
|   |-- low_stock.py
|   |-- main_window.py
|   |-- receive_stock.py
|   +-- register_medicine.py
|-- services/        # Business services
|   |-- medicine_service.py
|   |-- prescription_service.py
|   |-- report_service.py
|   +-- stock_service.py
|-- tests/           # Unit and integration tests
|   |-- test_dispensing.py
|   |-- test_medicine.py
|   |-- test_member2_gui.py
|   |-- test_member5_database.py
|   |-- test_prescription.py
|   |-- test_stock.py
|   |-- test_cindy_stock_report.py
|   +-- test_cindy_stock_service.py
|-- docs/            # Design, requirements, database design and diagrams
|   |-- database_design.md
|   |-- design.md
|   |-- interface_contract.md
|   |-- requirements.md
|   |-- test_report.md
|   +-- diagrams/
|-- main.py          # Application entry point
|-- README.md
|-- requirements.txt
+-- task_log.md
```

## 6. System architecture

The system uses four layers:

1. **GUI (`gui/`)** - Tkinter screens, input collection, navigation, messages and display refresh. No SQL.
2. **Application services (`app/services.py`)** - composition point for repositories and services.
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

The schema is implemented in `database/schema.sql` and is created automatically when the application starts.

Seed fictional development data with:

```powershell
python -m database.seed_data
```

This creates fictional branches, medicines, stock rows and one authorised prescriber. It does not use real patient information.

Do not commit generated `.db`, `.sqlite` or `.sqlite3` files.

## 10. How to run the application

Run the application with:

```powershell
python main.py
```

The application initialises the database, seeds fictional data, creates the shared services and opens the Tkinter main window.

## 11. How to run the available tests

Run all tests:

```powershell
python -m unittest discover -s tests -v
```

Implemented test suites include:
- Medicine and stock domain tests.
- Prescription and dispensing tests.
- Database and repository integration tests.
- StockService and ReportService tests.
- GUI smoke tests.

Tests use temporary databases and do not modify the live demonstration database.

## 12. Current implementation status

Completed:
- Database schema, connection management and seed data.
- Repositories for medicines, branches, stock, prescriptions and authorised prescribers.
- Medicine, branch, stock and prescription domain classes.
- MedicineService, StockService, ReportService and PrescriptionService.
- ApplicationServices facade and application entry point.
- Tkinter screens for dashboard, medicine registration, stock receiving, prescription creation, dispensing and low-stock reporting.
- Low-stock reporting with branch filtering.
- Atomic prescription dispensing with rollback.
- Database design, requirements, design and interface contract documentation.

Remaining work:
- Final manual GUI walkthrough and integration verification.
- Any fixes discovered during integration.

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

Last updated: 21 November 2026.