# Tasks: CU-A02 — Sales Metrics & Reports (MVP)

Feature dir: `specs/010-sales-metrics-reports` | Plan: [plan.md](plan.md)

Format: `- [ ] ID [P] Description (path)`. `[P]` = parallelizable. Mark a task done only after its outcome and checks were observed; record each executed check and its result in the Evidence Ledger at the end. Validation is local-only. Contract tasks (X-*) precede implementation. Do not apply migrations to an active database; use disposable PostgreSQL for integration tests.

## Cross-cutting: Contracts (blocking)

- [x] X-1 Add `adminSalesMetrics(from, to, categories, productIds)` and payload types (`SalesMetrics`, `TopProduct`, `RevenueByDay`, `StatusCount`) to `bgg-shop-core/specs/schema.graphql`. Document staff/superuser access; UTC half-open range; revenue and `ordersCount` by `paid_at`; status counts by `created_at`; gross line-subtotal revenue; exact filters with matching orders counted once; dispatch rules; errors `UNAUTHENTICATED`/`FORBIDDEN`/`INVALID` with `extensions.field`; maximum range 366 days; and last 30 days when both bounds are omitted.
- [x] X-2 Add `GET /api/v1/admin/sales-metrics` to `bgg-shop-bff/specs/openapi.yaml` with optional `from`/`to`, repeated `category`/`product_id`, responses 200/400/401/403, `Cache-Control: no-store`, and planned status; document the business rules from X-1.
- [x] X-3 Add `GET /api/v1/admin/sales-metrics/categories` (distinct stored category values; 200/401/403/502; `Cache-Control: no-store`; planned) to the OpenAPI and matching `adminSalesCategories` query to the SDL with staff/superuser access and authorization error semantics.
- [x] X-4 Validate both contract documents and run `bgg-shop-bff/scripts/run_contracts.sh`; record the contract assertions and service-test result separately. Structural contract assertions passed; unrelated BFF service tests failed (see Evidence Ledger).
- [x] X-5 Document that callers provide both `from` and `to`, or omit both; a one-sided range returns `INVALID` with `extensions.field` set to the missing bound, and omitting both defaults to the last 30 days.

For future service work, check both BFF OpenAPI routes and Core GraphQL operations for existing or required contract definitions before implementation.

## Core (`bgg-shop-core`)

- [x] C-1 Write failing PostgreSQL tests in `bgg-shop-core/tests/test_admin_sales_metrics_postgres.py` (disposable DB), covering range/revenue rules, exact filters independently and together, top-10 tie-breaks, UTC daily aggregation, dispatch boundaries/status exclusions, status dates, validation, authorization, and category retrieval. (depends on X-4; expected RED observed)
- [x] C-1a Add PostgreSQL GraphQL tests for `from`-only (missing `to`) and `to`-only (missing `from`), explicitly passing `None` for each omitted bound; observe expected RED before resolver implementation.
- [x] C-2 Implement the resolver for `adminSalesMetrics` in `bgg-shop-core/saleor/graphql/api.py` with staff/superuser guard, input validation and parameterized SQL (no interpolated user values; Decimal database results retained through Graphene serialization). Metrics and filter cases in C-1/C-1a pass. (depends on C-1 and C-1a)
- [x] C-3 Implement `adminSalesCategories` resolver and test. (depends on X-3)
- [x] C-4 Review local query plans on seeded data. No index migration was justified by this synthetic workload; revisit only with representative volume/latency requirements.
- [x] C-5 Run Core test suite for touched areas and record results.
- [x] C-6 Add exact Core OpKey delegation mappings for both sales-metrics routes with route/root mismatch tests; required for OpKey-authenticated BFF calls in F-5.

## BFF (`bgg-shop-bff`)

- [x] B-1 Write failing tests in `bgg-shop-bff/tests/test_admin_sales_metrics.py`: auth for metrics and categories, staff/superuser access, date/filter validation, repeated-filter forwarding, `Cache-Control: no-store`, and upstream-detail redaction. Expected RED observed with successful collection. (depends on X-5)
- [x] B-2 Add proxy calls in `bgg-shop-bff/src/proxy.py` and services in `bgg-shop-bff/src/services.py`, following `list_admin_audit`. (depends on B-1)
- [x] B-3 Add `bgg-shop-bff/src/controllers/admin_sales_controller.py` with validation and error mapping; register both GET routes in `bgg-shop-bff/app.py`. B-1 and added validation cases pass. (depends on B-2)
- [x] B-4 Add the categories endpoint with tests; implemented and covered within B-2/B-3 and B-1. (depends on X-3)
- [x] B-5 Update `bgg-shop-bff/README.md` with endpoint paths, filters, date semantics, access, cache behavior, and error responses.
- [x] B-6 Run BFF tests and contract tests; record results, noting existing unrelated service failures.

