# Spec 007 Closeout

## Objective

Close all 17 tracked Spec 007 tasks after the verified local integration,
recording the final isolated browser and PostgreSQL evidence. Validation is
local-only; no CI, deployment or remote result is part of this closeout.

## Constraints

- Work locally only; no remote CI/deployment or production/active database.
- Local verification is complete; this record must not imply CI, deployment or
  other non-local validation.
- Preserve the existing `fix/spec-follow-ups` branch and dirty worktree. Do not
  stage, commit, switch branches, or revert unrelated changes.
- Preserve unrelated dirty and untracked changes; make no source or test edits.
- Treat the permanent stock movement UUID binding requirement as requiring
  movement identity rows to remain available for replay/conflict checks; do not
  introduce automatic purging.
- The audit cursor orders by `(created_at DESC, id DESC)`. Add a matching
  database index if current model/migrations confirm it is absent; verify the
  migration on a disposable local PostgreSQL database.

## Browser-flow integration gaps addressed before final E2E

- The OpKey-only BFF admin path forwards the validated `op_key` through audit
  and coupon controller/service/proxy calls so Core receives delegated admin
  identity.
- Core's delegated-operation allowlist covers only exact supported audit and
  coupon routes/GraphQL roots while retaining method, path, root-field,
  argument-binding, and fail-closed checks. The exact product detail binding
  (`GET /api/v1/admin/products/{bggId}` to `productByBggId(bggId)`) is also
  restored for the BFF's staff-protected F-2 edit/readback flow; mismatched
  product IDs, methods, routes, or GraphQL operations remain denied. This
  supersedes the earlier test expectation that denied product lookup.
- The promotions DTO accepts and validates optional nullable
  `product_bgg_id` and preserves its camel-case proxy mapping. Admin store
  promotions now support global offers, with product-specific precedence and
  highest-global selection; coupon-linked promotion rows remain coupon-only.
- The final local E2E and focused PostgreSQL checkout tests are recorded below;
  work unit 7 and F-1 through F-5 are closed in the current task ledger.

## Newly approved promotion behavior (2026-11-02)

- Admin promotions may omit `product_bgg_id` or set it to `null`; update may
  explicitly clear the product link. Core GraphQL `productBggId` remains
  nullable and the BFF OpenAPI request/response field shapes do not change.
- A qualifying active product-specific store promotion takes precedence over
  every global offer for that cart product, even when a global percentage is
  higher. Otherwise, the highest eligible global percentage applies. Store
  promotions never stack; existing coupon comparison and rounding are
  unchanged.
- Coupon-linked promotion rows (`coupon.promotion_id`) are coupon discounts,
  not store promotions. Exclude them from store-promotion selection and the
  admin promotion list; continue exposing them through coupon routes.
- Keep the product-specific active uniqueness rule. Do not add a migration or
  schema field unless code inspection proves one necessary.
- The plan/tasks wording and OpenAPI/Core SDL descriptions were reconciled
  before behavior changes. Test-first regressions cover nullable admin
  mutations, listing, checkout precedence, global selection and coupon
  exclusion. At this earlier pre-final-E2E snapshot, task 7 and F-1..F-5 were
  still pending; the final local browser acceptance below supersedes that
  status.

## Work units

1. [x] **Stock recovery (C-2):** late replay and permanent movement identity
   retention verified; no runtime fix was needed.
2. [x] **Coupon concurrency (X-3/C-3):** add/complete concurrent reservation
   and reconciliation evidence on disposable PostgreSQL; document local
   operational mitigation and failure semantics.
3. [x] **Events/cache (C-4/B-3):** run a real local outbox→signed BFF→Redis
   invalidation and retry/failure flow; fix only demonstrated integration gaps.
4. [x] **Admin/audit (C-5/B-1/B-2):** audit cursor index migration and audit
   coverage verified; BFF admin route, authorization, validation and error
   suite passed.
5. [x] **Cross-service integration (B-4):** local contract/failure-path suites
   passed, and Core GraphQL SDL/runtime semantic drift was reconciled. The
   focused Core product and contract suites passed 67 tests.
