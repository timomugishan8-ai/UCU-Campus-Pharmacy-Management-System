# Requirements Specification
## Multi-Branch Campus Pharmacy Inventory, Dispensing and Reporting System

**Course:** CSC2105 — Object-Oriented Programming Using Python  
**Institution:** Uganda Christian University  
**Semester:** Advent 2026  
**Milestone:** 1 — Requirements and Object-Oriented Design  
**Document owner:** Member 1 — Architecture and Integration Coordinator  
**Status:** Design baseline for group review

---

## 1. Purpose

This document defines the problem, scope, actors, functional and non-functional requirements, business rules, use cases, workflows and traceability for the Multi-Branch Campus Pharmacy Inventory, Dispensing and Reporting System.

It is the requirements baseline for the group's implementation. The system is a Python desktop application using tkinter for its graphical interface and SQLite for persistence. The implementation is constrained to Python's standard library unless the lecturer approves an additional dependency in writing.

## 2. Problem statement

Uganda Christian University Health Services operates a campus pharmacy with more than one dispensing point, such as the Main Campus and a satellite clinic. Medicines may be held at multiple branches, and the quantity available at one branch can differ from the quantity available at another.

The project requires a system that models medicines, branches, branch-specific stock, prescriptions and dispensing. It must prevent invalid medicine data, negative stock, unauthorised dispensing of controlled medicines and partial stock deductions when a multi-line prescription cannot be fully supplied. It must also identify low-stock items at each branch and preserve operational data in SQLite between application sessions.

The proposed application provides a shared desktop interface for pharmacy operations while keeping user-interface code, application workflows, domain rules and database access in separate layers.

## 3. Scope

### 3.1 In scope

- Registering ordinary and controlled medicines.
- Recording medicine code, name, unit price, reorder level and controlled status.
- Representing pharmacy branches and keeping stock separate by branch.
- Receiving stock into a specified branch.
- Creating prescriptions for fictional patient identifiers.
- Recording one or more medicine lines on each prescription.
- Recording the prescription's branch, prescriber code and status.
- Checking a controlled medicine's prescriber code against a simulated authorised-prescriber allow-list at dispensing time.
- Dispensing a prescription as one atomic database operation.
- Rejecting repeat dispensing and dispensing of cancelled prescriptions.
- Viewing low-stock items using the rule quantity less than or equal to reorder level.
- Persisting data in SQLite.
- Providing tkinter screens for the required workflows.
- Testing success paths, rejection paths, rollback and persistence.

### 3.2 Out of scope

The following are not established as requirements by the examination brief or group agreement and are excluded from the baseline unless the group formally agrees to add them:

- Real patient records or real prescriber records.
- Connection to a national health, insurance or electronic medical-record system.
- Online payments, billing integrations or insurance claims.
- Automatic purchasing or supplier integrations.
- Pharmacological advice, dosage recommendations or clinical decision support.
- Multi-branch stock transfers.
- User authentication, role-based access control or audit-log functionality.
- Networked or cloud deployment.

## 4. Stakeholders and actors

| Actor / stakeholder | Role in the system |
|---|---|
| Pharmacy attendant | Uses the desktop application to register medicines, receive stock, create prescriptions, dispense eligible prescriptions and view low-stock records. |
| Authorised prescriber | Is represented by a fictional/simulated prescriber code. The application checks that code against its allow-list when a prescription contains a controlled medicine. The group specification does not require a separate prescriber login or prescriber-facing screen. |
| Pharmacy administrator / project operator | Maintains or loads branch and simulated allow-list data as supported by the agreed implementation. The exact administration workflow is not specified in the baseline. |
| UCU Health Services | Operational context and intended beneficiary of the system. |
| Lecturer / examiner | Assesses the implementation against the examination milestones and demonstration requirements. |

The pharmacy attendant is the primary interactive actor. The authorised prescriber is a represented entity whose code is validated; this does not imply that the prescriber directly operates the application.

## 5. Functional requirements

Requirement IDs are stable identifiers used by the traceability matrix.

### 5.1 Medicine catalogue

- **FR-MED-01:** The system shall register a medicine with a unique medicine code.
- **FR-MED-02:** The system shall store a non-empty medicine name.
- **FR-MED-03:** The system shall store a unit price that is numeric and strictly greater than zero.
- **FR-MED-04:** The system shall store a reorder level that is a non-negative integer. Boolean and fractional values shall be rejected.
- **FR-MED-05:** The system shall distinguish ordinary medicines from controlled medicines.
- **FR-MED-06:** The system shall retrieve registered medicines for use by other workflows.

