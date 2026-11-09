# Code Coverage Report: Supplier, Alerts and Reports

|  |  |
| --- | --- |
| Project | ESIMS: Electronics Store Inventory Management System (Team 8) |
| Module | Supplier management, low-stock alerts, reports, health check (ESIMS-26 to ESIMS-35) |
| Feature Test Owner | Rishitth G R |
| Report version / date | 1.0 / 09 / 11 / 2026 |
| Build tested | `6d6f97e` (main) plus the Phase 3 test additions listed in the Unit Test Report |
| Related documents | Software Test Plan (`ESIMS_STP_Team_8.pdf`), `docs/DEVIATIONS.md`, `docs/DEPLOYMENT.md` |

**Run:** 09 / 11 / 2026, PostgreSQL 16.15, 356 tests, all passing.
**Command:** `coverage run --branch --source=accounts,catalog,esims,reports,suppliers,transactions manage.py test -v 1` then `coverage report -m --omit="*/tests.py,*/test_*.py,*/testutils.py,*/migrations/*,*/asgi.py,*/wsgi.py"`
**Scope:** application code. Test files, migrations and the ASGI/WSGI start-up files are left out.

## 1. Statement coverage for this module

Statement coverage = statements that ran divided by all statements. Files: `suppliers/*`, `reports/*`, `esims/health.py`, `esims/urls.py`.

| File | Statements | Missed | Statement coverage | Missed lines |
| --- | --- | --- | --- | --- |
| `esims/health.py` | 9 | 0 | 100.0% | - |
| `esims/urls.py` | 5 | 0 | 100.0% | - |
| `reports/admin.py` | 1 | 0 | 100.0% | - |
| `reports/alerts.py` | 6 | 0 | 100.0% | - |
| `reports/apps.py` | 4 | 0 | 100.0% | - |
| `reports/forms.py` | 19 | 0 | 100.0% | - |
| `reports/models.py` | 1 | 0 | 100.0% | - |
| `reports/services.py` | 28 | 0 | 100.0% | - |
| `reports/urls.py` | 4 | 0 | 100.0% | - |
| `reports/views.py` | 58 | 0 | 100.0% | - |
| `suppliers/admin.py` | 7 | 0 | 100.0% | - |
| `suppliers/apps.py` | 4 | 0 | 100.0% | - |
| `suppliers/forms.py` | 17 | 1 | 94.1% | 20 |
| `suppliers/models.py` | 17 | 0 | 100.0% | - |
| `suppliers/urls.py` | 4 | 0 | 100.0% | - |
| `suppliers/views.py` | 54 | 0 | 100.0% | - |
| **Module total** | 238 | 1 | 99.6% |  |

**Result: 237 of 238 statements executed = 99.6%.** Everything is covered except one line.

### The one uncovered statement

`suppliers/forms.py` line 20 is `raise forms.ValidationError('Supplier name is required.')`. A blank name never reaches it, because Django's required-field check (which also strips spaces) rejects the input first. This was confirmed in a shell. The line is a second safety net and cannot run, so no test can cover it.

## 2. Statement coverage by module (whole project, for context)

| Module | Statements | Missed | Statement coverage | Branches | Branches covered | Partial | Branch coverage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| accounts | 310 | 8 | 97.4% | 44 | 37 | 7 | 84.1% |
| catalog | 288 | 75 | 74.0% | 64 | 43 | 5 | 67.2% |
| transactions | 274 | 0 | 100.0% | 50 | 50 | 0 | 100.0% |
| suppliers | 103 | 1 | 99.0% | 14 | 12 | 2 | 85.7% |
| reports | 121 | 0 | 100.0% | 22 | 22 | 0 | 100.0% |
| esims | 113 | 3 | 97.3% | 22 | 20 | 2 | 90.9% |
| **All application code** | 1209 | 87 | 92.8% | 216 | 184 | 16 | 85.2% |

The catalog figure is low only because its two command-line tools (`measure_search` and `seed_demo_products`) are not run by the test suite. That is the Catalog owner's module.

## 3. Reading these numbers

Coverage shows which lines ran during the tests. It does not prove the lines are correct, which is why the tests also check results and why the live walkthrough was run.

## 4. Raw evidence

`evidence/coverage_full_app.txt` (line-by-line report), `evidence/coverage_full.json`, `evidence/coverage_full.xml`, and `evidence/coverage_html/index.html` (open in a browser for the coloured source of this module). The branch figures are in the Branch Coverage Report.
