# Interface Contract — UCU Campus Pharmacy Management System

**Status:** Stage 3 working contract — existing group agreements documented; implementation details marked for owner confirmation.  
**Coordinator:** Member 1 — Architecture and Integration  
**Repository:** `timomugishan8-ai/UCU-Campus-Pharmacy-Management-System`

## 1. Purpose

This document records how the five members' components communicate. It consolidates the architecture, service names, screen contract and database conventions already agreed by the group. It does not replace those agreements or redesign the system.

Where the current repository contains an implementation, the contract records the observed interface. Where a component is still a placeholder, the document records the agreed public service contract and identifies the owner confirmation still required.

## 2. Agreed architecture

The system uses four layers:

1. **GUI (`gui/`)** — Tkinter screens, input collection, navigation, messages and display refresh. No SQL, repository construction or authoritative business rules.
2. **Application facade (`app/services.py`)** — creates and exposes the shared application services. It is the composition point for repositories and services.
3. **Services and domain (`services/`, `domain/`)** — services coordinate use cases; domain objects enforce object-level rules. Neither layer depends on Tkinter.
4. **Repository/database (`database/`)** — parameterized SQLite access, row mapping, connection management and transaction boundaries. No GUI code.

**Communication flow:** User → Tkinter screen → `ApplicationServices` → application service → domain/repository → SQLite. Results and expected errors return to the screen for display.

## 3. Shared database contract

### Database manager

The existing `database.connection.Database` interface is:

- `Database(db_path=None)`
- `connect() -> sqlite3.Connection`
- `connection() -> context manager yielding a connection`
- `transaction() -> context manager yielding a connection; commits on success and rolls back on exception`
- `initialize_schema(schema_path=None) -> None`
- `close() -> None` (compatibility no-op)

Each connection enables SQLite foreign keys. A single `Database` object must be injected into every repository and shared by services that coordinate transactions.

### Repository construction

The existing repository constructors accept an optional database argument:

- `MedicineRepository(database=None)`
- `BranchRepository(database=None)`
- `StockRepository(database=None)`
- `PrescriptionRepository(database=None)`
- `PrescriberRepository(database=None)`

**Integration rule:** The application facade must instantiate one `Database` and pass that same object to every repository. Do not rely on each repository's default constructor, because that can create separate database managers.

### Repository method contracts observed in the current code

| Repository | Public operations | Return format |
|---|---|---|
| `MedicineRepository` | `add(code, name, unit_price, reorder_level, is_controlled, conn=None)`; `update(...)`; `delete(code, conn=None)`; `get_by_code(code, conn=None)`; `list_all(conn=None)`; `exists(code, conn=None)` | Writes: `None`, `bool` or SQLite exception as documented; reads: dictionary/None, list of dictionaries or bool |
| `BranchRepository` | `add(name, conn=None)`; `update(branch_id, name, conn=None)`; `delete(branch_id, conn=None)`; `get_by_id(branch_id, conn=None)`; `get_by_name(name, conn=None)`; `list_all(conn=None)` | Generated integer ID; bool; dictionary/None; list of dictionaries |
| `StockRepository` | `set_quantity(medicine_code, branch_id, quantity, conn=None)`; `increase(medicine_code, branch_id, amount, conn=None)`; `decrease(medicine_code, branch_id, amount, conn=None)`; `delete(medicine_code, branch_id, conn=None)`; `get_quantity(medicine_code, branch_id, conn=None)`; `list_for_branch(branch_id, conn=None)`; `list_low_stock(branch_id=None, conn=None)` | Writes: `None` or bool; quantity: integer; list methods: list of dictionaries; invalid/insufficient stock may raise `ValueError` |
| `PrescriptionRepository` | `create(branch_id, patient_identifier, prescriber_code, lines, conn=None)`; `update_status(prescription_id, status, prescriber_code=None, dispensed_at=None, conn=None)`; `delete(prescription_id, conn=None)`; `get_by_id(prescription_id, conn=None)`; `get_lines(prescription_id, conn=None)`; `list_by_branch(branch_id, status=None, conn=None)` | Generated integer ID; row count integer; bool; dictionary/None; list of dictionaries |
| `PrescriberRepository` | `is_authorised(prescriber_code, conn=None)` | bool |

Repository methods that accept `conn` must use the supplied connection and must not start a separate transaction. This allows a service to keep related reads and writes in one transaction.

