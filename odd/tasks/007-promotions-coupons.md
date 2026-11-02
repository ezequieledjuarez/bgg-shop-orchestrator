# Spec 007 Promotions and Coupons

## Objective

Implement the approved promotions and coupons slice (C-3, X-3, F-4), without
closing or changing the open stock items C-2 and F-3. Defer browser E2E tests
until the requested implementation work across Spec 007 is ready.

## Problem and rationale

Promotion and coupon persistence exists, but approved discount calculation,
coupon preview and reservation/reconciliation behavior are not fully integrated
or verified. The current promotion UI and BFF coupon route also diverge from
the approved contracts.

## Authorized scope and constraints

- Align the existing Core GraphQL and BFF OpenAPI contracts before changing
  corresponding runtime behavior.
- Treat the 2026-11-02 decisions in the Spec 007 plan as authoritative where
  older contract text conflicts: retain decimal precision; round each
  competing savings total upward once to whole pesos; ties favor the store
  promotion. Preserve coupon maximum-discount rejection and validity rules.
- Implement coupon preview against the authenticated user's current cart; it
  must not reserve or consume a use. Checkout reservation/reconciliation must
  follow the approved atomic and uncertain-outcome rules.
- Align promotion administration with product association, explicit `active`
  on create, partial updates, and the 0–50% discount limit.
- Coupon administration is not yet exposed by the BFF/Core contracts. On
  2026-11-02 the user chose to store a whole-purchase coupon's percentage in an
  associated promotion record, rather than adding a dedicated coupon percentage
  field. That associated promotion is a coupon discount record, not a
  product-level promotion.
- The user approved the P-4 contract baseline: `GET`/`POST
  /api/v1/admin/coupons` and `PATCH /api/v1/admin/coupons/{coupon_id}`; fields
  are `code`, `discount_percent`, `remaining`, `active`, `starts_at`, and
  `ends_at`; IDs are numeric, code is immutable, response percentage is
  flattened, physical deletion is excluded in favor of deactivation, and
  create/update audit writes are atomic. Audit history reads remain in C-5.
- F-4 also requires a product-level promotion price preview, which remains
  separate from the current-cart coupon preview.
- The user approved the C-5/F-5 audit-read baseline on 2026-11-02:
  `GET /api/v1/admin/audit` with optional filters by entity type/ID, actor,
  action, and UTC date range; opaque cursor pagination ordered by
  `created_at DESC, id DESC`; default `limit=50`, maximum 100; response fields
  include audit ID, actor ID, action, entity type/ID, timestamp, and before/after
  changes; redact credentials, tokens, passwords, and payment data before
  returning records.
- The user approved the C-4/B-3 event/cache architecture on 2026-11-02:
  transactional Core outbox, authenticated HTTP delivery to BFF with retries
  and idempotent processing, plus BFF TTL caching invalidated by product,
  stock, and promotion events.
- P-8 implementation baseline: use a versioned minimal envelope
  (`event_id`, `event_type`, `occurred_at`, `aggregate_type`, `aggregate_id`);
  event types are `product.changed`, `stock.changed`, and `promotion.changed`.
  Sign the exact HTTP request body with HMAC-SHA256 using a configured shared
  secret and constant-time verification. Store outbox rows in the mutation
  transaction. Retry transient delivery failures indefinitely with exponential
  backoff capped at 5 minutes; mark delivered only on a successful BFF response.
  BFF invalidation is duplicate-safe. Cache public catalog list/detail
  responses in Redis for a configurable TTL defaulting to 60 seconds; event
  processing invalidates them by advancing the catalog cache generation.
- Add focused Core, BFF, and Frontend checks. Do not run browser E2E yet.
- Leave stock C-2/F-3 and all unrelated Spec 007 tasks unchanged.
- Preserve existing dirty worktree changes. Do not alter unrelated files,
  active databases, or contact remote services.

## Acceptance criteria

- Core and BFF contracts agree on routes, payloads, response/error shapes, and
  the approved savings rounding and coupon-preview rules.
- Promotions calculate and apply according to the accepted discount comparison
  rules; invalid coupons are rejected with the accepted reasons.
- Coupon reservation is atomic under concurrent checkout attempts; confirmed
  failure releases it, uncertain outcomes retain it for reconciliation, and
  duplicate/retried operations do not consume twice.
- BFF validates and maps the Core behavior without exposing upstream details.
- Admin promotion and coupon UI follow the approved rules and show loading,
  success, empty, and error states accessibly.
