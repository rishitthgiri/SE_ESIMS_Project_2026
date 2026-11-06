# Test results for the Stock module (Samiksha: ESIMS-18 to ESIMS-25)

Feature Test Owner: Samiksha B N (Stock). Updated after the sprint changes for Part-3 (v1.1).

Copy these rows into the "Actual Result" and "Status" columns of the Test Case Document (STP section 13), replacing "Not Executed".

**How the evidence is produced** (Command Prompt, project folder, virtual environment active):

```
set DB_ENGINE=sqlite
python manage.py test transactions -v 2 > docs\evidence\stock_tests.txt 2>&1
coverage erase
coverage run --branch --source=transactions manage.py test transactions
coverage report -m --omit="*/tests.py,*/test_*.py,*/testutils.py,*/migrations/*" > docs\evidence\stock_coverage.txt
coverage html --omit="*/tests.py,*/test_*.py,*/testutils.py,*/migrations/*" -d docs\evidence\stock_coverage_html
```

A row is Pass only if its tests passed in `docs/evidence/stock_tests.txt`.

**Date run:** 06 / 11 / 2026
**Automated tests in `transactions`:** 76 run, 76 passed (confirm against `stock_tests.txt`)
**Environment:** SQLite (`DB_ENGINE=sqlite`), same as the GitHub Actions CI run

## STP test cases (original rows, re-run)

| STP test ID | Req | Automated test(s) (`transactions/...`) | Actual result | Status |
| --- | --- | --- | --- | --- |
| IT-STOCK-01 | FR-010 | `tests.StockInServiceTests.test_stock_in_increases_stock_and_saves_transaction` | Stock 5 + stock-in of 10 = 15; one IN transaction saved with the supplier and user | Pass |
| IT-STOCK-02 | FR-011 | `tests.StockOutServiceTests.test_stock_out_decreases_stock_and_saves_transaction` | Stock 5 - sale of 3 = 2; one OUT transaction saved, no supplier | Pass |
| UT-STOCK-02 | FR-012 | `tests.StockOutServiceTests.test_reject_over_sale_leaves_stock_unchanged`, `test_selling_exactly_all_stock_is_allowed`, `test_stock_logic.PureCalculationTests` | Stock 5, sale of 6 rejected with a clear message; stock stays 5; no transaction saved. Selling exactly 5 is allowed | Pass |
| IT-STOCK-03 | FR-013 | `tests.TransactionIdAndImmutabilityTests.test_every_transaction_gets_a_unique_id`, `test_duplicate_transaction_id_is_blocked_by_database` | Every transaction gets its own UUID; the database refuses a duplicate ID | Pass |
| ST-STOCK-04 | FR-014 | `test_audit.AuditRecordTests`, `test_audit.AuditAccessTests`, `test_audit.AuditFilterTests`, `tests.TransactionIdAndImmutabilityTests.test_transactions_cannot_be_edited_or_deleted` | User, timestamp, quantity and type are stored on every record; records cannot be edited or deleted through the model; the Administrator audit page (`/transactions/audit/`, added in Sprint, deviation 16) shows them and can filter. Screenshot: `docs/evidence/audit_trail.png` | Pass |
| ST-REL-01 | NFR-004 | `test_double_submit.DoubleSubmitServiceTests`, `test_double_submit.DoubleSubmitViewTests` | Submitting the same form twice (one-time `request_token`, deviation 17) creates exactly one transaction and changes stock once; the user is told it was already recorded; a rejected sale does not use the token up | Pass |
| ST-USE-01 | NFR-003 | `test_usability.FewScreensTests` and `docs/USABILITY_WALKTHROUGH.md` | Counted from the dashboard (deviation 19): stock-in and stock-out each take 3 screens (limit 4); an error keeps the user on the same screen. Manual run recorded in the walkthrough | Pass |
| ST-SEC-03 | SEC-003 | `tests.StockViewTests.test_invalid_input_is_rejected_by_the_form`, `tests.StockInServiceTests.test_stock_in_rejects_bad_quantities`, `tests.StockOutServiceTests.test_stock_out_rejects_bad_quantities_and_disabled_product` | Negative, zero, text, empty, too-large and malformed quantities are rejected; stock and history unchanged | Pass |
| UT-ALERT-01 (called ST-ALERT-01 in STP section 13) | FR-017 | `test_stock_logic.ThresholdTests` | Low stock means strictly below the threshold (equal is not low); a sale crossing it raises the alert, a stock-in clears it; disabled products are excluded | Pass |
| UT-STOCK-01 | NFR-006 | `test_stock_logic.PureCalculationTests`, `test_stock_logic.LedgerConsistencyTests`, `test_stock_logic.SeparationFromUITests` | Stock arithmetic runs without the UI or a database (deviation 20); stock always equals start + stock-ins - stock-outs over 60 random operations; views contain no stock arithmetic | Pass |
| ST-SEC-02 (audit page) | SEC-002 | `test_audit.AuditAccessTests` | Staff get 403 on the audit page and the attempt is written to the security log; logged-out visitors go to login | Pass |

