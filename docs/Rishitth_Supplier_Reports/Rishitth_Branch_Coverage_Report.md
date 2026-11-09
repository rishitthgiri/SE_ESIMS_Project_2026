# Branch Coverage Report: Supplier, Alerts and Reports

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

## 1. What is measured

A branch is one of the two ways an `if`, loop or condition can go. Branch coverage = branches that ran divided by all branches. A *partial* branch is a decision where only one of its ways ran. Files with no decisions are not listed.

## 2. Branch coverage for this module

| File | Branches | Covered | Partial decisions | Branch coverage |
| --- | --- | --- | --- | --- |
| `reports/forms.py` | 4 | 4 | 0 | 100.0% |
| `reports/services.py` | 4 | 4 | 0 | 100.0% |
| `reports/views.py` | 14 | 14 | 0 | 100.0% |
| `suppliers/forms.py` | 6 | 4 | 2 | 66.7% |
| `suppliers/views.py` | 8 | 8 | 0 | 100.0% |
| **Module total** | 36 | 34 | 2 | 94.4% |

**Result: 34 of 36 branches executed = 94.4%.** `reports/*`, `suppliers/views.py` and `esims/health.py` have every branch covered.

## 3. The two branches that did not run

Both are in `suppliers/forms.py`, in `clean_name`:

| Branch | Why it cannot run |
| --- | --- |
| Line 19 to 20: the name is blank after stripping spaces | Django rejects a blank or all-space name with "This field is required" before `clean_name` is called. |
| Line 22 to 24: the form's supplier has no id yet | A new `Supplier` gets its UUID id when the object is created, so the id is always present and the duplicate check always excludes it. The check is still correct for both new and existing suppliers. |

They are leftover safety checks. They do no harm and cannot be reached, so they are accepted instead of tested.

## 4. Branch coverage by module (whole project, for context)

| Module | Branches | Covered | Partial | Branch coverage |
| --- | --- | --- | --- | --- |
| accounts | 44 | 37 | 7 | 84.1% |
| catalog | 64 | 43 | 5 | 67.2% |
| transactions | 50 | 50 | 0 | 100.0% |
| suppliers | 14 | 12 | 2 | 85.7% |
| reports | 22 | 22 | 0 | 100.0% |
| esims | 22 | 20 | 2 | 90.9% |
| **All application code** | 216 | 184 | 16 | 85.2% |

The remaining partial branches in other modules are listed per file in `evidence/coverage_full_app.txt` (column "Missing", entries like `70->72`) and belong to their Feature Test Owners.

## 5. Raw evidence

`evidence/coverage_full_app.txt`, `evidence/coverage_full.json`, `evidence/coverage_html/index.html`.
