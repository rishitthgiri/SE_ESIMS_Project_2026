# Test Case Document: Stock module (STP section 13 format)

| | |
|---|---|
| Project | ESIMS, Team 8 |
| Module | Stock transactions (ESIMS-18 to ESIMS-25) |
| Feature Test Owner | Samiksha B N (STP section 9) |
| Executed | 06-11-2026 |
| Environment | Django 5.2.18, Python 3.13, SQLite (CI) and PostgreSQL (`evidence/stock_tests_postgres.txt`); 76 tests, 76 passed |
| Evidence | `evidence/stock_tests.txt`, `evidence/stock_tests_postgres.txt`, `evidence/stock_coverage.txt`, `evidence/stock_coverage_html/`, `evidence/ESIMS_Samiksha_Evidence.pdf` |

Test IDs, Req IDs, Scenario, Precondition, Test Data / Action and Expected Result are the STP section 13 wording. Rows marked (new) were added or changed during the sprints (see `Samiksha_ESIMS_Unit_Test_Report.md` and `Samiksha_System_Validation_Report.md`).

| Test ID | Req ID | Scenario | Precondition | Test Data / Action | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|---|
| IT-STOCK-01 | FR-010 | Record stock-in | Valid supplier/product | Quantity > 0 | Stock increases; transaction recorded | Stock 5 + 10 = 15; one IN transaction saved with supplier and user | Pass |
| IT-STOCK-02 | FR-011 | Record stock-out | Active product with stock | Sell quantity <= stock | Stock decreases; transaction recorded | Stock 5 - 3 = 2; one OUT transaction saved | Pass |
| UT-STOCK-02 | FR-012 | Reject over-sale | Product stock = 5 | Attempt sale = 6 | Transaction rejected; stock remains 5 | Sale of 6 rejected with message; stock stays 5; nothing saved; selling exactly 5 allowed | Pass |
| IT-STOCK-03 | FR-013 | Unique transaction ID | New stock transaction | Record transaction | Unique transaction ID generated | Every transaction gets its own UUID; database refuses a duplicate | Pass |
| ST-STOCK-04 | FR-014 | Audit trail | Recorded stock transaction | Inspect audit record | User, timestamp and quantity present | User, timestamp, quantity and type stored; records cannot be edited or deleted via the model; Admin audit page `/transactions/audit/` shows and filters them | Pass |
| ST-REL-01 | NFR-004 | Duplicate submission | Valid stock transaction form | Double-submit / retry | Only one transaction recorded | Same form twice records one transaction and changes stock once; user told "already recorded"; rejected sale does not use the token up | Pass |
| ST-USE-01 | NFR-003 | Transaction usability | Staff test user | Complete stock-in/out | Completed in <= 4 screens/steps | 3 screens from the dashboard for stock-in and for stock-out | Pass |
| ST-SEC-03 | SEC-003 | Input validation | Stock forms | Submit negative/malformed quantity | Input rejected safely | Negative, zero, text, empty, too-large and malformed quantities rejected; stock and history unchanged | Pass |
| ST-ALERT-01 (RTM calls it UT-ALERT-01) | FR-017 | Low-stock threshold logic (stock side) | Product threshold configured | Reduce quantity below threshold | Alert appears in Staff/Admin view | Low means strictly below threshold; a sale crossing it raises the alert, a stock-in clears it; disabled products excluded | Pass |
| ST-SEC-02 (audit page) | SEC-002 | Staff access to admin-only audit page | Staff account | Open `/transactions/audit/` | Access denied; event logged | Staff get 403 and the attempt is written to the security log; logged-out users go to login | Pass |
| UT-STOCK-01 (new) | NFR-006 | Stock calculation independent of UI | Pure functions in `services.py` | Run `stock_after_in` / `stock_after_out`; 60 random operations | Correct results without UI or database | Arithmetic runs without UI or database; stock = start + ins - outs; views contain no stock arithmetic | Pass |
| IT-STOCK-04 (new) | FR-014 | Role-based transaction list | Staff and Admin accounts with transactions | Open `/transactions/` as each; filter by type | Staff see own; Admin sees all | Staff see only their own; Admin sees all; IN/OUT filter works | Pass |
| IT-STOCK-05 (new) | FR-007 / FR-010 / FR-011 | Disabled product or supplier | Disabled product and supplier | Try stock-in / stock-out | Refused; not offered in dropdowns | Refused by the service and not offered in dropdowns | Pass |
| IT-STOCK-06 (new) | NFR-004 | Rollback on failure | Active product, stock 5 | Force failure after stock update | Stock and history never diverge | Stock stays 5, 0 transactions; form shows the failure | Pass |
| UT-STOCK-03 (new) | FR-010 / FR-011 / FR-013 | Edge cases | Deleted product; DB error injected | Submit stock operations | Clear error; nothing saved | Deleted product rejected ("does not exist"); unrelated DB error not hidden; nothing saved | Pass |

## Fix in the team RTM (STP 13.1)

Use the STP section 13 IDs. In the RTM replace `ST-STOCK-01` with `IT-STOCK-01` and `ST-STOCK-02` with `UT-STOCK-02`. The threshold test is `ST-ALERT-01` in section 13 and `UT-ALERT-01` in the RTM: the team must pick one.

## Coverage (`transactions` app, branch measurement on)

274 statements, 0 missed; 50 branches, 0 partial; 100% (`evidence/stock_coverage.txt`).

## Defects

None found in this cycle.
