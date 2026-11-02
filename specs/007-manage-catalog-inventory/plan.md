# Plan: CU-A01 — Manage Catalog, Inventory & Promotions (Overall)

Feature branch: CU-ADM-01
Feature dir: specs/007-manage-catalog-inventory

## Goal
Deliver a locally validated admin flow to manage products, stock, promotions and coupons with safe business rules. Product price is greater than zero, name is unique, and quantity is nonnegative. `Product` maps the existing `product_boardgame` table as unmanaged. Admin store promotions may be product-specific or global (`product_bgg_id` omitted/null), allow a 0–50% discount, and retain at most one active product-specific promotion per product; multiple global offers may be active. Creation requires an explicit `active` boolean, updates are partial and may clear the product link, and existing promotions become inactive during migration. Coupon-linked promotion rows are coupon offers, not global store promotions.

`IN` increases stock and `OUT` reduces it, including partially; zero stock leaves the product visible as «Sin stock», without reservation behavior. If `OUT` exceeds available stock, apply only the available quantity and report requested and applied quantities. A movement UUID is permanent and bound to product, direction and quantity; payload mismatch rejects. A retry after confirmed no-change may use the same payload indefinitely. A timeout or HTTP error does not establish rollback.

Discount coupons apply to the whole purchase; product-specific coupons are outside this MVP. For each cart product, an eligible product-specific store promotion wins over any global store offer, even when the global percentage is higher; otherwise choose the highest eligible global percentage. Store promotions never stack, and coupon-linked promotion rows are excluded from store-offer selection. Sum the selected per-product promotion savings and compare them with the coupon saving calculated against the undiscounted cart subtotal. Keep decimal precision while calculating, round each total alternative once upward to whole pesos, then choose the larger saving; ties favor the store promotion. Coupon discounts above 50% of the undiscounted cart subtotal are rejected, not capped. There are no configurable exclusions. Gift cards and credit are payment methods, not discounts. Other closed checkout specs are unchanged. These rules are implemented and covered by focused calculation/contract tests and the local PostgreSQL checkout-path integration test cited in the closeout evidence; this is not CI or deployment validation.

## Phases & Milestones
Coupon decisions confirmed on 2026-11-02 supersede conflicting older statements in this plan: active coupons may be listed without a cart; preview requires an authenticated user and that user's current cart. `POST /api/v1/cart/coupons/preview` is read-only and neither reserves nor consumes a use. At checkout, the chosen coupon is reserved atomically. Confirmed failure or cancellation releases the reservation; an uncertain outcome retains it for provider reconciliation, and unresolved cases go to manual review. Timeout alone never releases it. Codes use exact case-sensitive equality without normalization; remaining uses are nonnegative. When both UTC validity dates exist, `starts_at < ends_at`, and validity is `[starts_at, ends_at)`. Reject inactive, not-yet-valid, expired, exhausted or over-50% coupons with a reason; a missing code returns `404` and unauthenticated preview returns `401`. These are contract requirements, not implementation evidence.

If an `IN`/`OUT` operation does not affect the database, it is cancelled or rejected; a confirmed no-change permits retrying the same payload indefinitely. A communication or HTTP error does not prove rollback: the server may commit and the response may be lost. Each movement UUID is permanently bound to product, direction and quantity; reuse with different data rejects, and an identical retry must not apply the change twice. The stock change, audit and final result must commit atomically. Report requested and applied quantities when an `OUT` is partial. Inform the user and log errors safely without sensitive details. The final focused and browser evidence is local-only; see the task ledger and closeout.

Stock trace: requirement `specs/006-manage-catalog-inventory/spec.md`; contracts `bgg-shop-core/specs/schema.graphql` and `bgg-shop-bff/specs/openapi.yaml`; implementation `bgg-shop-core/saleor/graphql/api.py` and `bgg-shop-bff/src/controllers/admin_products_controller.py`; related tests `bgg-shop-core/tests/test_graphql_credit_postgres.py` and `bgg-shop-bff/tests/test_admin_validation.py`. UUID-bound movements and recovery on retry are implemented and tested on disposable PostgreSQL. Migrations have not been applied to the active database.

Basic audit remains in scope: record user, date, action, and previous and new values for product changes, stock movements, promotions, and coupons. Audit reads, filters, pagination and redaction, and event/cache behavior have local implementation/test evidence recorded in the task ledger. An existing AuditLog model alone does not establish coverage. Weekly audit ZIP generation and related retention enforcement remain outside Spec 007 scope.

1. Design & Contracts (2 days)
   - Complete API contract Core↔BFF (schemas, errors)
   - Approve DB migration plan
2. Core Implementation (6-12 days)
   - Models, migrations, business logic (product stock, promotions, coupons); no stock reservations
   - Events and audit
   - Concurrency tests
3. BFF Integration (4-8 days)
   - Admin endpoints, validation, error mapping, cache invalidation
   - Contract tests with Core
4. Frontend Admin (4-8 days)
   - Product list, create/edit forms, stock controls, promotions UI, audit view
   - E2E tests
5. Verification & CI (2-4 days)
   - Add CI jobs for contract tests and E2E
   - Run applicable functional and security verification locally

## Owners
- Core: `bgg-shop-core` team (models, migrations, business rules)
- BFF: `bgg-shop-bff` team (API façade, validation, cache)
- Frontend: `bgg-shop-frontend` team (admin UI, UX)

