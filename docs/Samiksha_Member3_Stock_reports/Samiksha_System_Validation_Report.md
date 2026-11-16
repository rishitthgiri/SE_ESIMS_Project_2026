# System Validation Report

## Stock module

| | |
|---|---|
| Project | ESIMS, Team 8 |
| Section owner | Samiksha B N (Stock module, ESIMS-18 to ESIMS-25) |
| Date | 06-11-2026 |
| Environment | Windows 11, Python 3.13, Django 5.2.18, SQLite and PostgreSQL |

### Scope
Integration and system-level validation: services with the database, views and forms, audit page, access control, duplicate submission, usability, and a real-browser walkthrough.

### Results
| Test file | Focus | Tests | Passed |
|---|---|---|---|
| `transactions/test_audit.py` | Audit record, Administrator audit page, access | 15 | 15 |
| `transactions/test_double_submit.py` | One-time token, repeated submits | 16 | 16 |
| `transactions/test_usability.py` | Screens counted from the dashboard | 5 | 5 |

Manual walkthrough in the browser: `evidence/USABILITY_WALKTHROUGH.md`. Screenshots: `evidence/ESIMS_Samiksha_Evidence.pdf`.

### Validation test cases (STP IDs)
| Test ID | Req | Scenario | Status |
|---|---|---|---|
| IT-STOCK-01 | FR-010 | Record stock-in | Pass |
| IT-STOCK-02 | FR-011 | Record stock-out | Pass |
| IT-STOCK-03 | FR-013 | Unique transaction ID | Pass |
| ST-STOCK-04 | FR-014 | Audit trail and audit page | Pass |
| ST-REL-01 | NFR-004 | Duplicate submission records one transaction | Pass |
| ST-USE-01 | NFR-003 | 3 screens to complete a stock operation (limit 4) | Pass |
| ST-SEC-03 | SEC-003 | Bad quantities rejected, no change | Pass |
| ST-SEC-02 | SEC-002 | Staff get 403 on the audit page, logged | Pass |
| IT-STOCK-04 (new) | FR-014 | Role-based transaction list | Pass |
| IT-STOCK-05 (new) | FR-007 / FR-010 / FR-011 | Disabled product or supplier refused | Pass |
| IT-STOCK-06 (new) | NFR-004 | Rollback on failure | Pass |

Full table with expected and actual results: `Samiksha_ESIMS_Test_Case_Document.md`.

### Changes since the original Test Plan
| Change | Effect on testing |
|---|---|
| Deviation 5: transaction list per role | New case IT-STOCK-04 |
| Deviation 16: Administrator audit page | ST-STOCK-04 also tests `/transactions/audit/`; ST-SEC-02 covers Staff 403 |
| Deviation 17: one-time `request_token` | ST-REL-01 means a repeat POST records nothing |
| Deviation 19: NFR-003 counted from the dashboard | ST-USE-01 expects 3 screens |
| Deviation 20: pure stock functions | UT-STOCK-01 tests them without the database |
| Deviation 21: disabled items keep history | New case IT-STOCK-05 |

### Defects
None found in this cycle.

### Limitations
1. Bulk `update()` and `delete()` on transactions are not blocked (deviation 18).
2. Sale amount uses the current price, not a price at sale time.
3. Browser coverage is a smoke test on Chrome, Edge and Firefox.
4. Row locking was only tested on SQLite and one PostgreSQL run (deviation 6).
