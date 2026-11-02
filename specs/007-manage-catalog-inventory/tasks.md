# Tasks: CU-A01 — Manage Catalog, Inventory & Promotions

Feature branch: CU-ADM-01
Feature dir: specs/007-manage-catalog-inventory

## Approved contracts-and-data scope (2026-11-02)

The initial bounded implementation authorization covered X-1, X-2 and C-1;
subsequent approved local work completed the remaining task groups and final
browser acceptance as recorded in the current status table. These decisions
supersede conflicting earlier statements below, including open-ended preview,
rounding and uncertain-payment notes. Validation is local-only; do not contact
remote services, deploy, or apply migrations to an active database. Preserve
existing worktree changes, do not rename or switch the current
`fix/spec-follow-ups` branch, and do not stage or commit pre-existing user
changes.

- Admin access requires an active `is_staff` or `is_superuser` user in both BFF
  and Core.
- `Product` maps the existing `product_boardgame` table as unmanaged. Product
  base price is greater than zero, name is unique, and quantity is nonnegative.
  Create requires name, price and quantity; updates are partial and cannot
  modify BGG ID or quantity. Exactly one `.webp` image reference (URL or
  path/filename) is supplied; binary upload is out of scope.
- Coupon codes are unique by exact, case-sensitive equality without
  normalization. Remaining uses are nonnegative. When both UTC validity dates
  exist, `starts_at < ends_at`; the interval is `[starts_at, ends_at)`.
- Promotion discounts are 0–50%. Admin store promotions may be global
  (`product_bgg_id` omitted/null) or product-specific; partial updates may
  explicitly clear the product link. At most one active product-specific
  promotion may target a product. Coupon-linked promotion rows are not global
  store offers. Creation requires an explicit `active` boolean; existing
  promotions become inactive during migration.
- `OUT` is partial-to-zero with requested/applied quantity in the result.
  A movement UUID is permanent and bound to product, direction and quantity;
  payload mismatch rejects. A retry with the same payload is permitted
  indefinitely after confirmed no-change. Never infer rollback from timeout
  or HTTP error.
- `POST /api/v1/cart/coupons/preview` is authenticated and read-only against
  the current user's cart; it does not reserve or consume. Checkout receives
  the chosen coupon and atomically reserves its use. Confirmed
  failure/cancellation releases it; uncertain outcomes remain reserved for
  provider reconciliation and unresolved cases go to manual review. Timeout
  alone never releases it.
- Coupon discounts above 50% of undiscounted cart subtotal are rejected, not
  capped. Calculate savings with decimal precision: sum all product-promotion
  savings and calculate the coupon saving on the undiscounted subtotal; round
  each total alternative once upward to whole pesos, then compare. The higher
  saving wins; ties favor the store promotion. There are no configurable
  exclusions; gift cards and credit are payment methods, not discounts.
- For store discounts, an eligible product-specific promotion takes precedence
  over all global offers for that cart product, even if a global percentage is
  higher. If no eligible specific offer exists, use the highest eligible
  global percentage. Do not stack promotions, and exclude coupon-linked
  promotion rows from both store-promotion selection and the admin promotion
  list; coupon routes continue to expose those rows.
- Audit read filters, pagination and redaction, and event/cache decisions are
  approved. Their implementation and local verification are recorded in the
  task status table; this introductory contracts-and-data scope is not itself
  the evidence.

These decisions are requirements; implementation and verification evidence is
recorded separately below. An ambiguous movement response must not be treated
as rollback. These contract decisions do not by themselves establish runtime
behavior.

Stock trace: requirement `specs/006-manage-catalog-inventory/spec.md`; contracts `bgg-shop-core/specs/schema.graphql` and `bgg-shop-bff/specs/openapi.yaml`; implementation `bgg-shop-core/saleor/graphql/api.py` and `bgg-shop-bff/src/controllers/admin_products_controller.py`; related tests `bgg-shop-core/tests/test_graphql_credit_postgres.py` and `bgg-shop-bff/tests/test_admin_validation.py`. UUID-bound movements, replay, recovery on retry, conflict and audit are implemented and tested on disposable PostgreSQL; migrations are not applied to the active database.

Verification (2026-11-01): 176 Core product and OpKey tests and 152 BFF administrative and contract tests passed; two existing BFF product-creation tests were excluded. All 17 selected stock-movement PostgreSQL tests passed in a disposable container. OpenAPI validation and `git diff --check` passed; SDL and runtime introspection matched for types, fields, arguments, enum values and descriptions after normalizing argument order. All Django-discovered migrations passed on disposable PostgreSQL with synthetic pre-existing commercial tables, not a copy of the active database; the later promotion migration discovery check below limits that result. A local HTTP flow through running BFF and Core with a synthetic OpKey verified unauthenticated rejection, movement creation, an `OUT` exceeding stock, replay, status lookup and identity conflict; the database contained one applied movement and one audit entry with stock at zero. The services and disposable database were stopped after verification.

