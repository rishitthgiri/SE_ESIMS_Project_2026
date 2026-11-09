"""ST-AVAIL-01 supporting check: does /health/ notice a database outage and notice the recovery?

Stops PostgreSQL, polls /health/ twice a second, starts PostgreSQL again and records how
long the monitor would have seen the service as DOWN.
"""
import json
import subprocess
import time
import urllib.error
import urllib.request

URL = 'http://127.0.0.1:8765/health/'


def status():
    try:
        return urllib.request.urlopen(URL, timeout=5).status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


log = []
def poll(seconds):
    end = time.time() + seconds
    while time.time() < end:
        log.append((time.time(), status()))
        time.sleep(0.5)

poll(3)
t_stop = time.time()
subprocess.run(['pg_ctlcluster', '16', 'main', 'stop', '-m', 'fast'], check=True)
poll(6)
t_start = time.time()
subprocess.run(['pg_ctlcluster', '16', 'main', 'start'], check=True)
poll(10)

before = [s for t, s in log if t < t_stop]
during = [s for t, s in log if t_stop <= t < t_start]
after = [(t, s) for t, s in log if t >= t_start]
recovered = next((t for t, s in after if s == 200), None)
result = {
    'before_outage': sorted(set(before)),
    'during_outage_codes': sorted(set(during)),
    'down_checks': during.count(503),
    'recovered_after_seconds': round(recovered - t_start, 1) if recovered else None,
    'checks_total': len(log),
}
print(json.dumps(result, indent=2))
json.dump(result, open('/home/claude/evidence/outage_check_results.json', 'w'), indent=2)
