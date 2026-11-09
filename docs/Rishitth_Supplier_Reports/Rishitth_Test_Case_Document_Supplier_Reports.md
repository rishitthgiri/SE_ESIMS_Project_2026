# Updated Test Case Document: Supplier, Alerts and Reports

|  |  |
| --- | --- |
| Project | ESIMS: Electronics Store Inventory Management System (Team 8) |
| Module | Supplier management, low-stock alerts, reports, health check (ESIMS-26 to ESIMS-35) |
| Feature Test Owner | Rishitth G R |
| Report version / date | 1.0 / 09 / 11 / 2026 |
| Build tested | `6d6f97e` (main) plus the Phase 3 test additions listed in the Unit Test Report |
| Related documents | Software Test Plan (`ESIMS_STP_Team_8.pdf`), `docs/DEVIATIONS.md`, `docs/DEPLOYMENT.md` |

## 1. Purpose

This document updates the Supplier / Alerts / Reports test cases that Rishitth G R wrote in section 13 of the Software Test Plan (`ESIMS_STP_Team_8.pdf`), so they match what was actually built during Sprint 1 and Sprint 2. The submitted STP PDF stays as the baseline. Where the build changed, the case is marked **Updated**; cases added because of new behaviour are marked **New**. Every case now shows its real execution result.

## 2. What changed in the build, and which cases it affects

| Requirement | Planned in the STP | Built | Cases |
| --- | --- | --- | --- |
| FR-015 supplier CRUD | Admin adds, edits and removes a supplier | "Remove" is a soft delete (status Disabled). Names must be unique (any letter case). Administrator only. Disable works only by POST. List can be filtered by status. | UT-SUP-01, 02, 03 |
| FR-016 supplier on stock-in | Transaction references the supplier | Disabled suppliers cannot be used for new stock-ins. Supplier name is on the transaction list. Each supplier has a page listing its stock-ins. | IT-SUP-02, 03, 04 |
| FR-017 low-stock alert | Alert when quantity is below the threshold | Computed from Product data (no alert table). Strictly below the threshold. Active products only. Shown on the dashboard and at /reports/low-stock/ for Staff and Administrator. | UT-ALERT-01, ST-ALERT-01, 02 |
| FR-018 report for a date range | Aggregated stock/sales report | Administrator-only page with a date range (default last 30 days), a sales table, a stock table and CSV export. Sale amount = quantity x current price. | ST-REPORT-01, 03, 04, 05 |
| FR-019 top-selling products | Items ranked from recorded sales | Top 10 by units sold; optional date range; ties by name; Administrator only. | ST-REPORT-02, 04 |
| NFR-002 availability | Observe availability in business hours | Public /health/ page (200 or 503, no data) and a monitoring plan in `docs/DEPLOYMENT.md`. | ST-AVAIL-01, 02 |
| SEC-005 no data when logged out | Open protected view while logged out | Every page except login, logout and health requires login. An automated test crawls all URLs. | ST-SEC-05 |

## 3. Updated test cases

All cases were executed on 09 / 11 / 2026. Automated evidence is listed per case in Appendix A. Live evidence (SV-xx) comes from the real-HTTP walkthrough in the System Validation Report.

