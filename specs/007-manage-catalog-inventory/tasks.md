# Tasks: CU-A01 — Manage Catalog, Inventory & Promotions

Feature branch: CU-ADM-01
Feature dir: specs/007-manage-catalog-inventory

## Cross-cutting
1. Task X-1 — Define API contract between Core ↔ BFF
   - Description: Produce exact JSON schemas (requests/responses), error codes, and example payloads for all Core internal endpoints the BFF will call (products, variants, stock adjust, promotions, coupons, audit). Include HTTP status mapping for failure cases and concurrency error shapes.
   - Acceptance: JSON schemas reviewed and approved by Core and BFF; example cURLs; OpenAPI/GraphQL SDL draft present.
   - Estimate: S
   - Owner: Core + BFF

2. Task X-2 — DB Migrations & Data Model Changes (Core)
   - Description: Add `stackable` flag to promotions, add coupon global counter field and any tables needed for atomic counters, ensure audit table exists, add indices for reservation queries.
   - Acceptance: Migrations apply cleanly in dev; unit tests for new fields; schema documented.
   - Estimate: M
   - Owner: Core

3. Task X-3 — Concurrency tests & runbook
   - Description: Design and implement integration tests for concurrent stock adjustments and concurrent coupon redemptions; document expected behavior and rollback strategy.
   - Acceptance: Repro scripts and CI job passing; documented mitigation steps.
   - Estimate: M
   - Owner: Core

## Core (Saleor / Core E-commerce)
1. Task C-1 — Models & persistence
   - Description: Implement Product/Variant/Promotion/Coupon/Audit models and relations per spec. Ensure reserved units can be computed or joined from orders/reservations.
   - Acceptance: ORM models exist; unit tests for field constraints and serialization.
   - Estimate: M
   - Owner: Core

2. Task C-2 — Business logic: stock and reservation checks
   - Description: Implement atomic stock adjustment APIs and validations that prevent setting stock below reservations.
   - Acceptance: API rejects invalid reductions with explicit code; tests for reserved vs available flows.
   - Estimate: M
   - Owner: Core

3. Task C-3 — Promotion & coupon logic (stackable + global limit)
   - Description: Implement promotion evaluation service honoring `stackable` flag and coupon application with atomic decrement of global counter.
   - Acceptance: Unit & integration tests verifying stackable/no-stackable combinations and coupon exhaustion.
   - Estimate: M
   - Owner: Core

4. Task C-4 — Events / Webhooks
   - Description: Emit product.updated, stock.changed, promotion.updated, coupon.used, audit.logged events to event bus/webhooks for BFF cache invalidation.
   - Acceptance: Events published with documented payload; BFF can subscribe in dev environment.
   - Estimate: S
   - Owner: Core

5. Task C-5 — Audit logging
   - Description: Persist audit entries for admin create/edit/delete actions including diffs, actor, timestamp.
   - Acceptance: Queries can return audit history; test assertion on actions creates logs.
   - Estimate: S
   - Owner: Core

## BFF (Flask)
1. Task B-1 — Admin endpoints and validation
   - Description: Implement `/admin/products`, `/admin/promotions`, `/admin/coupons`, `/admin/audit` endpoints; validate payloads and require Admin role.
   - Acceptance: Endpoints respond with correct HTTP codes; field-level errors returned.
   - Estimate: M
   - Owner: BFF

2. Task B-2 — Error mapping & UX-friendly messages
   - Description: Map Core error codes to friendly messages and consistent HTTP responses for the Frontend.
   - Acceptance: Contract doc with mappings; tests verifying message shapes.
   - Estimate: S
   - Owner: BFF

3. Task B-3 — Cache and invalidation
   - Description: Implement caching strategy for product list/details and invalidate cache on Core events; configurable TTL.
   - Acceptance: Cached responses served; invalidation triggered by product/stock/promotion events within configured window.
   - Estimate: M
   - Owner: BFF

4. Task B-4 — Contract tests & integration
   - Description: Create contract/integration tests to validate BFF ↔ Core interactions and failure scenarios.
   - Acceptance: Tests pass in CI; documented failure handling.
   - Estimate: M
   - Owner: BFF

## Frontend (React Admin UI)
1. Task F-1 — Products list & search UI
   - Description: Implement product listing page with pagination, filters and search; link to edit/create forms.
   - Acceptance: Admin can browse products and navigate to edit/create.
   - Estimate: S
   - Owner: Frontend

2. Task F-2 — Create/Edit Product form
   - Description: Implement form with fields (title, description, category, price, variants, images) and client-side validation; image upload flow.
   - Acceptance: Form validates inputs, uploads images (mocked in tests), and shows server-field errors inline.
   - Estimate: M
   - Owner: Frontend

3. Task F-3 — Stock management UI
   - Description: Variant-level stock controls; use data from BFF to prevent reducing stock below `min_allowed_stock` / reserved units; show explanatory message.
   - Acceptance: UI blocks invalid reductions and shows message; integration test with BFF response shape.
   - Estimate: S
   - Owner: Frontend

4. Task F-4 — Promotions & Coupons UI
   - Description: Admin panel to create/edit promotions and coupons; include `stackable` flag and preview effective price.
   - Acceptance: Can create promotion/coupon, preview at product-level and save; errors rendered inline.
   - Estimate: M
   - Owner: Frontend

5. Task F-5 — Audit view & confirmations
   - Description: Show audit history for a product and add confirmation modals for destructive actions.
   - Acceptance: Audit entries visible; delete/unpublish requires explicit confirm.
   - Estimate: S
   - Owner: Frontend

## Testing & CI
- Add unit tests for each component (Core/BFF/Frontend) and end-to-end tests for admin flows (create/edit product, stock adjust, apply promotion).
- Add a lightweight CI job to run contract tests and frontend E2E on feature branch `CU-ADM-01`.

## Delivery & Acceptance
- Each completed task must include: implementation, unit tests, integration/contract tests (where applicable), and documentation (API schema, migrations, runbook).
- Bundle work-unit commits per task on branch `CU-ADM-01` with Conventional Commit messages.

## Estimates summary (T-shirt)
- S ~ 1-2 days, M ~ 3-6 days

---

If you want, I can now:
- Create `tasks.md` (done), or
- Open a set of subtasks as GitHub issues (requires GH access), or
- Start implementing the first Core task (models/migrations) locally.
