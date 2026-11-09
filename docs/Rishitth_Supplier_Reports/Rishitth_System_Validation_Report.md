# System Validation Report: Supplier, Alerts and Reports

|  |  |
| --- | --- |
| Project | ESIMS: Electronics Store Inventory Management System (Team 8) |
| Module | Supplier management, low-stock alerts, reports, health check (ESIMS-26 to ESIMS-35) |
| Feature Test Owner | Rishitth G R |
| Report version / date | 1.0 / 09 / 11 / 2026 |
| Build tested | `6d6f97e` (main) plus the Phase 3 test additions listed in the Unit Test Report |
| Related documents | Software Test Plan (`ESIMS_STP_Team_8.pdf`), `docs/DEVIATIONS.md`, `docs/DEPLOYMENT.md` |

## 1. Purpose and scope

Validation of the finished workflows against the Software Test Plan, through the running web application and not through the test framework. It covers supplier management, supplier link on stock-in, low-stock alerts, reports and CSV export, top sellers, access rules for Staff and logged-out visitors, and availability evidence for NFR-002.

## 2. Method and environment

| Item | Value |
| --- | --- |
| Operating system | Linux x86_64 (Ubuntu 24.04), cloud test machine |
| Python / Django | Python 3.12.3 / Django 5.2.18 |
| Database (primary) | PostgreSQL 16.15 (the STP names 15.x; same behaviour for these tests) |
| Database (second run) | SQLite in memory (`DB_ENGINE=sqlite`, what GitHub Actions uses) |
| Test runner | Django test runner: `python manage.py test` |
| Coverage tool | coverage.py 7.17.0 with `--branch` |
| Live server (system validation) | gunicorn 26.2.0, 3 workers, PostgreSQL |

A script (`scripts/system_validation.py`) drives the running server over real HTTP the way a browser does: it opens the login page, submits forms with the CSRF token and hidden fields, keeps cookies, and checks redirects, status codes and page content. Data is created through the application's own forms (category, products, suppliers, stock-in and stock-out). The server ran on a freshly created PostgreSQL database with the demo users from `seed_demo_users`. Run started 2026-11-09 04:42:38.

## 3. Result

**28 of 28 checks passed, 0 failed.**

| Check | STP test | Req | Action | Expected | Actual | Result |
| --- | --- | --- | --- | --- | --- | --- |
| SV-01 | ST-SEC-05 | SEC-005 | Open 6 protected pages (suppliers, products, transactions, 2 reports, low stock) while logged out | Every page redirects (302) to the login page | All 6 redirected to /login/ | PASS |
| SV-02 | ST-AVAIL-01 | NFR-002 | Open /health/ while logged out | HTTP 200 and {"status": "ok"}, no data | HTTP 200 {"status": "ok"} | PASS |
| SV-03 | UT-AUTH-01 | FR-001 | Log in as Administrator (admin) | Redirect to the dashboard (302 to /) | HTTP 302 -> / | PASS |
| SV-04 | UT-SUP-01 | FR-015 | Add supplier "Zenith Distributors d5a71b" | Redirect to list; supplier shown as Active | HTTP 302; listed=True | PASS |
| SV-05 | UT-SUP-01 | FR-015 | Edit the supplier contact | Redirect to list; new contact shown | HTTP 302; new contact shown=True | PASS |
| SV-06 | UT-SUP-01 | FR-015 | Add a second supplier with the same name in capitals | Rejected: "already exists", page stays on the form (200) | HTTP 200; message shown=True | PASS |
| SV-07 | ST-SEC-03 | SEC-003 | Add a supplier with a blank name | Rejected (200), nothing saved | HTTP 200 | PASS |
| SV-08 | UT-CAT-01 | FR-005 | Set-up: create a category and two products (thresholds 5 and 2) | Both products appear in the catalog | found=True | PASS |
| SV-09 | IT-SUP-02 | FR-016 | Stock-in 10 x Alpha from Zenith | Redirect to transactions; list shows the supplier name | HTTP 302; supplier on list=True | PASS |
| SV-10 | IT-SUP-02 | FR-016 | Stock-in with NO supplier chosen | Rejected (200), no transaction saved | HTTP 200 | PASS |
| SV-11 | IT-SUP-02 | FR-016 | Open the supplier page for Zenith | Shows the Alpha stock-in of 10 | HTTP 200; Alpha shown=True | PASS |
| SV-12 | ST-ALERT-01 | FR-017 | Sell 5 so stock (5) EQUALS the threshold (5) | Alpha is NOT in the low-stock list | Alpha listed in table=False | PASS |
| SV-13 | ST-ALERT-01 | FR-017 | Sell 1 more so stock (4) is BELOW the threshold (5) | Alpha is in the low-stock list and on the dashboard | low-stock table=True; dashboard table=True | PASS |
| SV-14 | UT-STOCK-02 | FR-012 | Try to sell 99 when only 4 are in stock | Rejected (200), stock unchanged | HTTP 200 | PASS |
| SV-15 | ST-ALERT-01 | FR-017 | Restock 20 so stock (24) is above the threshold | Alpha disappears from the low-stock list | Alpha listed in table=False | PASS |
| SV-16 | IT-SUP-02 | FR-015/016 | Disable supplier Orbit, then open the stock-in form | Orbit is no longer offered; supplier still in the list as Disabled | disable HTTP 302; offered=False; listed=True | PASS |
| SV-17 | UT-SUP-01 | FR-015 | Open the disable URL with GET (not POST) | HTTP 405, nothing changes | HTTP 405 | PASS |
| SV-18 | ST-REPORT-01 | FR-018 | Open the stock/sales report (default last 30 days) | Sales table and totals shown; both products listed | HTTP 200; Alpha=True; Beta=True | PASS |
| SV-19 | ST-REPORT-01 | FR-018 | Export the sales CSV for today and add up our two products | Header as specified; Alpha 6 units = 1500.00; Beta 35 units = 3500.00 | HTTP 200; text/csv; Alpha 6 units = 1500.00; Beta 35 units = 3500.00 | PASS |
| SV-20 | ST-REPORT-01 | FR-018 | Export the stock CSV and check stock value = quantity x price | Alpha 24 x 250.00 = 6000.00; Beta 15 x 100.00 = 1500.00 | Alpha 24 -> 6000.00; Beta 15 -> 1500.00 | PASS |
| SV-21 | ST-REPORT-01 | FR-018 | Ask for a range where the start date is after the end date | Error message, no report (200) | HTTP 200; message=True | PASS |
| SV-22 | ST-REPORT-01 | FR-018 | Ask for a month with no sales (January 2020) | "No sales in this date range." and 0 units | HTTP 200; empty message=True | PASS |
| SV-23 | ST-REPORT-02 | FR-019 | Open top-selling products | Beta (35 units) is ranked above Alpha (6 units) | HTTP 200; Beta position=2881; Alpha position=3081 | PASS |
| SV-24 | UT-AUTH-01 | FR-001 | Log in as Staff (staff1) | Redirect to the dashboard | HTTP 302 -> / | PASS |
| SV-25 | ST-SEC-02 | SEC-002 | As Staff open suppliers, supplier page, sales report, top sellers | All four show 403 Forbidden | /suppliers/=403, /suppliers/81dae9ec-2100-48b6-9b06-adb55f80f063/=403, /reports/sales/=403, /reports/top-selling/=403 | PASS |
| SV-26 | ST-ALERT-01 | FR-017 | As Staff open the low-stock list | HTTP 200 (visible to Staff and Administrator) | HTTP 200 | PASS |
| SV-27 | IT-STOCK-02 | FR-011 | As Staff record a stock-out; check Staff only see their own transactions | Sale accepted; list shows own sale but not the administrator's Zenith stock-in | HTTP 302; Zenith in staff list=False | PASS |
| SV-28 | ST-AVAIL-01 | NFR-002 | Poll /health/ once a second for 120 seconds | 100% of checks HTTP 200 (target 99% of business hours) | 119/119 checks = 100.00% available; latency median 10.7 ms, 95th percentile 15.0 ms | PASS |