Recovery verification (2026-11-01): 19 selected stock-movement PostgreSQL tests passed on a disposable database, including an abandoned provisional record, competing attempts, a locked active movement, rollback, uncertain commit and recovery through the BFF test client. Core product and OpKey tests passed (176), as did BFF administrative and contract tests (152; two existing product-creation tests excluded). OpenAPI and the changed GraphQL mutation's SDL/runtime types and description validated. At that point the live HTTP flow predated this recovery change and frontend integration remained untested.

Follow-up verification (2026-11-01): 21 stock-movement PostgreSQL tests passed on a disposable database, including 10 plus 20 yielding 30 and replay of the original result after a later partial stock reduction and a new database connection. A live local BFF-to-Core HTTP check on synthetic migrated data verified `IN_PROGRESS`, an identity conflict, recovery, replay and final `APPLIED` status; the database contained one audit record and one applied movement with stock 8. The test services and container were stopped. Two previously excluded BFF product-creation tests were corrected to use the registered route; the selected administrative and contract suite then passed all 154 tests without exclusions. This does not establish indefinite retention or frontend integration.

Product error follow-up (2026-11-01): BFF product creation and update now map known Core errors to static public messages and fields; technical or unknown errors return a sanitized `502`. Tests cover private upstream message, field and code values, known business errors, and endpoint-specific authentication, authorization and not-found statuses. Three additional administrative tests were corrected to use the registered route and current list service. The selected BFF administrative and contract suite passed 185 tests without exclusions, and OpenAPI validated. Other administrative resources have not been established as sanitized by this check.

Promotion contract follow-up (2026-11-01): BFF promotion DTOs now reject values and properties outside the OpenAPI request schemas, and update maps `discount_percent` to Core's `discountPercent`. The actual update document and variables validate against the Core SDL; no real promotion persistence was verified. GraphQL validation found that the BFF promotion list requests `discountPercent` and `active`, neither of which exists on Core's `Promotion` type, and coupon preview requests an input type and mutation absent from the SDL. Core accepts `active` in promotion inputs but does not persist it. On in-memory SQLite, `manage.py showmigrations promotions` reported no migrations although `saleor/promotions/migrations/0001_initial.py` exists without a package initializer; this migration was not included in the earlier migration test. Existing imported tables and migration adoption remain to be reconciled without modifying the active database. The selected BFF administrative and contract suite passed 218 tests; OpenAPI validated.

Promotion activation follow-up (2026-11-02; historical snapshot): Existing promotions must be inactive after migration. The BFF list now aliases Core's `discountPct` to `discountPercent`, preserving the public `discount_percent` field; the actual query validates against the Core SDL. Four focused tests passed on disposable PostgreSQL by applying the migration SQL to synthetic tables: existing rows remain intact and inactive, active state persists through GraphQL create/update/list, and coupon lookup returns the state. Core product tests passed (47), BFF promotion tests passed (30), BFF OpenAPI contract tests passed (5), and OpenAPI validated. At that snapshot, SQLite discovered `graphql.0014_promotion_manual_activation`, while `promotions` had no discovered migrations. The focused SQL tests did not establish that the full migration chain applies to existing databases, nor that checkout applies activation rules. The active database was not modified. The subsequent contract-first/state-sync work closes the earlier migration-discovery gap and records the approved preview contract; runtime checkout behavior remains unverified.

Coupon listing follow-up (2026-11-02; historical snapshot): Core exposes `availableCoupons` and BFF exposes public `GET /api/v1/coupons`, returning coupon codes and UTC validity dates without consuming uses. A coupon is listed when active, with remaining uses and both dates configured, from its start inclusive until its end exclusive. Migration `graphql.0015_coupon_availability` gives existing coupons independent inactive status and null dates; it was tested using synthetic PostgreSQL tables and has not been applied to the active database. Five selected PostgreSQL tests passed, alongside 47 Core product/schema tests and 40 BFF promotion/contract tests. A local in-process BFF-to-Core check with synthetic PostgreSQL data passed; it did not exercise HTTP transport between services. OpenAPI validated, and Django discovered the migration. At that snapshot, the full migration chain, management UI, payment application and uncertain-payment handling were not yet verified; later local results are in the current status table. Listing reflects stored remaining uses and is not a guarantee of availability at payment.

