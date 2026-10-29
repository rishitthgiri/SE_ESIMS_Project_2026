# Demo users (seed)

One command creates a login for every kind of user ESIMS has. Anyone on the team can run it
after `python manage.py migrate`:

```bash
python manage.py seed_demo_users            # safe to re-run: existing users are left alone
python manage.py seed_demo_users --reset    # put the demo users back to the table below
```

| Username | Password | Role | What it is for |
|---|---|---|---|
| `admin` | `Admin@12345` | Administrator + Django superuser | Everything, including Django `/admin/` |
| `manager` | `Admin@12345` | Administrator (not superuser) | Proves the Administrator role works on its own |
| `staff1` | `Staff@12345` | Staff | Day-to-day user: stock-in/out, own transactions |
| `staff2` | `Staff@12345` | Staff | Second Staff user (test "only my transactions") |
| `inactive_staff` | `Staff@12345` | Staff, **deactivated** | Login must be refused (ESIMS-05) |

Log in with the **username or the email** (`<username>@esims.local`; `inactive_staff` uses `inactive@esims.local`).

* **Demo only.** The command refuses to run when `DEBUG` is off (add `--force` to override - never in production).
* To use one password for all demo users: set `ESIMS_SEED_PASSWORD` before running the command.
* Passwords are stored hashed (PBKDF2) like any other user; the values above exist only in this file and the seed script.