## Frontend (`bgg-shop-frontend`)

- [x] F-1 Run `npm run generate:types` after X-2/X-3; regenerated `src/types/generated/bff-api.d.ts` includes both sales endpoints and is not hand-edited. (depends on X-4)
- [x] F-2 Write failing Vitest tests in `bgg-shop-frontend/src/admin/sales/SalesPanel.test.tsx`: loading, error, empty and success states; filter wiring (dates, category, product); default range; display of dispatch states in Spanish; keyboard accessibility and accessible names. Expected RED observed because `SalesPanel` is not implemented. (depends on F-1)
- [x] F-3 Implement `bgg-shop-frontend/src/admin/sales/SalesPanel.tsx`: date range and filters, revenue/orders summary, top-10 table, dispatch and payment status counts, native SVG/CSS bar chart for `revenueByDay`; fetch metrics and categories in parallel. F-2 passes. (depends on F-2)
- [x] F-4 Register `/admin/sales` and add a "Ventas" link in `bgg-shop-frontend/src/admin/AdminRouter.tsx`.
- [x] F-5 Seed deterministic sales rows and complete Playwright flow `bgg-shop-frontend/tests/e2e/sales.spec.ts` (admin login → dashboard → apply filter → compare UI/BFF output with direct SQL); follow `audit.spec.ts` conventions. Use only a disposable local DB; never use the active `saleor` database. (depends on F-3, F-4)
- [x] F-6 Run lint, build, Vitest and the E2E flow; record results.

## Verification & Documentation

- [x] V-1 Compare dashboard totals (revenue, order counts, top products, dispatch counts) against direct SQL on the local seeded database; record queries and results.
- [x] V-2 Local security checks: non-admin and unauthenticated rejected, no PII in payload, redacted errors, parameterized queries reviewed.
- [x] V-3 Update `specs/010-sales-metrics-reports/plan.md` status and README references; keep claims limited to executed local checks (no CI/deployment).

## Dependencies

X-1..X-3 → X-4 → X-5 → (C-1/C-1a → C-2, B-1 → B-2 → B-3, F-1 → F-2 → F-3/F-4, C-6) → F-5 → V-*.
 Core, BFF, and frontend tracks can run in parallel after X-5; the BFF integration check against real Core and E2E need C-2, B-3, and C-6 for OpKey delegation.

## Evidence Ledger

