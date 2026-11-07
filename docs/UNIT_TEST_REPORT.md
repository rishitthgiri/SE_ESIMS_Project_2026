# Unit and integration test report

**Project:** Electronics Store Inventory Management System (ESIMS), Team 8
**Revision:** `feature/ESIMS-17-modular-code-tests` at `6791b55`
**Execution date:** 2026-11-07
**Test database:** SQLite (in-memory Django test database)

## Result

| Measure | Result |
| --- | ---: |
| Tests discovered and run | 342 |
| Passed | 342 |
| Failed / errors | 0 |
| Outcome | PASS |
| Django system check | PASS (0 issues) |

The suite covers accounts and authorization, catalog and search, health,
reports, supplier management, stock transaction logic, double-submit behavior,
audit history, validation, and usability checks. The user-assigned catalog cases
and their updated mappings are listed in `docs/TEST_CASE_UPDATES.md`.

## Reproduction

From the repository root in PowerShell:

```powershell
$env:DB_ENGINE = "sqlite"
python manage.py check
python manage.py test -v 1
```

The verbose execution log for the coverage-instrumented repeat is
`docs/evidence/full_test_run.txt`. The original complete run finished with
`Ran 342 tests ... OK`.
