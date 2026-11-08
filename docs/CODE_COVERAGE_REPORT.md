# Code coverage report

**Run date:** 2026-11-07
**Revision:** `6791b55` (`feature/ESIMS-17-modular-code-tests`)
**Command:** `coverage run --branch --source=accounts,catalog,esims,reports,suppliers,transactions manage.py test -v 1`
**Scope:** application code; tests, migrations, ASGI/WSGI bootstrap files omitted from this summary.

## Statement coverage

| Scope | Statements | Missed | Statement coverage |
| --- | ---: | ---: | ---: |
| All application modules | 1,209 | 92 | 92.4% |
| Catalog module (includes management commands) | 288 | 75 | 74.0% |
| Catalog web/model code (management commands excluded) | 216 | 3 | 98.6% |

The catalog module's lower total is from its two standalone management commands
(`measure_search` and `seed_demo_products`), which had no direct execution in
this test run. Catalog forms have three missed statements. The detailed
line-by-line results are in `docs/evidence/coverage_app_code.txt`; the complete
unfiltered run is in `docs/evidence/coverage_full.txt`.

## Notes

The test suite exercised 342 cases. Coverage indicates which statements ran; it
does not prove correctness by itself. The detailed table also includes branch
data because a single branch-aware run was used for both requested coverage
reports. See `docs/BRANCH_COVERAGE_REPORT.md` for branch counts.