## 4. Agreed service interfaces

These public names and parameter meanings are the group-level contract and should not be renamed without group agreement.

### MedicineService

- `register_medicine(medicine)`
- `get_all_medicines()`
- `get_medicine_by_code(medicine_code)`

**Owner:** Member 2.  
**Current implementation status:** `services/medicine_service.py` is currently a placeholder in the inspected branch. Member 2 must confirm constructor dependencies, accepted medicine object types, return formats and validation exceptions.

### StockService

- `receive_stock(medicine_code, branch_id, quantity)`
- `get_branch_stock(branch_id)`
- `get_low_stock(branch_id=None)`

**Owner:** Member 5 / as allocated by the group.  
**Current implementation status:** `services/stock_service.py` is currently a placeholder in the inspected branch. Confirm constructor dependencies, return formats and errors. It is expected to coordinate stock, medicine and branch repositories.

### PrescriptionService

The current implementation exposes:

- `PrescriptionService(prescription_repository, medicine_repository, stock_repository, prescriber_repository=None, branch_repository=None)`
- `create_prescription(patient_identifier, branch_id, prescriber_code, lines) -> Prescription`
- `get_prescription(prescription_id) -> Prescription | None`
- `dispense_prescription(prescription_id) -> Prescription`
- `cancel_prescription(prescription_id) -> Prescription`

Accepted `lines` formats in the current implementation are a sequence of `(medicine_code, quantity)` pairs, dictionaries containing those keys, or `PrescriptionLine` objects. Duplicate medicine codes on one prescription are rejected.

Expected errors include `ValueError` and the domain exceptions `UnknownMedicineError`, `InsufficientStockError`, `UnauthorisedPrescriberError` and `InvalidPrescriptionStateError` (all prescription exceptions derive from `PrescriptionError`).

**Integration rule:** Inject the shared prescriber and branch repositories explicitly through the facade. Do not allow this service to create repositories with independent database managers during application startup.

### ReportService

- `get_low_stock_report(branch_id=None)`
- `get_branch_stock_summary()`

**Current implementation status:** `services/report_service.py` is currently a placeholder in the inspected branch. Confirm constructor dependencies and exact returned data shape before GUI report screens are integrated.

## 5. Domain object contract

### Prescription domain (observed implementation)

- `PrescriptionLine(medicine_code, quantity, line_id=None, prescription_id=None, medicine_name=None, is_controlled=False)`
- `Prescription(branch_id, patient_identifier, lines, prescription_id=None, prescriber_code=None, status="pending", created_at=None, dispensed_at=None)`

Prescription statuses are `pending`, `dispensed` and `cancelled`. A prescription requires at least one line; duplicate medicine codes are not allowed. Only pending prescriptions may be dispensed or cancelled. `Prescription.from_dict(data)` maps repository data into a domain object; `to_dict()` provides a dictionary representation.

### Medicine and branch domain

The agreed design requires `Medicine`, `OrdinaryMedicine` and `ControlledMedicine`, with meaningful inheritance and polymorphic behaviour. The medicine domain file in the inspected branch is currently a placeholder. Member 2 must confirm constructor signatures, validation methods, and the common behaviour used to determine whether a medicine requires prescriber authorisation. The agreed medicine fields include medicine code, name, unit price, reorder level and controlled status.

Branch and Stock domain object interfaces must follow the group's design and be confirmed by their owners if domain classes are implemented separately. Do not invent GUI dependencies in these classes.

## 6. GUI screen contract

Every feature screen is constructed using:

```python
class FeatureScreen:
    def __init__(self, parent, services):
        self.parent = parent
        self.services = services
```

Existing prescription screens use this pattern:

- `CreatePrescriptionScreen(parent, services)`
- `DispenseScreen(parent, services)`

Screens access application operations through the shared facade, for example:

```python
self.services.prescription_service.create_prescription(
    patient_identifier, branch_id, prescriber_code, lines
)
```

GUI callbacks may:
- read and perform basic format conversion on widget input;
- call the relevant service method;
- catch expected application/domain errors;
- display success or failure messages; and
- refresh the displayed data.

GUI callbacks must not:
- execute SQL or create SQLite connections;
- instantiate repositories or services;
- implement authoritative stock, prescription or authorisation rules.

**Owner:** Member 4. Confirm the final screen list, navigation approach and the way screens are mounted/refreshed by the main window.

