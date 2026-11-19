# System Design Specification
## Multi-Branch Campus Pharmacy Inventory, Dispensing and Reporting System

**Course:** CSC2105 — Object-Oriented Programming Using Python  
**Institution:** Uganda Christian University  
**Semester:** Advent 2026  
**Milestone:** 1 — Requirements and Object-Oriented Design  
**Document owner:** Member 1 — Architecture and Integration Coordinator  
**Status:** Design baseline for group review

---

## 1. Design purpose

This document translates the agreed project requirements into a software design. It defines the architecture, domain model, object-oriented approach, service/repository boundaries, database outline, GUI structure and critical workflows.

The design follows the group's Group Development Standard & Technical Agreement. It does not replace that agreement or authorise unilateral changes to the folder structure, database schema or public service contracts.

## 2. System overview

The system is a Python desktop application for managing medicines, branch-specific stock, prescriptions, dispensing and low-stock reporting at multiple UCU campus pharmacy locations.

The application uses:
- Python 3.
- tkinter for the desktop GUI.
- SQLite for persistent storage.
- Python standard-library modules unless an additional dependency is approved in writing.

The system is divided into four layers:

1. GUI / tkinter.
2. Application services.
3. Domain model.
4. Repositories / database.

The layers communicate through defined interfaces. The GUI does not execute SQL. Services do not create tkinter widgets. Domain classes do not open database connections. Repositories do not contain GUI behaviour.

## 3. Architecture

### 3.1 Four-layer architecture

| Layer | Responsibilities | Must not |
|---|---|---|
| GUI / tkinter | Collect input; convert basic form values; show screens, navigation, messages and tables; call services; refresh displays | Execute SQL; open its own database connection; own authoritative business rules |
| Application services | Coordinate use cases; validate/normalise inputs; call domain behaviour and repositories; manage application workflow and transaction orchestration | Import tkinter; embed SQL in callbacks or service logic |
| Domain | Represent Medicine, Branch, Stock, Prescription and PrescriptionLine; enforce object-level invariants; expose behaviour through methods/properties | Import tkinter; open database connections; know repository SQL |
| Repositories / database | Own parameterised SQL; map rows to documented records/objects; enforce persistence constraints; provide shared connection and transaction facilities | Import tkinter; display message boxes; decide screen behaviour |

### 3.2 Communication flow

```text
User
  |
  v
Tkinter screen
  |
  | calls agreed public service method
  v
ApplicationServices / feature service
  |
  | validates use case and invokes domain behaviour
  v
Domain objects
  |
  | valid operation / domain result
  v
Repository
  |
  | parameterised SQL through shared connection
  v
Database manager
  |
  v
SQLite database

Results or documented exceptions return through the service to the GUI.
The GUI displays a success message, refreshed data or a useful error.
```

### 3.3 Dependency direction

The GUI depends on the application-services interface. Application services depend on domain objects and repository interfaces. Repositories depend on the Database manager and SQLite. Domain objects are independent of the GUI and database.

This separation makes business rules testable without opening a window and prevents UI changes from changing database rules.

## 4. Application composition and shared services

### 4.1 ApplicationServices facade

The agreed facade is defined in `app/services.py`:

```python
class ApplicationServices:
    def __init__(self, database):
        self.medicine_service = ...
        self.stock_service = ...
        self.prescription_service = ...
        self.report_service = ...
```

The constructor receives one shared Database manager. It creates the repository objects and injects them into the services. The main window and every feature screen receive the same `ApplicationServices` instance.

### 4.2 Known integration dependencies

The repository inspected for this design already contains a prescription implementation and a `PrescriberRepository` addition. The prescription service constructor currently accepts:
- `prescription_repository`
- `medicine_repository`
- `stock_repository`
- optional `prescriber_repository`
- optional `branch_repository`

The service obtains its Database manager from the prescription repository and constructs the prescriber and branch repositories when overrides are not supplied.

Therefore, Member 1 and Member 5 must agree the exact repository construction in `ApplicationServices`. The facade must not create duplicate Database managers or duplicate service graphs. The existing three required positional repository arguments must be preserved unless Members 3 and 5 jointly approve a change.

### 4.3 Agreed service contracts

| Service | Public methods |
|---|---|
| MedicineService | `register_medicine(medicine)`, `get_all_medicines()`, `get_medicine_by_code(medicine_code)` |
| StockService | `receive_stock(medicine_code, branch_id, quantity)`, `get_branch_stock(branch_id)`, `get_low_stock(branch_id=None)` |
| PrescriptionService | `create_prescription(patient_identifier, branch_id, prescriber_code, lines)`, `dispense_prescription(prescription_id)`, `cancel_prescription(prescription_id)`, `get_prescription(prescription_id)` |
| ReportService | `get_low_stock_report(branch_id=None)`, `get_branch_stock_summary()` |

