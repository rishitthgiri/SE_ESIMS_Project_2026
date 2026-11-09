"""System validation walkthrough for the Supplier / Alerts / Reports features (Rishitth G R).

Drives a RUNNING ESIMS server over real HTTP (login form, CSRF, cookies, redirects) the way a
browser would. It records one row per check with the STP test ID, expected and actual result.

    python system_validation.py http://127.0.0.1:8765 results.json

Needs the demo users from `python manage.py seed_demo_users`. Creates its own uniquely named data.
"""
import csv
import http.cookiejar
import io
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime

BASE = sys.argv[1].rstrip('/') if len(sys.argv) > 1 else 'http://127.0.0.1:8000'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'system_validation_results.json'
RUN = uuid.uuid4().hex[:6]
RESULTS = []


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class Browser:
    def __init__(self):
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar), NoRedirect)

    def _do(self, req):
        started = time.perf_counter()
        try:
            r = self.opener.open(req, timeout=20)
            status, headers, body = r.status, r.headers, r.read()
        except urllib.error.HTTPError as e:
            status, headers, body = e.code, e.headers, e.read()
        return Resp(status, headers, body, time.perf_counter() - started)

    def get(self, path):
        return self._do(urllib.request.Request(BASE + path))

    def follow(self, path, limit=5):
        r = self.get(path)
        while r.status in (301, 302) and limit:
            r = self.get(urllib.parse.urlparse(r.headers['Location']).path +
                         ('?' + urllib.parse.urlparse(r.headers['Location']).query
                          if urllib.parse.urlparse(r.headers['Location']).query else ''))
            limit -= 1
        return r

    def csrf(self):
        for c in self.jar:
            if c.name == 'csrftoken':
                return c.value
        return ''

    def post(self, path, data):
        if not self.csrf():
            self.get('/login/')
        data = dict(data, csrfmiddlewaretoken=self.csrf())
        body = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(BASE + path, data=body, headers={'Referer': BASE + path})
        return self._do(req)

    def login(self, username, password):
        self.get('/login/')
        return self.post('/login/', {'username': username, 'password': password})

    def submit_form(self, path, data):
        """GET the page first (to receive hidden tokens), then POST like a browser."""
        page = self.get(path)
        hidden = dict(re.findall(r'<input type="hidden" name="(?!csrfmiddlewaretoken)([^"]+)" value="([^"]*)"', page.text))
        return self.post(path, {**hidden, **data})


class Resp:
    def __init__(self, status, headers, body, seconds):
        self.status, self.headers, self.body, self.seconds = status, headers, body, seconds

    @property
    def text(self):
        return self.body.decode('utf-8', 'replace')

    @property
    def location(self):
        return self.headers.get('Location', '')


def record(sid, stp, req, action, expected, actual, ok):
    RESULTS.append({'id': sid, 'stp': stp, 'requirement': req, 'action': action, 'expected': expected,
                    'actual': actual, 'status': 'PASS' if ok else 'FAIL',
                    'time': datetime.now().strftime('%H:%M:%S')})
    print(f"{sid:7} {stp:13} {'PASS' if ok else 'FAIL'}  {action}")


def option_value(html, label_part):
    m = re.search(r'<option value="([^"]+)"[^>]*>\s*([^<]*' + re.escape(label_part) + r'[^<]*)</option>', html)
    return m.group(1) if m else None


def tables(html):
    """Only the <table> parts of a page (flash messages such as 'Alpha stock is now 5' are ignored)."""
    return ' '.join(re.findall(r'<table.*?</table>', html, re.S))


def txt(html):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html))


SUPP = f'Zenith Distributors {RUN}'
SUPP2 = f'Orbit Wholesale {RUN}'
CAT = f'Phones {RUN}'
P1, P2 = f'Alpha Phone {RUN}', f'Beta Phone {RUN}'

# ---------------------------------------------------------------- SV-01 logged out (ST-SEC-05 / SEC-005)
anon = Browser()
pages = ['/suppliers/', '/catalog/products/', '/transactions/', '/reports/sales/', '/reports/top-selling/', '/reports/low-stock/']
bad = []
for p in pages:
    r = anon.get(p)
    if not (r.status == 302 and '/login/' in r.location):
        bad.append(f'{p} -> {r.status}')
record('SV-01', 'ST-SEC-05', 'SEC-005', 'Open 6 protected pages (suppliers, products, transactions, 2 reports, low stock) while logged out',
       'Every page redirects (302) to the login page', 'All 6 redirected to /login/' if not bad else '; '.join(bad), not bad)
r = anon.get('/health/')
record('SV-02', 'ST-AVAIL-01', 'NFR-002', 'Open /health/ while logged out', 'HTTP 200 and {"status": "ok"}, no data',
       f'HTTP {r.status} {r.text.strip()}', r.status == 200 and json.loads(r.text) == {'status': 'ok'})

