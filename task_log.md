# Task Log

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

## 2026-11-19 - Member 4 (Matilda) - Low-stock GUI screen

- **Files changed**
  - `gui/low_stock.py` (new, 171 lines): `LowStockScreen` built on `ttk.Frame`, following the agreed `Screen(parent, services)` constructor pattern.
- **Feature**: read-only low-stock report with a branch filter dropdown, Refresh button, results table and status line. Calls only `services.report_service.get_low_stock_report(branch_id=...)`; contains no SQL and creates no database connection.
- **Tests**: `python -m py_compile gui/low_stock.py` passed. Runtime/GUI tests are still not possible because `app/services.py`, `gui/main_window.py` and Members 1/2's screens are not yet implemented. Cindy's `ReportService` is now available with the agreed method signatures and field names.
- **Issues / decisions to confirm**
  - Confirmed with Member 5 (2026-11-19): `get_low_stock_report(branch_id=None)` returns exactly the fields this screen reads (`medicine_code`, `medicine_name`, `branch_id`, `branch_name`, `quantity`, `reorder_level`, `is_controlled`) with `quantity <= reorder_level`. No change needed for the report data.
  - Agreed with Member 5 (revised 2026-11-19): `get_branch_stock_summary()` returns one dict per branch with `branch_id`, `branch_name`, `medicine_count`, `total_quantity`, `low_stock_count`; branches with no stock appear with zeros. The aggregate SQL lives in `StockRepository`; `ReportService` only calls the repository method.
  - The branch dropdown now reads `branch_id`/`branch_name` from `get_branch_stock_summary()` instead of low-stock rows, so branches with no low-stock items are still offered in the filter.
  - The screen currently inherits `ttk.Frame` because `app/base_screen.py` is empty; it will switch to `BaseScreen` once Member 1 implements it.
  - `show()` is proposed as the navigation hook — the exact name must be agreed with Member 1.
  - `except Exception` is temporary until Member 5 defines a specific application-exception class.
- **Next steps**: agree the GUI contract with Member 1, integrate all screens into `gui/main_window.py`, then run the full GUI walkthrough including low stock at quantity equal to the reorder level.

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

