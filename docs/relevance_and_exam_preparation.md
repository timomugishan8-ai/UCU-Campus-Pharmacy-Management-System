# Project Relevance, Study Guide and Exam Preparation

**Course:** CSC2105 — Object Oriented Programming (Python)
**Project:** UCU Campus Pharmacy Management System
**Audience:** the whole group (all five members) preparing for the project defence
**Last updated:** 2026-11-20

---

## 1. Why this project matters (relevance)

### 1.1 The real-world problem it solves

A campus pharmacy that manages medicines "in one head" or in a paper book makes four
expensive mistakes:

1. **Medication errors.** Without a catalogue that distinguishes ordinary from
   controlled medicines, a dispenser can hand out a controlled drug with no
   prescriber record. Our system refuses that: `ControlledMedicine.
   requires_prescriber_code()` returns `True` and the dispensing rule demands an
   authorised prescriber code before the prescription can be created/dispensed.
2. **Stock-outs of essential medicine.** Shelves run empty because nobody notices
   quantities falling below the reorder level. Our low-stock report
   (`quantity <= reorder_level`) tells the pharmacist what to reorder, per branch.
3. **Wrong-branch inventory.** A medicine exists "somewhere" but not where the
   patient is standing. Stock in this system is always
   `(medicine_code, branch_id)` — there is no global quantity to hide behind.
4. **Controlled-drug accountability.** Regulators require an audit trail for
   narcotics/psychotropics. Prescriptions carry status
   (`pending → dispensed/cancelled`), and a dispensed prescription can never be
   dispensed twice.

### 1.2 Why it matters for UCU

UCU runs a campus pharmacy (and satellite services) where students and staff are
served quickly at a counter. A desktop tool with a cashier-style sidebar —
Dashboard, Register Medicine, Receive Stock, Prescriptions, Dispense Medicine,
Low Stock — fits how a single-operator counter actually works. Patient data is
kept to a **fictional identifier only** (no patient accounts, no passwords), which
is both an exam requirement and the right privacy posture for records that never
hold real people's data.

### 1.3 Why it matters for CSC2105 (the exam angle)

The project is a **working demonstration of the OOP pillars inside a layered
architecture**, not a toy script:

| Exam theme | Where it lives in this codebase |
|---|---|
| Encapsulation | Read-only properties backed by private fields (`domain/medicine.py`, `branch.py`, `stock.py`); SQL hidden behind repositories |
| Abstraction | `Medicine(ABC)` with `@abstractmethod requires_prescriber_code()`; the `ApplicationServices` facade hides construction wiring |
| Inheritance | `OrdinaryMedicine` / `ControlledMedicine` extend `Medicine`; all screens extend `BaseScreen` |
| Method overriding | Each subclass answers the same method signature differently |
| Polymorphism | `Medicine.from_dict()` builds the right subtype from `is_controlled`; the dispensing rule calls `requires_prescriber_code()` **without knowing the subclass** |
| Composition | Services *have* repositories; the facade *has* services; screens *have* services |
| Exception design | `ValueError`-derived hierarchies (`MedicineError`, `StockError`, `PrescriptionError`) so one GUI `except ValueError` boundary stays honest |
| Design-by-contract | Interface contract fixes method names, argument shapes and return formats before implementation |
| Testing | 120+ `unittest` tests, including GUI tests with mocked dialogs |
| Team engineering | Five member branches, pull requests, task log, conflict resolution, no caches in Git |

### 1.4 Professional practice demonstrated

Agile-style division of labour with written contracts, PR-based review, a personal
**task log** as contribution evidence, and separation of concerns so five people
could build the same system in parallel without stepping on each other — this is
the part employers actually look at.

---

## 2. How to prepare and understand the project

### 2.1 Read the documentation in this order (~1 hour)

1. `README.md` — overview, members, folder structure, how to run.
2. `docs/requirements.md` — the problem, the 5 use cases (UC-01…UC-05), business rules.
3. `docs/design.md` — four-layer architecture, domain model, OOP section (§6),
   agreed service contracts (§4.3).
4. `docs/database_design.md` — the 6 tables and the integration contract per member (§11).
5. `docs/interface_contract.md` — who owns which method, exact signatures.
6. `docs/test_report.md` — what the tests prove.
7. `task_log.md` — **every member's entry; know your own by heart, skim the rest.**
8. `docs/diagrams/*.mmd` — architecture, class diagram, ERD, workflows.

### 2.2 The architecture in 30 seconds (memorise this)

```text
User → Tkinter screen → Feature service → Domain object → Repository → SQLite
         (GUI layer)     (services layer)  (domain layer)  (database layer)
```