# ---------------------------------------------------------------- Administrator
admin = Browser()
r = admin.login('admin', 'Admin@12345')
record('SV-03', 'UT-AUTH-01', 'FR-001', 'Log in as Administrator (admin)', 'Redirect to the dashboard (302 to /)',
       f'HTTP {r.status} -> {r.location}', r.status == 302 and r.location in ('/', ''))

# Supplier CRUD (UT-SUP-01 / FR-015)
r = admin.submit_form('/suppliers/add/', {'name': SUPP, 'contact': 'zenith@example.test'})
lst = admin.get('/suppliers/')
record('SV-04', 'UT-SUP-01', 'FR-015', f'Add supplier "{SUPP}"', 'Redirect to list; supplier shown as Active',
       f'HTTP {r.status}; listed={SUPP in lst.text}', r.status == 302 and SUPP in lst.text)
sid = re.search(r'/suppliers/([0-9a-f-]{36})/">' + re.escape(SUPP) + '<', lst.text)
sid = sid.group(1) if sid else None
r = admin.submit_form(f'/suppliers/{sid}/edit/', {'name': SUPP, 'contact': 'sales@zenith.test'})
lst = admin.get('/suppliers/')
record('SV-05', 'UT-SUP-01', 'FR-015', 'Edit the supplier contact', 'Redirect to list; new contact shown',
       f'HTTP {r.status}; new contact shown={"sales@zenith.test" in lst.text}', r.status == 302 and 'sales@zenith.test' in lst.text)
r = admin.submit_form('/suppliers/add/', {'name': SUPP.upper(), 'contact': ''})
record('SV-06', 'UT-SUP-01', 'FR-015', 'Add a second supplier with the same name in capitals', 'Rejected: "already exists", page stays on the form (200)',
       f'HTTP {r.status}; message shown={"already exists" in r.text}', r.status == 200 and 'already exists' in r.text)
r = admin.submit_form('/suppliers/add/', {'name': '   ', 'contact': ''})
record('SV-07', 'ST-SEC-03', 'SEC-003', 'Add a supplier with a blank name', 'Rejected (200), nothing saved',
       f'HTTP {r.status}', r.status == 200)
admin.submit_form('/suppliers/add/', {'name': SUPP2, 'contact': 'orbit@example.test'})

# Category and products (set-up data through the UI)
admin.submit_form('/catalog/categories/add/', {'name': CAT, 'status': 'active'})
cat_page = admin.get('/catalog/products/add/')
cat_id = option_value(cat_page.text, CAT)
for sku, name, thr in (('A-' + RUN, P1, 5), ('B-' + RUN, P2, 2)):
    admin.submit_form('/catalog/products/add/', {'sku': sku, 'name': name, 'category': cat_id, 'price': '250.00' if sku[0] == 'A' else '100.00',
                                                  'reorder_threshold': thr, 'supplier': '', 'status': 'active'})
products = admin.get('/catalog/products/?q=' + RUN)
record('SV-08', 'UT-CAT-01', 'FR-005', 'Set-up: create a category and two products (thresholds 5 and 2)', 'Both products appear in the catalog',
       f'found={P1 in products.text and P2 in products.text}', P1 in products.text and P2 in products.text)

# Stock-in linked to supplier (IT-SUP-02 / FR-016)
form = admin.get('/transactions/in/')
p1_id = option_value(form.text, P1)
p2_id = option_value(form.text, P2)
s1_id = option_value(form.text, SUPP)
s2_id = option_value(form.text, SUPP2)
r = admin.submit_form('/transactions/in/', {'product': p1_id, 'supplier': s1_id, 'quantity': 10})
tl = admin.get('/transactions/')
record('SV-09', 'IT-SUP-02', 'FR-016', 'Stock-in 10 x Alpha from Zenith', 'Redirect to transactions; list shows the supplier name',
       f'HTTP {r.status}; supplier on list={SUPP in tl.text}', r.status == 302 and SUPP in tl.text)
r = admin.submit_form('/transactions/in/', {'product': p1_id, 'supplier': '', 'quantity': 5})
record('SV-10', 'IT-SUP-02', 'FR-016', 'Stock-in with NO supplier chosen', 'Rejected (200), no transaction saved',
       f'HTTP {r.status}', r.status == 200)
detail = admin.get(f'/suppliers/{s1_id}/')
record('SV-11', 'IT-SUP-02', 'FR-016', 'Open the supplier page for Zenith', 'Shows the Alpha stock-in of 10',
       f'HTTP {detail.status}; Alpha shown={P1 in detail.text}', detail.status == 200 and P1 in detail.text)