- Admins can create and edit coupon codes with their whole-purchase discount,
  remaining uses, active state, and validity dates using a contract-backed
  endpoint; coupon changes follow the approved audit requirements.
- Audit reads require admin access, validate the approved filters and cursor
  pagination, and return redacted change records only.
- Focused local Core/BFF/Frontend checks pass. Browser E2E remains explicitly
  pending.

## Tasks and route

- [x] P-1 — Align and validate Core GraphQL and BFF OpenAPI contracts.
  - Route: delegated writer. Trigger: public contracts span Core and BFF.
  - Risk: high; Core SDL and BFF OpenAPI contract checks pass locally.
- [x] P-2 — Implement promotion/coupon calculations, eligibility, and safe
  reservation/reconciliation with focused Core and BFF tests.
  - Route: delegated writer. Trigger: multiple services and transactional
    behavior.
  - Risk: high; local calculation/contract and disposable PostgreSQL
    concurrency/reconciliation tests passed.
  - Status: complete for the approved local non-E2E scope. Core and BFF coupon
    calculations, authenticated current-cart preview, X-Op-Key checkout
    forwarding, reservation/release states, and
    retry/reconciliation logic are implemented. The coupon preview response
    fields `coupon_code`, `discount_amount`, and `new_total` are required and
    non-null in both contracts and runtime; `reason` remains nullable. A
    successful preview always returns the exact submitted code; an unknown
    coupon returns 404 instead of a preview object.
    - Duplicate checkout requests received before the original payment URL is
      available return `PENDING_PAYMENT`/409 rather than a success with a null URL.
  - Evidence: concurrent coupon checkout/reservation and uncertain outcome
    reconciliation passed the focused disposable-PostgreSQL selector below.
- [x] P-3 — Implement promotion and coupon administration/preview UI with
  focused Frontend tests and generated API types as applicable.
  - Route: delegated writer. Trigger: multiple non-trivial Frontend files.
  - Risk: medium; finalized OpenAPI types regenerated; focused component tests,
    TypeScript build, and targeted lint pass.
- [ ] P-4 — Define and implement the admin coupon management contract and
  create/edit flow on top of an associated product-less promotion record, and
  add product-level promotion price preview.
  - Route: delegated direct. Trigger: public contract and coordinated Core,
    BFF, and Frontend behavior across multiple non-trivial files.
  - Risk: high; contract-first validation, transactional/audit tests, focused
    component tests and build.
  - Status: partial. The approved GET/POST collection and PATCH item contract,
    backend create/update/audit behavior, frontend coupon list/create/edit,
    immutable code handling, and product-level price preview are implemented.
    Backend and focused Frontend checks passed; generated API types were
    regenerated from the finalized BFF OpenAPI.
  - Pending: browser E2E remains deferred until the Spec 007 implementation is
    ready; this does not close F-4 or mark P-4 complete.
- [ ] P-5 — Define and implement audit-read contracts, Core query, BFF route,
  error sanitization, and verify audit-write coverage across product, stock,
  promotion, and coupon changes.
  - Route: delegated direct. Trigger: contract and behavior span Core and BFF,
    plus existing transactional audit flows.
  - Risk: high; contract-first tests, disposable PostgreSQL audit checks, BFF
    negative disclosure checks, and diff review.
- [ ] P-6 — Add the accessible Frontend audit history view using generated
  contract types, filters, stable cursor pagination, redacted records, and
  loading/empty/error states.
  - Route: delegated direct. Trigger: multi-file React route, component, API
    integration, and tests.
  - Risk: medium; focused component tests and build. No browser E2E.
  - Status: partial. The admin route and typed audit history view, filter
    validation, redacted-value display, and forward-only opaque cursor
    pagination are implemented. The focused audit/admin component tests passed
    (25 tests), as did the TypeScript production build and targeted Oxlint.
    E2E integration remains deferred, so P-6 stays open.
- [ ] P-7 — Complete catalog listing/search/pagination and product
  create/edit/image-reference validation (F-1/F-2) using existing contracts.
  - Route: delegated direct. Trigger: multi-file React behavior and tests.
  - Risk: medium; focused component tests and build. No browser E2E.
  - Status: partial. F-1/F-2 use the approved admin product query and
    pagination response, with contract-backed search/filters, create/edit
    navigation, numeric validation, a single `.webp` image reference, partial
    edits without quantity, and inline server field errors. The focused product
    tests, production build, and targeted Oxlint passed. The existing generated
    API types already match the OpenAPI contract; regeneration was not needed.
  - Pending: final browser E2E is deferred until the full Spec 007 work is ready;
    no E2E was run and P-7/F-1/F-2 remain partial.
