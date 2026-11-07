# Test case updates - catalog (Sakthevel Saravanan)

This execution addendum updates the catalog feature cases in section 13 of
`ESIMS_STP_Team_8.pdf` for the sprint changes present in this repository. The
submitted PDF is retained as the baseline. Automated results are recorded after
the current revision's test run; browser walkthroughs and production-like
PostgreSQL checks are identified separately where they were not executed.

## Revised catalog test cases

| Test ID | Requirement | Updated scenario and expected result | Automated evidence | Result |
| --- | --- | --- | --- | --- |
| UT-CAT-01 | FR-005 | Administrator creates a product with a unique SKU, valid active category, optional active supplier, valid price and threshold. Product is saved with zero starting stock; stock supplied in the form is ignored. | `catalog.tests.test_views_products.ProductAddTests`; `catalog.tests.test_forms.CatalogFormTests`; `catalog.tests.test_models.CatalogModelTests` | Pass |
| UT-CAT-02 | FR-006 | Administrator edits product details. Own SKU may be retained; a duplicate SKU is rejected. Stock cannot be changed through the edit form. | `catalog.tests.test_views_products.ProductEditTests` | Pass |
| ST-CAT-01 | FR-007 | Administrator confirms a deliberate POST disable action. Product is marked disabled, removed from active sale choices, and remains stored with its transaction history protected. | `catalog.tests.test_views_products.ProductDisableTests`; `catalog.tests.test_models.CatalogModelTests` | Pass |
| ST-CAT-02 | FR-008 | Search by name or SKU (case-insensitive) and combine category/status filters. Invalid category filters do not error; pagination preserves active filters and handles invalid/out-of-range page values. | `catalog.tests.test_selectors.SearchProductsTests`; `catalog.tests.test_views_products.ProductSearchFilterTests`; `ProductPaginationSelectorTests` | Pass |
| ST-CAT-03 | FR-009 | Product list shows current on-hand quantity for unfiltered and filtered results; search results do not expose inconsistent stock values. | `catalog.tests.test_views_products.ProductStockDisplayTests` | Pass |
| ST-CAT-04 | FR-005-FR-008 | Catalog authorization matrix: anonymous users are redirected, Staff can view catalog lists, and only Administrators can add/edit/disable products or manage categories. | `catalog.tests.test_views_products.CatalogPermissionMatrixTests`; `catalog.tests.test_views_categories.CategoryTests` | Pass |
| UT-CAT-03 | FR-005-FR-006 | Reject blank or whitespace identifiers/names, case-insensitive duplicate SKU/category, negative price/threshold, disabled category/supplier choices, and malformed required fields without persisting invalid data. | `catalog.tests.test_forms.CatalogFormTests`; `ProductAddTests`; `ProductEditTests`; `catalog.tests.test_views_categories.CategoryTests`; `catalog.tests.test_models.CatalogModelTests` | Pass |
| ST-PERF-01 | NFR-001 | Search remains below the two-second target for the automated 500-product fixture; query count remains constant as the product catalogue grows; pagination limits each page to 25 products. The submitted local 5k/10k sequential benchmarks remain environment-specific evidence. | `catalog.tests.test_views_products.ProductPaginationSelectorTests`; `catalog.tests.test_views_products.ProductSearchFilterTests` | Pass |

## Execution record

Execution date: 2026-11-07. Database: SQLite. Environment: local Django test
runner. All listed automated cases passed in the 342-test run. The overall test outcome and current-revision coverage are in
`docs/UNIT_TEST_REPORT.md`, `docs/SYSTEM_VALIDATION_REPORT.md`,
`docs/CODE_COVERAGE_REPORT.md`, and `docs/BRANCH_COVERAGE_REPORT.md`.