# Low-stock alert (ST-ALERT-01 / FR-017)
admin.submit_form('/transactions/out/', {'product': p1_id, 'quantity': 5})   # 10 -> 5 (equal threshold)
low = admin.get('/reports/low-stock/')
record('SV-12', 'ST-ALERT-01', 'FR-017', 'Sell 5 so stock (5) EQUALS the threshold (5)', 'Alpha is NOT in the low-stock list',
       f'Alpha listed in table={P1 in tables(low.text)}', P1 not in tables(low.text))
admin.submit_form('/transactions/out/', {'product': p1_id, 'quantity': 1})   # 5 -> 4
low = admin.get('/reports/low-stock/')
dash = admin.get('/')
record('SV-13', 'ST-ALERT-01', 'FR-017', 'Sell 1 more so stock (4) is BELOW the threshold (5)', 'Alpha is in the low-stock list and on the dashboard',
       f'low-stock table={P1 in tables(low.text)}; dashboard table={P1 in tables(dash.text)}', P1 in tables(low.text) and P1 in tables(dash.text))
r = admin.submit_form('/transactions/out/', {'product': p1_id, 'quantity': 99})
record('SV-14', 'UT-STOCK-02', 'FR-012', 'Try to sell 99 when only 4 are in stock', 'Rejected (200), stock unchanged',
       f'HTTP {r.status}', r.status == 200)
admin.submit_form('/transactions/in/', {'product': p1_id, 'supplier': s1_id, 'quantity': 20})   # 4 -> 24
low = admin.get('/reports/low-stock/')
record('SV-15', 'ST-ALERT-01', 'FR-017', 'Restock 20 so stock (24) is above the threshold', 'Alpha disappears from the low-stock list',
       f'Alpha listed in table={P1 in tables(low.text)}', P1 not in tables(low.text))

# Disabled supplier
r = admin.post(f'/suppliers/{s2_id}/disable/', {})
form = admin.get('/transactions/in/')
record('SV-16', 'IT-SUP-02', 'FR-015/016', 'Disable supplier Orbit, then open the stock-in form', 'Orbit is no longer offered; supplier still in the list as Disabled',
       f'disable HTTP {r.status}; offered={option_value(form.text, SUPP2) is not None}; listed={SUPP2 in admin.get("/suppliers/").text}',
       r.status == 302 and option_value(form.text, SUPP2) is None and SUPP2 in admin.get('/suppliers/').text)
r = admin.get(f'/suppliers/{s2_id}/disable/')
record('SV-17', 'UT-SUP-01', 'FR-015', 'Open the disable URL with GET (not POST)', 'HTTP 405, nothing changes', f'HTTP {r.status}', r.status == 405)

# Sales for the reports: Beta sells more than Alpha
admin.submit_form('/transactions/in/', {'product': p2_id, 'supplier': s1_id, 'quantity': 50})
admin.submit_form('/transactions/out/', {'product': p2_id, 'quantity': 30})
admin.submit_form('/transactions/out/', {'product': p2_id, 'quantity': 5})

# Reports (ST-REPORT-01 / FR-018)
rep = admin.get('/reports/sales/')
text = txt(rep.text)
# Alpha sold 5+1 = 6 x 250.00 = 1500.00 ; Beta sold 35 x 100.00 = 3500.00 (plus any earlier data)
record('SV-18', 'ST-REPORT-01', 'FR-018', 'Open the stock/sales report (default last 30 days)', 'Sales table and totals shown; both products listed',
       f'HTTP {rep.status}; Alpha={P1 in rep.text}; Beta={P2 in rep.text}', rep.status == 200 and P1 in rep.text and P2 in rep.text)
today = datetime.now().strftime('%Y-%m-%d')
csvr = admin.get(f'/reports/sales/?start={today}&end={today}&export=sales')
rows = list(csv.reader(io.StringIO(csvr.text)))
mine = [r for r in rows[1:] if r[1] in (P1, P2)]
units = {P1: 0, P2: 0}
amount = {P1: 0.0, P2: 0.0}
for r_ in mine:
    units[r_[1]] += int(r_[2]); amount[r_[1]] += float(r_[3])
ok = rows[0] == ['Transaction reference', 'Product', 'Quantity sold', 'Sale amount', 'Date', 'Staff member'] and \
    units == {P1: 6, P2: 35} and abs(amount[P1] - 1500) < 0.01 and abs(amount[P2] - 3500) < 0.01
record('SV-19', 'ST-REPORT-01', 'FR-018', 'Export the sales CSV for today and add up our two products', 'Header as specified; Alpha 6 units = 1500.00; Beta 35 units = 3500.00',
       f'HTTP {csvr.status}; {csvr.headers.get("Content-Type")}; Alpha {units[P1]} units = {amount[P1]:.2f}; Beta {units[P2]} units = {amount[P2]:.2f}',
       ok and csvr.status == 200)
