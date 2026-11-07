# Stock Module Test Report

|                    |                                                                                                               |
| ------------------ | ------------------------------------------------------------------------------------------------------------- |
| Project            | ESIMS: Electronics Store Inventory Management System (Team 8)                                                 |
| Module             | Stock transactions (stock-in, stock-out, audit trail, double-submit protection)                               |
| Stories            | ESIMS-18 to ESIMS-25                                                                                          |
| Feature Test Owner | Samiksha B N                                                                                                  |
| Report version     | 1.0                                                                                                           |
| Date               | 06 / 11 / 2026                                                                                                |
| Related documents  | Software Test Plan (STP), `docs/STOCK_TEST_RESULTS.md`, `docs/DEVIATIONS.md`, `docs/USABILITY_WALKTHROUGH.md` |

## 1. Purpose and scope

This report gives the results of testing the Stock module against the Software Test Plan, after the sprint changes. It feeds the team's Unit Test Report, System Validation Report, Code Coverage Report and Branch Coverage Report.

**In scope:** stock-in (FR-010), stock-out (FR-011), over-sale rejection (FR-012), unique transaction ID (FR-013), audit trail (FR-014), low-stock threshold logic (FR-017), duplicate-submit protection (NFR-004), usability of stock screens (NFR-003), stock calculation independent of the UI (NFR-006), and input validation and access control on the stock pages (SEC-002, SEC-003).

**Out of scope (tested by other owners):** login and roles (Auth), products and search (Catalog), suppliers and reports.

## 2. Test environment

| Item             | Value                                                                                                                                                    |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Operating system | Windows 11                                                                                                                                               |
| Python           | Python 3.13.15                                                                                                                                           |
| Django           | 5.2.18                                                                                                                                                   |
| Database         | SQLite (`DB_ENGINE=sqlite`); PostgreSQL: run also done (76 tests passed)                                                                                 |
| Test runner      | Django test runner (`python manage.py test transactions -v 2`)                                                                                           |
| Coverage tool    | coverage.py, branch measurement on (`--branch`)                                                                                                          |
| Browsers         | Chrome ;Edge ; Firefox                                                                                                                                   |
| Test data        | Created by the tests themselves (user staff1/admin1, product MOB-001 with stock 5, one supplier) and demo users from `seed_demo_users` for manual checks |

## 3. Test approach

| Level           | What was done                                                          | Where                                                            |
| --------------- | ---------------------------------------------------------------------- | ---------------------------------------------------------------- |
| Unit            | Pure stock arithmetic and threshold rules without UI or database       | `test_stock_logic.py`                                            |
| Integration     | Services, database rules, views and forms working together             | `tests.py`, `test_audit.py`, `test_double_submit.py`             |
| System / manual | Real browser walkthrough of stock-in, stock-out, audit page, usability | `docs/USABILITY_WALKTHROUGH.md`, screenshots in `docs/evidence/` |
| Non-functional  | Screen count (NFR-003), duplicate submission (NFR-004)                 | `test_usability.py`, `test_double_submit.py`                     |

## 4. Results summary

| Measure                | Result                                                  |
| ---------------------- | ------------------------------------------------------- |
| Automated tests run    | Ran 76 tests                                            |
| Passed                 | 76                                                      |
| Failed                 | 0                                                       |
| Errors / skipped       | 0                                                       |
| Run time               | 25.818s                                                 |
| STP test cases covered | 11 original rows + 4 new rows (see section 5), all Pass |

Per test file:

| File                    | Focus                                            | Tests |
| ----------------------- | ------------------------------------------------ | ----- |
| `tests.py`              | Stock services, views, forms, edge cases         | 25    |
| `test_audit.py`         | Audit record and Administrator audit page        | 15    |
| `test_double_submit.py` | One-time token, repeated submits                 | 16    |
| `test_stock_logic.py`   | Pure calculations, threshold, ledger consistency | 15    |
| `test_usability.py`     | Screens counted from the dashboard               | 5     |

## 5. Test case results