| Layer | Does | Never does |
|---|---|---|
| **GUI** (`gui/`, `app/base_screen.py`) | Collect input, show tables/messages, call services, refresh | Execute SQL, open its own DB connection |
| **Services** (`services/`, facade `app/services.py`) | Coordinate use cases, validate, run transactions | Import tkinter, embed SQL |
| **Domain** (`domain/`) | Hold rules (never-negative stock, positive price, controlled → prescriber) | Import tkinter, open DB connections |
| **Repositories** (`database/repositories/`) | Parameterised SQL, row↔object mapping | Commit/rollback (the *service* owns the transaction), display UI |

Dependency direction: **GUI → services → domain/repositories → database.**
Domain objects depend on nothing — that is why all 120+ tests run without a window.

### 2.3 The data model (6 tables)

`medicines`, `branches`, `stock`, `prescriptions`, `prescription_lines`,
`authorised_prescribers`.
Key facts: stock is per branch; `stock` has a composite key
`(medicine_code, branch_id)`; CHECK constraints (`price > 0`, `reorder_level >= 0`,
`quantity >= 0`) **mirror** the domain validation — the same rule is enforced twice
on purpose (defence in depth).

### 2.4 The five use cases (be able to narrate each end-to-end)

- **UC-01 Register medicine** — form → `Medicine.create()` (picks subclass) →
  `MedicineService.register_medicine()` → duplicate check → repository INSERT.
- **UC-02 Receive stock** — dropdowns (branches from `get_branch_stock_summary()` so
  empty branches appear) → `StockService.receive_stock()` → quantity increases.
- **UC-03 Create prescription** — fictional patient + branch + prescriber + lines;
  controlled lines force an authorised prescriber code.
- **UC-04 Dispense** — one SQLite transaction: validate status `pending`, check each
  branch stock (`can_fulfil`), decrease, set `dispensed`. Any failure → rollback,
  nothing half-done.
- **UC-05 Low stock** — `quantity <= reorder_level`, aggregated SQL lives in
  `StockRepository`, `ReportService` only delegates.

### 2.5 Run it yourself (hands-on prep)

```bash
python -m unittest discover -s tests -v     # full test suite (expect 120+ OK)
python main.py                              # launch the app
```

In the app, walk the loop once: **Dashboard → Register Medicine (try price `0` →
error dialog) → Register again with same code (duplicate error) → Receive Stock →
Prescriptions → Dispense Medicine → Low Stock.** If you can narrate what each
click does *in which layer*, you are ready.

### 2.6 OOP concept → file map (prepare one concrete example per pillar)

- **Encapsulation:** `Stock.quantity` is read-only; it changes only via
  `receive()` / `decrease()`, so it can never go negative.
- **Abstraction:** `Medicine` cannot even be instantiated (`TypeError`), because
  `requires_prescriber_code()` is `@abstractmethod`.
- **Inheritance + overriding:** `OrdinaryMedicine` returns `False`,
  `ControlledMedicine` returns `True` — same signature, different behaviour.
- **Polymorphism:** `prescription.requires_authorised_prescriber(medicines)` iterates
  lines and calls `medicine.requires_prescriber_code()` — it never checks
  `isinstance`, and adding a new medicine type would not change that code.
- **Composition:** `ApplicationServices` wires repositories into services once;
  every screen receives the same facade instance.
- **Exceptions:** why `MedicineError(ValueError)`? Because every screen's boundary
  is `except ValueError` — a new domain error is automatically caught there.

### 2.7 Who owns what (so you can answer scope questions honestly)

| Member | Scope |
|---|---|
| Timothy (1) | Architecture, design docs, diagrams, `ApplicationServices` facade, `main.py`, integration |
| Mulisa (2) | `Medicine`/`OrdinaryMedicine`/`ControlledMedicine`, `Branch`, `Stock`, `MedicineService`, Register Medicine + Receive Stock screens |
| Conrad (3) | `Prescription`/`PrescriptionLine`, `PrescriptionService`, dispensing transaction, Create Prescription + Dispense screens |
| Matilda (4) | GUI coordination, `main_window` navigation, `BaseScreen`, Low Stock + Dashboard screens |
| Cindy (5) | Connection/schema/seed, repositories, `StockService`, `ReportService`, test report, documentation |

---

## 3. Questions we must prepare for

> Each question includes a short pointer to where the answer lives. **Everyone must
> be able to answer §3.1–§3.3; then master your own row of §3.6.**

### 3.1 OOP fundamentals (asked of everyone)

1. **What are the four layers and what may each layer never do?**
   → §2.2 table; `docs/design.md` §3.1.
2. **Show me encapsulation in this codebase — and what breaks without it?**
   → Read-only `Stock.quantity`; without it, `quantity = -5` becomes representable.
3. **Difference between inheritance and polymorphism here? Give one example of each.**
   → Inheritance: `ControlledMedicine(Medicine)`. Polymorphism: the dispensing rule
   calling `requires_prescriber_code()` on unknown subtype.
