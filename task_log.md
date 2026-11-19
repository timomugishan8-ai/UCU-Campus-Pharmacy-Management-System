# Task Log

## 2026-11-19 - Member 2 (Mulisa) - Medicine, branch and stock domain

- **Branch**: `member-2-domain` (PR opened against `main`)
- **Files changed**
  - `domain/medicine.py`: abstract `Medicine` base with validated, read-only attributes; `OrdinaryMedicine` and `ControlledMedicine` overriding `requires_prescriber_code()`; `Medicine.create()` / `Medicine.from_dict()` subtype mapping; `MedicineError`, `InvalidMedicineError`, `DuplicateMedicineError` (all derive from `ValueError` for the GUI boundary).
  - `domain/branch.py`: `Branch` with `branch_id`/`branch_name`, validation, `from_dict`/`to_dict`.
  - `domain/stock.py`: `Stock` per `(medicine_code, branch_id)` with `receive()`, `can_fulfil()`, `decrease()`, `is_low_stock()` and `InsufficientStockError`; quantity never negative.
  - `services/medicine_service.py`: agreed contract methods `register_medicine(medicine)`, `get_all_medicines()`, `get_medicine_by_code(medicine_code)` returning `Medicine` objects (return format confirmed by Member 2 per interface contract section 10).
  - `tests/test_medicine.py`, `tests/test_stock.py`: 52 tests covering inheritance, overriding, polymorphism through the dispensing rule, validation rejections, read-only encapsulation, round trips, duplicate/invalid-price registration rejection and persistence across service restart.
- **Feature**: medicine catalogue registration and lookup; branch and stock domain rules including per-branch quantities and the low-stock boundary (`quantity <= reorder_level`).
- **Tests**: `py -m unittest discover -s tests` -> 107 tests passed (55 existing + 52 new).
- **Decisions / confirmations**
  - MedicineService ownership confirmed as Member 2 per interface contract section 4 (supersedes the earlier task-allocation question).
  - MedicineService returns domain objects, not dictionaries; `Medicine.to_dict()` is available for screens that prefer row shape.
  - ReportService agreed formats verified as already implemented in `StockRepository.get_branch_stock_summary()`; Matilda's low-stock screen already sources its branch filter from the summary.
  - No changes to shared interfaces, repositories or schema.
- **Next steps**: coordinate with Matilda on `register_medicine` / `receive_stock` screens (second batch, after her `base_screen.py` lands); confirm constructor with Timothy for the `ApplicationServices` facade.

## 2026-11-18 - Member 3 (Conrad) - Prescription and dispensing

- **Files changed**
  - `domain/prescription.py`: `Prescription`, `PrescriptionLine`, status constants, valid transitions and prescription exceptions.
  - `services/prescription_service.py`: agreed public methods plus the single-transaction dispensing flow.
  - `gui/create_prescription.py`, `gui/dispense.py`: screens using `Screen(parent, services)` with no SQL.
  - `tests/test_prescription.py`, `tests/test_dispensing.py`: 23 tests covering creation, authorisation, rollback and invalid states.
  - `database/repositories/prescriber_repository.py` (new, needs Cindy review): allow-list lookup with optional shared `conn`.
- **Feature**: multi-line prescription creation, pending/dispensed/cancelled states, controlled-medicine prescriber check, atomic all-or-nothing dispensing.
- **Tests**: `py -m unittest discover -s tests -v` -> 31 tests passed (23 Member 3 + 8 Cindy). Temporary databases only.
- **Issues / decisions to confirm**
  - The shared agreement named no repository for `authorised_prescribers`; a new repository file was added so the check stays in the repository layer and joins the dispensing transaction.
  - `create_prescription()` returns a `Prescription` object; `get_prescription()` returns `Prescription | None`. Confirm this with Members 1, 4 and Cindy before integration.
  - `PrescriptionService` constructor takes `(prescription_repository, medicine_repository, stock_repository)`; prescriber/branch repositories are built automatically from the shared `Database`.
- **Next steps**: Cindy to review `prescriber_repository.py`, Member 4/1 to place the two screens in the main window, full GUI walkthrough after other members' branches land.

## Cindy – Database, Repositories, Stock Services and Reporting

- **Files changed**
  - `database/connection.py`: reusable SQLite connection manager with foreign-key enforcement.
  - `database/schema.sql`: six agreed tables, constraints, indexes and deletion rules.
  - `database/seed_data.py`: fictional seed data and idempotent seeding.
  - `database/repositories/medicine_repository.py`: medicine persistence.
  - `database/repositories/branch_repository.py`: branch persistence.
  - `database/repositories/stock_repository.py`: branch-specific stock persistence, safe decrease and branch stock summary SQL.
  - `database/repositories/prescription_repository.py`: prescription and line persistence.
  - `database/repositories/prescriber_repository.py`: authorised prescriber allow-list lookup, reviewed for compatibility.
  - `services/stock_service.py`: stock receipt and stock availability service.
  - `services/report_service.py`: low-stock report and branch stock summary service.
  - `tests/test_member5_database.py`: database and repository integration tests.
  - `tests/test_cindy_stock_report.py`: StockRepository reporting and ReportService tests.
  - `tests/test_cindy_stock_service.py`: StockService tests.
  - `docs/database_design.md`: database contract and integration notes.
  - `README.md`: project guide, setup, architecture, status and contribution information.
  - `task_log.md`: Cindy contribution entry.
- **Completed responsibilities**
  - Database connection manager and SQLite schema.
  - Database seed data and repositories.
  - StockRepository branch stock summary SQL.
  - ReportService implementation.
  - StockService implementation.
  - Reporting and StockService tests.
  - Database design documentation.
- **Pull requests merged into main**
  - Documentation pull request: `cindy-documentation`.
  - Implementation pull request: `cindy-database-services`.
- **Verification results**
  - 10 reporting tests passed.
  - 14 StockService tests passed.
  - 55 tests passed in the full suite after merging.
  - `git diff --check` passed.
- **Outstanding work**
  - Participate in full application integration testing.
  - Coordinate with Timothy on ApplicationServices.
  - Coordinate with Matilda on GUI integration.
  - Address any issues discovered during integration.