Contracts and data follow-up (2026-11-02): Django's GraphQL migration chain through `0016_coupon_constraints` passed on disposable PostgreSQL with synthetic pre-existing commercial tables and auth migration records. Existing synthetic promotions and coupons were preserved and set inactive; stock and an order were preserved. Migration `0016` enforces nonnegative coupon uses and ordered validity dates. A separate test confirmed that incompatible legacy data causes `0016` to roll back without altering that record or marking the migration applied. This does not establish adoption of the active database or the undiscovered `promotions` migration. The active database was not modified. Core now exposes `productByBggId`; BFF admin detail uses this direct lookup and returns `400`, `404` or sanitized `502` instead of scanning or returning cached placeholder price and stock. The actual BFF promotion and coupon-list GraphQL documents validated against the SDL and runtime; an in-process admin detail integration passed with a simulated database, not HTTP or real PostgreSQL. Verification: 66 Core tests, 201 BFF tests, eight selected PostgreSQL tests, two cross-service tests and OpenAPI validation passed.

ZIP archive generation remains outside the current Spec 007 scope.

Contracts/data implementation follow-up (2026-11-02): X-1 contracts are
recorded in OpenAPI 3.2 and Core SDL, including staff/superuser authorization,
positive product price, partial immutable-ID/quantity updates, one `.webp`
reference, product-linked non-combinable promotions, stock partial-to-zero
results, and read-only current-cart coupon preview with checkout reservation
and uncertain-payment handling. The system `openapi-spec-validator 0.9.0`
accepted `bgg-shop-bff/specs/openapi.yaml`; Core SDL syntax is checked by the
focused test. C-1 model metadata maps the existing product table and keeps
existing coupon-counter and audit models. X-2 adds the discovered
`graphql.0017_007_contract_data_dependencies` migration with positive product
price and 0–50% promotion checks, product BGG foreign key, partial unique
active-promotion index, and explicit validation of existing rows. Existing
coupon constraints in `0016` are reused, not duplicated.

Earlier verification snapshot (2026-11-02; superseded by the state-sync and
current-verification records below): `python -m pytest -q
tests/test_007_catalog_data_contracts.py` passed five tests; `python manage.py
check` passed; `python manage.py makemigrations --check --dry-run` reported no
changes but warned that migration history could not be checked because the
configured local host `db` did not resolve. Migration graph validation passed
inside the focused test. No disposable local PostgreSQL DSN was configured,
so migration SQL was not executed; no active database was contacted or
modified. X-2 remains partial until safe isolated migration execution. The
requested database-migration instruction and Engram mirror are unavailable.
No other task was closed. A safe work-unit commit was not possible because the
worktree contains pre-existing user changes and untracked files.

Migration-discovery and contract follow-up (2026-11-02): Added the
`promotions` migration package marker and an explicit dependency from
`graphql.0014_promotion_manual_activation` to `promotions.0001_initial`, while
preserving its existing GraphQL dependency. A focused `MigrationLoader(None)`
test now confirms discovery, graph consistency and ordering. The OpenAPI
contract test confirms create/update inherit the shared strictly-positive
price rule; Core SDL now documents the positive update price and staff/
superuser authorization for stock adjustment. Focused tests passed (6), Django
system checks passed, and the installed OpenAPI 3.2 validator passed.

At that earlier snapshot, the migration drift check did not pass. With an in-memory SQLite
override, `makemigrations --check --dry-run` raises `ValueError: too many
values to unpack` because the existing `promotions.0001_initial` migration
uses the invalid target `saleor.promotions.Promotion`; fixing it needs approval
to edit `bgg-shop-core/saleor/promotions/migrations/0001_initial.py`. The
default-host invocation attempted `db` at `192.168.1.202` and received
connection refused; no connection was established, and no migration was
applied. There is no disposable local PostgreSQL DSN.

At that earlier snapshot, the C-1 model constraints for the approved decisions
were present, but
independent verification also found that the existing DDL's unique
`product_boardgame.name` is not represented by the model and Promotion/Coupon
model IDs use the default `BigAutoField` while the DDL and initial migration
use `SERIAL`/`AutoField`. Resolving these model/DDL mismatches requires
approval to edit `bgg-shop-core/saleor/promotions/models.py`; C-1 was therefore
partial at that snapshot. The subsequent state-sync work and current model
state are recorded below. This task does not edit the separate frontend task
document.

## Current verification snapshot (2026-11-02)

Trace: requirements are in `specs/007-manage-catalog-inventory/plan.md` and
this task ledger; contracts are `bgg-shop-bff/specs/openapi.yaml` and
`bgg-shop-core/specs/schema.graphql`; implementation is
`bgg-shop-core/saleor/promotions/models.py`,
`bgg-shop-core/saleor/graphql/migrations/0017_007_contract_data_dependencies.py`
and `bgg-shop-core/saleor/promotions/migrations/0002_007_state_sync.py`;
focused tests are `bgg-shop-core/tests/test_007_catalog_data_contracts.py`.