4. **What does an abstract class give you that a normal base class does not?**
   → `Medicine(ABC)` prevents instantiation and forces subclasses to override the
   abstract method — proven by `test_medicine_base_cannot_be_instantiated`.
5. **Where exactly is method overriding used, and how do you know?**
   → Same signature, different body in both subclasses; `super()` used in screens.
6. **Why do your exceptions derive from `ValueError`?**
   → One GUI error boundary (`except ValueError`) catches all domain errors without
   ever swallowing unrelated exceptions... and `TypeError` for wrong object type.
7. **Is this inheritance or composition between a screen and a service? Explain.**
   → Composition: the screen *receives* `services` and delegates to it.
8. **What is the difference between `@abstractmethod` and a method that just
   `raise NotImplementedError`?**
   → ABC enforces it at *instantiation time* by the metaclass; you cannot create
  an accidentally half-implemented base — the interpreter refuses it.

### 3.2 Architecture and design

9. **Why can't the GUI run SQL? What concrete bug does that rule prevent?**
   → Layer contract; prevents duplicated rules, untestable logic, injection points
   multiplying across six screens.
10. **Why does the same validation exist in the domain *and* in the CHECK
    constraints?**
    → Defence in depth: domain gives a friendly message; DB guarantees integrity
    even for rows written by future code paths.
11. **What is the `ApplicationServices` facade and why does it exist?**
    → One object owning shared `Database`, repositories and services; screens get
    one constructor argument instead of five; swappable in tests.
12. **Who owns the transaction — repository or service? Why?**
    → The service. Repositories accept an optional shared connection and never
    commit/rollback, so multi-table operations commit **once** or roll back **once**.
13. **Where is the aggregate SQL for reports, and why there?**
    → `StockRepository` (`get_branch_stock_summary`, `get_low_stock_report`);
    `ReportService` delegates only — SQL knowledge stays in one layer.
14. **Why are branch dropdowns built from the summary and not from low-stock rows?**
    → A branch with no low-stock items would vanish from the filter. This was a
    recorded group decision (Matilda/Cindy, 2026-11-19).
15. **How do you add a new screen? What must it conform to?**
    → `Screen(parent, services)` (i.e. inherit `BaseScreen`), optional `refresh()`
    hook called by `show_screen()`, register it in `gui/main_window.py`.

### 3.3 Data and business rules

16. **State the low-stock rule. Where is it evaluated?**
    → `quantity <= reorder_level`; evaluated in SQL (`StockRepository`) for reports
    and in `Stock.is_low_stock()` for the domain view.
17. **Why is stock never global — what breaks if we drop `branch_id`?**
    → Two branches would share one counter; receiving at A would falsely stock B.
18. **How are duplicate medicine codes prevented — and what if two users submit the
    same code at the same instant?**
    → Service pre-check (`repository.exists()`) + DB `UNIQUE` + `IntegrityError`
    converted to `DuplicateMedicineError` as the race backstop.
19. **How does the system know a medicine needs a prescriber? What happens if we
    add a third subtype next term?**
    → Polymorphic `requires_prescriber_code()`; a new subclass needs **zero**
    changes to dispensing logic — that is the open-closed benefit.
20. **Can a dispensed prescription be dispensed again? Cancelled? Why?**
    → No: status is no longer `pending`, and status transitions are validated in
    the domain (`domain/prescription.py`).
21. **What happens halfway through a dispensing if stock is short?**
    → Nothing persists: validation/`can_fulfil` failure raises, the transaction
    rolls back — patient, prescription and stock all remain as before.
22. **What is stored about a patient? Do patients have accounts?**
    → Only `patient_identifier` (fictional). No accounts, no passwords, no
    authentication anywhere — this is a pharmacy-counter tool; doctors appear only
    as rows in `authorised_prescribers`.

### 3.4 Testing and quality

23. **How do you run the tests, and what is the current result?**
    → `python -m unittest discover -s tests -v` → all green (120+ tests).
24. **How do you test a tkinter screen without clicking it?**
    → Construct the real screen on a withdrawn root, drive its handlers directly,
    and `unittest.mock.patch` the `messagebox` functions so no dialog blocks the run.
25. **Give an example of a test that proves a *rule*, not just a feature.**
    → `test_decrease_below_zero_raises_and_changes_nothing` — attempts 11 from 10,
    asserts `InsufficientStockError` **and** that quantity is still 10.
26. **What is the riskiest part of this system and how is it tested?**
    → The dispensing transaction: success, insufficient stock, wrong status, and
    rollback-to-zero cases in Conrad's tests.
27. **Why mock the message boxes — what would happen without mocking?**
    → A real dialog would hang an unattended/CI run; tests must never wait for a
    human.