## Deliverables per Phase
- API contract (OpenAPI or JSON schemas)
- DB migrations + migration runbook
- Unit/integration tests for business rules
- Admin endpoints + contract tests
- Admin UI + E2E tests
- CI pipeline updates

## Risks & Mitigations
- Concurrency (coupon redemptions, stock): mitigate with DB-level atomic counters and integration tests.
- Cache inconsistency: implement and test the approved event/cache behavior.
- Image references: verify one `.webp` image per product using a URL or filename.

## Acceptance Criteria
- All in-scope component acceptance criteria are supported by local focused
  contract/unit/integration checks and the final isolated admin browser run.
- No CI, deployment or remote validation is claimed; local-only validation
  matches the project constraint.

## Timeline (rough)
Total ~3–5 weeks depending on parallel work and reviews.

## Next Steps
- Spec 007 implementation and local acceptance are closed for the 17 tracked
  tasks; see `specs/007-manage-catalog-inventory/tasks.md` and
  `odd/tasks/007-closeout.md`.
- Weekly audit ZIP generation/retention remains explicitly outside this task.

## Contracts-and-data scope and current state (2026-11-02)

The initial approved implementation scope was X-1 (contracts), X-2 (data
constraints/migration) and C-1 (models/persistence); subsequent approved local
work closed the remaining task groups and final browser acceptance. Admin
access requires an active `is_staff` or `is_superuser` user in
both BFF and Core. Product price is positive, name is unique, and quantity is
nonnegative; the unmanaged `Product` model maps existing `product_boardgame`.
Creation requires name, price and quantity; updates are partial and cannot
change BGG ID or quantity; exactly one `.webp` image URL or path/filename is
referenced, with no binary upload. Admin store promotions may be global when
`product_bgg_id` is omitted or null, or target a product; product-specific
promotions permit at most one active offer per product. Creation requires
explicit `active`; partial updates may clear the product link; existing
promotions become inactive during migration. Coupon-linked promotion rows
remain coupon offers and are not global store offers. At checkout, eligible
product-specific store offers beat global offers for that product; absent a
specific offer, the highest eligible global offer wins. Promotions do not
stack. Existing coupon constraints are reused, not duplicated.

The BFF contract defines the authenticated, read-only current-cart coupon
preview and checkout reservation/reconciliation rules. Focused Core/BFF tests
and a local PostgreSQL checkout-path integration test provide implementation
evidence; the final isolated browser run verifies the admin promotion, coupon
and audit flows. These checks are local-only.

Trace: requirements and decisions are in this plan and
`specs/007-manage-catalog-inventory/tasks.md`; contracts are
`bgg-shop-bff/specs/openapi.yaml` and `bgg-shop-core/specs/schema.graphql`;
implementation is in `bgg-shop-core/saleor/promotions/models.py`,
`bgg-shop-core/saleor/graphql/migrations/0017_007_contract_data_dependencies.py`
`bgg-shop-core/saleor/promotions/migrations/0002_007_state_sync.py`, and
`bgg-shop-core/saleor/promotions/migrations/0003_stock_reservation_constraints.py`;
focused tests are
`bgg-shop-core/tests/test_007_catalog_data_contracts.py` and
`bgg-shop-core/tests/test_graphql_credit_postgres.py`.

The checkout selector test
`test_checkout_store_promotions_select_specific_and_highest_global_but_exclude_coupon_rows`
and the full checkout-path test
`test_checkout_total_uses_specific_and_highest_global_store_promotions` in
`bgg-shop-core/tests/test_graphql_credit_postgres.py` each passed as selected
tests on newly created disposable PostgreSQL 15 databases. The latter asserts
the persisted order total and provider total: a product-specific offer beats
a higher global percentage, another product receives the highest global
offer, offers do not stack, and coupon-linked rows are excluded. The whole
PostgreSQL file was not run.

The final isolated browser command
`cd bgg-shop-frontend && E2E_CORE_CONTAINER=bgg-e2e-007-closeout-api npm run test:e2e:opkey`
passed 9 tests on 1 worker, covering admin login/navigation, product
create/readback/edit, stock adjustment, audit filters/pagination, coupon
create/list/edit, product-specific promotion preview/create/list and global
promotion create/list. Output included `Audit verified` and `Synthetic user
removed`. Final independent checks also passed: BFF focused admin suite (108),
Core OpKey suite (148), Core calculations/contracts (30), and focused Frontend
promotion UI tests (14). Root and each service's `git diff --check` passed.
PostgreSQL integration used newly created local disposable PostgreSQL 15
containers, generated ephemeral credentials, loopback-only ports and unique
`credit_test_<uuid>` databases; both test containers were stopped and removed.
Existing E2E Core/DB/Redis services were untouched. No CI, deployment or remote
validation is claimed.

X-1 is complete: OpenAPI 3.2 and Core SDL validate, and focused contract tests
pass. X-2 and C-1 are complete for the approved contracts-and-data scope. The full
chain through `graphql.0017` and `promotions.0003` passed in temporary
PostgreSQL schemas for both fresh installation and adoption of existing tables.
The new idempotent migration adds and validates the stock-reservation FK/check
when absent while preserving them when already present. Tests confirm
reservation violations are rejected and legacy product, order, promotion,
coupon and reservation data is preserved. Nine focused Core tests passed;
`manage.py check` and `makemigrations --check --dry-run` passed on SQLite
in-memory. The temporary database and role were removed and verified absent.
The active database and unrelated Spec 007 tasks were not modified. Verification
was local-only; no commit was made.
