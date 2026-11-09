# Unit Test Report: Supplier, Alerts and Reports

|  |  |
| --- | --- |
| Project | ESIMS: Electronics Store Inventory Management System (Team 8) |
| Module | Supplier management, low-stock alerts, reports, health check (ESIMS-26 to ESIMS-35) |
| Feature Test Owner | Rishitth G R |
| Report version / date | 1.0 / 09 / 11 / 2026 |
| Build tested | `6d6f97e` (main) plus the Phase 3 test additions listed in the Unit Test Report |
| Related documents | Software Test Plan (`ESIMS_STP_Team_8.pdf`), `docs/DEVIATIONS.md`, `docs/DEPLOYMENT.md` |

## 1. Purpose and scope

Results of the automated unit and integration tests for the supplier module (ESIMS-27, 28), the alert and report services (ESIMS-29, 31, 32), the logged-out access rule (ESIMS-33) and the health check (ESIMS-34). Tests for login, catalog and stock belong to the other Feature Test Owners.

## 2. Environment

| Item | Value |
| --- | --- |
| Operating system | Linux x86_64 (Ubuntu 24.04), cloud test machine |
| Python / Django | Python 3.12.3 / Django 5.2.18 |
| Database (primary) | PostgreSQL 16.15 (the STP names 15.x; same behaviour for these tests) |
| Database (second run) | SQLite in memory (`DB_ENGINE=sqlite`, what GitHub Actions uses) |
| Test runner | Django test runner: `python manage.py test` |
| Coverage tool | coverage.py 7.17.0 with `--branch` |
| Live server (system validation) | gunicorn 26.2.0, 3 workers, PostgreSQL |

## 3. Results summary

| Measure | Result |
| --- | --- |
| Tests in this module (suppliers, reports, health) | 66 |
| Passed (PostgreSQL) | 66 |
| Passed (SQLite) | 66 |
| Failed / errors / skipped | 0 / 0 / 0 |
| Full project suite on PostgreSQL | 356 run, 356 passed, 0 failed |
| Full project suite on SQLite | 356 run, 356 passed, 0 failed |
| Django system check | No issues |
| Missing migrations check (`makemigrations --check`) | No changes detected |
| Outcome | PASS |

### Results by test class

| File | Test class | Tests | Passed | Failed |
| --- | --- | --- | --- | --- |
| `suppliers/tests.py` | SupplierCrudTests | 8 | 8 | 0 |
| `suppliers/tests.py` | SupplierPermissionTests | 2 | 2 | 0 |
| `suppliers/tests.py` | SupplierStockLinkTests | 5 | 5 | 0 |
| `suppliers/test_detail_and_edit.py (new)` | SupplierEditAndDetailTests | 6 | 6 | 0 |
| `reports/tests.py` | LowStockRuleTests | 6 | 6 | 0 |
| `reports/tests.py` | LowStockViewTests | 4 | 4 | 0 |
| `reports/test_alert_flow.py (new)` | LowStockFlowTests | 4 | 4 | 0 |
| `reports/test_alert_flow.py (new)` | ReportAmountRuleTests | 1 | 1 | 0 |
| `reports/test_reports.py` | ReportAccessTests | 4 | 4 | 0 |
| `reports/test_reports.py` | SalesReportTests | 9 | 9 | 0 |
| `reports/test_reports.py` | CsvExportTests | 4 | 4 | 0 |
| `reports/test_reports.py` | TopSellingTests | 6 | 6 | 0 |
| `reports/test_reports.py` | ServiceTests | 1 | 1 | 0 |
| `reports/test_sec005.py` | LoggedOutAccessTests | 4 | 4 | 0 |
| `esims/test_health.py` | HealthTests | 2 | 2 | 0 |
|  |  | Total | Passed | Failed |
| --- | --- | --- | --- | --- |
|  |  | 66 | 66 | 0 |

### Results by test case