- [ ] P-8 — Define/validate and implement the approved transactional outbox,
  authenticated retrying Core→BFF delivery, idempotent event processing, and
  TTL cache invalidation for product, stock, and promotion events (C-4/B-3).
  - Status: partial. Core and BFF contract/runtime code and focused tests pass,
    including bounded webhook request handling and store-credit checkout stock
    events; live Core→BFF/Redis integration remains unverified and E2E stays
    deferred.
  - Route: delegated direct. Trigger: public contract and coordinated Core/BFF
    delivery, persistence, retry, and cache behavior.
  - Risk: high; contract-first tests, focused mutation/dispatcher tests, and
    local migration validation.
  - Implementation: BFF contract is `POST /internal/v1/catalog-events` with
    `X-Catalog-Event-Signature: sha256=<hex>` over the exact minimal envelope.
    Event aggregate type follows the event type; product and stock IDs are
    product BGG IDs, and promotion IDs are promotion IDs. Core stores events in
    the mutation transaction and Celery dispatches due rows with capped
    exponential retries. The BFF caches only public product list/detail data in
    Redis and invalidates by advancing a generation key. Both services read
    `CATALOG_EVENTS_HMAC_SECRET`, falling back to the existing shared
    `OPKEY_INTERNAL_SECRET`; the secret remains required.
  - Checks: Core `pytest -q tests/test_catalog_events.py` — 14 passed;
    BFF `PYTHONPATH=. pytest -q tests/test_catalog_events.py tests/test_catalog_cache.py`
    — 17 passed; `openapi-spec-validator specs/openapi.yaml` — passed;
    root/Core/BFF `git diff --check` — clean.
  - Pending: live Core→BFF/Redis integration and browser E2E remain deferred.
    C-2 and F-3 are unchanged.

## Verification commands

- Core: `pytest -q tests/test_007_catalog_data_contracts.py` plus focused
  promotion/coupon tests added or identified during implementation.
- BFF: `PYTHONPATH=. pytest -q tests/test_admin_promotions.py tests/test_admin_coupons.py`
  plus relevant contract tests.
- Frontend: `npm run test -- --run src/admin/audit/AuditPanel.test.tsx
  src/admin/coupons/CouponsPanel.test.tsx src/admin/coupons/CouponForm.test.tsx`;
  run the project build if frontend files or generated types change.
- Run `git diff --check`.
- Do not run Playwright or other browser E2E tests in this slice.
- Do not commit or switch branches; preserve all pre-existing worktree changes.

## Local reconciliation runbook

- If checkout's provider result is uncertain, keep its coupon use reserved.
  Reconcile the order against the provider before deciding whether the attempt
  failed; a timeout alone is not evidence to release the use.
- A retry with the same exact operation key returns the existing attempt when
  its payment URL is available, or `PENDING_PAYMENT` while it is being
  reconciled; it must not reserve another coupon use.
- A confirmed rejection or cancellation releases the reservation. A confirmed
  approval follows the existing payment confirmation and released-use recovery
  rules.
- If the provider outcome remains unresolved, leave the reservation in review
  and route the case to manual review; do not make the use available to another
  checkout.
- Validation is local-only. This work requires disposable local PostgreSQL
  evidence, not a CI job or remote environment.

## Progress and evidence

- 2026-11-02: Read-only mapping found C-3 and X-3 partial and F-4 unverified.
  The plan contains the approved discount and coupon decisions; the current
  OpenAPI rounding text conflicts with the newer plan decision, so P-1 must
  align the contract before runtime implementation. Existing promotion UI and
  BFF coupon route also diverge from the approved contracts.
- 2026-11-02: P-1 contract text now matches decimal-preserving, per-alternative
  upward whole-peso rounding and store-promotion tie preference. Focused Core
  SDL/OpenAPI and BFF OpenAPI tests pass. Added a unit-tested Core savings
  selector, but P-2 remains incomplete: no preview resolver, checkout
  reservation/release, BFF adapter, or PostgreSQL verification was completed.
  Focused BFF admin tests currently fail because they request `/admin/...`
  while the app registers `/api/v1/admin/...`; those routes predate this change.
- User-authorized edit-surface expansions added
  `bgg-shop-core/saleor/graphql/orders.py` and BFF
  `bgg-shop-bff/app.py` plus `bgg-shop-bff/src/services.py`; no other paths
  were added beyond the originally approved surfaces.
