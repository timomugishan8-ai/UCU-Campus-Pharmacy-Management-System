# Task Log

## Mugisha Timothy 

- Reviewed the project requirements and identified the need for a centralized architecture to integrate all five members' contributions.
- Established the system's four-layer architecture: Presentation (GUI), Application, Service/Domain, and Database/Repository layers.
- Defined the communication flow between GUI screens, application services, domain logic, repositories, and the SQLite database.
- Developed the ApplicationServices class in app/services.py to centralize dependency creation and service composition.
- Configured a single shared database instance to be injected into all five repositories.
- Integrated the medicine, stock, prescription, and report services into the application services facade.
- Implemented BaseScreen in app/base_screen.py to provide a common foundation for GUI screens and shared service access.
- Designed and implemented MainWindow in gui/main_window.py to provide the main application window, navigation panel, screen registration, and screen switching.
- Developed the application entry point in main.py to coordinate service initialization, database schema creation, sample data seeding, GUI startup, and the Tkinter event loop.
- Reviewed existing database connection and seed-data implementations to understand and align the application startup process.
- Prepared the interface_contract.md documentation to define component interfaces, constructors, service methods, dependencies, database conventions, and integration requirements.
- Prepared architecture and workflow diagrams to visually document the system structure and component interactions.
- Established integration guidelines to minimize coupling, avoid duplicated dependencies, and ensure consistency across members' implementations.
- Prepared the integration and verification approach for reviewing, connecting, and testing individual components before final system delivery.


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
