# Implementation Plan: CU-A02 — Sales Metrics & Reports (MVP)

**Feature dir**: `specs/010-sales-metrics-reports` | **Date**: 2026-11-02 | **Source**: `CasosDeUso.md` (CU-A02)
**Status**: Implemented and locally verified on 2026-11-05. Core, BFF, generated frontend types, the admin dashboard, and the isolated OpKey sales E2E are implemented. Core touched-area tests passed (180); frontend lint, build and Vitest passed (212), and the isolated OpKey Playwright suite passed (10). The full BFF suite still has 12 unrelated legacy service-test failures; focused sales/admin tests passed (52). See `tasks.md` for exact commands and limitations. No CI or non-local deployment was run.

## Summary

Read-only admin dashboard: pick a date range and optional category/product filters, then see invoiced revenue, top-selling titles and order counts by status. No writes, no exports, no scheduled reports.

## Technical Context

- **Core**: Django/Graphene, PostgreSQL. Source data: `purchase_order`, `purchase_order_line`, `invoice`, `product_boardgame` (`category`) defined in `import_catalog.sql`. Contract: `bgg-shop-core/specs/schema.graphql`.
- **BFF**: Flask. Contract: `bgg-shop-bff/specs/openapi.yaml`. Follow the existing admin pattern (`admin_audit_controller.py`: staff/superuser guard, `UNAUTHENTICATED`/`FORBIDDEN`/`INVALID` errors, non-cacheable).
- **Frontend**: React/TS under `bgg-shop-frontend/src/admin` (new `sales/` module registered in `AdminRouter.tsx`). Types generated with `npm run generate:types`; never hand-edit.
- **Tests**: Core/BFF pytest, frontend Vitest, local Playwright. Local-only validation.

## MVP Scope

**In**
1. One query: `adminSalesMetrics(from, to, categories?, productIds?)` returning:
   - `revenueTotal` and `ordersCount` (paid orders in range),
   - `topProducts[]` (bgg_id, name, units, revenue; top 10 by units, tie → revenue, then bgg_id),
   - `ordersByDispatchStatus[]` (Pendiente / En preparación / Enviado / Entregado → count),
   - `ordersByPaymentStatus[]` (payment status → count),
   - `revenueByDay[]` (series for the chart).
2. Dashboard screen: date range + category/product filters, three summary blocks, loading/error/empty/success states, keyboard-accessible controls.
3. One simple chart (revenue per day) using native SVG/CSS; no chart library.
4. Category filter options retrieved from distinct stored category strings through `adminSalesCategories` and its BFF endpoint.

**Out (deferred)**: CSV/PDF export, saved reports, comparisons with prior periods, margin/profit, customer analytics, real-time updates, caching, role granularity beyond staff/superuser.

## Business Rules

- **Revenue** = sum of `purchase_order_line.subtotal` for orders with `status = 'paid'` and `paid_at` in `[from, to)` (UTC). When a category/product filter is active it sums only matching lines, keeping filtered and unfiltered totals consistent.
- `paid_stock_conflict`, `pending_payment`, `rejected`, `cancelled` do not count as revenue. Their counts are reported in `ordersByPaymentStatus`, filtered by `created_at` in range.
- **Dispatch status (derived, no new column; academic-project rule)**, computed at query time from `status` and `paid_at` (UTC), for orders in range by `created_at`:
  - `Pendiente`: `status = 'pending_payment'`.
  - `En preparación`: `status = 'paid'` and less than 24 h since `paid_at`.
  - `Enviado`: `status = 'paid'` and 24 h to less than 72 h since `paid_at`.
  - `Entregado`: `status = 'paid'` and 72 h (3 days) or more since `paid_at`.
  - `rejected`, `cancelled` and `paid_stock_conflict` have no dispatch status; they appear only in `ordersByPaymentStatus`.
  - The status is derived from the time of the query and is not persisted; `pickup` orders follow the same rule.
- Date range: timezone-aware ISO instants, `from < to`, maximum 366 days; invalid input fails with `extensions.code INVALID` + `field`.
- Callers must provide both `from` and `to`, or omit both. If exactly one is supplied, return `INVALID` and set `extensions.field` to the missing bound; if both are omitted, use the last 30 days. Bounds are normalized to UTC and interpreted as `[from, to)`.
- The categories operation returns distinct stored `product_boardgame.category` strings, requires staff or superuser access, and is non-cacheable.
- Money: Decimal end to end, ARS, serialized as in existing contracts.
- Default range if omitted: last 30 days.

