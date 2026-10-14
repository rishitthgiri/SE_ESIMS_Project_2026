# ESIMS - Electronics Store Inventory Management System

Django + PostgreSQL web app (PES University, UE24CS341A Software Engineering mini-project).

## Modules (Django apps)
| App | Purpose |
|---|---|
| `accounts` | Authentication, roles (Staff/Admin), staff management (Sprint 1) |
| `catalog` | Products & categories (Sprint 2+) |
| `suppliers` | Supplier management |
| `transactions` | Stock-in / stock-out |
| `reports` | Reports & low-stock alerts |

## Setup
```bash
git clone https://github.com/<org>/SE_ESIMS_Project_2026.git
cd SE_ESIMS_Project_2026
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                # Windows: copy .env.example .env

docker compose up -d db             # starts PostgreSQL (or use your own local PostgreSQL)
python manage.py migrate
python manage.py seed_demo_users    # DEMO users only: admin / staff1
python manage.py runserver
```
Open http://127.0.0.1:8000/ and log in.

Demo credentials (local only): `admin / Admin@12345`, `staff1 / Staff@12345`

## Run tests
Without PostgreSQL (quick):
```bash
DB_ENGINE=sqlite python manage.py test          # Windows PowerShell: $env:DB_ENGINE="sqlite"; python manage.py test
```
Coverage (line + branch):
```bash
DB_ENGINE=sqlite coverage run --branch --source=accounts manage.py test
coverage report -m
```

## Branching & workflow
- `main` is protected; work on `feature/ESIMS-<n>-<short-name>` branches.
- One PR per story, reviewed by a teammate, with `Closes #<issue>` in the description.