6. [x] **Frontend implementation review (F-1/F-2/F-4/F-5):** focused tests,
   production build and lint passed. At that earlier snapshot, browser E2E
   remained for work unit 7; its final result is recorded below.
7. [x] **Final local browser integration (F-1–F-5):** repair stale E2E setup
   and selectors, cover product create/edit, stock, promotion/coupon and audit
   flows; isolated browser acceptance passed, so frontend statuses are closed.
   Route: delegated test writer; trigger: multiple non-trivial E2E specs.
   Risk was high; the final focused Playwright command was independently
   verified against the isolated local stack.
   Observed E2E (2026-11-02, disposable stack, 1 worker): 2 passed, 6 failed;
   login and `admin.spec.ts` passed. Missing operation flows: product
   create/edit/stock readback (`GET /api/v1/admin/products/{bggId}` not
   delegated by Core), coupon update (`PATCH /api/v1/admin/coupons/{id}` not
   delegated, sanitized 502), promotion create (400, `X-Op-Key` not forwarded
   by BFF controller/service/proxy for create/update), and the global
   (productless) promotion UI path. Correction applied: exact Core
   `productByBggId` and `updateAdminCoupon` bindings, BFF OpKey forwarding for
   promotion create/update, promotion list `product_bgg_id`, global option in
   the promotion form, plus focused unit tests and one new browser test.
   Historical initial failure/setup record; superseded by the final passing
   run below. Engram mirror: pending (Engram unavailable), not synchronized.

## Status and evidence

- The dated entries below are historical verification snapshots. Their earlier
  pending/unverified conclusions are superseded by the final local evidence in
  the last section; the exact product detail route rationale remains current.
- Feature document created before implementation work.
- Initial mapping found concrete non-E2E gaps in C-2, X-3/C-3, C-4/B-3,
  C-5/B-1, and B-4. F-1/F-2/F-4/F-5 were then implementation-complete pending
  E2E; that pre-final snapshot is superseded by the completed status below.
- Browser-flow integration repair (2026-11-02): added regression coverage and
  repaired validated OpKey forwarding from the BFF through audit and coupon
  services/proxies, exact Core delegated route/root allowlisting for audit and
  coupons, and optional nullable promotion `product_bgg_id` validation plus
  Core camel-case mapping. New BFF regressions were observed failing before
  implementation, then passed. The required BFF command passed (103 tests).
  At that initial snapshot, the required Core file had 136 passing tests and
  one `productByBggId` delegated-operation case failed; the new audit/coupon
  allowlist selector passed all 8 cases. That regression was attributed and
  corrected in the later promotion implementation verification below. At that
  initial snapshot, work unit 7 remained pending, no browser suite had run and
  no frontend acceptance status had changed.
- C-2 required no runtime change: the status table keys movement UUIDs without
  expiry, details reference status with `ON DELETE RESTRICT`, and no
  application-managed identity purge was found. Added a PostgreSQL regression
  for retrying the same UUID/payload after confirmed `NO_STOCK`, replenishment,
  an intervening movement, and a reopened connection; existing replay coverage
  also confirms the applied result survives later stock changes and reconnect.
- Focused Core check passed on a disposable local PostgreSQL 15 container:
  `PYTHONPATH=. pytest -q tests/test_graphql_credit_postgres.py -k 'stock_movement'`
  with `CREDIT_TEST_POSTGRES_DSN` set to the unique loopback-only test database
  (22 passed, 117 deselected; independently repeated by the parent). The test
  fixture now creates the event-outbox
  table required by the stock mutation's existing transactional event write.
  Container, test database, and role were removed with the container; absence
  of the container was verified. No E2E was run.