- The project skill registry `.atl/skill-registry.md` is absent. Engram
  recovery mirror is unavailable in this session and remains pending.
- P-2 follow-up: contract-first nullability checks initially exposed that
  OpenAPI and Core SDL marked preview values nullable although the resolver and
  BFF always return them for successful previews. The contracts and Graphene
  runtime now require `couponCode`, `discountAmount`, and `newTotal`; only
  `reason` is nullable. Focused Core checks passed:
  `cd bgg-shop-core && PYTHONPATH=. pytest -q tests/test_007_catalog_data_contracts.py tests/test_coupon_calculations.py`
  (22 passed). Focused BFF checks passed:
  `cd bgg-shop-bff && PYTHONPATH=. pytest -q tests/test_admin_promotions.py tests/test_admin_coupons.py tests/test_coupon_contract_rules.py`
  (45 passed). Core and BFF `git diff --check` plus focused Python syntax checks
  passed. The runtime-schema test was observed failing before the Graphene
  fields were made non-null, then passed in the final Core run. The duplicate
  replay pending-state test was also observed failing before the helper was
  implemented, then passed. PostgreSQL reservation concurrency/reconciliation
  tests remain unrun; no active database was used.
- 2026-11-02 review follow-up: the independent review identified that an
  approved payment arriving after a rejected attempt could consume a released
  coupon without reacquiring its use. `confirm_payment` now atomically attempts
  to re-reserve a released use before applying payment/stock effects; if the
  coupon is no longer eligible or has no remaining uses, it returns
  `PAYMENT_REQUIRES_REVIEW` without marking the order paid or changing stock.
  Follow-up review found the review return did not persist a durable review row.
  It now inserts `(order_id, payment_id)` into `credit_payment_review` with
  `ON CONFLICT DO NOTHING` before returning. The regression asserts the review
  row, unchanged `mp_payment_id`/`payment_status`/`paid_at` on the failure path,
  and persisted payment ID plus `paid_at` on success. Exhausted, inactive, and
  expired coupon cases are covered.
  Regression test-first evidence: on isolated PostgreSQL,
  `PYTHONPATH=. pytest -q tests/test_graphql_credit_postgres.py::test_late_approved_payment_reacquires_released_coupon_use`
  failed before the fix (both parameter cases) and passed after it (2 passed).
  Final focused command:
  `PYTHONPATH=. pytest -q tests/test_graphql_credit_postgres.py::test_late_approved_payment_reacquires_released_coupon_use tests/test_graphql_credit_postgres.py::test_repeated_simulated_confirmation_preserves_order_effects`
  passed before this review follow-up (6 passed). After the durable review-row
  fix and expanded assertions, the same exact command passed again (8 passed):
  `PYTHONPATH=. pytest -q tests/test_graphql_credit_postgres.py::test_late_approved_payment_reacquires_released_coupon_use tests/test_graphql_credit_postgres.py::test_repeated_simulated_confirmation_preserves_order_effects`.
  The test fixture now includes the coupon tables required by
  confirmation code. Each test run used an ephemeral local Postgres 15
  container with loopback-only random port and no volume; cleanup was observed
  (`podman stop` and `podman rm` succeeded; `podman container exists` returned
  1, absent).
  Earlier focused coupon migration/query selectors
  (`test_migration_chain_preserves_existing_promotions_and_coupons`,
  `test_coupon_constraint_migration_preserves_invalid_legacy_data`,
  `test_coupon_query_returns_promotion_activation`,
  `test_available_coupons_migration_and_public_query`,
  `test_coupon_constraints_reject_negative_uses_and_inverted_dates`) produced
  4 passed and 1 failure: the invalid-legacy-data test raised
  `DuplicateTable` because its migration executor creates `promotion` after
  the test already created it. That run's disposable container was also
  removed. Concurrent checkout races remain untested.
- 2026-11-02: P-3 Frontend evidence: after backend confirmation that the
  OpenAPI preview response requires non-null `coupon_code`, `discount_amount`,
  and `new_total` with nullable `reason`, regenerated types using
  `cd bgg-shop-frontend && npm run generate:types`. Focused tests passed:
  `npm run test -- --run src/admin/promotions/PromotionForm.test.tsx src/admin/promotions/PromotionsPanel.test.tsx src/App.cart.test.tsx`
  (3 files, 19 tests). `npm run build` passed, targeted Oxlint passed with
  zero warnings/errors, and `git -C bgg-shop-frontend diff --check` passed.
  Coupon UI submits the exact code only for the authenticated current cart;
  no reserve/consume behavior is invoked. Browser E2E remains deferred.
