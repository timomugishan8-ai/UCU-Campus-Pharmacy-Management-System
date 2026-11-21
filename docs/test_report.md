# Test Report

UCU Campus Pharmacy Management System
CSC2105 - Object-Oriented Programming Using Python

## Test command

```powershell
python -m unittest discover -s tests -v
```

## Result

- Tests run: 120
- Result: OK
- All tests passed.
- `git diff --check`: passed.

## Test coverage summary

- `tests/test_medicine.py`: medicine domain validation and behaviour.
- `tests/test_stock.py`: stock domain validation and behaviour.
- `tests/test_prescription.py`: prescription creation and state transitions.
- `tests/test_dispensing.py`: atomic dispensing, authorisation and rollback.
- `tests/test_member5_database.py`: database schema, repositories and integration workflows.
- `tests/test_cindy_stock_report.py`: branch stock summary and low-stock reporting.
- `tests/test_cindy_stock_service.py`: StockService validation and behaviour.
- `tests/test_member2_gui.py`: GUI-related unit tests.

## Database and transaction tests

Verified with temporary SQLite databases:
- Schema creation and all six tables.
- Foreign-key enforcement.
- Medicine, branch and stock repository operations.
- Branch-specific stock quantities.
- Stock increase and decrease.
- Conditional decrease prevents negative stock.
- Prescription creation and retrieval.
- Failed shared transaction rollback.
- Successful shared transaction commit.
- Repeated conditional dispensing update returns zero.
- Seed data idempotency.
- Low-stock report with and without branch filter.
- Branch stock summary including empty branches.
- Quantity equal to reorder level is treated as low stock.

## Service tests

Verified:
- Medicine registration and lookup.
- Stock receipt validation.
- Unknown medicine and unknown branch rejection.
- Positive integer quantity validation.
- Decimal, text, boolean, zero and negative quantity rejection.
- Branch stock retrieval.
- Low-stock retrieval for one branch and all branches.
- ReportService delegation and branch summary.

## GUI and application checks

- `main.py` was launched successfully.
- The Tkinter application ran for 5 seconds without startup errors.
- `ApplicationServices` was constructed successfully.
- MainWindow and all feature screens were constructed successfully.
- GUI service calls were exercised through service-level workflow tests.

## Known limitations

- GUI tests are mostly structural and service-level; full manual GUI interaction was not automated.
- `docs/test_report.md` was previously empty and has now been populated with the current test results.
- Application entry point and all main workflows are implemented, but final manual GUI walkthrough is still recommended.
- Real patient data is not used; only fictional identifiers and simulated prescriber codes are used.