### 5.2 Branches and stock

- **FR-STK-01:** The system shall represent each pharmacy branch using a unique branch identifier and unique branch name.
- **FR-STK-02:** The system shall maintain stock separately for each medicine at each branch.
- **FR-STK-03:** The system shall receive stock against a medicine code, branch identifier and positive integer quantity.
- **FR-STK-04:** The system shall reject stock receipt for an unknown medicine or branch.
- **FR-STK-05:** The system shall prevent stock quantities from becoming negative.
- **FR-STK-06:** The system shall retrieve stock for a selected branch.

### 5.3 Prescriptions

- **FR-RX-01:** The system shall create a prescription using a fictional, non-empty patient identifier.
- **FR-RX-02:** Each prescription shall be associated with one valid branch.
- **FR-RX-03:** Each prescription shall contain at least one medicine line.
- **FR-RX-04:** Each line shall reference an existing medicine and have a positive integer quantity.
- **FR-RX-05:** The system shall record a prescription status of `pending`, `dispensed` or `cancelled`.
- **FR-RX-06:** The system shall record the prescriber code where supplied. A controlled medicine's authorisation shall be checked against the simulated allow-list at dispensing time.
- **FR-RX-07:** The system shall reject invalid prescription data, including an empty line collection, unknown medicine, invalid quantity or invalid branch.
- **FR-RX-08:** The system shall prevent invalid status transitions. A dispensed or cancelled prescription is final.

### 5.4 Dispensing

- **FR-DSP-01:** The system shall dispense only a prescription that exists and is pending.
- **FR-DSP-02:** For every controlled medicine on a prescription, the system shall verify that the prescriber code is on the simulated authorised-prescriber allow-list.
- **FR-DSP-03:** The system shall not require the controlled-medicine allow-list check for ordinary medicines.
- **FR-DSP-04:** The system shall verify sufficient stock for every prescription line at the prescription's branch.
- **FR-DSP-05:** The system shall reduce all relevant stock quantities and change the prescription status to `dispensed` within one database transaction.
- **FR-DSP-06:** If any dispensing check or write fails, the system shall roll back all stock reductions and leave the prescription pending.
- **FR-DSP-07:** The system shall reject repeat dispensing of a dispensed prescription.
- **FR-DSP-08:** The system shall reject dispensing of a cancelled prescription.

### 5.5 Low-stock reporting

- **FR-LOW-01:** The system shall identify low-stock records where branch stock quantity is less than or equal to the medicine's reorder level.
- **FR-LOW-02:** The system shall calculate low-stock status separately for each branch.
- **FR-LOW-03:** The system shall support viewing low-stock records for one branch or across branches, as provided by the agreed service interface.

### 5.6 User interface and persistence

- **FR-UI-01:** The tkinter application shall provide screens or equivalent views for registering medicines, receiving stock, creating prescriptions, dispensing prescriptions and viewing low-stock items.
- **FR-UI-02:** Every screen shall receive its parent widget and the shared application-services object using the `Screen(parent, services)` constructor contract.
- **FR-UI-03:** GUI callbacks shall call application services and shall not execute SQL or open their own database connections.
- **FR-UI-04:** The GUI shall display understandable success and validation/application error messages and refresh relevant displays after successful operations.
- **FR-DB-01:** The system shall persist medicines, branches, stock and prescription data in SQLite.
- **FR-DB-02:** Saved data shall remain available after the application is closed and reopened.
- **FR-DB-03:** Database access shall use parameterised SQL and enabled foreign-key enforcement.
- **FR-DB-04:** Tests shall use a separate temporary/test database rather than the live demonstration database.

## 6. Non-functional requirements

- **NFR-01 — Usability:** Screens shall use clear labels, straightforward data entry and understandable feedback for successful and rejected operations.
- **NFR-02 — Data integrity:** Validation shall exist beyond the GUI. Domain/service validation and SQLite constraints shall protect important rules.
- **NFR-03 — Transaction reliability:** Dispensing shall be all-or-nothing; no partial stock deduction shall remain after a failed dispense.
- **NFR-04 — Maintainability:** The application shall follow the agreed four-layer architecture and the agreed repository structure.
- **NFR-05 — Separation of concerns:** GUI, services, domain and repositories shall have distinct responsibilities and shall not bypass their defined boundaries.
- **NFR-06 — Portability:** The solution shall use Python 3, tkinter and SQLite, with standard-library modules unless an additional dependency is approved.
- **NFR-07 — Privacy:** Only fictional patient identifiers and simulated prescriber data shall be used. Real patient or prescriber information shall not be stored.
- **NFR-08 — Testability:** Business rules and persistence behaviour shall be testable without launching the GUI; tests shall use isolated test data.
- **NFR-09 — Traceability:** Requirements shall map to design components and test evidence.
- **NFR-10 — Explainability:** Each member shall understand and be able to explain their own contribution and relevant design decisions during oral defence.

