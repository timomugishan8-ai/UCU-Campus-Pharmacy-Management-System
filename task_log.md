# Task Log

## Mugisha Timothy 

1. During Stage 2, I developed the project's Milestone 1 design package, covering the system requirements, functional and non-functional requirements, business rules, use cases and workflows. I documented the four-layer architecture, defined the responsibilities of the domain classes, services, repositories and GUI, and addressed key OOP concepts such as encapsulation, inheritance and polymorphism. I also prepared UML and database diagrams, including the class, use-case, architecture, ER and workflow diagrams. Finally, I established a requirements traceability matrix and identified key integration decisions requiring group review before implementation.

## 2026-11-19 - Member 2 (Mulisa) - Medicine, branch and stock domain

- **Branch**: `member-2-domain` (PR #7, merged into `main`); follow-up branch `member-2-navigation-refresh`
- **Files changed**
  - `domain/medicine.py`: abstract `Medicine` base with validated, read-only attributes; `OrdinaryMedicine` and `ControlledMedicine` overriding `requires_prescriber_code()`; `Medicine.create()` / `Medicine.from_dict()` subtype mapping; `MedicineError`, `InvalidMedicineError`, `DuplicateMedicineError` (all derive from `ValueError` for the GUI boundary).
  - `domain/branch.py`: `Branch` with `branch_id`/`branch_name`, validation, `from_dict`/`to_dict`.
  - `domain/stock.py`: `Stock` per `(medicine_code, branch_id)` with `receive()`, `can_fulfil()`, `decrease()`, `is_low_stock()` and `InsufficientStockError`; quantity never negative.
  - `services/medicine_service.py`: agreed contract methods `register_medicine(medicine)`, `get_all_medicines()`, `get_medicine_by_code(medicine_code)` returning `Medicine` objects (return format confirmed by Member 2 per interface contract section 10).
  - `tests/test_medicine.py`, `tests/test_stock.py`: 52 tests covering inheritance, overriding, polymorphism through the dispensing rule, validation rejections, read-only encapsulation, round trips, duplicate/invalid-price registration rejection and persistence across service restart.
  - `gui/register_medicine.py`: registration screen following the agreed `Screen(parent, services)` pattern; catalogue listing; controlled-medicine checkbox; error dialogs for invalid price, duplicate code and blank fields.
  - `gui/receive_stock.py`: stock receipt screen; medicine/branch dropdowns; branch options sourced from `report_service.get_branch_stock_summary()` per the 2026-11-19 agreement so empty branches still appear; branch stock listing.
  - `tests/test_member2_gui.py`: 13 tkinter smoke tests driving both screens against a temporary database with `messagebox` mocked (no dialogs block the run).
- **Feature**: medicine catalogue registration and lookup; branch and stock domain rules including per-branch quantities and the low-stock boundary (`quantity <= reorder_level`); medicine registration and stock receiving screens.
- **Tests**: `py -m unittest discover -s tests` -> 120 tests passed (55 existing + 52 domain/service + 13 GUI); 122 after the navigation follow-up below.
- **Decisions / confirmations**
  - MedicineService ownership confirmed as Member 2 per interface contract section 4 (supersedes the earlier task-allocation question).
  - MedicineService returns domain objects, not dictionaries; `Medicine.to_dict()` is available for screens that prefer row shape.
  - ReportService agreed formats verified as already implemented in `StockRepository.get_branch_stock_summary()`; Matilda's low-stock screen already sources its branch filter from the summary.
  - No changes to shared interfaces, repositories or schema.
- **Follow-up (2026-11-20, branch `member-2-navigation-refresh`)**: after PR #7 merged and Timothy's `MainWindow` navigation landed, both of my screens now inherit `app.base_screen.BaseScreen` and expose the optional `refresh()` hook that `show_screen()` calls on navigation, so their catalogue, dropdowns and stock listings reload when the user switches screens; 2 navigation tests added (suite now 122). Conrad's `create_prescription.py` and `dispense.py` have the same gap (`ttk.Frame`, no `refresh()`) — flagged for him, not changed by me.
- **Next steps**: joint GUI walkthrough with Member 4; watch Conrad's screens adopt `BaseScreen`/`refresh()` for consistency.

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

## 2026-11-19 - Member 4 (Matilda) - GUI coordination, low-stock screen and dashboard

**Where I worked.** I did all of my work inside the cloned repository at `C:\Users\HP\Desktop\yr2-1\Pharmacy-Project`, on my own branch `member-4-gui` before the changes were merged into `main`. Before writing any code I inspected the existing folder structure and read the group's shared Word document, *Group Development Standard & Technical Agreement*, so that I would stay inside my assigned files and follow the agreed `Screen(parent, services)` pattern. At that point my three files — `gui/low_stock.py`, `app/base_screen.py` and `gui/main_window.py` — were empty placeholders, so I worked from the interface contract rather than guessing what the other members had built.

**Building the low-stock screen.** I created `gui/low_stock.py` and wrote `LowStockScreen` with the required `LowStockScreen(parent, services)` constructor. The screen has a branch filter dropdown, a Refresh button, a `ttk.Treeview` results table and a status line at the bottom. I made a conscious decision that the file would call only `services.report_service.get_low_stock_report(branch_id=...)`; there is no SQL, no `sqlite3` import and no second database connection anywhere in it, because our layered architecture says the GUI must never talk to the database directly. I added a small private `_clear_rows()` helper that is called before every refresh so that clicking Refresh twice cannot duplicate rows, and a `show()` method that the main window can call when it navigates to the screen. Early on, while the other layers were still empty, I set up a temporary demo launcher in `C:\Users\HP\AppData\Local\Temp\opencode\low_stock_demo.py` with a fake report service so that I could see and click my real screen before integration — that file was never part of the repository.

**Decisions I made with the other members.** I prepared the interface-contract points for Member 1 covering the constructor signature, the `show()`/`refresh()` navigation hook and the four service attributes on the facade, so that I would not depend on names that might change. With Cindy (Member 5) I agreed the exact return format of `get_low_stock_report()`: the dictionary keys `medicine_code`, `medicine_name`, `branch_id`, `branch_name`, `quantity`, `reorder_level` and `is_controlled`, with low stock defined as `quantity <= reorder_level`. Her first suggestion was that I build the branch dropdown from the low-stock rows themselves. I pointed out that any branch with no low-stock items would then disappear from the filter, so we revised the decision: the dropdown now reads `branch_id` and `branch_name` from `get_branch_stock_summary()` instead. That change touched only `_load_branch_options()` in `gui/low_stock.py`; the report table itself still uses `get_low_stock_report()`. I also agreed with Cindy that the aggregate SQL belongs in `StockRepository` and that `ReportService` should only call the repository method, and I recorded both decisions here in `task_log.md` so the group had a written record.

**Integration work.** When Members 1 and 2 pushed their branches, I created a local `integration-test` branch and merged their work into it rather than committing over their files. In `gui/low_stock.py` I changed the base class from `ttk.Frame` to Member 1's `BaseScreen` and switched to `super().__init__(parent, services)`, so the shared base now stores `parent` and `services` for every screen. In `gui/main_window.py` I registered all five feature screens with navigation buttons, and kept a single `show_screen()` method that highlights the active button, calls `tkraise()` and then an optional `refresh()`. I resolved several `task_log.md` merge conflicts by keeping every member's entry, and I removed 30 committed `__pycache__/*.pyc` files from Git tracking because the agreement forbids committing caches. Later I standardised my table headings — `Medicine code`, `Name`, `Quantity` — to match the other four screens, again changing only my own file.

**The dashboard.** For the visual work I used the four WhatsApp reference images the group shared. I chose the UCU Pharmacy identity from the dark navy sidebar image and the stat-card layout from the MediStock Pro image, and I confirmed those choices before coding. I created `gui/dashboard.py` with `DashboardScreen(parent, services)`: four stat cards (Total Medicines, Low Stock Items, Total Stock Units and Branches) read from `medicine_service`, `stock_service` and `report_service`; an Inventory Status table that computes each row's status from `quantity <= reorder_level` and colours it red, amber or green; and a Branch Overview table built from the branch summary. I deliberately did not invent trend percentages or expiry figures because our system does not store that data. I also restyled `gui/main_window.py` with the navy sidebar, teal pill logo, UCU Pharmacy branding, the new menu labels, an active-item highlight and one shared `ttk.Style` for table headings, and made the dashboard the landing screen. I left out the "Reports" item from the reference because no Reports screen exists.

**Verification and evidence.** I checked each file with `python -m py_compile` and ran the full suite with `python -m unittest discover -s tests`, which passed all 120 tests. I also smoke-tested the GUI against a temporary SQLite database: all six screens construct, the dashboard cards show 5 / 3 / 167 / 2, the inventory table shows 8 rows, the branch table 2 rows, and navigation switching works. My work was pushed through PRs #3, #8, #9 and #10 and merged into `main`. The four reference images are still untracked in the project folder and were never committed.

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

