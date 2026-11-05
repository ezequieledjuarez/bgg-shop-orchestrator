# Tasks: CU-A02 — Sales Metrics & Reports (MVP)

Feature dir: `specs/010-sales-metrics-reports` | Plan: [plan.md](plan.md)

Format: `- [ ] ID [P] Description (path)`. `[P]` = parallelizable. Mark a task done only after its outcome and checks were observed; record each executed check and its result in the Evidence Ledger at the end. Validation is local-only. Contract tasks (X-*) precede implementation. Do not apply migrations to an active database; use disposable PostgreSQL for integration tests.

## Cross-cutting: Contracts (blocking)

- [x] X-1 Add `adminSalesMetrics(from, to, categories, productIds)` and payload types (`SalesMetrics`, `TopProduct`, `RevenueByDay`, `StatusCount`) to `bgg-shop-core/specs/schema.graphql`. Document staff/superuser access; UTC half-open range; revenue and `ordersCount` by `paid_at`; status counts by `created_at`; gross line-subtotal revenue; exact filters with matching orders counted once; dispatch rules; errors `UNAUTHENTICATED`/`FORBIDDEN`/`INVALID` with `extensions.field`; maximum range 366 days; and last 30 days when both bounds are omitted.
- [x] X-2 Add `GET /api/v1/admin/sales-metrics` to `bgg-shop-bff/specs/openapi.yaml` with optional `from`/`to`, repeated `category`/`product_id`, responses 200/400/401/403, `Cache-Control: no-store`, and planned status; document the business rules from X-1.
- [x] X-3 Add `GET /api/v1/admin/sales-metrics/categories` (distinct stored category values; 200/401/403/502; `Cache-Control: no-store`; planned) to the OpenAPI and matching `adminSalesCategories` query to the SDL with staff/superuser access and authorization error semantics.
- [x] X-4 Validate both contract documents and run `bgg-shop-bff/scripts/run_contracts.sh`; record the contract assertions and service-test result separately. Structural contract assertions passed; unrelated BFF service tests failed (see Evidence Ledger).

For future service work, check both BFF OpenAPI routes and Core GraphQL operations for existing or required contract definitions before implementation.

## Core (`bgg-shop-core`)

- [ ] C-1 Write failing PostgreSQL tests in `bgg-shop-core/tests/test_admin_sales_metrics_postgres.py` (disposable DB): `[from, to)` boundaries; only `paid` counts as revenue; subtotal-based gross revenue; category exact match and product filter; order with ≥1 matching line counted once while revenue sums only matching lines; top-10 ordering (units, revenue, bgg_id); `revenueByDay` (UTC days, zero-filled or documented gaps); dispatch boundaries at 23h59m, 24h, 71h59m, 72h; rejected/cancelled/`paid_stock_conflict` excluded from dispatch counts; payment-status counts by `created_at`; empty range; invalid range, >366 days, `from >= to`; 401/403 cases. (depends on X-4)
- [ ] C-2 Implement the resolver for `adminSalesMetrics` in `bgg-shop-core/saleor/graphql/api.py` (or a new module imported there) with staff/superuser guard, input validation and parameterized SQL (no string-built SQL, `Decimal` throughout). Make C-1 pass. (depends on C-1)
- [ ] C-3 Implement `adminSalesCategories` resolver and test. (depends on X-3)
- [ ] C-4 Check query plan locally with `EXPLAIN` on seeded data; add an index migration only if justified, as a separate reviewed step. Record result either way.
- [ ] C-5 Run Core test suite for touched areas and record results.

## BFF (`bgg-shop-bff`)

- [ ] B-1 Write failing tests in `bgg-shop-bff/tests/test_admin_sales_metrics.py`: auth required (401), non-admin (403), param validation (invalid/missing-tz dates, `from >= to`, >366 days, non-integer `product_id`), forwarding of repeated filters, `Cache-Control: no-store`, and negative tests proving no leakage of upstream exceptions, traces, internal URLs or credentials. (depends on X-4)
- [ ] B-2 Add proxy call in `bgg-shop-bff/src/proxy.py` and service in `bgg-shop-bff/src/services.py`, following `list_admin_audit`. (depends on B-1)
- [ ] B-3 Add `bgg-shop-bff/src/controllers/admin_sales_controller.py` with validation and error mapping; register it where other admin controllers are registered. Make B-1 pass. (depends on B-2)
- [ ] B-4 Add the categories endpoint with tests. (depends on X-3)
- [ ] B-5 Update `bgg-shop-bff/README.md` with the endpoints, filters and date semantics.
- [ ] B-6 Run BFF tests and contract tests; record results.

