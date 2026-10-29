# Deployment and availability notes (ESIMS-34 / NFR-002)

NFR-002: the application shall be available **at least 99% of defined business hours**, excluding planned maintenance.
This page says how ESIMS is deployed, how that target is measured, and how we recover from a failure.

## 1. Defined business hours and what 99% means
| Item | Value (store owner may change these) |
|---|---|
| Business hours | Monday to Saturday, 09:00 to 21:00 (12 h x 26 days = 312 h per month) |
| Planned maintenance window | Sunday 02:00 to 04:00 (excluded from the 99% figure) |
| Allowed unplanned downtime | 1% of 312 h = **about 3 hours per month** |

Availability % = (business minutes with a successful health check / business minutes) x 100.

## 2. What we deploy
| Part | Choice |
|---|---|
| Server | Linux (Ubuntu 22.04 or later), 1 vCPU / 1 GB RAM is enough for one store |
| App server | gunicorn running the Django project (`esims.wsgi:application`) |
| Web server | nginx in front: HTTPS (SEC / SRS section on communication), static files, proxy to gunicorn |
| Database | PostgreSQL 16 (`docker-compose.yml` has the same version for local work) |
| Process manager | systemd, `Restart=always`, so a crashed app comes back by itself |

## 3. Environment variables
Copy `.env.example`, never commit the real file.

| Variable | Production value |
|---|---|
| `DJANGO_SECRET_KEY` | a long random string, different from development |
| `DJANGO_DEBUG` | `0` |
| `DJANGO_ALLOWED_HOSTS` | the real host name(s), comma separated, e.g. `esims.example.com` |
| `DB_ENGINE` | `postgres` (anything else uses SQLite, local work only) |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | the PostgreSQL connection |
| `SESSION_TIMEOUT_SECONDS` | idle timeout, default 1800 (30 minutes) |

Generate a secret key: `python -c "import secrets; print(secrets.token_urlsafe(50))"`

## 4. First deployment (Ubuntu)
```bash
sudo apt update && sudo apt install -y python3-venv postgresql nginx
sudo -u postgres psql -c "CREATE USER esims WITH PASSWORD 'CHANGE-ME';"
sudo -u postgres psql -c "CREATE DATABASE esims OWNER esims;"

git clone https://github.com/rishitthgiri/SE_ESIMS_Project_2026.git /srv/esims
cd /srv/esims
python3 -m venv venv && . venv/bin/activate
pip install -r requirements.txt gunicorn
# put the variables from section 3 in /srv/esims/.env (chmod 600)

set -a; . ./.env; set +a
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser        # then set this user's role to Administrator
```
`/etc/systemd/system/esims.service`:
```ini
[Unit]
Description=ESIMS (gunicorn)
After=network.target postgresql.service

[Service]
WorkingDirectory=/srv/esims
EnvironmentFile=/srv/esims/.env
ExecStart=/srv/esims/venv/bin/gunicorn esims.wsgi:application --bind 127.0.0.1:8000 --workers 3
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload && sudo systemctl enable --now esims
```
nginx (inside the HTTPS `server` block): serve `/static/` from `/srv/esims/staticfiles/` and `proxy_pass http://127.0.0.1:8000;` for everything else, with `proxy_set_header Host $host;` and `proxy_set_header X-Forwarded-Proto $scheme;`.

## 5. Updating the running system (planned maintenance)
Do this inside the Sunday maintenance window.
```bash
cd /srv/esims && . venv/bin/activate && set -a && . ./.env && set +a
git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart esims
curl -fsS https://esims.example.com/health/        # must print {"status": "ok"}
```
If the new version is broken: `git checkout <previous-tag>`, run the same commands, and restore the database backup if a migration was involved.

## 6. Monitoring (how we measure the 99%)
* `GET /health/` is public, shows no data, and returns `{"status": "ok"}` (HTTP 200) when the app can reach the database, or HTTP 503 when it cannot.
* Check it every minute from outside the server (UptimeRobot or any similar monitor, or `* * * * * curl -fsS -m 10 https://esims.example.com/health/ || echo down >> /var/log/esims-down.log`).
* At month end: count failed checks inside business hours and apply the formula in section 1. Keep the figure as evidence for ST-AVAIL-01.

## 7. Backups and recovery
* Nightly dump (cron, 01:00): `pg_dump -U esims esims | gzip > /var/backups/esims/esims-$(date +%F).sql.gz`, keep 14 days.
* Restore: `gunzip -c esims-YYYY-MM-DD.sql.gz | psql -U esims esims` on an empty database.
* Stock transactions are never edited or deleted by the app, so the backup is also the audit history.

## 8. Known gaps (be honest in the final demo)
* Production HTTPS is handled by nginx, but the Django settings for secure cookies and HTTPS redirects (`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`) are not switched on yet. `python manage.py check --deploy` lists them. Turn them on once the site is served over HTTPS.
* Availability has not been measured over a real month; the plan above is the method. The project demo runs locally on SQLite.