| Test ID | Requirement | Change | Scenario (precondition and action) | Expected result | Evidence | Result |
| --- | --- | --- | --- | --- | --- | --- |
| **UT-SUP-01** | FR-015 | Updated | Administrator is logged in. Add a supplier, edit its name and contact, filter the list by status, then "remove" it (POST). | Supplier is saved as Active and shown in the list. Edits are shown. "Remove" sets the status to Disabled and keeps the record. Disable by GET is refused (405). Disabling twice is harmless. | 8 automated; live: SV-04, SV-05, SV-17 | Pass |
| **UT-SUP-02** | FR-015, SEC-003 | New | Supplier "Acme Parts" exists. Try a blank name, the same name in other letter case, keeping the supplier's own name on edit, and renaming to another supplier's name. | Blank name rejected. Duplicate name rejected ignoring case. Keeping the own name is allowed. A failed edit leaves the old values unchanged. | 4 automated; live: SV-06, SV-07 | Pass |
| **UT-SUP-03** | FR-015, SEC-002 | New | Anonymous visitor, Staff user and Administrator open the supplier list, add, edit, supplier page and disable. Also an unknown supplier id. | Anonymous goes to login. Staff gets 403 on every page and action and nothing changes. Administrator succeeds. Unknown id gives 404. | 4 automated; live: SV-25 | Pass |
| **IT-SUP-02** | FR-016 | Updated | A registered, active supplier and an active product exist. Record a stock-in with the supplier, then open the transaction list and the supplier page. Also try a stock-in with no supplier. | The transaction stores the supplier. The supplier name is shown on the transaction list. The supplier page lists the stock-in. A stock-in without a supplier is rejected. | 2 automated; live: SV-09, SV-10, SV-11 | Pass |
| **IT-SUP-03** | FR-015, FR-016 | New | A supplier with stock-in history is disabled by the Administrator. Open the stock-in form and try to use the supplier. | The disabled supplier is no longer offered or accepted for new stock-ins. Its history stays visible. | 2 automated; live: SV-16 | Pass |
| **IT-SUP-04** | FR-016 | New | Record a stock-out for a product, then open the supplier page. | The supplier page lists stock-ins only; sales are not listed. | 1 automated; live: none | Pass |
| **UT-ALERT-01** | FR-017 | Updated | Products with stock below, equal to and above the reorder threshold, a threshold of 0, and a disabled product. | A product is low only when stock is strictly below the threshold. Equal and above are not low. Threshold 0 is never low. Disabled products are excluded. Most urgent first. | 7 automated; live: SV-12, SV-13 | Pass |
| **ST-ALERT-01** | FR-017 | Updated | Product with a reorder threshold. Reduce the quantity below the threshold with stock-outs, then restock above it. | The product appears in the low-stock list and on the dashboard for both Staff and Administrator. Anonymous users are sent to login. The alert disappears after restocking. Empty state shows a message. | 6 automated; live: SV-12, SV-13, SV-15, SV-26 | Pass |
| **ST-ALERT-02** | FR-017 | New | A low-stock product is disabled. | The disabled product is removed from the alert list. | 1 automated; live: none | Pass |
| **ST-REPORT-01** | FR-018 | Updated | Sales and stock-in transactions exist. The Administrator requests the report for a date range (default last 30 days; both dates inclusive). Also: start after end, garbage date, empty database, empty range. | Sales table (transaction reference, product, quantity sold, sale amount, date, staff member) with totals. Stock table (product, SKU, category, current stock, reorder threshold, stock value, units in and out in the range). Stock-ins are not counted as sales. Bad ranges show an error and no report. | 10 automated; live: SV-18, SV-21, SV-22 | Pass |
| **ST-REPORT-02** | FR-019 | Updated | Sales history exists. The Administrator opens the top-selling products page. Also: date filter, no dates, bad range, stock-ins only. | Top 10 products ranked by units sold (stock-outs only). Ties ordered by name. No dates means all recorded sales. Bad range shows an error. | 6 automated; live: SV-23 | Pass |
| **ST-REPORT-03** | FR-018 (UC-09 exported) | New | Export the sales report and the stock report as CSV for a date range. Include a product whose name starts with "=". | CSV downloads with the specified header row. Money has two decimals. The range is respected. Text that starts with = + - or @ is prefixed so a spreadsheet will not run it as a formula. | 4 automated; live: SV-19, SV-20 | Pass |
| **ST-REPORT-04** | FR-018, FR-019, SEC-002 | New | Anonymous visitor, Staff user and Administrator open the two report pages and the CSV export. | Anonymous goes to login. Staff gets 403 (also on export). Administrator gets 200. | 4 automated; live: SV-25 | Pass |
| **ST-REPORT-05** | FR-018 | New | Record a sale, then change the product price. | The report amount follows the CURRENT price. This is the documented deviation 8 (transactions store no price snapshot); the test pins the behaviour so a change is noticed. | 1 automated; live: none | Pass |
| **ST-AVAIL-01** | NFR-002 | Updated | Service is running. Poll the health page for the measuring window. | The health page answers HTTP 200 with {"status": "ok"} without login. Availability is at least 99% over the window. | 1 automated; live: SV-02, SV-28 | Pass (2-minute sample; the 99% business-hours target needs long-term monitoring) |
| **ST-AVAIL-02** | NFR-002 | New | The database is stopped and started again while the health page is polled. | The health page returns 503 with no error details while the database is down, and 200 again after the restart. | 1 automated; live: Outage check | Pass |
| **ST-SEC-05** | SEC-005 | Updated | A logged-out browser opens every protected URL in the project (GET and POST), with and without following redirects, and the Django admin. | Every page except login, logout and health redirects to login. No supplier or pricing data appears in any response. The test walks all URLs, so a new unprotected page fails it. | 4 automated; live: SV-01 | Pass |

