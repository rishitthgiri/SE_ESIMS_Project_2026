# Branch coverage report

**Run date:** 2026-11-07
**Revision:** `6791b55` (`feature/ESIMS-17-modular-code-tests`)
**Command:** `coverage run --branch --source=accounts,catalog,esims,reports,suppliers,transactions manage.py test -v 1`
**Scope:** application code; tests, migrations, ASGI/WSGI bootstrap files omitted from this summary.

## Results

| Scope | Branch opportunities | Partial / missed branches | Branch coverage |
| --- | ---: | ---: | ---: |
| All application modules | 216 | 18 | 91.7% |
| Catalog module (includes management commands) | 64 | 5 partial plus 16 in unexecuted commands | 67.2% |
| Catalog web/model code (management commands excluded) | 48 | 5 partial | 89.6% |

Catalog branch results exclude the branches in `measure_search` and
`seed_demo_products` from the web/model subtotal; those commands' branches were
not executed. The catalog forms account for the five partial branches in the
web/model subtotal. These results identify follow-up opportunities for direct
tests of command-line behavior and remaining form-validation paths.

The branch-aware raw report is `docs/evidence/coverage_app_code.txt` (filtered
application code) and `docs/evidence/coverage_full.txt` (all measured files).
Coverage counts report executed paths, not defect-free behavior.