## 7. Business rules and invariants

An invariant is a condition that must remain true throughout the system's operation.

| ID | Rule / invariant |
|---|---|
| BR-01 | A medicine code is unique and non-empty. |
| BR-02 | A medicine name is non-empty. |
| BR-03 | A medicine unit price is numeric and strictly greater than zero. |
| BR-04 | A reorder level is an integer greater than or equal to zero; booleans and fractional values are invalid. |
| BR-05 | A branch identifier and branch name are unique. |
| BR-06 | Stock is identified by the medicine-branch pair; quantities at different branches are independent. |
| BR-07 | Stock quantity is an integer greater than or equal to zero. |
| BR-08 | A stock receipt quantity is a positive integer. |
| BR-09 | A prescription has a fictional, non-empty patient identifier, one valid branch and at least one valid line. |
| BR-10 | Each prescription line references an existing medicine and has a positive integer quantity. |
| BR-11 | A prescription status is one of `pending`, `dispensed` or `cancelled`. |
| BR-12 | Only a pending prescription may be dispensed or cancelled. Dispensed and cancelled states are final. |
| BR-13 | Controlled medicines require an authorised simulated prescriber code at dispensing; ordinary medicines do not. |
| BR-14 | Dispensing reduces stock only at the prescription's branch. |
| BR-15 | Dispensing is atomic: all stock changes and the status update commit together or all roll back. |
| BR-16 | Low stock is quantity less than or equal to reorder level, evaluated per branch. |
| BR-17 | No real patient or prescriber information is stored. |

## 8. Use cases

### UC-01 — Register medicine

**Primary actor:** Pharmacy attendant  
**Preconditions:** The application is open.  
**Main flow:**
1. The attendant opens the medicine-registration screen.
2. The attendant enters medicine code, name, unit price, reorder level and medicine type.
3. The screen converts input values and calls `MedicineService.register_medicine(medicine)`.
4. The service/domain validates the medicine.
5. The repository stores the medicine.
6. The GUI reports success and refreshes the medicine display.

**Alternative / rejection flows:** Reject a blank code/name, duplicate code, non-numeric or non-positive price, and negative, fractional or boolean reorder level.  
**Postcondition:** A valid medicine is persisted and can be selected by stock and prescription workflows.

### UC-02 — Receive stock

**Primary actor:** Pharmacy attendant  
**Preconditions:** The medicine and branch exist.  
**Main flow:**
1. The attendant opens the receive-stock screen.
2. The attendant selects a medicine and branch and enters a quantity.
3. The screen calls `StockService.receive_stock(medicine_code, branch_id, quantity)`.
4. The service validates the positive integer quantity.
5. The repository records the receipt for that medicine-branch pair.
6. The GUI reports success and refreshes branch stock.

**Alternative / rejection flows:** Reject an unknown medicine, unknown branch, zero/negative quantity, fractional quantity or boolean quantity.  
**Postcondition:** Only the selected branch's stock is increased.

### UC-03 — Create prescription

**Primary actor:** Pharmacy attendant  
**Preconditions:** The branch and all selected medicines exist.  
**Main flow:**
1. The attendant opens the create-prescription screen.
2. The attendant enters a fictional patient identifier, selects a branch, optionally enters the prescriber code and adds one or more medicine lines.
3. The screen calls `PrescriptionService.create_prescription(patient_identifier, branch_id, prescriber_code, lines)`.
4. The service validates the patient identifier, branch and line collection and verifies referenced records.
5. The repository stores the prescription and its lines with `pending` status.
6. The GUI displays the new prescription identifier and details.

**Alternative / rejection flows:** Reject blank patient identifier, unknown branch, empty lines, unknown medicine, duplicate medicine line or non-positive/non-integer quantity.  
**Postcondition:** A pending prescription and its lines are persisted.

### UC-04 — Dispense prescription