**Totals:** 17 cases (8 from the STP: UT-SUP-01, IT-SUP-02, UT-ALERT-01, ST-ALERT-01, ST-REPORT-01, ST-REPORT-02, ST-AVAIL-01, ST-SEC-05, all Updated; 9 New). All executed, 17 pass. 66 automated tests back them, all passing.

## 4. Updated traceability (RTM) for this module

| Req ID | Component | Unit / integration case | System case | Coverage |
| --- | --- | --- | --- | --- |
| FR-015 | suppliers app | UT-SUP-01, UT-SUP-02, UT-SUP-03 | SV-04 to SV-07, SV-17 | Covered, executed |
| FR-016 | suppliers + transactions | IT-SUP-02, IT-SUP-03, IT-SUP-04 | SV-09 to SV-11, SV-16 | Covered, executed |
| FR-017 | reports/alerts.py | UT-ALERT-01 | ST-ALERT-01, ST-ALERT-02 (SV-12 to SV-15, SV-26) | Covered, executed |
| FR-018 | reports/services.py | ST-REPORT-01, ST-REPORT-03, ST-REPORT-05 | SV-18 to SV-22 | Covered, executed |
| FR-019 | reports/services.py | ST-REPORT-02 | SV-23 | Covered, executed |
| NFR-002 | esims/health.py | ST-AVAIL-01, ST-AVAIL-02 (unit part) | SV-02, SV-28, outage check | Partly covered: 2-minute sample only |
| SEC-005 | all views | ST-SEC-05 | SV-01 | Covered, executed |
| SEC-002 (supplier and report pages) | suppliers + reports views | UT-SUP-03, ST-REPORT-04 | SV-25 | Covered, executed |

## Appendix A: automated tests behind each case

**UT-SUP-01**

- `suppliers.tests.SupplierCrudTests.test_admin_can_add_supplier`: Pass
- `suppliers.tests.SupplierCrudTests.test_admin_can_edit_supplier`: Pass
- `suppliers.tests.SupplierCrudTests.test_disable_is_soft_delete`: Pass
- `suppliers.tests.SupplierCrudTests.test_disable_requires_post`: Pass
- `suppliers.tests.SupplierCrudTests.test_list_filter_by_status`: Pass
- `suppliers.test_detail_and_edit.SupplierEditAndDetailTests.test_edit_page_shows_current_values`: Pass
- `suppliers.test_detail_and_edit.SupplierEditAndDetailTests.test_disabling_twice_is_harmless`: Pass
- `suppliers.test_detail_and_edit.SupplierEditAndDetailTests.test_string_form_is_the_name`: Pass

**UT-SUP-02**

- `suppliers.tests.SupplierCrudTests.test_blank_name_rejected`: Pass
- `suppliers.tests.SupplierCrudTests.test_duplicate_name_rejected_case_insensitive`: Pass
- `suppliers.tests.SupplierCrudTests.test_edit_keeping_same_name_is_allowed`: Pass
- `suppliers.test_detail_and_edit.SupplierEditAndDetailTests.test_invalid_edit_keeps_old_values`: Pass

**UT-SUP-03**

- `suppliers.tests.SupplierPermissionTests.test_anonymous_redirected_to_login`: Pass
- `suppliers.tests.SupplierPermissionTests.test_staff_get_403_everywhere`: Pass
- `suppliers.test_detail_and_edit.SupplierEditAndDetailTests.test_supplier_page_is_admin_only`: Pass
- `suppliers.test_detail_and_edit.SupplierEditAndDetailTests.test_unknown_supplier_gives_404`: Pass

**IT-SUP-02**

- `suppliers.tests.SupplierStockLinkTests.test_stock_in_is_linked_to_supplier_and_shown_on_supplier_page`: Pass
- `suppliers.tests.SupplierStockLinkTests.test_supplier_shown_on_transaction_list`: Pass

**IT-SUP-03**

- `suppliers.tests.SupplierStockLinkTests.test_disabled_supplier_cannot_be_used_for_stock_in`: Pass
- `suppliers.tests.SupplierStockLinkTests.test_disabled_supplier_history_is_kept`: Pass

**IT-SUP-04**

- `suppliers.tests.SupplierStockLinkTests.test_stock_out_not_listed_on_supplier_page`: Pass

**UT-ALERT-01**