- 2026-11-02: F-4 acceptance review found that promotion administration and
  current-cart coupon preview are implemented, but coupon create/edit is
  absent from both Core and BFF contracts and the admin UI. The existing model
  stores the coupon discount through `Coupon.promotion_id`; after clarification,
  the user chose to reuse an associated product-less promotion record rather
  than add a dedicated coupon percentage column. P-4 will define the service
  contract before implementing this behavior. The root Spec 007 tracker now
  records F-4 as partial; no E2E was run.
- 2026-11-02: The user approved the admin coupon contract baseline:
  `GET`/`POST /api/v1/admin/coupons`, `PATCH
  /api/v1/admin/coupons/{coupon_id}`, numeric IDs, immutable codes, flattened
  discount percentage, no physical delete, and atomic create/update audit
  writes. P-4 will validate the Core/BFF contract before runtime changes and
  include product-level promotion price preview.
- 2026-11-02: Implemented the P-4 Core/BFF coupon-administration backend
  portion. Core SDL and BFF OpenAPI were updated and validated before runtime
  changes (Core contract validator: 10 passed; BFF coupon contract validator:
  8 passed). The API exposes the approved GET/POST collection and PATCH item
  routes, numeric IDs, flattened discounts, immutable codes, and no delete.
  Core writes a product-less Promotion plus Coupon and actor/action/target/
  previous/new audit values in one transaction; a coupon audit failure rolls
  back both records. Updates atomically write their audit entry as well.
  Verification after implementation: Core contract/calculation tests 24
  passed; focused disposable-loopback-PostgreSQL coupon-admin tests 4 passed;
  BFF admin-coupon and contract tests 21 passed; Python syntax and Core/BFF/root
  `git diff --check` passed. The preloaded local PostgreSQL container used a
  unique temporary role/database, random loopback port, and no volume; cleanup
  was verified. No schema migration was needed. C-2/F-3 and browser E2E remain
  unchanged/deferred; this does not complete P-4.
- 2026-11-02: Implemented the P-4 Frontend coupon list/create/edit flow against
  the finalized generated contract. Codes remain exact-case and immutable on
  edit; update requests contain only changed fields, and deactivation uses
  `active=false`. The product promotion form now previews an estimated price
  from the selected product's current API price without changing the existing
  current-cart coupon preview. Focused coupon/promotion/cart tests, the
  production build, targeted lint, and diff checks passed. Browser E2E remains
  deferred; P-4 and F-4 remain partial.
- 2026-11-02: The user approved the audit-read contract details for C-5/F-5:
  filters by entity type/ID, actor, action, and UTC date range; opaque cursor
  pagination ordered by `created_at DESC, id DESC`, default 50/max 100; return
  audit ID, actor ID, action, target type/ID, timestamp, and before/after
  changes; redact credentials, tokens, passwords, and payment data. P-5/P-6
  will implement this baseline; no E2E has been run.
- 2026-11-02: The user approved the event/cache architecture for C-4/B-3:
  transactional outbox in Core, authenticated HTTP delivery to BFF with
  retries and idempotent processing, and BFF TTL cache invalidation on product,
  stock, and promotion events. P-8 will define exact payload/security/TTL
  contracts before runtime behavior.
- 2026-11-02: P-8 implementation details resolved from the approved
  architecture: versioned envelope with stable UUID event ID and only event
  type/time/aggregate identity; HMAC-SHA256 of exact request body with
  constant-time verification; transactional outbox; indefinite transient retry
  with exponential delay capped at five minutes; duplicate-safe BFF invalidation
  through a Redis generation key; catalog list/detail TTL configurable with a
  60-second default. This is the contract baseline to validate before code.