X-1, X-2 and C-1 are complete. OpenAPI 3.2, Core SDL parity, migration
application and data/constraint behavior were verified locally; see the
contracts and migration references above and focused checks below. Final
checkout integration is covered by
`bgg-shop-core/tests/test_graphql_credit_postgres.py`:
`test_checkout_store_promotions_select_specific_and_highest_global_but_exclude_coupon_rows`
and `test_checkout_total_uses_specific_and_highest_global_store_promotions`
each passed against newly created disposable PostgreSQL 15 databases. These
were selected tests, not a run of the entire PostgreSQL test file.

Final local focused checks: BFF
`python -m pytest -q tests/test_admin_promotions.py tests/test_admin_coupons.py tests/test_admin_audit.py tests/test_opkey_admin.py`
passed 108 tests; Core
`python -m pytest -q tests/test_opkeys_internal.py` passed 148 tests;
Core `python -m pytest -q tests/test_coupon_calculations.py tests/test_007_catalog_data_contracts.py`
passed 30 tests; Frontend
`npm run test -- --run src/admin/promotions/PromotionForm.test.tsx src/admin/promotions/PromotionsPanel.test.tsx`
passed 14 tests. The final isolated browser command
`cd bgg-shop-frontend && E2E_CORE_CONTAINER=bgg-e2e-007-closeout-api npm run test:e2e:opkey`
passed 9 tests on 1 worker. Its covered admin flows and final integration
details are recorded in `odd/tasks/007-closeout.md`. Root and each service's
`git diff --check` passed in independent verification. This evidence is
local-only; no CI, deployment or remote validation is claimed. Historical
dated snapshots below remain historical and are superseded where they report
open, partial or unverified status for these completed tasks.

## Current Task Status

Snapshot: 2026-11-02. This table counts the 17 overall tasks below once;
service-specific and historical task lists are supporting breakdowns and are
not additional tasks in this count. **Totals: 17 completed / 0 partial /
0 unverified.** Completion evidence below is from local checks only.

