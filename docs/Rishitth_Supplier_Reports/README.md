# Phase 3 reports: Supplier, Alerts and Reports (Rishitth G R)

Mini-Project Deliverables Part 3 (test cases updation and testing). Everything here covers ESIMS-26 to ESIMS-35.

| Deliverable | File |
| --- | --- |
| Updated test cases (Test Case Document) | `Rishitth_Test_Case_Document_Supplier_Reports.md` |
| Unit Test Report | `Rishitth_Unit_Test_Report.md` |
| System Validation Report | `Rishitth_System_Validation_Report.md` |
| Code Coverage Report | `Rishitth_Code_Coverage_Report.md` |
| Branch Coverage Report | `Rishitth_Branch_Coverage_Report.md` |
| Raw logs, coverage data and HTML | `evidence/` |
| Scripts used for the live validation | `scripts/` |

## Headline results (09 / 11 / 2026)

- Module tests: **66 of 66 pass** on PostgreSQL and on SQLite. Full project suite: **356 of 356 pass**.
- Statement coverage for this module: **99.6%**. Branch coverage: **94.4%**.
- Live system validation over real HTTP: **28 of 28 checks pass**.
- No defects found in the application code in this module. See the Unit Test Report, section 5.

## Repeat the run (PowerShell, repository root)

```powershell
$env:DB_ENGINE = "sqlite"
python manage.py test suppliers reports esims -v 2
coverage run --branch --source=accounts,catalog,esims,reports,suppliers,transactions manage.py test -v 1
coverage report -m --omit="*/tests.py,*/test_*.py,*/testutils.py,*/migrations/*,*/asgi.py,*/wsgi.py"
coverage html -d docs/Rishitth_Supplier_Reports/evidence/coverage_html --include="suppliers/*,reports/*,esims/health.py,esims/urls.py"
```

Live validation: start the server, then `python docs/Rishitth_Supplier_Reports/scripts/system_validation.py http://127.0.0.1:8000 results.json` (needs `python manage.py seed_demo_users` first).