- Coupon concurrency/reconciliation: the same-key concurrent replay regression
  reproduced a PostgreSQL deadlock when replay locked reservation/order rows
  against preference completion's order-then-reservation lock order. Removing
  those unnecessary replay locks fixed the issue without changing the approved
  idempotency policy. Added coverage for competing last-use reservations,
  same-key replay, uncertain outcomes retained through pending status, and
  confirmed rejection/cancellation release. Deterministic calculations passed:
  `cd bgg-shop-core && python -m pytest -q tests/test_coupon_calculations.py`
  (13 passed; one existing `USE_TZ` deprecation warning). Final disposable
  PostgreSQL 15 selector:
  `cd bgg-shop-core && CREDIT_TEST_POSTGRES_DSN=<unique loopback DSN> PYTHONPATH=. python -m pytest -q tests/test_graphql_credit_postgres.py -k 'parallel_coupon_checkouts_reserve_the_last_use_once or parallel_coupon_checkout_same_key_replays_without_second_reservation or uncertain_coupon_payment_stays_reserved_until_confirmed_failure or late_approved_payment_reacquires_released_coupon_use or ambiguous_initial_preference_requires_reconciliation or initial_preference_blocks_concurrent_retry'`
  (10 passed, 133 deselected; one existing `USE_TZ` deprecation warning).
  The unique loopback PostgreSQL 15 container used no volume and was verified
  absent after the run. X-3/C-3 are complete. The local mitigation/runbook is
  recorded in `odd/tasks/007-promotions-coupons.md`; CI evidence is excluded
  because this project is deployed and validated locally only.
- Independent parent rerun of the coupon selector on a second disposable,
  loopback-only PostgreSQL 15 container also passed (10 passed, 133 deselected).
  That container was removed and verified absent; an unrelated pre-existing
  exited container was not touched.
- Events/cache integration (2026-11-02): the Core `record_catalog_event`
  helper and `dispatch_due_catalog_events` delivered real HTTP requests to a
  running BFF route bound to `127.0.0.1:18081`; the BFF validated Core HMAC
  signatures and invalidated a real Redis generation on a loopback-only
  disposable Redis container. The cached generation-0 response became
  unreachable, generation advanced to 3 across product, stock and promotion
  events, and the next cache read loaded fresh data. The product event first
  received BFF 503 when its Redis client targeted an unused loopback port:
  the outbox stayed pending with one attempt and no delivery timestamp. After
  restoring the real Redis client, the dispatcher retried the same event UUID
  and received 204; stock and promotion events also received 204. Observed
  HTTP statuses were `503, 204, 204, 204`; the failure response contained only
  the generic error and no connection detail.
  Setup command:
  `podman run -d --name spec007-c4b3-redis-20261102-live --pull=never --read-only --tmpfs /data:rw,noexec,nosuid,size=32m -p 127.0.0.1:16379:6379 docker.io/library/redis:7-alpine redis-server --save '' --appendonly no --dir /data`
  The local image was already present; the Redis container had no data-volume
  mounts and was bound only to loopback. The in-memory Core harness was invoked
  as `cd bgg-shop-core && DATABASE_URL=sqlite:///:memory: python -` with
  one-off inline Python; no reusable test/runtime code was added. Django
  timezone settings were overridden to UTC and raw UUID text was normalized
  to SQLite's UUIDField representation to match PostgreSQL UUID storage. This
  is an HTTP/Redis integration proof, not a PostgreSQL persistence proof.
  The BFF server thread stopped and joined; the Redis container was removed
  and verified absent, and both loopback ports were free.
  Runtime Core source review found catalog event emitters on product create
  and update (`saleor/graphql/api.py:1782,1903`), stock adjustment
  (`api.py:2052`), payment checkout (`saleor/graphql/orders.py:1097`),
  store-credit checkout (`saleor/graphql/credit.py:230`), and promotion
  create/update (`api.py:2102,2162`). The coupon-admin promotion rows are
  explicitly product-less and do not change catalog product pricing.
- Administration/audit checks (2026-11-02): added and independently verified
  `graphql.0018_audit_log_cursor_index`, creating the descending composite
  `(created_at, id)` index used by audit cursor pagination. The disposable
  PostgreSQL suite passed 14 tests, including migration apply/reverse/reapply
  and stable cursor ordering. BFF admin/auth/error suites passed 262 tests.
  Coupon upstream failures remain static and sanitized; no controller change
  was necessary. At that snapshot C-5/B-1/B-2 were complete and F-5 browser
  E2E was still deferred; the final browser result is recorded below.
