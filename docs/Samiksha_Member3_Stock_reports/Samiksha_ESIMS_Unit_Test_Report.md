# Unit Test Report

## Stock module

| | |
|---|---|
| Project | ESIMS, Team 8 |
| Section owner | Samiksha B N (Stock module, ESIMS-18 to ESIMS-25) |
| Date | 06-11-2026 |
| Environment | Windows 11, Python 3.13, Django 5.2.18, SQLite and PostgreSQL |

### Scope
Unit-level tests of stock logic: pure stock arithmetic, over-sale rule, low-stock threshold, transaction ID rules and service edge cases. No UI is needed for these.

### Results
| Test file | Focus | Tests | Passed |
|---|---|---|---|
| `transactions/test_stock_logic.py` | Pure calculations, threshold, ledger consistency | 15 | 15 |
| `transactions/tests.py` | Stock services, forms, edge cases | 25 | 25 |

Whole stock app run: 76 tests, 76 passed, 0 failed, 0 errors (run time 25.8 s). Output: `evidence/stock_tests.txt` (SQLite) and `evidence/stock_tests_postgres.txt` (PostgreSQL).

### Unit test cases (STP IDs)
| Test ID | Req | Scenario | Status |
|---|---|---|---|
| UT-STOCK-01 | NFR-006 | Stock calculation independent of UI | Pass |
| UT-STOCK-02 | FR-012 | Reject over-sale (sale of 6 with stock 5) | Pass |
| UT-STOCK-03 (new) | FR-010 / FR-011 / FR-013 | Edge cases: deleted product, hidden DB error, text form | Pass |
| ST-ALERT-01 | FR-017 | Low-stock threshold: strictly below threshold is low | Pass |

Full table with expected and actual results: `Samiksha_ESIMS_Test_Case_Document.md`.

### Defects
None found in this cycle.
