# Code Coverage and Branch Coverage Report

## Stock module (`transactions` app)

| | |
|---|---|
| Project | ESIMS, Team 8 |
| Section owner | Samiksha B N (Stock module, ESIMS-18 to ESIMS-25) |
| Date | 06-11-2026 |
| Environment | Windows 11, Python 3.13, Django 5.2.18, SQLite and PostgreSQL |

Command (project folder):
```
coverage run --branch --source=transactions manage.py test transactions
coverage report -m --omit="*/tests.py,*/test_*.py,*/testutils.py,*/migrations/*"
coverage html --omit="*/tests.py,*/test_*.py,*/testutils.py,*/migrations/*" -d evidence/stock_coverage_html
```

| File | Statements | Missed | Statement cover |
|---|---|---|---|
| `admin.py` | 13 | 0 | 100% |
| `forms.py` | 43 | 0 | 100% |
| `models.py` | 27 | 0 | 100% |
| `services.py` | 85 | 0 | 100% |
| `views.py` | 98 | 0 | 100% |
| `apps.py`, `urls.py` | 8 | 0 | 100% |
| **Total** | **274** | **0** | **100%** |

Evidence: `evidence/stock_coverage.txt`; browsable report `evidence/stock_coverage_html/index.html`.

Test files, migrations and `testutils.py` are excluded from the measurement.


## Branch coverage

Measured with `coverage run --branch` (same run as the Code Coverage Report).

| File | Branches | Partial (not fully taken) | Branch cover |
|---|---|---|---|
| `forms.py` | 2 | 0 | 100% |
| `models.py` | 2 | 0 | 100% |
| `services.py` | 24 | 0 | 100% |
| `views.py` | 22 | 0 | 100% |
| `admin.py`, `apps.py`, `urls.py` | 0 | 0 | n/a |
| **Total** | **50** | **0** | **100%** |

Evidence: `evidence/stock_coverage.txt` (Branch and BrPart columns); `evidence/stock_coverage_html/index.html` shows branch detail per file.

All decision points in the stock services and views, such as over-sale, bad input, repeated token and role checks, are exercised both ways.