## Test cases added or changed during the sprints (new rows)

| STP test ID | Req | Automated test(s) (`transactions/...`) | Why added | Actual result | Status |
| --- | --- | --- | --- | --- | --- |
| IT-STOCK-04 (new) | FR-014 | `tests.StockViewTests.test_staff_see_own_transactions_admin_sees_all`, `test_transaction_list_type_filter` | Deviation 5: transaction list is per role | Staff see only their own transactions; Administrators see all; the list can be filtered by type (IN/OUT) | Pass |
| IT-STOCK-05 (new) | FR-007 / FR-010 / FR-011 | `tests.StockInServiceTests.test_stock_in_rejects_disabled_product_and_supplier`, `tests.StockOutServiceTests.test_stock_out_rejects_bad_quantities_and_disabled_product`, `tests.StockViewTests.test_dropdowns_only_offer_active_products` | Deviation 21: disabled products and suppliers keep their history but cannot be used | Disabled products/suppliers are refused by the service and are not offered in the dropdowns | Pass |
| IT-STOCK-06 (new) | NFR-004 | `tests.StockOutServiceTests.test_failure_after_stock_update_rolls_everything_back`, `tests.StockViewTests.test_unexpected_stock_rule_failure_is_shown_on_the_form` | Atomicity (SAD 4.4): stock and history can never diverge | If saving the transaction fails, the stock change is rolled back (stock stays 5, 0 transactions); the form shows the failure | Pass |
| UT-STOCK-03 (new) | FR-010 / FR-011 / FR-013 | `tests.EdgeCaseCoverageTests` (3 tests) | Closes the last uncovered lines in `transactions` | A deleted product is rejected with "does not exist"; an unrelated database error is not hidden and nothing is saved; a transaction's text shows its quantity and ID | Pass |

## RTM IDs to fix in the documents

The Requirements Traceability Matrix (STP 13.1) and the test-case table (STP 13) use different IDs for the same stock tests. Use the **STP test ID** column above everywhere. In the RTM replace `ST-STOCK-01` with `IT-STOCK-01` and `ST-STOCK-02` with `UT-STOCK-02`. The RTM calls the threshold test `UT-ALERT-01` while STP section 13 calls it `ST-ALERT-01`: use one ID in both and tell the team which one.

## Known limitations (stated honestly)

1. Bulk `QuerySet.update()` and `.delete()` on `StockTransaction` are not blocked (deviation 18). Only edits through the model and the admin screen are refused.
2. Tests run on SQLite (deviation 6). The row lock (`select_for_update`) only really locks on PostgreSQL, so concurrent over-sale is not proven by these tests.
3. Sale amounts use the product's current price (not a snapshot taken at sale time).

## Evidence files in `docs/evidence/`

| File | What it shows |
| --- | --- |
| `stock_tests.txt` | Full test run output |
| `stock_coverage.txt` | Statement and branch coverage of `transactions` |
| `stock_coverage_html/` | Browsable coverage report |
| `audit_trail.png` | `/transactions/audit/` as admin |
| `over_sale_rejected.png` | The red "Only N unit(s)" message |
| `double_submit.png` | Double-submit test output |
| `usability_*.png` | Usability screenshots |