| Task | Check run | Result | Date |
|------|-----------|--------|------|
| C-2 | `PYTHONPATH=. python -m pytest -q -p no:cacheprovider --tb=short tests/test_admin_sales_metrics_postgres.py -k 'not categories'` with fresh loopback-only Podman PostgreSQL 15 | PASS: 17 passed, 4 deselected, 1 Django deprecation warning in 4.25s; temporary container removal explicitly verified. | 2026-11-05 |
| C-2 | `python -m py_compile saleor/graphql/api.py`; `git diff --check` | PASS for both checks. | 2026-11-05 |
| C-2 | Parent rerun of the focused Core metrics/filter suite against a fresh Podman PostgreSQL 15 container | PASS: 17 passed, 4 deselected, 1 Django warning in 4.20s. `py_compile` and `git diff --check` passed. The container remained after the command despite its exit trap; it was removed explicitly and absence was verified. | 2026-11-05 |
| C-2 | Work-unit commits | Core `b447261a93d6f127963646ea24874ea9a9eb487d`; orchestrator `717be40568313763f6c09f94f64aa8455871fe6c` | 2026-11-05 |
| C-2 | `PYTHONPATH=. python -m pytest -q -p no:cacheprovider --tb=short tests/test_graphql_products.py::test_generated_schema_matches_reference_sdl` | FAIL: runtime/SDL parity differs only because `adminSalesCategories` remains unimplemented for C-3; targeted comparison confirmed the C-2 metrics operation, arguments, payload fields, and description match. | 2026-11-05 |
| C-4 | `EXPLAIN (ANALYZE, BUFFERS)` for paid_at range, category/product-filtered metrics, and created_at status counts on 100,000 synthetic orders/lines and 500 products | PASS: plans completed in 28–46 ms; combined category/product filter matched 12 rows and scanned lines sequentially. No index justified without representative workload/latency requirements; temporary DB/container removed, active `saleor` untouched. | 2026-11-05 |
| X-1..X-3 | PyYAML parse and OpenAPI route/schema/parameter/response assertions; `graphql-core` parse and SDL operation/type assertions | PASS: `OPENAPI_PARSE_AND_ASSERTIONS=PASS`; `GRAPHQL_PARSE_AND_ASSERTIONS=PASS` | 2026-11-05 |
| X-4 | Direct `scripts/run_contracts.sh` from BFF | EXIT 126: script is not executable; rerun through Bash | 2026-11-05 |
| X-4 | `bash scripts/run_contracts.sh` after initial SDL update | EXIT 0: command reported pass; script runs `pytest tests/test_services_* -q` rather than schema parsers | 2026-11-05 |
| X-4 | Final `bash scripts/run_contracts.sh` after OpenAPI response-schema update | EXIT 1: 9 failed, 7 passed in 5.80s; failures are unchanged cart/product, GraphQL service, wishlist and order service tests (`allow_redirects` unexpected; `op_key` undefined), not contract parsing | 2026-11-05 |
| X-4 | Final PyYAML/OpenAPI and graphql-core/SDL parse plus shape assertions after duplicate-constraint fix | PASS: both admin paths, filters, response sets, `no-store`, planned status, Core operations/types, and CartItemRequest maximum verified | 2026-11-05 |
| C-1 | `python -m py_compile tests/test_admin_sales_metrics_postgres.py` from Core | PASS: test module syntax compiles; not a behavior test | 2026-11-05 |
| C-1 | `pytest -q tests/test_admin_sales_metrics_postgres.py` from Core | ERROR during collection: `ModuleNotFoundError: No module named 'saleor'`; repository root was not on the entrypoint import path | 2026-11-05 |
| C-1 | `PYTHONPATH=. pytest -q tests/test_admin_sales_metrics_postgres.py` from Core | 18 skipped, 1 warning: `SALES_METRICS_TEST_POSTGRES_DSN` is absent; no behavior-test RED observed and no database connection attempted | 2026-11-05 |
| C-1 | `PYTHONPATH=. python -m pytest -q -p no:cacheprovider --tb=short tests/test_admin_sales_metrics_postgres.py` with dedicated temporary PostgreSQL 15 container bound to `127.0.0.1` | 18 failed as expected: Graphene `Query` lacks `adminSalesMetrics` and `adminSalesCategories`; tests reached GraphQL validation and did not connect to the active `saleor` database. Temporary container removal verified. | 2026-11-05 |
| X-5 | PyYAML parse and OpenAPI paired-bound assertions; graphql-core parse and SDL paired-bound assertions | PASS: both contracts parse; paired semantics, missing-bound wording, optional parameters, and operation arguments verified | 2026-11-05 |
| C-1a | `python -m py_compile bgg-shop-core/tests/test_admin_sales_metrics_postgres.py` | PASS | 2026-11-05 |
| C-1a | `PYTHONPATH=. python -m pytest -q -p no:cacheprovider --tb=short tests/test_admin_sales_metrics_postgres.py` with a fresh cached `postgres:15-alpine` container bound to `127.0.0.1` | EXPECTED RED: 20 failed, 1 warning in 5.35s; Graphene lacks `adminSalesMetrics` and `adminSalesCategories`; no collection or database setup errors. Container `sales_metrics_test_132aad8945184637bdc7a7913aa4dd5c` removed and absence verified. | 2026-11-05 |
| C-1a | Parent rerun of `PYTHONPATH=. python -m pytest -q -p no:cacheprovider --tb=short tests/test_admin_sales_metrics_postgres.py` with a fresh Podman PostgreSQL 15 container | EXPECTED RED: 20 failed, 1 warning in 5.23s for missing Graphene query fields and resulting error assertions; container cleanup passed. | 2026-11-05 |
| C-1a | Delegated execution-verifier rerun using Podman | NOT ACCEPTED as behavior evidence: reported 20 setup errors in 1.59s without a traceback. Parent rerun immediately afterward reproduced the expected 20 GraphQL field failures with successful setup and cleanup. | 2026-11-05 |
| C-3 | Category-only RED before implementation, using a fresh loopback-only Podman PostgreSQL 15 container | EXPECTED RED: 4 failed, 17 deselected, 1 warning because `adminSalesCategories` was missing; temporary container removed and absence checked. | 2026-11-05 |
| C-3 | `PYTHONPATH=. python -m pytest -q -p no:cacheprovider --tb=short tests/test_admin_sales_metrics_postgres.py -k categories` with fresh loopback-only Podman PostgreSQL 15 | PASS: 5 passed, 17 deselected, 1 Django deprecation warning in 2.23s; container explicitly removed and absence verified. | 2026-11-05 |
| C-3 | `PYTHONPATH=. python -m pytest -q -p no:cacheprovider --tb=short tests/test_admin_sales_metrics_postgres.py` with fresh cached `docker.io/library/postgres:15-alpine` Podman container bound to `127.0.0.1` | PASS: 22 passed, 1 Django deprecation warning in 4.73s; container explicitly removed and absence verified; active `saleor` database not used. | 2026-11-05 |
| C-3 | `python -m py_compile saleor/graphql/api.py`; `git diff --check` | PASS for both checks. | 2026-11-05 |
| C-3 | `PYTHONPATH=. python -m pytest -q -p no:cacheprovider tests/test_graphql_products.py::test_generated_schema_matches_reference_sdl` | PASS: 1 passed, 1 Django deprecation warning in 1.72s. The test compares schemas in memory and does not connect to PostgreSQL. | 2026-11-05 |
| B-1 | `pytest -q tests/test_admin_sales_metrics.py` from BFF | COLLECTION ERROR: `ModuleNotFoundError: No module named 'app'`; this console entrypoint did not add the BFF root to the import path. | 2026-11-05 |
| B-1 | `PYTHONPATH=. .venv/bin/pytest -q tests/test_admin_sales_metrics.py` | COLLECTION ERROR: BFF virtual environment lacks `redis`, imported by `app.py`; no dependency installed. | 2026-11-05 |
| B-1 | `PYTHONPATH=. pytest -q tests/test_admin_sales_metrics.py` | EXPECTED RED: 20 failed, 20 warnings; collection succeeded. Each request received 405 from the generic OPTIONS-only catch-all because the metrics/category GET routes are not registered. GraphQL requests were mocked; no database/network access. | 2026-11-05 |
| B-1 | Work-unit commits | BFF `6f40f5ef54b0e480b6520841ad329f214e702e34`; orchestrator `ecedb1752c11c12e7aee331fd0210c721c22e946` | 2026-11-05 |
| B-2/B-3 | Initial `PYTHONPATH=. pytest -q tests/test_admin_sales_metrics.py` | FAIL: 1 failed, 26 passed; a timezone-naive `from` returned the missing `to` field. Validation was reordered to report the malformed bound first. | 2026-11-05 |
| B-2/B-3 | `PYTHONPATH=. pytest -q tests/test_admin_sales_metrics.py` | PASS: 27 passed, 27 existing `datetime.utcnow()` deprecation warnings. GraphQL calls were mocked; no database or network calls. | 2026-11-05 |
| B-2/B-3 | `PYTHONPATH=. pytest -q tests/test_admin.py` | PASS: 25 passed, 17 deprecation warnings. | 2026-11-05 |
| B-2/B-3 | `git diff --check` from BFF | PASS. No commit made, per user instruction. | 2026-11-05 |
| B-2..B-4 | Parent combined run `PYTHONPATH=. pytest -q --tb=short tests/test_admin_sales_metrics.py tests/test_admin.py` | PASS: 52 passed, 44 existing `datetime.utcnow()` deprecation warnings. Core calls mocked; no database or network calls. | 2026-11-05 |
| B-5 | README structural review | PASS: metrics and categories endpoints, access, filters, paired bounds/default/max range, response shape, no-store, and error responses documented. | 2026-11-05 |
| B-6 | `PYTHONPATH=. pytest -q --tb=short` from BFF | PARTIAL: 597 passed, 12 failed, 431 warnings in 13.69s. Existing unrelated service tests fail on undefined `op_key` and mock signatures rejecting `allow_redirects`; metrics tests passed. | 2026-11-05 |
| B-6 | `bash scripts/run_contracts.sh` from BFF | PARTIAL: 9 failed, 7 passed; existing service-contract mock/signature failures, unrelated to metrics routes. | 2026-11-05 |
| B-6 | PyYAML/OpenAPI paths and graphql-core/SDL fields | PASS: both admin REST routes and both Core query fields parsed and asserted. | 2026-11-05 |
| F-1 | `npm run generate:types`; generated-path check; `git diff --check` | PASS: both admin sales paths appear in the generated declaration; only the generated types file changed. | 2026-11-05 |
| F-2 | `npm test -- --run src/admin/sales/SalesPanel.test.tsx` | EXPECTED RED: Vitest collected the test file and failed resolving `./SalesPanel`, which is not implemented yet. | 2026-11-05 |
| F-3 | `npm test -- --run src/admin/sales/SalesPanel.test.tsx` | PASS: 6 tests passed on parent rerun after implementation and status-heading ID fix. `get_errors` and `git diff --check` reported no issues before the final ID adjustment; focused tests passed after it. | 2026-11-05 |
| F-4 | `npm test -- --run src/admin/sales/SalesPanel.test.tsx`; `get_errors`; `git diff --check` | PASS: all 7 focused tests passed, including route rendering and the "Ventas" navigation link. | 2026-11-05 |
| F-5 | Initial `npx playwright test tests/e2e/sales.spec.ts --list` check before isolated stack provisioning | PASS: one Chromium test discovered. Runtime was not configured at that earlier point; later isolated E2E execution is recorded below. | 2026-11-05 |
| F-6 | Initial lint/build/Vitest check before isolated stack provisioning | PARTIAL at that earlier point: lint/build and 20 Vitest files/212 tests passed; the OpKey browser run was still pending. Superseded by final F-6 result below. | 2026-11-05 |
| C-5/C-6 | `PYTHONPATH=. python -m pytest -q -p no:cacheprovider --tb=short tests/test_admin_sales_metrics_postgres.py tests/test_opkeys_internal.py` with the unique loopback disposable DB | PASS: 180 passed, 1 Django warning in 6.51s. | 2026-11-05 |
| F-5 | `E2E_CORE_CONTAINER=bgg-e2e-007-closeout-api npm run test:e2e:opkey` in frontend | PASS: 10 Playwright tests, 1 worker. SQL fixture independently verified revenue 25.50, 1 paid order, top product (2 units / 25.50), payment status `approved: 1`, dispatch status `En preparación: 1`. Cleanup confirmed 0 fixture products, 0 fixture orders, 0 synthetic users. All containers were isolated from `saleor_db`. | 2026-11-05 |
| F-6 | `npm run lint`; `npm run build`; `npm test -- --run --reporter=dot`; isolated OpKey E2E | PASS: lint/build exit 0; 20 Vitest files/212 tests; Playwright 10/10. | 2026-11-05 |
| V-1 | Runner `verifySeed` direct SQL on the disposable DB | PASS: revenue 25.50, paid-order count 1, top product quantity/revenue, payment status, and derived dispatch status all matched the fixture/API expectations. | 2026-11-05 |
| V-3 | Plan/Core README/Frontend README structural review | PASS: plan status and local-only caveats updated; Core operations, Frontend `/admin/sales`, and BFF endpoints documented. | 2026-11-05 |
| V-2 | Core metrics/OpKey tests, BFF sales/admin tests, resolver and payload review | PASS: Core 180 touched-area tests and BFF 52 focused tests; unauthenticated/non-admin denied, upstream trace/URL/token/password details redacted, no customer identity in metrics payload, SQL values bound as parameters. | 2026-11-05 |
| C-6 | `PYTHONPATH=. python -m pytest -q -p no:cacheprovider --tb=short tests/test_opkeys_internal.py -k sales_metrics_delegation` before mapping | EXPECTED RED: 2 failed, 8 passed, 148 deselected, 1 Django `USE_TZ` deprecation warning in 2.29s; only the two expected positive cases failed. | 2026-11-05 |
| C-6 | Same focused command after mapping | PASS: 10 passed, 148 deselected, 1 Django `USE_TZ` deprecation warning in 1.51s. | 2026-11-05 |
| C-6 | `python -m py_compile opkeys/middleware.py tests/test_opkeys_internal.py`; `git diff --check` from Core | PASS for both checks. | 2026-11-05 |