Public method names and parameter meanings are fixed by the group agreement. Return types and record shapes must be documented and agreed before dependent GUI code is integrated.

## 5. Domain model

### 5.1 Medicine hierarchy

`Medicine` is the common base class for medicine catalogue data. It should encapsulate:
- `medicine_code`
- `name`
- `unit_price`
- `reorder_level`

It should expose a meaningful behaviour such as `requires_prescriber_code()`.

Two subclasses are required by the group agreement:

- `OrdinaryMedicine`: inherits from `Medicine` and returns `False` for `requires_prescriber_code()`.
- `ControlledMedicine`: inherits from `Medicine` and overrides `requires_prescriber_code()` to return `True`.

This is a behavioural distinction. It is not merely a type label: dispensing logic can call the common method polymorphically without repeatedly checking concrete subclass names.

The current SQLite schema represents this distinction with `medicines.is_controlled` (0 or 1). Repository mapping must turn that persisted value into the appropriate domain subtype or otherwise preserve the common behaviour. The exact factory/mapping implementation belongs with the domain/database owners and must be agreed.

### 5.2 Branch

`Branch` represents a pharmacy location. It has:
- `branch_id`
- `branch_name`

The branch identifier and name are unique in the agreed model. Stock belongs to a branch; it must not be treated as a single global medicine quantity.

### 5.3 Stock

`Stock` represents the quantity of one medicine at one branch. It has:
- medicine reference/code
- branch reference/ID
- quantity

The medicine-branch pair identifies the stock record. Quantity must be a non-negative integer. Receiving stock adds a positive integer quantity. Dispensing reduces stock only if enough quantity is available.

### 5.4 PrescriptionLine

`PrescriptionLine` represents one medicine and quantity on a prescription. It has:
- line identifier (where persisted)
- prescription identifier (where persisted)
- medicine code
- positive integer quantity

The current schema enforces one line per medicine code per prescription through a unique constraint. The current prescription domain/service implementation also rejects duplicate medicine codes in a prescription.

### 5.5 Prescription

`Prescription` represents a prescription header and its lines. It has:
- prescription identifier
- fictional patient identifier
- branch identifier
- optional prescriber code
- status
- created timestamp
- dispensed timestamp (where recorded)
- one or more `PrescriptionLine` objects

Valid statuses are `pending`, `dispensed` and `cancelled`. Only a pending prescription can move to either final state. A dispensed or cancelled prescription cannot transition again.

### 5.6 Authorised prescriber

The simulated allow-list is represented by `authorised_prescribers`. The current schema contains `prescriber_code` as the primary key and an optional `prescriber_name`. The group agreement describes an active/authorised status; whether an explicit status field is required must be confirmed with Member 5 before changing the schema.

The allow-list contains fictional codes only. A non-empty string is not proof of authorisation; the code must be found in the allow-list.

## 6. Encapsulation, inheritance, overriding and polymorphism

### Encapsulation

Each domain class protects its own state by validating values during construction and, where appropriate, through controlled properties or methods. Examples:
- Medicine rejects blank code/name, non-positive price and invalid reorder level.
- Stock rejects negative or non-integer quantity.
- Prescription rejects an empty line collection, invalid status and invalid lines.
- Prescription state changes occur through methods such as `mark_dispensed()` and `mark_cancelled()` rather than arbitrary UI assignment.

### Inheritance

`OrdinaryMedicine` and `ControlledMedicine` inherit common attributes and behaviour from `Medicine`. Shared validation and data belong in the base class.

### Method overriding

`ControlledMedicine` overrides `requires_prescriber_code()` to express its additional dispensing requirement. `OrdinaryMedicine` uses the ordinary behaviour.

### Polymorphism

The dispensing workflow uses the common medicine behaviour:

```python
if medicine.requires_prescriber_code():
    # verify the prescriber against the simulated allow-list
```

The service does not need to branch on class names such as `OrdinaryMedicine` or `ControlledMedicine`. This allows the same workflow to work with either subtype.

## 7. Database design

### 7.1 Entity outline

