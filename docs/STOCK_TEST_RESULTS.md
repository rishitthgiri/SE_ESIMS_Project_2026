# Test results for the Stock module (Samiksha: ESIMS-18 to ESIMS-25)

Copy these rows into the "Actual Result" and "Status" columns of the Software Test Plan (section 13), replacing "Not Executed".

**How the evidence is produced** (run in the project folder, virtual environment active, `DB_ENGINE=sqlite`):

```
mkdir docs\evidence
python manage.py test transactions -v 2 > docs\evidence\stock_tests.txt 2>&1
coverage run --source=transactions manage.py test transactions
coverage report -m --omit="*/tests.py,*/test_*.py,*/testutils.py,*/migrations/*" > docs\evidence\stock_coverage.txt
```

Fill the **Date run** and re-check the Status after YOUR run. A row is Pass only if its tests passed in `stock_tests.txt`.
Date run: ____ / ____ / 2026

## STP test cases

| STP test ID | Req | Automated test(s) (`transactions/...`) | Actual result | Status |
|---|---|---|---|---|
| IT-STOCK-01 | FR-010 | `tests.StockInServiceTests.test_stock_in_increases_stock_and_saves_transaction` | Stock 5 + stock-in of 10 = 15; one IN transaction saved with the supplier and user | Pass |
| IT-STOCK-02 | FR-011 | `tests.StockOutServiceTests.test_stock_out_decreases_stock_and_saves_transaction` | Stock 5 - sale of 3 = 2; one OUT transaction saved, no supplier | Pass |
| UT-STOCK-02 | FR-012 | `tests.StockOutServiceTests.test_reject_over_sale_leaves_stock_unchanged`, `test_stock_logic.PureCalculationTests` | Stock 5, sale of 6 rejected with a clear message; stock stays 5; no transaction saved. Selling exactly 5 is allowed | Pass |
| IT-STOCK-03 | FR-013 | `tests.TransactionIdAndImmutabilityTests.test_every_transaction_gets_a_unique_id`, `test_duplicate_transaction_id_is_blocked_by_database` | Every transaction gets its own UUID; the database refuses a duplicate ID | Pass |
| ST-STOCK-04 | FR-014 | `test_audit.AuditRecordTests`, `test_audit.AuditAccessTests`, `test_audit.AuditFilterTests` | User, timestamp, quantity and type are stored on every record; records cannot be edited or deleted; the Administrator audit list shows them and can filter | Pass (also take the audit-page screenshot below) |
| ST-REL-01 | NFR-004 | `test_double_submit.DoubleSubmitServiceTests`, `test_double_submit.DoubleSubmitViewTests` | Submitting the same form twice creates exactly one transaction and changes stock once; the user is told it was already recorded; a rejected sale does not use the token up | Pass |
| ST-USE-01 | NFR-003 | `test_usability.FewScreensTests` and `docs/USABILITY_WALKTHROUGH.md` | Stock-in and stock-out each take 3 screens from the dashboard (limit 4); an error keeps the user on the same screen | Pass (also fill the manual table) |
| ST-SEC-03 | SEC-003 | `tests.StockViewTests.test_invalid_input_is_rejected_by_the_form`, `tests.StockInServiceTests.test_stock_in_rejects_bad_quantities`, `accounts.test_validation` | Negative, zero, text, empty, too-large and malformed quantities are rejected; stock and history unchanged | Pass |
| UT-ALERT-01 | FR-017 | `test_stock_logic.ThresholdTests` | Low stock means strictly below the threshold (equal is not low); a sale crossing it raises the alert, a stock-in clears it; disabled products are excluded | Pass |
| UT-STOCK-01 | NFR-006 | `test_stock_logic.PureCalculationTests`, `test_stock_logic.LedgerConsistencyTests`, `test_stock_logic.SeparationFromUITests` | Stock arithmetic runs without the UI or a database; stock always equals start + stock-ins - stock-outs over 60 random operations; views contain no stock arithmetic | Pass |
| ST-SEC-02 (audit page) | SEC-002 | `test_audit.AuditAccessTests` | Staff get 403 on the audit page and the attempt is written to the security log; logged-out visitors go to login | Pass |

## RTM IDs to fix in the documents

The Requirements Traceability Matrix and the test-case table use different IDs for the same stock tests. Use the **STP test ID** column above everywhere. Replace in the RTM: `IT-STOCK-01` stays, `ST-STOCK-01` becomes `IT-STOCK-01`, `ST-STOCK-02` becomes `UT-STOCK-02`, `UT-ALERT-01` stays (it is `test_stock_logic.ThresholdTests`).

## Screenshots to save in `docs/evidence/`
1. `stock_tests.txt` (the test run) and `stock_coverage.txt`.
2. `audit_trail.png`: `/transactions/audit/` as admin, showing user, timestamp, quantity and IDs.
3. `over_sale_rejected.png`: the red "Only N unit(s)" message.
4. `double_submit.png`: the blue "already recorded" message (see the manual double-click check in the notes).
5. The usability screenshots listed in `docs/USABILITY_WALKTHROUGH.md`.