- Frontend focused verification (2026-11-02; pre-final-browser snapshot):
  8 files / 59 tests passed;
  `npm run build` passed and `npm run lint` passed with 51 existing warnings
  and no errors. F-1/F-2/F-3/F-4/F-5 were implementation-complete; integrated
  browser E2E was then deferred.
- Cross-service contract verification (2026-11-02): BFF services/OpenAPI,
  order, credit and product selector had 154 passed and one checkout proxy
  expectation failed because the contract-aligned optional `checkoutKey` and
  `couponCode` variables were absent from the test expectation. The expectation
  was updated; the full BFF `test_orders.py` then passed (48 tests). Core product
  tests exposed three mock failures due to the already-existing outbox write;
  the mocks were updated and the module passed 48 tests with the unrelated
  `test_generated_schema_matches_reference_sdl` deselected. At that point the
  SDL parity test still failed and the subsequent comparison found semantic
  field/input drift. These findings were fixed and verified in the later
  reconciliation below; this initial result is retained only as history.
- Core GraphQL SDL/runtime reconciliation (2026-11-02): the reference SDL
  parity test first failed, and five focused coupon-validity/product-linkage
  tests failed before implementation. Added the missing coupon validity fields
  and product linkage, persisted/validated product-bound promotion mutations,
  kept product-less coupon promotions out of the product promotion listing,
  and aligned Graphene descriptions with the SDL. Final command:
  `cd bgg-shop-core && python -m pytest -q tests/test_graphql_products.py tests/test_007_catalog_data_contracts.py`
  passed (67 tests; one existing Django `USE_TZ` deprecation warning). This
  includes the exact generated-schema/reference-SDL introspection parity test.
  Coupon calculations also passed:
  `cd bgg-shop-core && python -m pytest -q tests/test_coupon_calculations.py`
  (13 tests; one existing Django `USE_TZ` deprecation warning). No browser E2E
  or PostgreSQL integration test was run in this work unit.
  Final focused BFF admin and cross-service suite passed 417 tests across
  admin, OpenAPI contracts, orders, credit and product flows. OpenAPI
  validation and Core/BFF/root `git diff --check` passed. Existing
  `datetime.utcnow()` deprecation warnings remain; there were no test failures.
  B-4 is complete; only the authorized final browser E2E flows for F-1 through
  F-5 remain.
- ODD Engram mirror: unavailable in this runtime; pending.

- Global-promotion implementation verification (2026-11-02): the plan/tasks
  wording and OpenAPI/Core SDL descriptions now record optional nullable
  product links, product-specific-wins precedence, highest-percent global
  selection, no stacking, and coupon-linked row exclusion. Request/response
  shapes remain unchanged. Core create/update accept null product IDs, the
  admin list includes non-coupon global promotions, and checkout selects
  specific offers before the highest eligible global offer. Coupon comparison
  and rounding remain unchanged; no migration or schema field was added.
- Test-first evidence: the newly added focused Core unit/schema tests were
  observed red before behavior changes (8 failures). Final required BFF suites
  passed 55 tests; required Core suites passed 210 tests. The OpenAPI validator
  returned `specs/openapi.yaml: OK`, generated-SDL/reference-SDL parity passed,
  and root/BFF/Core `git diff --check` passed. Existing Django timezone and
  BFF `datetime.utcnow()` deprecation warnings remain.
- At an earlier snapshot, the new PostgreSQL promotion selector test reported
  `1 skipped` because `CREDIT_TEST_POSTGRES_DSN` was not set. Its fixture
  requires a disposable loopback database; the later selected PostgreSQL
  tests recorded below close that earlier checkout evidence gap.
- Historical OpKey regression experiment: the failure was reproduced before
  correction. Temporarily removing the delegated `GET
  /api/v1/admin/products/{bggId}` binding restored the test's intended denial;
  route/root/argument-binding checks passed (20 cases). The accepted route is
  restored as documented above.