### 3.5 Git, process and teamwork

28. **What is your branching and review workflow?**
    → Feature branches per member (`member-N-*`), never direct commits to `main`,
    PR before merge, task log updated, full suite green before any push.
29. **How did five people edit the same repository without chaos?**
    → The interface contract froze shared signatures first; each member's file set
    was disjoint; conflicts (e.g. `task_log.md`) were resolved by **keeping every
    member's entry**.
30. **Why were 30 `__pycache__` files removed from Git? What rule does that
    reflect?**
    → Generated artefacts must never be tracked (agreement); they caused phantom
    diffs on everyone's status.
31. **Where is your personal contribution evidence?**
    → `task_log.md` entries + your commits/PRs (PRs #7 and the navigation
    follow-up for Mulisa; #2-style entries for others).
32. **You rewrote commit messages after pushing — what did that require and how
    was it made safe?**
    → A tagged backup, content-identical verification (`git diff` empty) and
    `--force-with-lease`, done **before** any PR existed so no reviewer was affected.

### 3.6 Member-specific deep-dive questions

| Member | Prepare these |
|---|---|
| **Mulisa (2)** | Why an ABC for `Medicine`? Walk through `register_medicine()` step by step. Why return `Medicine` objects instead of dicts? Why is `is_controlled` derived from a method and not stored twice? How does `from_dict()` choose the subclass? Why does `receive_stock` screen source branches from the summary? |
| **Conrad (3)** | Explain the dispensing transaction line by line. Why can't a cancelled prescription be dispensed? How do you model one-to-many prescription↔lines? Why capture `prescriber_code` at creation? |
| **Matilda (4)** | What is `BaseScreen` and what does the optional `refresh()` hook do? How do you keep the GUI dumb (no business rules)? How were six screens kept visually consistent? |
| **Cindy (5)** | Why parameterised SQL only? Why don't repositories commit? How is the low-stock aggregate written, and why `LEFT JOIN` so zero-stock branches appear in the summary? |
| **Timothy (1)** | Justify the four layers and the dependency direction. How does the facade support parallel work? How was the interface contract used to unblock members before code existed? |

### 3.7 Likely "pressure" questions (what-if and criticism)

33. **What is missing / what would you add with more time?**
    → Honest answer: staff authentication with roles, an audit trail for controlled
    dispensing, expiry-date tracking, barcode/input masks, multi-user concurrency
    beyond SQLite, and printable reports. (Do **not** claim these exist.)
34. **Why SQLite instead of PostgreSQL? Is that production-ready?**
    → Exam constraint: standard library only, zero setup, file-based; the repository
    layer isolates SQL, so swapping engines touches one layer.
35. **Why tkinter instead of a web app?**
    → Same constraint; plus the actual use case is a single counter operator.
36. **Isn't `except ValueError` too broad?**
    → It is broad *by design at the screen boundary* but every raised subtype
    (`MedicineError`, `StockError`, `PrescriptionError`) carries a user-meaningful
    message; `TypeError`/programming errors still surface loudly.
37. **What happens when two dispensers use the app simultaneously?**
    → SQLite single-file locking plus transactional dispensing keeps stock correct;
    high-concurrency multi-user scale is explicitly out of scope (stated in
    requirements §3.2).
38. **How do you know the tests are not just green but *meaningful*?**
    → They assert rules and invariants (never-negative, boundary `<=`,
    subtype identity, rollback), not only "no exception raised".
39. **If a requirement changed (e.g. a medicine can be controlled at one branch
    only), what would you modify?**
    → Domain first (rule + tests), then schema if persistent, then service
    orchestration — GUI last. Say this order confidently; it shows you know the
    layers.
40. **Where is the code you are most proud of / most responsible for?**
    → Prepare a 60-second tour of your own files with one design decision and one
    trade-off (see §3.6).

---

## 4. One-page cheat sheet

- **Stack:** Python 3 · tkinter (8.6) · SQLite · `unittest` — **100% standard library**.
- **Structure:** 4 layers · 6 tables · 6 screens · 5 use cases · 5 members · 120+ tests.
- **Entry points:** `python main.py` (app) · `python -m unittest discover -s tests` (tests).
- **Rule boundaries:** price `> 0` · reorder `>= 0` · quantity `>= 0` ·
  low stock `quantity <= reorder_level` · stock never negative ·
  dispensed once only · duplicate codes impossible.
- **Controlled medicines** → `requires_prescriber_code()` → authorised prescriber required.
- **Layer law:** GUI never touches SQL · services never import tkinter ·
  domain never opens connections · repositories never commit.
- **Our process:** feature branch → tests green → commit (action verbs) → push →
  PR → task log → merge by review, never on `main`.
- **Privacy:** fictional patient identifiers only; no accounts, no real data.