**Primary actor:** Pharmacy attendant  
**Preconditions:** The prescription exists and is pending.  
**Main flow:**
1. The attendant opens the dispense screen and selects a prescription.
2. The screen calls `PrescriptionService.dispense_prescription(prescription_id)`.
3. The service begins one database transaction and loads the prescription, lines and medicines.
4. It verifies the prescription is pending.
5. It checks the simulated prescriber allow-list for controlled medicines.
6. It verifies sufficient stock for every line at the prescription's branch.
7. It conditionally reduces each stock quantity and conditionally changes the prescription status to `dispensed`.
8. The transaction commits once all operations succeed.
9. The GUI reports success and refreshes the prescription and stock displays.

**Alternative / rejection flows:** Unknown prescription, already dispensed, cancelled, unauthorised prescriber, unknown medicine or insufficient stock. If any step fails, the transaction rolls back; no line is partially deducted and the prescription remains pending.  
**Postcondition:** On success, all relevant stock is reduced and the prescription is dispensed. On failure, persistent state is unchanged by the attempted dispense.

### UC-05 — View low stock

**Primary actor:** Pharmacy attendant  
**Preconditions:** Branches, medicines and stock records have been loaded.  
**Main flow:**
1. The attendant opens the low-stock screen.
2. The attendant selects a branch or the all-branches option.
3. The screen calls `StockService.get_low_stock(branch_id=None)` or the agreed `ReportService.get_low_stock_report(branch_id=None)`.
4. The service/repository retrieves records whose quantity is less than or equal to reorder level.
5. The GUI displays the results.

**Alternative flow:** If no items meet the condition, the GUI displays a clear empty-state message.  
**Postcondition:** The attendant sees low-stock records for the requested scope.

## 9. Use-case workflow summary

### Stock receipt

`Select medicine + branch -> enter quantity -> service validation -> repository update -> refresh branch stock`

### Prescription creation

`Enter fictional patient ID -> select branch -> add one or more medicine lines -> service validation -> persist prescription + lines -> show pending prescription`

### Dispensing

`Select pending prescription -> begin transaction -> validate status -> validate controlled-prescriber allow-list -> check every branch stock line -> conditional stock reductions -> conditional status update -> commit`

If any dispensing step fails:

`Failure -> rollback entire transaction -> prescription remains pending -> no stock reduction remains`

### Low-stock review

`Select branch / all branches -> retrieve branch-specific stock and reorder levels -> apply quantity <= reorder level -> display results`

## 10. User-interface requirements

The agreed tkinter interface includes these screens:

| Screen / view | Main responsibility | Service boundary |
|---|---|---|
| Main window / navigation | Application shell and navigation between feature screens | Receives the shared `ApplicationServices` object |
| Register medicine | Collect medicine details and display validation feedback | `medicine_service.register_medicine(medicine)` and medicine retrieval methods |
| Receive stock | Select medicine and branch, enter quantity, show updated stock | `stock_service.receive_stock(...)`, `get_branch_stock(...)` |
| Create prescription | Collect fictional patient identifier, branch, prescriber code and medicine lines | `prescription_service.create_prescription(...)` |
| Dispense | Select a prescription and request dispensing; show result or expected rejection | `prescription_service.dispense_prescription(...)`, `get_prescription(...)` |
| Low stock | Display low-stock items for a branch or all branches | `stock_service.get_low_stock(...)` and/or `report_service.get_low_stock_report(...)` |

Branch records and simulated authorised-prescriber entries must exist for the workflows to operate. The baseline requires these records in the data model; it does not prescribe a separate branch-management or prescriber-management GUI screen.

## 11. Service interface baseline

The following public service methods are fixed by the group agreement. Do not rename them or change their parameter meanings/return formats without group agreement.

| Service | Agreed public methods |
|---|---|
| `MedicineService` | `register_medicine(medicine)`, `get_all_medicines()`, `get_medicine_by_code(medicine_code)` |
| `StockService` | `receive_stock(medicine_code, branch_id, quantity)`, `get_branch_stock(branch_id)`, `get_low_stock(branch_id=None)` |
| `PrescriptionService` | `create_prescription(patient_identifier, branch_id, prescriber_code, lines)`, `dispense_prescription(prescription_id)`, `cancel_prescription(prescription_id)`, `get_prescription(prescription_id)` |
| `ReportService` | `get_low_stock_report(branch_id=None)`, `get_branch_stock_summary()` |

The `ApplicationServices` facade receives the shared Database manager, constructs the repository/service graph and exposes `medicine_service`, `stock_service`, `prescription_service` and `report_service`. The exact constructor wiring is an integration decision to be agreed with Member 5, taking account of the existing `PrescriberRepository` used by the prescription feature.

## 12. Requirements traceability matrix