## 4. Availability evidence (ST-AVAIL-01, ST-AVAIL-02, NFR-002)

| Evidence | Result |
| --- | --- |
| Health page without login | HTTP 200, {"status": "ok"}, no data shown (SV-02) |
| Two-minute sample, one check per second | 119/119 checks = 100.00% available; latency median 10.7 ms, 95th percentile 15.0 ms (SV-28) |
| Database stopped for about 6 seconds | 12 checks returned HTTP 503 and nothing else; before the outage every check returned 200 |
| Recovery after the database was started again | /health/ answered 200 again 2.2 seconds after the start command |

This shows the health page works as a monitor input: it reports an outage as 503 and reports the recovery. It does **not** prove 99% availability over business hours, which needs monitoring over weeks as planned in `docs/DEPLOYMENT.md`. ST-AVAIL-01 is therefore recorded as passed for the sample and open for the long-term target.

## 5. STP exit criteria for this module

| Exit criterion | Status |
| --- | --- |
| All planned test cases executed | Yes: 8 of 8 planned cases (UT-SUP-01, IT-SUP-02, UT-ALERT-01, ST-ALERT-01, ST-REPORT-01, ST-REPORT-02, ST-AVAIL-01, ST-SEC-05) plus 9 added cases |
| Critical / high severity blockers | None found |
| NFR thresholds evaluated | NFR-002: sample only (see section 4). NFR-001 belongs to the Catalog owner |
| Security-critical tests completed | SEC-005 passed (SV-01 and the automated URL crawl). SEC-002 on supplier and report pages passed (SV-25) |
| RTM updated with execution evidence | Yes: Test Case Document section 4 |

## 6. Limits of this validation

- The checks use HTTP requests, not a real browser. Page layout, colours and clicking were not tested, and there are no screenshots. The STP's Chrome, Edge and Firefox checks were not run here.
- The server was reached over HTTP on the local machine. HTTPS and nginx are described in `docs/DEPLOYMENT.md` but were not part of this run.
- Load and performance testing of catalog search (NFR-001) is the Catalog owner's.
- The tests ran in a cloud test machine, not on a store server.

## 7. Raw evidence

`evidence/system_validation_results.json`, `evidence/system_validation_output.txt`, `evidence/outage_check_results.json`, `evidence/gunicorn.log`, and the scripts in `scripts/`.