| Task | Status | Remaining work or evidence |
| --- | --- | --- |
| X-1 | Completed | OpenAPI 3.2 and Core SDL record (promotion creation requires an explicit boolean `active`; updates stay partial) the approved admin, product, promotion, stock, coupon-preview and checkout contracts. OpenAPI validation and exact Core Graphene introspection parity against the SDL passed locally. |
| X-2 | Completed | The full migration chain through `graphql.0017` and `promotions.0003` applied on a fresh temporary PostgreSQL schema and an adopted legacy schema. Product/promotion/coupon constraints, stock-reservation FK/check, data preservation, and legacy promotion deactivation were verified. No active database was modified. |
| X-3 | Completed | Stock and coupon concurrency are tested. Coupon checkout uses the existing `X-Op-Key` flow and late approvals safely reacquire released uses or enter durable manual review. Final disposable PostgreSQL 15 selector passed 10 tests (133 deselected), covering concurrent last-use reservation, same-key replay, uncertain outcomes retained through pending status, confirmed failure/cancellation release, late approval, and payment reconciliation. The local runbook records the approved mitigation; CI evidence is excluded because validation is local-only. |
| C-1 | Completed | Model state and persisted PostgreSQL constraints were verified on fresh and legacy schemas, including product price/quantity, promotion discount/product, coupon validity/remaining uses, and stock-reservation FK/nonnegative quantity. Reservation behavior is not implemented by this task. |
| C-2 | Completed | Core UUID stock adjustment guarantees passed 22 focused PostgreSQL tests, including replay after later stock changes/reconnection and a confirmed `NO_STOCK` retry after replenishment/reconnection. The status UUID primary key has no expiry, details use `ON DELETE RESTRICT`, and no application-managed purge was found. Identity conflicts, concurrency and BFF/Core recovery are covered. Frontend preserves uncertain UUID/payload and provides explicit retry/status lookup. |
| C-3 | Completed | Core/BFF discount calculations, authenticated read-only current-cart coupon preview, checkout reservation/release and reconciliation passed focused contract/unit checks (Core 22, BFF 45; deterministic calculation suite 13 passed) and the final disposable PostgreSQL 15 selector (10 passed, 133 deselected). Coverage includes concurrent reservations, idempotent same-key replay, uncertain outcomes retaining the reservation through pending status, and confirmed rejection/cancellation release. |
| C-4 | Completed | Local Core outbox→signed BFF HTTP→real Redis flow passed for product, stock, and promotion events. A BFF 503 left the product event pending; the same event UUID retried successfully, and all three deliveries invalidated cached generation data. Source emitters cover product create/update, stock adjustment, payment checkout, store-credit checkout, and promotion create/update. |
| C-5 | Completed | Stock, coupon, product and promotion audit writes and protected reads (filters, cursor, redaction) are verified. The new `(created_at DESC, id DESC)` index migration passed isolated PostgreSQL apply/reverse/reapply and cursor-order tests (14 audit tests passed); the final browser audit flow also passed. |
| B-1 | Completed | Product, stock, promotion, coupon, gift-card and audit admin routes, validation and staff authorization passed the focused BFF admin suite (262 tests). |
| B-2 | Completed | Core error mapping is tested; BFF product, promotion, coupon, gift-card and audit errors use consistent sanitized public responses. The focused BFF admin/error suite passed 262 tests, including private-upstream disclosure checks. |
| B-3 | Completed | Public product list/detail responses use a configurable 60-second-default Redis TTL and generation invalidation; oversized internal event requests are rejected before body reads. The local integration verified real Redis generation invalidation, fresh cache loading, generic failure responses, and retry delivery after Redis recovery. |
| B-4 | Completed | Local outbox→signed BFF→Redis delivery/retry was verified; the final focused BFF admin and cross-service contract/order/credit/product suite passed 417 tests. Core GraphQL SDL/runtime semantic drift is reconciled: exact introspection parity and Core product/contract suites passed (67 tests), and coupon calculations passed (13 tests). CI evidence is excluded by the local-only project constraint. |
| F-1 | Completed | Product create/readback/edit and admin navigation passed in the final 9-test isolated browser run. Code: `bgg-shop-frontend/src/admin/products/ProductsList.tsx`; E2E: `bgg-shop-frontend/tests/e2e/product-create.spec.ts`, `product-edit.spec.ts`, `admin.spec.ts`. |
| F-2 | Completed | Create/readback/edit passed in the final browser run. Code: `bgg-shop-frontend/src/admin/products/ProductForm.tsx`, `bgg-shop-bff/src/proxy.py`, `bgg-shop-core/saleor/graphql/api.py`. The exact Core binding is `GET /api/v1/admin/products/{bggId}` → `productByBggId(bggId)`; mismatched IDs, methods, routes and GraphQL roots are rejected by `bgg-shop-core/tests/test_opkeys_internal.py`. |
| F-3 | Completed | Browser stock adjustment passed. Code/test references: `bgg-shop-frontend/src/admin/products/StockAdjustmentForm.tsx`, `StockAdjustmentForm.test.tsx`, `tests/e2e/variants-stock.spec.ts`, and `bgg-shop-core/tests/test_graphql_credit_postgres.py`. |
| F-4 | Completed | Coupon create/list/edit, product-specific promotion preview/create/list, and global promotion create/list passed in the final browser run. Authenticated current-cart coupon preview passed 9 focused Frontend tests. Code: `bgg-shop-bff/src/controllers/admin_promotions_controller.py`, `bgg-shop-core/saleor/graphql/orders.py`; tests: Frontend promotion UI (14 passed), `bgg-shop-frontend/src/App.cart.test.tsx` (9 passed), `bgg-shop-frontend/tests/e2e/coupons.spec.ts`, `promotions.spec.ts`, `src/admin/promotions/PromotionForm.test.tsx`, `src/admin/promotions/PromotionsPanel.test.tsx`, Core calculations/contracts (30 passed), and selected PostgreSQL tests (1 passed each) in `bgg-shop-core/tests/test_coupon_calculations.py` and `bgg-shop-core/tests/test_graphql_credit_postgres.py`. |
| F-5 | Completed | Audit filters and pagination passed in the final browser run, which also printed `Audit verified`. Code/tests: `bgg-shop-frontend/src/admin/audit/AuditPanel.tsx`, `AuditPanel.test.tsx`, and `tests/e2e/audit.spec.ts`; final command details are in `odd/tasks/007-closeout.md`. Weekly audit ZIP generation and retention remain outside Spec 007. |

**Count:** 17 completed, 0 partial and 0 unverified. Weekly audit ZIP generation and retention remain outside this task count and Spec 007 scope.

## Suggested closure batches

These are execution groups, not separate task counts. The current task-status
table above is authoritative; this breakdown does not reopen completed work.

1. **Stock recovery — C-2, F-3**
   - C-2 is complete: application-managed UUID expiry/purge is absent, and
     focused PostgreSQL tests cover late replay and retained identity.
   - F-3's UI and focused tests are implemented; stock adjustment passed in
     the final isolated browser run.
