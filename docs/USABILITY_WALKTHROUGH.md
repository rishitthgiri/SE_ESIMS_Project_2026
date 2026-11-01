# Usability walkthrough: stock-in and stock-out in 4 screens or fewer (ST-USE-01 / NFR-003 / ESIMS-24)

**Requirement (NFR-003):** a Staff member can complete a stock-in or stock-out in no more than 4 screens/steps.
**Counting rule:** screens are counted from the dashboard, the page every user lands on after logging in.

## Stock-in (purchase): 3 screens

| Screen | What the user sees                                                                         | What the user does                                                      |
| ------ | ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------- |
| 1      | Dashboard (menu bar with **Stock-in**)                                                     | Click **Stock-in**                                                      |
| 2      | Stock-in form: product, supplier, quantity                                                 | Choose product and supplier, type the quantity, click **Save stock-in** |
| 3      | Transactions list with a green message: the new **transaction ID** and the new stock level | Done                                                                    |

## Stock-out (sale): 3 screens

| Screen | What the user sees                                                | What the user does                                          |
| ------ | ----------------------------------------------------------------- | ----------------------------------------------------------- |
| 1      | Dashboard                                                         | Click **Stock-out**                                         |
| 2      | Stock-out form: product, quantity                                 | Choose product, type the quantity, click **Save stock-out** |
| 3      | Transactions list with a green message and the new transaction ID | Done                                                        |

If the sale is **rejected** (more than the stock), the user stays on screen 2: the same form shows a red message ("Only N unit(s) ... in stock") and the quantity can be corrected and resubmitted. An error never adds a screen.

## Result

Both flows take **3 screens, which is within the limit of 4.** The automated check is `transactions/test_usability.py` (it walks dashboard, form, result and asserts the count).

Screenshots to save in `docs/evidence/`.

**Conclusion:** All runs took 3 screens, under the limit of 4.