| STP ID            | Req            | Scenario                              | Result                                                       | Status |
| ----------------- | -------------- | ------------------------------------- | ------------------------------------------------------------ | ------ |
| IT-STOCK-01       | FR-010         | Record stock-in                       | Stock 5 + 10 = 15; IN transaction saved                      | Pass   |
| IT-STOCK-02       | FR-011         | Record stock-out                      | Stock 5 - 3 = 2; OUT transaction saved                       | Pass   |
| UT-STOCK-02       | FR-012         | Reject over-sale                      | Sale of 6 rejected, stock stays 5; selling exactly 5 allowed | Pass   |
| IT-STOCK-03       | FR-013         | Unique transaction ID                 | Unique UUID each time; duplicate refused by the database     | Pass   |
| ST-STOCK-04       | FR-014         | Audit trail                           | User, timestamp, quantity, type stored; audit page works     | Pass   |
| ST-REL-01         | NFR-004        | Duplicate submit                      | Same form twice records one transaction                      | Pass   |
| ST-USE-01         | NFR-003        | Screens to complete a stock operation | 3 screens (limit 4)                                          | Pass   |
| ST-SEC-03         | SEC-003        | Input validation                      | Bad quantities rejected, no change                           | Pass   |
| UT-ALERT-01       | FR-017         | Low-stock threshold                   | Strictly below threshold is low                              | Pass   |
| UT-STOCK-01       | NFR-006        | Calculation independent of UI         | Pure functions, ledger consistent                            | Pass   |
| ST-SEC-02         | SEC-002        | Audit page access                     | Staff get 403, logged; anonymous go to login                 | Pass   |
| IT-STOCK-04 (new) | FR-014         | Role-based transaction list           | Staff see own, Admin sees all                                | Pass   |
| IT-STOCK-05 (new) | FR-007/010/011 | Disabled product/supplier             | Refused and not offered                                      | Pass   |
| IT-STOCK-06 (new) | NFR-004        | Rollback on failure                   | Stock and history never diverge                              | Pass   |
| UT-STOCK-03 (new) | FR-010/011/013 | Edge cases                            | Deleted product, hidden DB error, text form                  | Pass   |

Full detail (test function names, actual results) is in `docs/STOCK_TEST_RESULTS.md`.

## 6. Changes since the original Test Plan

| Change                                           | Effect on testing                                                             |
| ------------------------------------------------ | ----------------------------------------------------------------------------- |
| Deviation 5: transaction list per role           | New case IT-STOCK-04                                                          |
| Deviation 16: Administrator audit page           | ST-STOCK-04 now also tests `/transactions/audit/`; ST-SEC-02 covers Staff 403 |
| Deviation 17: one-time `request_token`           | ST-REL-01 now means "repeat POST records nothing"                             |
| Deviation 19: NFR-003 counted from the dashboard | ST-USE-01 expected result is 3 screens                                        |
| Deviation 20: pure stock functions               | UT-STOCK-01 tests them without the database                                   |
| Deviation 21: disabled items keep history        | New case IT-STOCK-05                                                          |
| Deviation 6: tests on SQLite                     | Row locking not proven (see limitations)                                      |

## 7. Code coverage and branch coverage (`transactions` app)

Measured with `coverage run --branch --source=transactions manage.py test transactions`. Test files, migrations and `testutils.py` are excluded.

| File          | Statements | Missed | Branches | Partial | Cover |
| ------------- | ---------- | ------ | -------- | ------- | ----- |
| `admin.py`    | 13         | 0      | 0        | 0       | 100%  |
| `forms.py`    | 43         | 0      | 2        | 0       | 100%  |
| `models.py`   | 27         | 0      | 2        | 0       | 100%  |
| `services.py` | 85         | 0      | 24       | 0       | 100%  |
| `views.py`    | 98         | 0      | 22       | 0       | 100%  |
| **Total**     | 274        | 0      | 50       | 0       | 100%  |

## 8. Defects

| ID                            | Description | Severity | Status |
| ----------------------------- | ----------- | -------- | ------ |
| None found in this test cycle |             |          |        |

Observations that are known design limits, not defects, are in section 9.

## 9. Limitations and risks

1. **Bulk update/delete not blocked.** `StockTransaction` refuses edit and delete through the model and the admin screen, but bulk `QuerySet.update()` and `.delete()` are not blocked (deviation 18). Database triggers would be the next hardening step.
2. **Sale amount uses current price** and not a price snapshot at sale time.
3. **Browser coverage** is a smoke test only.

## 10. Evidence

| File (in `docs/evidence/`) | What it shows             |
| -------------------------- | ------------------------- |
| `stock_tests.txt`          | Full test run             |
| `stock_coverage.txt`       | Coverage with branches    |
| `stock_coverage_html/`     | Browsable coverage report |
| `audit_trail.png`          | Administrator audit page  |
| `over_sale_rejected.png`   | Over-sale error message   |
| `double_submit.png`        | Double-submit test output |
| `usability_*.png`          | Usability screenshots     |

## 11. Conclusion

All planned Stock module test cases were executed and all passed. Statement coverage of the `transactions` app is 100% and branch coverage is 100%. The remaining risks are listed in section 9.The module is ready for release with the limitations stated in section 9.

| Role                       | Name         | Date           |
| -------------------------- | ------------ | -------------- |
| Feature Test Owner (Stock) | Samiksha B N | 06 / 11 / 2026 |