2. **Promotions and coupons — X-3, C-3, F-4**
   - X-3/C-3 are complete: the local PostgreSQL 15 selector passed 10 tests,
     and the local mitigation/runbook is documented. CI evidence is excluded
     by the local-only project constraint.
   - The local runbook mitigation is to keep uncertain reservations held,
     reconcile against the provider, release only after confirmed failure or
     cancellation, and leave unresolved cases for manual review. Timeout alone
     never releases a use.
   - F-4 promotion and coupon management flows passed in the final isolated
     browser run.
3. **Events and cache — C-4, B-3**
   - C-4 and B-3 are complete: the local Core dispatcher delivered signed
     product, stock and promotion events over HTTP to the BFF; real Redis
     generation invalidation and a BFF-failure/retry path passed.
   - The in-memory SQLite harness normalized UUID storage to the Django
     SQLite representation and used UTC-aware settings; PostgreSQL persistence
     was not part of this integration proof.
4. **Administration and audit — C-5, B-1, B-2, F-5**
   - C-5, B-1 and B-2 are complete: 14 isolated PostgreSQL audit tests verify
     migration apply/reverse, index definition and cursor order; 262 BFF admin
     tests verify route, authorization, validation and error handling.
   - F-5 audit filters and pagination passed in the final browser run.
5. **Catalog UI — F-1, F-2**
   - Implementation and focused tests are present; product create/readback/edit
     and admin navigation passed in the final browser run.
6. **Final browser E2E — F-1–F-5**
   - Local contracts and cross-service checks are complete. The final isolated
     browser command passed 9 tests on 1 worker; no CI or remote deployment
     validation is claimed.

**PostgreSQL verification (2026-11-02):** The focused catalog-contract suite and
the fresh/legacy migration tests passed (9 tests total) against a newly-created
local PostgreSQL database. The fresh schema rejects negative reservation
quantities and unknown product IDs; the legacy schema retains reservation,
product, order, promotion and coupon rows. The temporary database and role were
removed and verified absent. `DATABASE_URL=sqlite:///:memory: python manage.py
check` and `makemigrations --check --dry-run` passed; no model drift was detected.

**Stock UI verification (2026-11-02):** Review-driven fixes enforce the BFF
maximum quantity before UUID allocation, update the parent inventory display
only from a confirmed server result, and refuse to replace an unresolved
per-product movement found in local storage. Focused Frontend tests passed
(13), the production build passed, and 21 Core PostgreSQL stock-movement tests
passed. The temporary database and role were removed and verified absent.
At the time of this historical verification, F-3 remained partial pending the
browser E2E flow and C-2 remained partial pending late-replay and retention
evidence; see the stock-recovery closure below. The generated
`AdminUpdateProductRequest` type still permits `quantity` because OpenAPI uses
`not`; correcting that requires a separately authorized OpenAPI schema change.

**Stock recovery closure (2026-11-02):** C-2 is complete. Focused Core tests
passed against a disposable local PostgreSQL 15 container:
`PYTHONPATH=. pytest -q tests/test_graphql_credit_postgres.py -k 'stock_movement'`
(22 passed, 117 deselected). Coverage includes retry after confirmed `NO_STOCK`
once stock is replenished, an intervening movement, and a reopened connection;
the existing test also confirms an applied movement replays its original
result after a later stock change and reconnect. `stock_movement_status`
retains its UUID primary key without expiry, `stock_movement_details` references
it with `ON DELETE RESTRICT`, and no application-managed expiry/purge path was
found. The stock runtime already met the contract; no runtime code changed.
The PostgreSQL test fixture creates the catalog event-outbox table because the
stock mutation writes an event transactionally. The disposable container was
removed. In this earlier pre-final-browser snapshot, E2E had not run and F-3
remained open; the final browser result is recorded in the current status table.

## Cross-cutting
1. Task X-1 — Define API contract between Core ↔ BFF
   - Description: Define OpenAPI 3.2 and Core SDL contracts for the approved product, stock, promotion and coupon-preview/checkout decisions. Admin access requires an active staff or superuser user. Approved audit read and event/cache decisions remain implementation work in their respective tasks.
   - Acceptance: Approved request/response shapes and examples; OpenAPI/GraphQL SDL validated; runtime behavior remains separately tracked.
   - Estimate: S
   - Owner: Core + BFF

2. Task X-2 — DB Migrations & Data Model Changes (Core)
   - Description: Add a positive product price constraint, nullable promotion product linkage, 0–50% discount constraint, partial unique active-product-promotion-per-product index, and persisted stock-reservation FK/nonnegative check. Reuse existing coupon counter, audit table and coupon constraints; do not create duplicate tables or apply to an active database.
   - Acceptance: Migration graph and data constraints validate locally on both fresh and legacy schemas; isolated PostgreSQL migration execution is required before claiming database application.
   - Estimate: M
   - Owner: Core