| Requirement group | Design element(s) | Planned verification evidence |
|---|---|---|
| FR-MED-01–06 / BR-01–04 | `Medicine`, `OrdinaryMedicine`, `ControlledMedicine`; `MedicineService`; `MedicineRepository`; `medicines` table; register-medicine screen | Valid registration; duplicate code; blank name; invalid price; invalid reorder level; both medicine types |
| FR-STK-01–06 / BR-05–08 | `Branch`, `Stock`; `StockService`; `BranchRepository`, `StockRepository`; `branches` and `stock` tables; receive-stock screen | Branch uniqueness; separate branch quantities; successful receipt; unknown references; invalid quantity; no negative stock |
| FR-RX-01–08 / BR-09–12 | `Prescription`, `PrescriptionLine`; `PrescriptionService`; `PrescriptionRepository`; `prescriptions` and `prescription_lines` tables; create-prescription screen | Single/multi-line creation; empty lines; unknown medicine/branch; invalid quantity; status transitions |
| FR-DSP-01–08 / BR-13–15 | `PrescriptionService`; `PrescriberRepository`; `StockRepository`; `Database` transaction manager; dispense screen | Successful dispense; unauthorised prescriber; ordinary medicine allowed; insufficient-stock rollback; repeat/cancelled dispense rejected |
| FR-LOW-01–03 / BR-16 | `StockService` / `ReportService`; stock repository query; low-stock screen | Equal-to-threshold included; below included; above excluded; branch filter |
| FR-UI-01–04 | `MainWindow`, shared screen base and feature screens; `ApplicationServices` | Screen navigation; service calls; readable messages; refreshed displays; no SQL in GUI |
| FR-DB-01–04 / NFR-02, 03, 07, 08 | `Database`; schema; repositories; temporary test database | Schema creation; foreign-key enforcement; parameterised operations; persistence after restart; isolated tests |
| NFR-01, 04–06, 09–10 | Four-layer architecture, coding conventions, documentation and test plan | Architecture review; import/interface checks; standard-library check; traceability and viva explanation |

## 13. Assumptions and decisions requiring group confirmation

1. **Branch creation:** The system must represent branches, but the baseline does not specify a dedicated branch-registration screen. The initial branch records may be loaded as fictional seed data or maintained through an agreed administrative mechanism.
2. **Prescriber allow-list:** The allow-list is simulated. The group must use fictional codes only. The schema currently contains `authorised_prescribers(prescriber_code, prescriber_name)`; whether an explicit active/authorised flag is needed should be agreed with Member 5 because the group agreement describes an active/authorised status.
3. **Prescription line uniqueness:** The current schema uses `UNIQUE (prescription_id, medicine_code)`. The current domain/service implementation rejects duplicate medicine lines. The GUI should combine quantities for the same medicine before submission or reject duplicate entries consistently.
4. **Medicine inheritance:** The agreed OOP design is a common `Medicine` base class with `OrdinaryMedicine` and `ControlledMedicine` subclasses. The existing database schema stores the distinction as `is_controlled`; the repository/domain mapping must preserve the common object interface.
5. **Return formats:** The group agreement fixes public method names but says return formats must be documented. Member 5 and the feature owners must confirm the exact formats before the GUI is integrated.
6. **Branch identifiers:** The current schema uses an integer auto-incrementing branch ID and unique branch name. Screens should use the ID internally and display the branch name to the user.

These are coordination points, not permission to silently change the shared schema or public interfaces.

## 14. Acceptance criteria for the design baseline

The design package is ready for group review when:

- All mandatory examination workflows are represented.
- Functional and non-functional requirements have stable identifiers.
- Business rules and invariants are explicit.
- The four-layer architecture and responsibilities are consistent with the group agreement.
- The domain model demonstrates encapsulation, inheritance, overriding and polymorphism.
- The database outline matches the agreed entities and current schema fields.
- GUI screens use the shared services object and contain no SQL.
- Atomic dispensing and rollback are clearly specified.
- Requirements trace to design elements and planned tests.
- Open integration decisions are visible and assigned for group confirmation.

## 15. Source documents

1. Uganda Christian University, Department of Computing and Technology, **CSC2105 — Object-Oriented Programming Using Python, Advent 2026 Semester Examination**, project brief, pp. 1–3.
2. **Group Development Standard & Technical Agreement: Multi-Branch Campus Pharmacy Inventory, Dispensing and Reporting System**, CSC2105, Advent 2026, Sections 1–26.

This document was prepared from the supplied examination brief, group technical agreement and the repository files inspected for the current design baseline. AI-assisted drafting must be reviewed and declared in accordance with the examination's academic-integrity instructions.