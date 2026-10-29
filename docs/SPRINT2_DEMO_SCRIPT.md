# Sprint 2 demo video: 2 minutes (ESIMS-35)

Prepare before recording (not on camera): fresh database with `python manage.py migrate` and `python manage.py seed_demo_users`; as `admin`, create one category, two suppliers and three products (give one a reorder threshold above its stock); record a few stock-ins and stock-outs so the reports have data. Keep the tab for `staff1` ready in a private window.

| Time | Show |
|---|---|
| 0:00 | Log in as `admin`. Dashboard with the low-stock panel |
| 0:15 | Stock-out larger than stock: rejected. A valid stock-in and stock-out: new transaction IDs |
| 0:35 | Transactions list with the supplier shown. Suppliers page: stock-in counts, edit, disable |
| 0:55 | Reports > date range: sales table, totals, stock value. Click **Export sales CSV** |
| 1:15 | Top sellers: ranking changes after one more sale |
| 1:30 | Private window, logged out: open `/suppliers/` -> sent to login. Log in as `staff1`: `/reports/sales/` -> 403 page |
| 1:45 | Show the green GitHub Actions run and the Project board (all Done). Mention `docs/DEVIATIONS.md` |

Upload the file as `docs/sprint2-demo.mp4` (GitHub rejects files over 100 MB; record at 720p).
