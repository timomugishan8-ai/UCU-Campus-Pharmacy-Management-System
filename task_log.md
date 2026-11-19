# Task Log

## Mugisha Timothy 

1. During Stage 2, I developed the project's Milestone 1 design package, covering the system requirements, functional and non-functional requirements, business rules, use cases and workflows. I documented the four-layer architecture, defined the responsibilities of the domain classes, services, repositories and GUI, and addressed key OOP concepts such as encapsulation, inheritance and polymorphism. I also prepared UML and database diagrams, including the class, use-case, architecture, ER and workflow diagrams. Finally, I established a requirements traceability matrix and identified key integration decisions requiring group review before implementation.


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
