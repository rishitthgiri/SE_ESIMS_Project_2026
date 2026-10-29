# ESIMS - Electronics Store Inventory Management System

Django + PostgreSQL web app for a retail electronics store: products and stock, purchases (stock-in), sales (stock-out), suppliers, low-stock alerts and reports.
PES University, UE24CS341A Software Engineering mini-project, **Team 8**.

## What it does
| Who | Can do |
|---|---|
| Staff | Log in, search products and see stock levels, record stock-in and stock-out, see their own transactions, see the low-stock list |
| Administrator | Everything Staff can, plus: add/edit products and categories, manage suppliers, manage staff accounts, view the security log, see all transactions, stock/sales report with CSV export, top-selling products |

Rules enforced by the system: stock can never go below zero, every stock-in needs a registered supplier, every transaction gets a unique ID and is never edited or deleted, and nothing except the login page is visible without logging in.

## Modules (Django apps)
| App | Purpose |
|---|---|
| `accounts` | Login, roles (Staff/Admin), staff management, session timeout, security log |
| `catalog` | Categories and products, search and filter |
| `suppliers` | Supplier management and purchase history (Administrator only) |
| `transactions` | Stock-in / stock-out and the transaction list |
| `reports` | Low-stock alerts, stock/sales report, top-selling products |

Main pages: `/` dashboard, `/catalog/products/`, `/transactions/in/`, `/transactions/out/`, `/transactions/`, `/suppliers/`, `/reports/low-stock/`, `/reports/sales/`, `/reports/top-selling/`, `/staff/`, `/security-log/`, `/health/`.

## Run it locally
```bash
git clone https://github.com/rishitthgiri/SE_ESIMS_Project_2026.git
cd SE_ESIMS_Project_2026
python -m venv venv
venv\Scripts\activate               # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```
Quick start without PostgreSQL (SQLite):
```bash
set DB_ENGINE=sqlite                # PowerShell: $env:DB_ENGINE="sqlite"   macOS/Linux: export DB_ENGINE=sqlite
python manage.py migrate
python manage.py seed_demo_users    # demo users only: see docs/SEED_USERS.md
python manage.py runserver
```
With PostgreSQL: `cp .env.example .env`, `docker compose up -d db`, then the same `migrate`, `seed_demo_users` and `runserver` (the app reads real environment variables, not `.env` itself).

Open http://127.0.0.1:8000/ and log in with `admin / Admin@12345` (Administrator) or `staff1 / Staff@12345` (Staff). These are local demo accounts only.

## Run the tests
```bash
set DB_ENGINE=sqlite                # PowerShell: $env:DB_ENGINE="sqlite"
python manage.py test
```
GitHub Actions runs the checks, the migration check and the full test suite on every push and pull request to `main`.

## Documents
* `ESIMS_SRS_Team_8.docx`, `ESIMS_SAD_Team_8.pdf`, `ESIMS_STP_Team_8.pdf`, `ESIMS_Synopsis.docx` - the submitted documents
* `docs/DEVIATIONS.md` - where the build differs from those documents, and why
* `docs/DEPLOYMENT.md` - production deployment, availability target (99% of business hours), monitoring and backups
* `docs/SEED_USERS.md` - demo users

## Workflow
`main` is protected. Work on `feature/ESIMS-<n>-<short-name>` branches, one pull request per story, reviewed before merging, with `Closes #<issue>` in the description. Backlog and sprints are on the GitHub Project board "ESIMS Backlog".

## Team 8
Samiksha B N, Roopa Sreedhar A, Rishitth G R, Sakthevel Saravanan
