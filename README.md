# UCU Campus Pharmacy Management System

**Multi-Branch Campus Pharmacy Inventory, Dispensing and Reporting System**

- **Course:** CSC2105 - Object-Oriented Programming Using Python
- **Institution:** Uganda Christian University
- **Language:** Python 3.13
- **GUI:** Tkinter (desktop)
- **Database:** SQLite

> Status: This project is under active development. The application, database schema, services, repositories and tests are **not yet implemented**. Setup, database, application and testing instructions below are placeholders and will be updated as the project progresses.

---

## 1. Project overview

This system is a desktop application for managing pharmacy operations across multiple campus branches. It will track medicines, branch-specific stock levels, prescriptions, dispensing transactions and low-stock reports. The goal is to support accurate inventory control and safe dispensing of medicines (including controlled medicines that require an authorised simulated prescriber code) while keeping each branch's stock consistent.

The project follows a layered architecture:

- **Domain classes** hold core business entities and rules.
- **Services** coordinate business logic and orchestrate operations.
- **Repositories** handle all SQL and persistence against SQLite.
- **GUI (Tkinter)** communicates only with application services, never directly with SQL.

## 2. Main features (planned)

- Register and manage medicines (code, name, unit price, reorder level, controlled flag).
- Manage pharmacy branches.
- Track branch-specific stock levels and receive new stock.
- Create prescriptions with multiple medicine lines.
- Dispense prescriptions atomically: if any medicine cannot be supplied, no stock is deducted and the prescription remains pending.
- Enforce authorised simulated prescriber codes for controlled medicines.
- Generate low-stock reports per branch.
- Reporting on inventory and dispensing activity.

Optional medicine attributes (such as strength or form) may be added later if the group agrees; they are not mandatory requirements.

## 3. Technologies used

- Python 3.13
- Tkinter (standard library, desktop GUI)
- SQLite (standard library, file-based database)
- unittest (Python standard library, testing)
- Git and GitHub (version control and collaboration)

No third-party dependencies are required at this stage; requirements.txt will be updated if any are added.

## 4. Project folder structure

```text
UCU-Campus-Pharmacy-Management-System/
|-- app/            # Application entry points and shared screen services
|-- data/           # SQLite database file(s) (generated at runtime, not committed)
|-- database/       # Connection, schema, seed data and repositories
|   +-- repositories/
|-- domain/         # Core pharmacy domain models
|-- gui/            # Tkinter screens
|-- services/       # Business services
|-- tests/          # Unit and integration tests
|-- docs/           # Design, requirements and test reports
|-- main.py         # Application entry point
|-- requirements.txt
+-- README.md
```

## 5. Team contribution

This is a five-member group project (CSC2105). Placeholders - to be filled in with real names and responsibilities:

- **Member 1:** (to be assigned)
- **Member 2:** (to be assigned)
- **Member 3:** Conrad - Prescription and dispensing owner (prescription domain, prescription service, create/dispense screens and their tests).
- **Member 4:** (to be assigned)
- **Member 5:** Database development, repositories, selected services, testing coordination and documentation.

### 5.1 Member 3 contribution - Prescription and dispensing (Conrad)

This section was added by Member 3. It describes only the prescription and dispensing part; Member 5 owns the rest of this README.

**Files owned by Member 3**

- `domain/prescription.py` - `Prescription`, `PrescriptionLine`, status constants, valid transitions and prescription exceptions.
- `services/prescription_service.py` - the agreed public service methods and the dispensing transaction.
- `gui/create_prescription.py` - `CreatePrescriptionScreen(parent, services)`.
- `gui/dispense.py` - `DispenseScreen(parent, services)`.
- `tests/test_prescription.py` and `tests/test_dispensing.py` - 23 tests for this feature.
- `database/repositories/prescriber_repository.py` - new allow-list lookup (needs Member 5 review because Member 5 owns the database folder).