- `reports.tests.LowStockRuleTests.test_strictly_below_threshold_is_low`: Pass
- `reports.tests.LowStockRuleTests.test_equal_to_threshold_is_not_low`: Pass
- `reports.tests.LowStockRuleTests.test_above_threshold_is_not_low`: Pass
- `reports.tests.LowStockRuleTests.test_zero_threshold_never_low`: Pass
- `reports.tests.LowStockRuleTests.test_queryset_matches_rule_and_skips_disabled`: Pass
- `reports.tests.LowStockRuleTests.test_most_urgent_first`: Pass
- `reports.test_alert_flow.LowStockFlowTests.test_alert_appears_only_when_strictly_below_threshold`: Pass

**ST-ALERT-01**

- `reports.tests.LowStockViewTests.test_anonymous_redirected`: Pass
- `reports.tests.LowStockViewTests.test_staff_and_admin_can_view_report_and_dashboard`: Pass
- `reports.tests.LowStockViewTests.test_alert_clears_after_restock`: Pass
- `reports.tests.LowStockViewTests.test_empty_state_message`: Pass
- `reports.test_alert_flow.LowStockFlowTests.test_both_roles_see_the_alert_on_page_and_dashboard`: Pass
- `reports.test_alert_flow.LowStockFlowTests.test_restock_clears_the_alert`: Pass

**ST-ALERT-02**

- `reports.test_alert_flow.LowStockFlowTests.test_disabling_the_product_removes_the_alert`: Pass

**ST-REPORT-01**

- `reports.test_reports.SalesReportTests.test_default_range_is_last_30_days`: Pass
- `reports.test_reports.SalesReportTests.test_amount_is_quantity_times_price_and_totals_add_up`: Pass
- `reports.test_reports.SalesReportTests.test_start_and_end_dates_are_inclusive`: Pass
- `reports.test_reports.SalesReportTests.test_stock_in_is_not_a_sale`: Pass
- `reports.test_reports.SalesReportTests.test_sales_table_has_required_columns`: Pass
- `reports.test_reports.SalesReportTests.test_start_after_end_is_rejected`: Pass
- `reports.test_reports.SalesReportTests.test_garbage_date_is_rejected`: Pass
- `reports.test_reports.SalesReportTests.test_stock_section_value_and_movement`: Pass
- `reports.test_reports.SalesReportTests.test_empty_database_still_renders`: Pass
- `reports.test_reports.ServiceTests.test_disabled_products_still_appear_in_history`: Pass

**ST-REPORT-02**

- `reports.test_reports.TopSellingTests.test_ranked_by_units_sold`: Pass
- `reports.test_reports.TopSellingTests.test_stock_in_does_not_count`: Pass
- `reports.test_reports.TopSellingTests.test_ties_broken_by_name`: Pass
- `reports.test_reports.TopSellingTests.test_only_top_ten`: Pass
- `reports.test_reports.TopSellingTests.test_no_dates_means_all_time_and_dates_filter`: Pass
- `reports.test_reports.TopSellingTests.test_bad_range_is_rejected`: Pass

**ST-REPORT-03**

- `reports.test_reports.CsvExportTests.test_sales_csv`: Pass
- `reports.test_reports.CsvExportTests.test_stock_csv`: Pass
- `reports.test_reports.CsvExportTests.test_formula_injection_is_neutralised`: Pass
- `reports.test_reports.CsvExportTests.test_export_respects_date_range`: Pass

**ST-REPORT-04**

- `reports.test_reports.ReportAccessTests.test_anonymous_redirected_to_login`: Pass
- `reports.test_reports.ReportAccessTests.test_staff_gets_403`: Pass
- `reports.test_reports.ReportAccessTests.test_staff_cannot_export_csv`: Pass
- `reports.test_reports.ReportAccessTests.test_admin_gets_200`: Pass

**ST-REPORT-05**

- `reports.test_alert_flow.ReportAmountRuleTests.test_price_change_changes_old_sale_amounts`: Pass

**ST-AVAIL-01**

- `esims.test_health.HealthTests.test_ok_without_login`: Pass

**ST-AVAIL-02**

- `esims.test_health.HealthTests.test_database_down_gives_503`: Pass

**ST-SEC-05**

- `reports.test_sec005.LoggedOutAccessTests.test_crawler_actually_finds_the_app_urls`: Pass
- `reports.test_sec005.LoggedOutAccessTests.test_every_page_redirects_logged_out_visitors_to_login`: Pass
- `reports.test_sec005.LoggedOutAccessTests.test_no_sensitive_data_in_any_response`: Pass
- `reports.test_sec005.LoggedOutAccessTests.test_django_admin_requires_login_too`: Pass