- P-5 backend (partial; P-5 stays unchecked pending P-6 Frontend and deferred E2E):
  - Route: delegated direct; risk: high. Contract first: OpenAPI 3.2
    `GET /api/v1/admin/audit` (filters, signed opaque cursor, limit 1-100
    default 50, `created_at DESC, id DESC`, 400/401/403/502, `no-store`) and Core
    SDL `adminAuditLogs`; redaction of credential/token/password/payment keys.
  - Core: audit read resolver (parameterized SQL, signed cursor); atomic
    single-statement audit writes added for product and promotion create/update;
    stock and coupon audit pre-existing. BFF: proxy/service/controller/route;
    promotion/coupon admin errors now use static public messages.
  - Checks: Core `test_admin_audit_postgres.py` 13 passed on a disposable
    loopback no-volume postgres:15-alpine (container removed, verified);
    Core `test_007_catalog_data_contracts.py tests/test_graphql_products.py`
    61 passed, 1 failed (`test_generated_schema_matches_reference_sdl`,
    pre-existing description-wrapping diffs, failed before P-5);
    BFF `test_admin_error_mapping/audit/promotions/coupons` 98 passed;
    `test_admin_validation` 109 passed; OpenAPI validates as 3.2.0;
    py_compile and `git diff --check` clean in core, bff and root.
  - Pending: E2E (deferred), no index on `audit_log(created_at, id)` (no
    migration authorized), pre-existing reference-SDL test failure, Frontend P-6.
- P-6 Frontend (partial; F-5 remains open until the deferred E2E pass):
  `/admin/audit` is integrated with generated types. The screen validates
  entity/actor/action/date filters, displays only redacted API values, and
  follows the contract's forward-only opaque cursor. Focused audit/admin tests
  passed (25), production build passed, and targeted Oxlint reported zero
  warnings/errors. A parent rerun covering audit, coupon, promotion, and cart
  UI passed 45 tests across six files. No browser E2E was run.

- 2026-11-02: P-7 F-1/F-2 Frontend work is partial. Focused product tests passed
  (15 tests across two files), `npm run build` passed, and targeted Oxlint
  passed with zero warnings/errors. `npm run lint` passed with 51 workspace
  warnings and no errors. The product admin list uses the contract's
  `page`, `page_size`, `search`, year/player/category/price filters and returned
  pagination metadata. Product create/edit validates the generated request
  fields, sends one `.webp` URL or `image_file_name`, preserves partial updates,
  omits quantity on edit, and displays contract-shaped field errors.
  `bff-api.d.ts` already reflected the checked OpenAPI; type generation was not
  needed. Browser E2E was not run and remains deferred until all Spec 007 work
  is complete; C-2/F-3 and unrelated task statuses remain unchanged.

## X-3/C-3 concurrency and reconciliation follow-up (2026-11-02)

Added disposable-PostgreSQL regressions for a last coupon use racing across
two users, concurrent identical `X-Op-Key` replay consuming only once, and an
uncertain initial checkout result remaining reserved through a pending provider
status until confirmed rejection or cancellation. The same-key concurrency
regression initially reproduced a PostgreSQL deadlock: the replay lookup locked
the reservation and order rows while preference completion locks the order
before updating the reservation. Removed the unnecessary replay-row locks;
the existing operation-key advisory lock still guards initial reservation,
and replay remains a read-only check.

Observed deterministic check:
`cd bgg-shop-core && python -m pytest -q tests/test_coupon_calculations.py`
— 13 passed; one existing Django `USE_TZ` deprecation warning.

Observed integration check, using a cached `postgres:15-alpine` image with
`--pull=never`, a unique matching user/database, random loopback port, and
no-volume temporary data:
`cd bgg-shop-core && CREDIT_TEST_POSTGRES_DSN=<unique loopback DSN> PYTHONPATH=. python -m pytest -q tests/test_graphql_credit_postgres.py -k 'parallel_coupon_checkouts_reserve_the_last_use_once or parallel_coupon_checkout_same_key_replays_without_second_reservation or uncertain_coupon_payment_stays_reserved_until_confirmed_failure or late_approved_payment_reacquires_released_coupon_use or ambiguous_initial_preference_requires_reconciliation or initial_preference_blocks_concurrent_retry'`
— 10 passed, 133 deselected; one existing Django `USE_TZ` deprecation warning.
The disposable container was verified absent after the run. CI evidence is
excluded because deployment and validation are local-only.

## Next step

X-3/C-3 are complete on the observed local evidence. No CI job or remote
environment is required. P-8 implementation and focused checks are complete;
preserve the pending local Core→BFF/Redis
integration proof. Use the closure batches in
`specs/007-manage-catalog-inventory/tasks.md`: stock recovery (C-2/F-3),
promotions/coupons (X-3/C-3/F-4), events/cache (C-4/B-3), administration/audit
(C-5/B-1/B-2/F-5), and catalog UI (F-1/F-2). Then run B-4 integration and the
deferred browser E2E locally. Keep all tasks partial until their full acceptance
evidence is observed; do not change C-2/F-3 status based on implementation
alone.