| Table | Key fields and purpose |
|---|---|
| `medicines` | `medicine_code` primary key; `name`; `unit_price`; `reorder_level`; `is_controlled` |
| `branches` | `branch_id` primary key; unique `branch_name` |
| `stock` | `medicine_code` + `branch_id` composite primary key; `quantity`; foreign keys to medicine and branch |
| `prescriptions` | `prescription_id` primary key; `branch_id`; `patient_identifier`; `status`; `prescriber_code`; `created_at`; `dispensed_at` |
| `prescription_lines` | `line_id` primary key; `prescription_id`; `medicine_code`; `quantity`; unique prescription/medicine pair; foreign keys |
| `authorised_prescribers` | `prescriber_code` primary key; optional `prescriber_name`; simulated allow-list |

### 7.2 Constraints and persistence rules

The repository's current `database/schema.sql` includes:
- Primary keys for medicine, branch, prescription, line and prescriber identifiers.
- Unique branch names.
- Composite primary key for stock by medicine and branch.
- Foreign keys between stock, medicine and branch; prescription, branch; and prescription lines, prescription and medicine.
- `CHECK` constraints for positive medicine price, non-negative reorder level, boolean controlled flag, non-negative stock, valid prescription status and positive prescription-line quantity.
- A unique constraint preventing duplicate medicine lines within one prescription.
- Indexes for common branch, status and line lookups.

The connection layer must enable SQLite foreign-key enforcement on each connection. All user-supplied SQL values must be passed as parameters, not concatenated into SQL strings.

### 7.3 Current schema alignment notes

The current schema uses `is_controlled` rather than a text `medicine_type` column. It uses an integer auto-incrementing `branch_id`. The `authorised_prescribers` table currently has no explicit active flag. This document records the current repository design; it does not silently alter those fields.

The schema should be reviewed by Members 2, 3 and 5 for consistency with domain constructors and repository row mapping before it is treated as final.

## 8. Repository and service responsibilities

### Repositories

Repositories own SQL and persistence. Their responsibilities include:
- Execute parameterised SQL.
- Use the shared Database manager.
- Accept an optional existing connection where required by a transaction.
- Map database rows to documented records or domain objects.
- Raise meaningful persistence/application errors.
- Avoid tkinter imports and UI messages.

### Services

Services coordinate use cases:
- Validate and normalise inputs.
- Check referenced records.
- Call domain behaviour.
- Coordinate one or more repositories.
- Define the transaction boundary for multi-step operations such as dispensing.
- Return documented objects/records or raise meaningful exceptions.

Services do not contain tkinter widgets and do not embed SQL.

## 9. Atomic dispensing design

Atomic dispensing is a critical correctness requirement. The service must execute the following steps using one database transaction and one shared SQLite connection:

1. Begin the transaction.
2. Load the prescription and verify that it exists.
3. Verify that its status is `pending`.
4. Load all prescription lines and medicine records.
5. For every controlled medicine, check that the prescription's prescriber code is in the simulated authorised-prescriber allow-list.
6. Check that every line has sufficient stock at the prescription's branch.
7. Reduce each stock quantity using a conditional update that only succeeds when the current quantity is at least the requested quantity.
8. Check that each conditional stock update affected the expected row.
9. Change the prescription status from `pending` to `dispensed` using a conditional update.
10. Commit once, only after every check and update succeeds.

If any operation fails, the transaction rolls back. No stock reduction from that attempt remains, and the prescription remains pending.

### Why conditional updates matter

A prior read of stock is not enough to guarantee stock is still available when an update occurs. A conditional update such as `UPDATE stock SET quantity = quantity - ? WHERE medicine_code = ? AND branch_id = ? AND quantity >= ?` makes the database enforce the non-negative-stock condition at the moment of the update. The service must check the affected-row count.

### Required dispensing outcomes

| Scenario | Expected result |
|---|---|
| All items available; controlled prescriber authorised where required | All stock deductions and status update commit |
| Any line has insufficient stock | Roll back every deduction; status remains pending |
| Controlled medicine with unauthorised/missing prescriber | Reject; no stock change |
| Ordinary medicine with no prescriber code | Do not reject solely for missing prescriber code |
| Prescription already dispensed | Reject; no stock change |
| Prescription cancelled | Reject; no stock change |
| Unknown medicine or invalid line | Reject; no partial stock change |
| Competing dispense attempts | No negative stock; at most one valid status transition and stock consumption |

## 10. GUI design

Every screen uses the agreed constructor:

```python
class FeatureScreen:
    def __init__(self, parent, services):
        self.parent = parent
        self.services = services
```

### Screen responsibilities