3. Task X-3 — Concurrency tests & runbook
   - Description: Design and implement integration tests for concurrent stock adjustments and coupon reservations; document the approved confirmed-failure release and uncertain-outcome reconciliation behavior.
   - Acceptance: Focused integration tests pass against disposable local PostgreSQL and local mitigation steps are documented. CI jobs/evidence are excluded because this project is deployed and validated exclusively in local environments.
   - Estimate: M
   - Owner: Core

## Core (Saleor / Core E-commerce)
1. Task C-1 — Models & persistence
   - Description: Map the existing `product_boardgame` table as unmanaged and model Product/Promotion/Coupon/Audit relations per approved decisions. Each game edition or variant is a separate product with its own stock; reservation behavior is not implemented.
   - Acceptance: ORM models and state match the schema; tests cover field constraints and serialization, and isolated PostgreSQL checks verify persisted constraints and legacy data preservation.
   - Estimate: M
   - Owner: Core

2. Task C-2 — Business logic: product stock adjustments
   - Description: `IN` increases stock and `OUT` reduces it, including partially. At zero the product remains visible with «Sin stock»; reservation behavior and unpublishing are not part of this flow. When `OUT` exceeds available stock, apply partially to zero and report requested and applied quantities. A confirmed no-change allows retry with the same payload indefinitely; a timeout or HTTP error is not proof of rollback. Movement UUID identity and atomic commit are required as described above.
   - Acceptance: Once implemented, tests cover 10 plus 20 yielding 30, partial reduction, zero stock and confirmed no-change; they also cover same-payload retry without duplicate application, rejection of a reused ID with different product/direction/quantity, permanent UUID binding, and atomic commit. An ambiguous response must not be treated as rollback.
   - Estimate: M
   - Owner: Core

3. Task C-3 — Promotion & coupon logic
   - Manual activation: `active` is independent of validity dates; a disabled promotion does not apply within its date range, while an enabled promotion remains subject to the dates. Existing promotions become inactive during migration. Earlier focused synthetic-PostgreSQL checks covered promotion persistence and GraphQL exposure; they do not establish that the current full migration set was executed or that checkout applies promotions.
   - Coupon reservation: checkout atomically reserves the chosen coupon. Confirmed failure/cancellation releases the reservation; uncertain outcomes retain it for provider reconciliation. Unresolved cases go to manual review; timeout alone does not release the reservation. These are approved requirements, not runtime evidence.
   - Coupon limit and comparison: reject coupon discounts above 50% of undiscounted cart subtotal, not cap them. Keep decimal precision, sum all product-promotion savings, calculate coupon savings on the undiscounted subtotal, round each total alternative once upward to whole pesos, then compare; a tie favors the store promotion. There are no configurable exclusions. Gift cards and credit are payment methods, not discounts.
   - Coupon consultation: codes use exact case-sensitive equality without normalization; remaining uses are nonnegative. When both UTC validity dates exist, `starts_at < ends_at` and the interval is `[starts_at, ends_at)`. `POST /api/v1/cart/coupons/preview` requires authentication and the user's current cart; it is read-only and neither reserves nor consumes. Missing code returns `404`; unauthenticated preview returns `401`. Runtime behavior is not established.
   - Description: Implement the approved whole-purchase coupon and store-promotion rules. Per product, an eligible specific store promotion wins over every global offer; otherwise use the highest eligible global percentage. Exclude coupon-linked promotion rows from store offers and do not stack promotions. Sum selected per-product promotion savings and compare that total with coupon savings on the undiscounted cart subtotal. Round each alternative total once upward to whole pesos, choose the greater saving, and favor store promotions on a tie. Reject coupon discounts above 50% of undiscounted subtotal. Coupon codes are exact and case-sensitive; preview uses the authenticated user's current cart without reserving or consuming. Checkout reserves the chosen coupon atomically; release only on confirmed failure/cancellation, retain uncertain outcomes for reconciliation, and send unresolved cases to manual review. Timeout alone does not release a reservation. No configurable exclusions; gift cards and credit are payment methods, not discounts.
   - Acceptance: Tests verify the approved alternative calculation, rounding and tie behavior, coupon validation and preview non-consumption, and checkout reservation/release/reconciliation behavior. Focused Core/BFF contract and unit checks plus disposable local PostgreSQL concurrency/reconciliation checks passed; no remote or active database was used.
   - Estimate: M
   - Owner: Core

4. Task C-4 — Events / Webhooks
   - Description: Persist minimal catalog events transactionally in Core and deliver them to `POST /internal/v1/catalog-events` with HMAC-SHA256 authentication and retry.
   - Acceptance: Tests verify the exact event envelope/signature, product/stock/promotion and checkout stock-write paths, retry behavior, and BFF invalidation. Local Core→BFF delivery and real Redis invalidation/retry passed; CI/remote validation is not claimed.
   - Estimate: S
   - Owner: Core