stock_csv = admin.get(f'/reports/sales/?start={today}&end={today}&export=stock')
srows = [r for r in csv.reader(io.StringIO(stock_csv.text)) if r and r[0] in (P1, P2)]
by = {r[0]: r for r in srows}
ok = by[P1][3] == '24' and by[P1][5] == '6000.00' and by[P2][3] == '15' and by[P2][5] == '1500.00'
record('SV-20', 'ST-REPORT-01', 'FR-018', 'Export the stock CSV and check stock value = quantity x price', 'Alpha 24 x 250.00 = 6000.00; Beta 15 x 100.00 = 1500.00',
       f'Alpha {by[P1][3]} -> {by[P1][5]}; Beta {by[P2][3]} -> {by[P2][5]}', ok)
r = admin.get('/reports/sales/?start=2026-12-31&end=2026-01-01')
record('SV-21', 'ST-REPORT-01', 'FR-018', 'Ask for a range where the start date is after the end date', 'Error message, no report (200)',
       f'HTTP {r.status}; message={"start date must be on or before" in r.text}', r.status == 200 and 'start date must be on or before' in r.text)
r = admin.get('/reports/sales/?start=2020-01-01&end=2020-01-31')
record('SV-22', 'ST-REPORT-01', 'FR-018', 'Ask for a month with no sales (January 2020)', '"No sales in this date range." and 0 units',
       f'HTTP {r.status}; empty message={"No sales in this date range" in r.text}', r.status == 200 and 'No sales in this date range' in r.text)

# Top selling (ST-REPORT-02 / FR-019)
ts = admin.get('/reports/top-selling/')
i1, i2 = ts.text.find(P1), ts.text.find(P2)
record('SV-23', 'ST-REPORT-02', 'FR-019', 'Open top-selling products', 'Beta (35 units) is ranked above Alpha (6 units)',
       f'HTTP {ts.status}; Beta position={i2}; Alpha position={i1}', ts.status == 200 and 0 < i2 < i1)

# ---------------------------------------------------------------- Staff
staff = Browser()
r = staff.login('staff1', 'Staff@12345')
record('SV-24', 'UT-AUTH-01', 'FR-001', 'Log in as Staff (staff1)', 'Redirect to the dashboard', f'HTTP {r.status} -> {r.location}', r.status == 302)
codes = {p: staff.get(p).status for p in ('/suppliers/', f'/suppliers/{s1_id}/', '/reports/sales/', '/reports/top-selling/')}
record('SV-25', 'ST-SEC-02', 'SEC-002', 'As Staff open suppliers, supplier page, sales report, top sellers', 'All four show 403 Forbidden',
       ', '.join(f'{k}={v}' for k, v in codes.items()), all(v == 403 for v in codes.values()))
low = staff.get('/reports/low-stock/')
record('SV-26', 'ST-ALERT-01', 'FR-017', 'As Staff open the low-stock list', 'HTTP 200 (visible to Staff and Administrator)', f'HTTP {low.status}', low.status == 200)
r = staff.submit_form('/transactions/out/', {'product': p2_id, 'quantity': 1})
mine_list = staff.get('/transactions/')
record('SV-27', 'IT-STOCK-02', 'FR-011', 'As Staff record a stock-out; check Staff only see their own transactions', 'Sale accepted; list shows own sale but not the administrator\'s Zenith stock-in',
       f'HTTP {r.status}; Zenith in staff list={SUPP in mine_list.text}', r.status == 302 and SUPP not in mine_list.text)

# ---------------------------------------------------------------- Availability sample (ST-AVAIL-01 / NFR-002)
if '--no-sample' not in sys.argv:
    SECONDS = 120
    codes, lat = [], []
    t_end = time.time() + SECONDS
    while time.time() < t_end:
        r = anon.get('/health/')
        codes.append(r.status); lat.append(r.seconds * 1000)
        time.sleep(1)
    lat.sort()
    ok_n = codes.count(200)
    p95 = lat[int(len(lat) * 0.95) - 1]
    record('SV-28', 'ST-AVAIL-01', 'NFR-002', f'Poll /health/ once a second for {SECONDS} seconds', '100% of checks HTTP 200 (target 99% of business hours)',
           f'{ok_n}/{len(codes)} checks = {100 * ok_n / len(codes):.2f}% available; latency median {lat[len(lat) // 2]:.1f} ms, 95th percentile {p95:.1f} ms',
           ok_n / len(codes) >= 0.99)

failed = [r for r in RESULTS if r['status'] == 'FAIL']
print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
json.dump({'run': RUN, 'base': BASE, 'started': datetime.now().isoformat(timespec='seconds'), 'results': RESULTS}, open(OUT, 'w'), indent=2)
sys.exit(1 if failed else 0)
