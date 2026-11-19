# Task Log

## 2026-11-18 - Member 3 (Conrad) - Prescription and dispensing

- **Files changed**
  - `domain/prescription.py`: `Prescription`, `PrescriptionLine`, status constants, valid transitions and prescription exceptions.
  - `services/prescription_service.py`: agreed public methods plus the single-transaction dispensing flow.
  - `gui/create_prescription.py`, `gui/dispense.py`: screens using `Screen(parent, services)` with no SQL.
  - `tests/test_prescription.py`, `tests/test_dispensing.py`: 23 tests covering creation, authorisation, rollback and invalid states.
  - `database/repositories/prescriber_repository.py` (new, needs Member 5 review): allow-list lookup with optional shared `conn`.
- **Feature**: multi-line prescription creation, pending/dispensed/cancelled states, controlled-medicine prescriber check, atomic all-or-nothing dispensing.
- **Tests**: `py -m unittest discover -s tests -v` -> 31 tests passed (23 Member 3 + 8 Member 5). Temporary databases only.
- **Issues / decisions to confirm**
  - The shared agreement named no repository for `authorised_prescribers`; a new repository file was added so the check stays in the repository layer and joins the dispensing transaction.
  - `create_prescription()` returns a `Prescription` object; `get_prescription()` returns `Prescription | None`. Confirm this with Members 1, 4 and 5 before integration.
  - `PrescriptionService` constructor takes `(prescription_repository, medicine_repository, stock_repository)`; prescriber/branch repositories are built automatically from the shared `Database`.
- **Next steps**: Member 5 to review `prescriber_repository.py`, Member 4/1 to place the two screens in the main window, full GUI walkthrough after other members' branches land.

## 2026-11-19 - Member 4 (Matilda) - Low-stock GUI screen

- **Files changed**
  - `gui/low_stock.py` (new, 171 lines): `LowStockScreen` built on `ttk.Frame`, following the agreed `Screen(parent, services)` constructor pattern.
- **Feature**: read-only low-stock report with a branch filter dropdown, Refresh button, results table and status line. Calls only `services.report_service.get_low_stock_report(branch_id=...)`; contains no SQL and creates no database connection.
- **Tests**: `python -m py_compile gui/low_stock.py` passed. Runtime/GUI tests are not yet possible because `app/services.py`, `gui/main_window.py` and `services/report_service.py` are still empty placeholders on the other members' branches.
- **Issues / decisions to confirm**
  - Confirmed with Member 5 (2026-11-19): `get_low_stock_report(branch_id=None)` returns exactly the fields this screen reads (`medicine_code`, `medicine_name`, `branch_id`, `branch_name`, `quantity`, `reorder_level`, `is_controlled`) with `quantity <= reorder_level`. The branch dropdown is derived from `branch_id`/`branch_name` in those rows — approved; no `get_all_branches()` needed.
  - Agreed the `get_branch_stock_summary()` return shape with Member 5: a list of dicts with `branch_id`, `branch_name`, `total_medicine_types`, `total_units`, `low_stock_items`; include every branch even with zero stock, and use the same `quantity <= reorder_level` rule for `low_stock_items`. Not used by this screen.
  - The screen currently inherits `ttk.Frame` because `app/base_screen.py` is empty; it will switch to `BaseScreen` once Member 1 implements it.
  - `show()` is proposed as the navigation hook — the exact name must be agreed with Member 1.
  - `except Exception` is temporary until Member 5 defines a specific application-exception class.
- **Next steps**: agree the GUI contract with Member 1, integrate all screens into `gui/main_window.py`, then run the full GUI walkthrough including low stock at quantity equal to the reorder level.
