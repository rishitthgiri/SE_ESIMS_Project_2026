# Deviations from the submitted SRS, SAD and STP

Every place where the built system differs from the documents we submitted, and why.
(Required by the Sprint 1 and Sprint 2 deliverables; explain these in the final demo.)

| # | Document says | What we built | Why |
|---|---|---|---|
| 1 | SAD calls the stock module "Stock" | Stock-in and stock-out live in the `transactions` app | One app owns the transaction history; no separate "stock" app was needed |
| 2 | SRS Appendix B: UUID primary keys, long field names | `Category`, `Product` and `Supplier` use a UUID `id`; fields use the short names (`name`, `quantity_in_stock`). `StockTransaction` has a normal `id` plus a unique `transaction_id` UUID. `User` keeps Django's integer id | Matches the team's model contract; the integer ids on `User` and transactions come from Django defaults |
| 3 | SAD has a separate `LowStockAlert` table | Low stock is computed from `Product` (`reports/alerts.py`); no alert table in v1.0 | FR-017 needs no history of alerts, and a computed list can never go out of date |
| 4 | FR-005 and FR-006 say "authorized user" | Adding and editing products and categories is **Administrator only** | UC-02 and UC-03 name the Administrator as the actor |
| 5 | Transaction list not specified per role | Staff see their own transactions, Administrators see all | Least privilege; the full audit list is Administrator only |
| 6 | STP assumes PostgreSQL | Local work and the GitHub Actions CI run on SQLite (`DB_ENGINE=sqlite`); production uses PostgreSQL | No database server needed for quick tests. Row locking (`select_for_update`) only really locks on PostgreSQL |
| 7 | StockTransaction fields in SRS Appendix B | One extra field, `request_token` | Used by the double-submit protection (ESIMS-23) |
| 8 | FR-018 report lists a "Sale Amount" but not how it is calculated | Sale amount = quantity x the product's **current** price | Transactions do not store a price snapshot, so a later price change also changes old report amounts. A `unit_price` column on `StockTransaction` is the fix for a future version |
| 9 | FR-018 asks for a "stock/sales report for a date range" | One page with two parts. Sales are filtered by the date range. Stock shows the **current** stock and stock value, plus the units received and sold inside the range | Current stock cannot be rebuilt for an old date without a stock history table |
| 10 | UC-09: report "displayed/exported" | Displayed on screen and exported as CSV (sales and stock). Text that starts with `=`, `+`, `-` or `@` is prefixed so spreadsheets do not run it as a formula | Export was asked for; the prefix is a basic safety measure |
| 11 | Reports actor: Administrator | Stock/sales report and top-selling products are Administrator only. The low-stock list is visible to Staff and Administrator | Agreement section 5 (permissions table) |
| 12 | FR-019 gives no limit or date handling | Top 10 products by units sold; with no dates it uses all recorded sales; ties are ordered by product name | Simple, predictable ranking |
| 13 | NFR-002 (99% availability) has no measurement method | A public `/health/` endpoint (HTTP 200 / 503, no data shown) plus the monitoring plan in `docs/DEPLOYMENT.md`. Availability has **not** yet been measured over a real month | An operational review needs something to measure |
| 14 | SEC-005: no sensitive data to unauthenticated users | Every page except login, logout and `/health/` requires login. `reports/test_sec005.py` walks all URLs, so a new unprotected page fails the tests | Makes the rule automatic instead of a one-time design review |
| 15 | Navigation not specified | Menu links for every module (Reports and Top sellers for Administrators), supplier detail page, low-stock panel on the dashboard | Needed to demo the product |