- An initial root-directory pytest invocation used service-relative paths and
  found no tests; reruns from the service directories passed. At that earlier
  point task 7 and F-1..F-5 remained open for browser acceptance; final
  acceptance is recorded below. No branch switch, staging, commit, migration,
  service lifecycle action or remote operation occurred. Engram synchronization
  remains pending.

## Final local verification and closure (2026-11-02)

- Browser command:
  `cd bgg-shop-frontend && E2E_CORE_CONTAINER=bgg-e2e-007-closeout-api npm run test:e2e:opkey`
  — **9 passed on 1 worker**. Output included `Audit verified` and
  `Synthetic user removed`. Coverage: admin login/navigation; product
  create/readback/edit; stock adjustment; audit filters/pagination; coupon
  create/list/edit; product-specific promotion preview/create/list; and global
  promotion create/list.
- The initial E2E failures reflected a stale process/setup: the BFF had
  `--no-reload` and started before the promotion-forwarding source edits. After
  a controlled local restart, the sole remaining failure was an ambiguous
  `role=status` locator because preview and success messages share that role.
  The test now scopes to the exact success message; the final suite passed.
- Independent focused checks: BFF
  `python -m pytest -q tests/test_admin_promotions.py tests/test_admin_coupons.py tests/test_admin_audit.py tests/test_opkey_admin.py`
  — 108 passed; Core
  `python -m pytest -q tests/test_opkeys_internal.py` — 148 passed; Frontend
  `npm run test -- --run src/admin/promotions/PromotionForm.test.tsx src/admin/promotions/PromotionsPanel.test.tsx`
  — 14 passed; Core
  `python -m pytest -q tests/test_coupon_calculations.py tests/test_007_catalog_data_contracts.py`
  — 30 passed. Frontend
  `npm run test -- --run src/App.cart.test.tsx` — 9 passed, including
  authenticated current-cart coupon preview behavior.
- PostgreSQL checkout selection:
  `test_checkout_store_promotions_select_specific_and_highest_global_but_exclude_coupon_rows`
  passed (1 passed, 143 deselected); the real checkout-path
  `test_checkout_total_uses_specific_and_highest_global_store_promotions`
  passed (1 passed, 144 deselected), both in
  `bgg-shop-core/tests/test_graphql_credit_postgres.py`. The checkout-path test
  verifies persisted order/provider total, product-specific precedence over a
  higher global percentage, highest-global selection for another product, no
  stacking, and coupon-row exclusion. The complete PostgreSQL test file was
  not run.
- Both PostgreSQL tests used newly created disposable PostgreSQL 15 containers,
  generated ephemeral credentials, loopback-only ports and unique
  `credit_test_<uuid>` databases. Both test containers were stopped and
  removed. Existing E2E Core/DB/Redis services were untouched.
- Core product-detail delegation is restored exactly as
  `GET /api/v1/admin/products/{bggId}` → `productByBggId(bggId)` for the
  staff-protected BFF F-2 edit/readback flow. `bgg-shop-core/tests/test_opkeys_internal.py`
  rejects mismatched IDs, methods, routes and GraphQL roots; do not reinstate
  the earlier denial claim.
- Root and each service's `git diff --check` passed in independent
  verification. This documentation closeout does not rerun checks. No CI,
  deployment or remote validation is claimed. Engram mirror remains pending:
  Engram is unavailable in this runtime, so it was not synchronized.
- Final promotion semantics: omitted/null product ID is global; an eligible
  product-specific promotion wins even over a higher global percentage;
  otherwise the highest eligible global offer wins. Offers do not stack and
  coupon-linked rows are excluded. Coupon/store comparison and rounding remain
  as specified in the overall plan/contracts.

Work unit 7 and F-1 through F-5 are complete with local evidence. Weekly audit
ZIP generation/retention remains outside Spec 007 and is not included in its
17-task completion. There is no remaining blocker for this documentation
closeout.
