# Deviations from the SRS / SAD / STP (Sprint 1)

| # | Deviation | Reason |
|---|-----------|--------|
| 1 | Stock-in/out lives in the `transactions` app (the SAD calls this module "Stock"). | The skeleton already had a `transactions` app, and keeping it avoided a rename. |
| 2 | Primary keys are UUIDs (SRS Appendix B). Field names use short forms such as `name` and `quantity_in_stock`. | Matches the frozen model contract in the team agreement. |
| 3 | Low-stock alerts are computed from Product data (`reports/alerts.py`). The SAD's separate `LowStockAlert` table is not created in v1.0. | There is no extra table to keep in sync, and alerts are always accurate. Rule: quantity_in_stock < reorder_threshold (FR-017). |
| 4 | FR-005/006 "authorized user" is implemented as Administrator only. | Matches UC-02/UC-03. |
| 5 | Transaction list: Staff see their own transactions, Admin sees all. The full Admin audit list is ESIMS-22 (Sprint 2). | The SRS left this open. |
| 6 | Local development uses SQLite. CI and production use PostgreSQL. | Quick local setup. Row locking (`select_for_update`) only takes effect on PostgreSQL. |
| 7 | `StockTransaction` has an extra `request_token` field. | Reserved for double-submit protection (ESIMS-23, Sprint 2). |
| 8 | The login URL name is `accounts:login` (not `login`), with `LOGIN_URL = 'accounts:login'`. | The accounts app uses a namespace. |
| 9 | Only `reports:low_stock` is built. `reports:sales` and `reports:top_selling` move to Sprint 2. | Out of scope for Sprint 1 stories. |
| 10 | Added a supplier detail page (`suppliers:detail`) listing stock received from that supplier. | Implements ESIMS-28 without editing the `transactions` code. |
| 11 | Suppliers are disabled (soft delete), never hard-deleted. A disabled supplier cannot be used for new stock-in, but its history is kept. | Old transactions must keep pointing at the supplier. |