## Frontend (`bgg-shop-frontend`)

- [ ] F-1 Run `npm run generate:types` after X-2/X-3 and commit the regenerated `src/types/generated/bff-api.d.ts` (never hand-edit). (depends on X-4)
- [ ] F-2 Write failing Vitest tests in `bgg-shop-frontend/src/admin/sales/SalesPanel.test.tsx`: loading, error, empty and success states; filter wiring (dates, category, product); default range; display of dispatch states in Spanish; keyboard accessibility and accessible names. (depends on F-1)
- [ ] F-3 Implement `bgg-shop-frontend/src/admin/sales/SalesPanel.tsx`: date range and filters, revenue/orders summary, top-10 table, dispatch and payment status counts, native SVG/CSS bar chart for `revenueByDay`; fetch metrics and categories in parallel. Make F-2 pass. (depends on F-2)
- [ ] F-4 Register `/admin/sales` and add a "Ventas" link in `bgg-shop-frontend/src/admin/AdminRouter.tsx`.
- [ ] F-5 Add Playwright flow `bgg-shop-frontend/tests/e2e/sales.spec.ts` (admin login → dashboard → apply filter → values match seeded data); follow `audit.spec.ts` conventions. Run in the isolated local environment only. (depends on F-3, F-4)
- [ ] F-6 Run lint, build, Vitest and the E2E flow; record results.

## Verification & Documentation

- [ ] V-1 Compare dashboard totals (revenue, order counts, top products, dispatch counts) against direct SQL on the local seeded database; record queries and results.
- [ ] V-2 Local security checks: non-admin and unauthenticated rejected, no PII in payload, redacted errors, parameterized queries reviewed.
- [ ] V-3 Update `specs/010-sales-metrics-reports/plan.md` status and README references; keep claims limited to executed local checks (no CI/deployment).

## Dependencies

X-1..X-3 → X-4 → (C-1 → C-2, B-1 → B-2 → B-3, F-1 → F-2 → F-3) → F-5 → V-*.
Core, BFF and Frontend tracks can run in parallel after X-4; the BFF integration check against real Core and E2E need C-2 and B-3.

## Evidence Ledger

| Task | Check run | Result | Date |
|------|-----------|--------|------|
| X-1..X-3 | PyYAML parse and OpenAPI route/schema/parameter/response assertions; `graphql-core` parse and SDL operation/type assertions | PASS: `OPENAPI_PARSE_AND_ASSERTIONS=PASS`; `GRAPHQL_PARSE_AND_ASSERTIONS=PASS` | 2026-11-05 |
| X-4 | Direct `scripts/run_contracts.sh` from BFF | EXIT 126: script is not executable; rerun through Bash | 2026-11-05 |
| X-4 | `bash scripts/run_contracts.sh` after initial SDL update | EXIT 0: command reported pass; script runs `pytest tests/test_services_* -q` rather than schema parsers | 2026-11-05 |
| X-4 | Final `bash scripts/run_contracts.sh` after OpenAPI response-schema update | EXIT 1: 9 failed, 7 passed in 5.80s; failures are unchanged cart/product, GraphQL service, wishlist and order service tests (`allow_redirects` unexpected; `op_key` undefined), not contract parsing | 2026-11-05 |
| X-4 | Final PyYAML/OpenAPI and graphql-core/SDL parse plus shape assertions after duplicate-constraint fix | PASS: both admin paths, filters, response sets, `no-store`, planned status, Core operations/types, and CartItemRequest maximum verified | 2026-11-05 |
| C-1 | `python -m py_compile tests/test_admin_sales_metrics_postgres.py` from Core | PASS: test module syntax compiles; not a behavior test | 2026-11-05 |
| C-1 | `pytest -q tests/test_admin_sales_metrics_postgres.py` from Core | ERROR during collection: `ModuleNotFoundError: No module named 'saleor'`; repository root was not on the entrypoint import path | 2026-11-05 |
| C-1 | `PYTHONPATH=. pytest -q tests/test_admin_sales_metrics_postgres.py` from Core | 18 skipped, 1 warning: `SALES_METRICS_TEST_POSTGRES_DSN` is absent; no behavior-test RED observed and no database connection attempted | 2026-11-05 |