## Decisions (confirmed by the user, 2026-11-02)

1. **Dispatch status**: derived states `Pendiente`, `En preparación`, `Enviado`, `Entregado`; an order is `Entregado` once 3 days have passed since payment. A real persisted dispatch status with an admin update flow is out of scope.
2. **Revenue basis**: `paid_at`.
3. **Category filter**: exact match on the stored `product_boardgame.category` string (single `VARCHAR(250)`); options come from distinct existing values.
4. **Access**: staff or superuser, as in audit.

5. **24 h boundary** between `En preparación` and `Enviado` accepted.
6. **Filtered order counts**: with a product/category filter, an order counts if it has at least one matching line (counted once). Revenue sums only matching lines.
7. **Date semantics (document in the endpoint description)**: revenue and `ordersCount` use `paid_at`; payment/dispatch status counts use `created_at`. An order created outside the range and paid inside it appears in revenue but not in status counts.
8. **Gross revenue**: sum of line `subtotal` (historical price at purchase); it ignores coupons, promotions and credit, so it may differ from `purchase_order.total`. State this in the contract.
9. **UI placement**: a section inside the existing admin panel (`AdminRouter.tsx`).
10. **Paired date bounds**: callers provide both `from` and `to`, or omit both; a one-sided range returns `INVALID` with `extensions.field` identifying the missing bound. Omitting both defaults to the last 30 days.

## Unresolved Contract Decisions

None open.

## Work Plan (contract first, then implementation)
The contract step includes both `adminSalesMetrics` and `adminSalesCategories` in Core, and both `GET /api/v1/admin/sales-metrics` and `GET /api/v1/admin/sales-metrics/categories` in BFF; category retrieval is planned, staff/superuser-only, and non-cacheable.

1. **Contracts**: add `adminSalesMetrics` and `adminSalesCategories` + payload types to Core `schema.graphql`; add `GET /api/v1/admin/sales-metrics` and `GET /api/v1/admin/sales-metrics/categories` to BFF `openapi.yaml`. Validate both contract documents' structure and record the result of `bgg-shop-bff/scripts/run_contracts.sh` separately, since that script runs BFF service tests rather than contract parsers.
2. **Core (TDD)**: resolver with staff/superuser guard and parameterized SQL aggregates (no string-built SQL). Tests on disposable PostgreSQL: range boundaries `[from, to)`, non-paid exclusion, filter consistency, top-10 tie-break, dispatch-status boundaries (23h59m, 24h, 71h59m, 72h), empty range, invalid input, FORBIDDEN/UNAUTHENTICATED.
3. **BFF (TDD)**: `admin_sales_controller.py`, input validation, error mapping without upstream detail, negative tests proving no leakage of exceptions, traces, internal URLs or credentials, non-cacheable headers.
4. **Frontend**: regenerate types, `admin/sales` page, filters, chart, states; Vitest for states and filter wiring.
5. **Verify locally**: Core + BFF pytest, frontend lint/build/Vitest, and one Playwright admin flow on a disposable local PostgreSQL database. The isolated E2E runner seeds and cleans a deterministic paid order; the dashboard, filtered BFF response, and direct SQL totals must agree. Never use the active `saleor` database for this fixture.
6. **Document**: update BFF, Core and Frontend READMEs; keep a task ledger (`tasks.md`) recording only checks actually executed and their results.

## Risks & Mitigations

- **Aggregation cost**: add an index only if a local `EXPLAIN` on realistic volume shows need (candidate `purchase_order (status, paid_at)`); as a separate reviewed migration.
- **Inconsistent totals across filters**: single revenue definition, covered by a consistency test.
- **Data exposure**: admin-only, no customer PII in payload, redacted errors.
- **Time zones**: boundaries in UTC; UI converts for display only.

## Acceptance Criteria

- An admin selects a range/filters and sees revenue, top titles and status counts matching a direct SQL check on local data.
- Non-admin and unauthenticated requests are rejected (403/401); invalid ranges return 400 without internal details.
- SDL and OpenAPI are updated before implementation; generated frontend types match.
- Applicable local checks pass; no CI, deployment or remote validation is claimed.