## 7. ApplicationServices composition contract

The facade is the single composition root. The following wiring is the agreed integration direction; constructor signatures for unfinished services remain subject to owner confirmation.

```python
database = Database()

medicine_repository = MedicineRepository(database)
branch_repository = BranchRepository(database)
stock_repository = StockRepository(database)
prescription_repository = PrescriptionRepository(database)
prescriber_repository = PrescriberRepository(database)

# Construct each service with the repositories it needs.
# All repositories above share the same Database instance.
```

The facade exposes these attributes to the GUI:

- `services.medicine_service`
- `services.stock_service`
- `services.prescription_service`
- `services.report_service`

The facade must not create a second database manager for any service. The exact constructors for MedicineService, StockService and ReportService must be aligned with their owners before the facade is implemented.

## 8. Database and business-rule boundaries

The current schema establishes these principal tables: `medicines`, `branches`, `stock`, `prescriptions`, `prescription_lines` and `authorised_prescribers`.

The following rules remain part of the agreed system contract:

- Medicine codes are unique; names are non-empty; unit prices are positive; reorder levels are non-negative integers.
- Stock is branch-specific and cannot be negative. Stock receipt quantity must be a positive integer.
- Prescription lines require positive integer quantities and existing medicine codes.
- A prescription belongs to one branch and uses a fictional patient identifier.
- Controlled-medicine dispensing requires a prescriber code present in the simulated authorised-prescriber allow-list.
- Dispensing is atomic: prescription status, authorisation checks and all stock deductions occur in one transaction. Any failure rolls back the entire operation.
- A prescription cannot be dispensed twice or dispensed after cancellation.
- Low stock means quantity less than or equal to the medicine's reorder level for that branch.

## 9. Error-handling convention

- Domain and service layers raise meaningful exceptions; they do not display message boxes.
- Repository/database layers allow database exceptions to propagate or translate them only where the repository's documented contract requires it.
- GUI screens catch expected `ValueError`, domain-specific exceptions and expected database/application errors at the UI boundary, then display a useful message.
- Do not silently convert a failed operation into a success result.
- Preserve the original exception as the cause when translating an exception.

## 10. Items requiring owner confirmation

These are the remaining Stage 3 checks; they do not reopen the architecture or service names already agreed.

| Owner | Confirmation required |
|---|---|
| Member 2 — Domain/Medicine | Final `Medicine`, `OrdinaryMedicine`, `ControlledMedicine` constructors and methods; mapping from repository medicine dictionaries to the correct subtype; MedicineService constructor, accepted inputs and return formats |
| Member 3 — Prescription | Confirm the current Prescription/PrescriptionLine and PrescriptionService interfaces above; confirm exception names and the accepted line input formats; identify any changes on the member branch not yet reflected in the integration branch |
| Member 4 — GUI | Final screen list; main-window navigation/mounting contract; confirm all screens accept `(parent, services)` and call services only |
| Member 5 — Database/Testing | Confirm all repositories accept the shared `Database`; confirm the prescriber repository is part of the database contract; confirm repository methods/return shapes and test transaction behaviour |
| Service owners | Confirm exact constructor dependencies and return data shapes for MedicineService, StockService and ReportService |

### Prescriber allow-list note

The current schema has `authorised_prescribers(prescriber_code, prescriber_name)` and the current repository treats the presence of a code as authorisation. The earlier design discussion mentioned an active/authorised status. The group must decide whether presence in the allow-list is sufficient or whether an explicit active field is required. Do not add a field without Member 5's agreement.

### Branch data note

The current schema uses an auto-generated integer `branch_id` and a unique `branch_name`. Confirm how branch records are seeded or administered; the current GUI contract does not define a branch-registration screen.

## 11. Stage 3 completion checklist

- [ ] Members 2–5 have reviewed the sections relevant to their components.
- [ ] Constructor dependencies for all services are confirmed.
- [ ] Return formats for all service methods are confirmed.
- [ ] Medicine subtype mapping and prescriber authorisation representation are confirmed.
- [ ] Main-window screen navigation and refresh contract are confirmed.
- [ ] Any agreed amendments are recorded here before facade integration.
- [ ] The facade can be constructed with one shared Database instance and no implicit duplicate repositories.

**Stage 3 exit condition:** The owners have confirmed the outstanding details above, and Member 1 can implement the facade and main-window integration without guessing at another member's interface.