| Test ID | Requirement | Automated tests | Passed | Failed |
| --- | --- | --- | --- | --- |
| UT-SUP-01 | FR-015 | 8 | 8 | 0 |
| UT-SUP-02 | FR-015, SEC-003 | 4 | 4 | 0 |
| UT-SUP-03 | FR-015, SEC-002 | 4 | 4 | 0 |
| IT-SUP-02 | FR-016 | 2 | 2 | 0 |
| IT-SUP-03 | FR-015, FR-016 | 2 | 2 | 0 |
| IT-SUP-04 | FR-016 | 1 | 1 | 0 |
| UT-ALERT-01 | FR-017 | 7 | 7 | 0 |
| ST-ALERT-01 | FR-017 | 6 | 6 | 0 |
| ST-ALERT-02 | FR-017 | 1 | 1 | 0 |
| ST-REPORT-01 | FR-018 | 10 | 10 | 0 |
| ST-REPORT-02 | FR-019 | 6 | 6 | 0 |
| ST-REPORT-03 | FR-018 (UC-09 exported) | 4 | 4 | 0 |
| ST-REPORT-04 | FR-018, FR-019, SEC-002 | 4 | 4 | 0 |
| ST-REPORT-05 | FR-018 | 1 | 1 | 0 |
| ST-AVAIL-01 | NFR-002 | 1 | 1 | 0 |
| ST-AVAIL-02 | NFR-002 | 1 | 1 | 0 |
| ST-SEC-05 | SEC-005 | 4 | 4 | 0 |

The names of every test are in Appendix A of the Test Case Document and in the raw logs.

## 4. Tests added in Phase 3

11 tests were added to close gaps found while measuring coverage and while updating the cases. No application code was changed.

| File | Added tests | What they check |
| --- | --- | --- |
| `suppliers/test_detail_and_edit.py` | 6 | Edit page shows current values; failed edit keeps old values; unknown id gives 404; supplier page is Administrator only; disabling twice is harmless; supplier text form |
| `reports/test_alert_flow.py` | 5 | Alert appears only strictly below the threshold, step by step through real stock-outs; both roles see it; disabled product removed; restock clears it; report amount follows the current price (deviation 8) |

## 5. Defects and observations

No defect was found in the application code in this module's scope.

| # | Observation | Impact | Action |
| --- | --- | --- | --- |
| 1 | Two statements in `suppliers/forms.py` can never run (line 20 and the "instance has no id" path at line 22). A new `Supplier` already has its UUID id before saving, and Django already rejects a blank name before `clean_name` runs (checked in a shell). | None. Defensive code only. | Left as is (development is frozen). Listed in the coverage reports as the only uncovered code in this module. |
| 2 | Report amounts use the current product price, so changing a price changes old report amounts. | Low for v1.0. | Documented in `docs/DEVIATIONS.md` (8) and pinned by `test_price_change_changes_old_sale_amounts`. |
| 3 | The first dry run of the live system walkthrough showed 3 failed checks. All three were mistakes in the walkthrough script (it read a flash message that mentions the product name, and picked the wrong link on the supplier list). The database was checked and the application had behaved correctly. The script was fixed and run again on a clean database: 28 of 28 pass. | None on the product. | Fixed in `scripts/system_validation.py`. |

## 6. How to repeat the run

PowerShell, from the repository root:

```powershell
$env:DB_ENGINE = "sqlite"
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test suppliers reports esims -v 2
python manage.py test -v 1
```

For PostgreSQL set `DB_ENGINE=postgres` and the `DB_*` variables from `.env.example` instead.

## 7. Raw evidence

`evidence/module_tests_postgres.txt`, `evidence/module_tests_sqlite.txt`, `evidence/full_run_postgres.txt`, `evidence/full_run_sqlite.txt`. The permission-denied tracebacks inside the full-run logs are expected: some tests deliberately open a page that Staff must not see, and Django logs the refusal.