**What is implemented**

- Multi-line prescriptions tied to one branch and a fictional patient identifier.
- `pending`, `dispensed` and `cancelled` statuses; only pending prescriptions can dispense or cancel.
- Controlled medicines require an authorised simulated prescriber code; ordinary medicines do not.
- All-or-nothing dispensing: one SQLite transaction (`BEGIN IMMEDIATE`) covers status checks, controlled-medicine authorisation, stock checks, conditional stock reductions and the conditional status update. If any step fails, everything rolls back and no stock is deducted.

**Agreed public methods**

```python
PrescriptionService(prescription_repository, medicine_repository, stock_repository)

create_prescription(patient_identifier, branch_id, prescriber_code, lines) -> Prescription
dispense_prescription(prescription_id) -> Prescription
cancel_prescription(prescription_id) -> Prescription
get_prescription(prescription_id) -> Prescription | None
```

The prescriber and branch repositories are built automatically from the shared `Database`, so `app/services.py` only needs the three repository arguments above. The return format (`Prescription` object) should be confirmed with Members 1, 4 and 5 during integration.

**Tests**

```powershell
py -m unittest tests.test_prescription tests.test_dispensing -v
```

All 23 Member 3 tests pass; the whole suite (`py -m unittest discover -s tests -v`) passes 31 tests. Tests use temporary databases, never the live `data/pharmacy.db`.

**Integration notes**

- The group agreement did not name a repository for `authorised_prescribers`. `PrescriberRepository.is_authorised(code, conn=None)` was added so the allow-list check stays in the repository layer and joins the dispensing transaction.
- The two screens use the shared services object and contain no SQL.
- Branch: `member-3-prescriptions`.

## 6. Prerequisites

- Python 3.13 installed (with Tkinter and SQLite support).
- Git installed.
- Visual Studio Code (recommended) with the Python extension.
- (To be completed during development) Any additional dependencies listed in requirements.txt.

## 7. VS Code setup instructions

1. Open VS Code.
2. Select File -> Open Folder and choose the project folder.
3. Install the recommended Python extension (by Microsoft) if prompted.
4. Select the project's Python interpreter: open the Command Palette (Ctrl+Shift+P) -> Python: Select Interpreter -> choose the .venv interpreter.
5. (To be completed during development) Configure launch settings and tasks if needed.

## 8. Virtual environment (Windows PowerShell)

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If script execution is restricted, run once (as Administrator) or use:

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

## 9. Database setup instructions

The SQLite schema is implemented in `database/schema.sql` and is created automatically when the application or tests initialise a database.

Seed fictional development data with:

```powershell
python -m database.seed_data
```

Do not commit generated `.db`, `.sqlite` or `.sqlite3` files.

## 10. How to run the application

(To be completed during development)

```powershell
python main.py
```

The entry point and GUI are not implemented yet.

## 11. How to run tests

```powershell
python -m unittest discover -s tests
```

Member 5's database tests and Member 3's prescription/dispensing tests are implemented (31 tests pass). Other members' suites are still being added.

## 12. Git collaboration workflow

- Work on a dedicated feature branch per member (e.g. member-5-database-tests).
- Pull the latest main before starting work: git pull origin main.
- Make small, focused commits with clear messages.
- Do not commit generated files (.venv/, __pycache__/, *.db, .env).
- Open a pull request to main and request review before merging.
- Resolve conflicts locally and re-run tests before pushing.
- Never force-push to main.

## 13. Academic integrity and AI assistance note

This project is submitted for academic assessment (CSC2105). All members are responsible for understanding and being able to explain every part of the submitted code. AI tools may be used to assist with drafting, refactoring and documentation, but the final submission must reflect the group's own understanding. Any AI-assisted content must be reviewed, tested and owned by the group. Plagiarism or uncredited copying is not permitted.

---

Last updated: during initial repository setup (database, application and tests not yet implemented).