| Screen | Input / action | Service call | Expected display |
|---|---|---|---|
| Main window | Navigation selection | No business operation itself | Shared navigation shell and active screen |
| Register medicine | Code, name, price, reorder level, type | `medicine_service.register_medicine(medicine)` | Success or validation error; updated catalogue |
| Receive stock | Medicine, branch, quantity | `stock_service.receive_stock(...)` | Success or error; refreshed branch stock |
| Create prescription | Fictional patient ID, branch, prescriber code, lines | `prescription_service.create_prescription(...)` | Prescription ID/status or validation error |
| Dispense | Prescription selection | `prescription_service.dispense_prescription(...)` | Dispensed result or clear rejection |
| Low stock | Branch filter | `stock_service.get_low_stock(...)` and/or agreed report service | Low-stock rows or empty-state message |

The GUI may perform basic conversion of text-field values to Python values. It must not be the only place where validation occurs. It catches expected errors and presents understandable messages; unexpected exceptions must not be silently swallowed.

## 11. Application startup design

The intended startup sequence is:

1. `main.py` locates/initialises the shared SQLite database through `database/connection.py`.
2. The database schema is initialised using the agreed database setup method.
3. One `ApplicationServices(database)` object is constructed.
4. The tkinter root/main window is created.
5. The same services object is passed to the main window and feature screens.
6. The tkinter event loop starts.

The entry point must not execute feature SQL or duplicate service construction inside individual screens.

## 12. Agreed project structure and ownership

The group-agreed structure is retained. Member 1's owned files are:

- `main.py`
- `app/services.py`
- `app/base_screen.py`
- `gui/main_window.py`
- `docs/requirements.md`
- `docs/design.md`
- `docs/diagrams/`

Other members retain ownership of their assigned domain, feature, repository, database and screen files. Shared-file edits must be discussed before implementation.

## 13. Design risks and coordination decisions

| Issue | Why it matters | Required action |
|---|---|---|
| ApplicationServices wiring | Prescription service needs prescription, medicine and stock repositories and can use prescriber/branch repositories | Agree constructor wiring with Member 5; preserve one Database manager |
| Medicine row-to-object mapping | Schema stores `is_controlled`; OOP model requires ordinary/controlled subclasses | Member 2 and Member 5 agree factory/mapping and common method behaviour |
| Prescriber authorisation status | Group agreement refers to active/authorised status, current schema has code and optional name only | Members 3 and 5 decide whether presence in the table alone means authorised or an explicit flag is needed |
| Service return formats | GUI depends on stable result shapes | Feature owners and Member 5 document object/dict/list return formats before screen integration |
| Branch data management | Workflows need branch records; no branch-registration screen is mandated | Agree fictional seed branches or another minimal administration path |
| Duplicate prescription medicine lines | Schema and current prescription implementation reject duplicate medicine codes | GUI should combine quantities or reject duplicates before submission |
| Main window ownership | Member 1 and Member 4 coordinate shared GUI files | Agree one screen/navigation pattern; avoid independent edits to shared files |

## 14. Design verification checklist

- [ ] Four layers and their boundaries are explicit.
- [ ] GUI calls services and contains no SQL.
- [ ] One shared Database manager and one shared ApplicationServices graph are used.
- [ ] Domain classes represent the required pharmacy concepts.
- [ ] Medicine inheritance has meaningful overridden behaviour and polymorphic use.
- [ ] Validation is enforced in domain/services and backed by database constraints.
- [ ] Stock is branch-specific and cannot become negative.
- [ ] Prescription statuses and transitions are constrained.
- [ ] Controlled medicine authorisation checks a simulated allow-list.
- [ ] Dispensing is one transaction with rollback on any failure.
- [ ] Low-stock comparison includes quantity equal to reorder level.
- [ ] Data survives application restart.
- [ ] Tests use a temporary database.
- [ ] Open decisions are resolved with the responsible group members before dependent integration.

## 15. Source documents

1. Uganda Christian University, Department of Computing and Technology, **CSC2105 — Object-Oriented Programming Using Python, Advent 2026 Semester Examination**, project brief, pp. 1–3.
2. **Group Development Standard & Technical Agreement: Multi-Branch Campus Pharmacy Inventory, Dispensing and Reporting System**, CSC2105, Advent 2026, Sections 1–26.
3. Repository design evidence inspected for this draft: `database/schema.sql`, `domain/prescription.py`, `services/prescription_service.py` and `README.md` on the `member-1-architecture` branch.

AI-assisted drafting must be reviewed and declared in accordance with the examination's academic-integrity instructions.