5. Task C-5 — Audit logging
   - Description: Persist audit entries for admin create/edit/delete actions including diffs, actor and timestamp. Cover product changes, stock movements, promotions and coupons with user, date, action, and previous and new values. Implement the approved audit read filters, pagination and redaction. ZIP archive generation is outside Spec 007 scope; an existing AuditLog model does not prove coverage.
   - Acceptance: Tests verify audit records across all four areas and the approved access, filters, pagination and redaction. The existing reference to delete actions does not establish or require physical product deletion.
   - Estimate: S
   - Owner: Core

## BFF (Flask)
1. Task B-1 — Admin endpoints and validation
   - Description: Implement `/admin/products`, `/admin/promotions`, `/admin/coupons`, `/admin/audit` endpoints and validate payloads. Require an active `is_staff` or `is_superuser` user for admin operations; implement the approved audit access policy.
   - Acceptance: Endpoints respond with correct HTTP codes and field-level errors; audit access follows the approved contract.
   - Estimate: M
   - Owner: BFF

2. Task B-2 — Error mapping & UX-friendly messages
   - Description: Map Core error codes to friendly messages and consistent HTTP responses for the Frontend.
   - Acceptance: Contract doc with mappings; tests verifying message shapes.
   - Estimate: S
   - Owner: BFF

3. Task B-3 — Cache and invalidation
   - Description: Cache only public `/api/v1/products` and `/api/v1/games/{slug}` responses in Redis with a configurable 60-second default TTL and generation-based invalidation.
   - Acceptance: Tests verify normalized list/detail cache keys, TTL, cache-outage fallback, signed event validation, and generation invalidation. Local real-Redis integration and retry passed; CI/remote validation is not claimed.
   - Estimate: M
   - Owner: BFF

4. Task B-4 — Contract tests & integration
   - Description: Create contract/integration tests to validate BFF ↔ Core interactions and failure scenarios.
   - Acceptance: Focused local contract/integration tests pass and failure
     handling is documented. CI jobs/evidence are excluded because this project
     is deployed and validated exclusively in local environments.
   - Estimate: M
   - Owner: BFF

## Frontend (React Admin UI)
1. Task F-1 — Products list & search UI
   - Description: Implement product listing page with pagination, filters and search; link to edit/create forms.
   - Acceptance: Admin can browse products and navigate to edit/create.
   - Estimate: S
   - Owner: Frontend

2. Task F-2 — Create/Edit Product form
   - Description: Implement form with fields (title, description, category, price and one `.webp` image reference by URL or filename) and client-side validation, without assuming binary upload. Each edition is a separate product.
   - Acceptance: Form validates inputs, submits the image reference, and shows server-field errors inline.
   - Estimate: M
   - Owner: Frontend

3. Task F-3 — Stock management UI
   - Description: Product stock adjustments follow `IN` for increases and `OUT` for reductions, including partial reductions. Zero stock leaves the product visible; reservation behavior and unpublishing are not part of this flow. When `OUT` exceeds available stock, apply partially to zero and report requested and applied quantities.
   - Acceptance: Once implemented, tests cover increases, partial reductions, requested/applied quantities when `OUT` reaches zero, and a product visible with exactly «Sin stock» at zero, using the agreed BFF contract.
   - Estimate: S
   - Owner: Frontend

4. Task F-4 — Promotions & Coupons UI
   - Description: Admin panel to create/edit promotions and whole-purchase coupons using the approved discount and coupon-preview decisions.
   - Acceptance: Can create and save a promotion or coupon and preview the promotion at product level; coupon preview follows the approved authenticated-current-cart contract and does not reserve or consume a use. Errors are rendered inline.
   - Estimate: M
   - Owner: Frontend

5. Task F-5 — Audit view & confirmations
   - Description: Show audit history and add confirmation modals for destructive actions, using the approved audit read and redaction decisions.
   - Acceptance: Audit entries are visible according to the approved access, filters and pagination; redaction follows the approved rules. Confirmation requirements for destructive actions do not imply unpublishing or physical deletion. ZIP archive generation is outside the current 007 scope.
   - Estimate: S
   - Owner: Frontend

## Testing & CI
- Add unit tests for each component (Core/BFF/Frontend) and end-to-end tests for admin flows (create/edit product, stock adjust, apply promotion).
- This project is deployed and validated exclusively in local environments:
  the focused contract/integration/frontend checks and final isolated browser
  run passed locally, as recorded above and in `odd/tasks/007-closeout.md`.
  CI, deployment and remote evidence are not claimed.

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
