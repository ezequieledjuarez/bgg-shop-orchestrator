# Tasks: Storefront Discovery and Session Resilience

Source: [spec.md](spec.md), [plan.md](plan.md), and [contracts/](contracts/).
Implementation authorized on 2026-11-09. Local checks only. Preserve unrelated
worktree changes and the existing `.specify/feature.json`.

## Phase 1: Setup and contract gate

- [X] T001 Read the specification, confirmed global publisher-count decision,
  service boundaries, existing tests, and worktree state. No checklist directory
  exists. Core/BFF are initially clean; frontend contains pre-existing
  `.pytest-tmp/`. Parent feature branch is
  `015-storefront-discovery-session-resilience`.
- [X] T002 Update and validate canonical BFF OpenAPI and Core SDL for publisher
  facets and the exact `publisher` filter before implementing their behavior.
  Regenerated frontend types from canonical BFF OpenAPI. YAML and SDL syntax
  and required endpoint/field shapes validated locally.

## Phase 2: Core and BFF

- [X] T003 Add test-first Core publisher aggregation and exact publisher
  filtering. Count distinct eligible games globally, include zero-stock public
  products, omit blank names, trim identities, preserve case, and combine filters
  with AND. RED observed before implementation; 6 facet tests passed. Preserve
  catalog pagination and existing filters.
- [X] T004 Add test-first BFF publisher endpoint, upstream validation, exact
  filter forwarding, and appropriate existing catalog-cache integration. Real
  upstream failures remain sanitized errors, never empty/stale success. RED
  observed before implementation; 18 publisher tests passed and the filter is
  included in the existing cache key. Facets are not cached.
- [X] T005 Reproduce the order-history failure using deterministic local
  fixtures; correct only verified causes. Cover empty buyer/staff histories,
  ownership isolation, authentication errors, explicit upstream failure, and
  unchanged nonempty order/invoice behavior. Distinguish deterministic regression
  evidence from reproduction of the originally reported browser incident.
  Deterministic BFF test reproduced `get_orders()` passing undefined `op_key` to
  `_graphql_request`; removing that argument fixed the fixture. The original
  browser incident was not reproduced. Core own-order tests passed.

## Phase 3: Frontend

- [X] T006 Add test-first `/catalogo`, homepage selection, all catalog entry
  points, category controls, publisher names/counts, exact selection, URL filter
  state, reload/history, legacy fragments, and accessible loading/error/empty
  states. Counts remain global when filters change. Dedicated catalog/URL tests
  and existing catalog tests passed.
- [X] T007 Reproduce and correct stale session/permission UI with focused tests:
  invalid authentication versus forbidden versus unavailable, valid superuser,
  bounded refresh, and preservation of anonymous/cart data. Focused frontend
  session, capability, auth-screen, and admin-navigation tests passed. Follow-up
  coverage also verifies configured/fallback/relative refresh URLs, stale
  success/rejection after account changes, explicit retry after temporary
  unavailability, and bounded handling of a newly rejected access token.

## Phase 4: Verification and documentation

- [X] T008 Run affected Core/BFF/frontend tests, frontend build/type generation,
  contract consistency, and local browser/integration checks where available.
  Prior focused/affected test, build, lint, and contract evidence is retained
  below, including known broad-suite failures. Final isolated PostgreSQL/Core →
  BFF HTTP → Vite/Chromium checks passed; see the final integration ledger in
  `quickstart.md`. No authentication middleware or full migration deployment
  was claimed.
- [X] T009 Update directly related service documentation and this evidence
  ledger. No remote publishing, PR creation, merge, or commit was performed.

## Baseline remediation

- [X] T010 Correct seven independently reproduced baseline test failures:
  Core schema introspection parity (seven mismatched runtime descriptions), two
  review SQL assertions using legacy `APPROVED` instead of migration-canonical
  `ACCEPTED`, three BFF request doubles rejecting the existing redirect-safety
  argument, and the cart mutation `NameError` plus its request-double contract.
  Authorized 2026-11-09. Preserve authoritative SDL descriptions and redirect
  protection; keep the canonical cart API and public wire behavior unchanged.
  Verify guest cart IDs, bearer forwarding, non-forwarding of operation keys,
  cart warnings, and sanitized upstream failures with local deterministic tests.
  Focused GREEN checks: Core `tests/test_graphql_products.py` (56 passed) and
  BFF cart/request-double tests (19 passed). Parent independently reran the
  original affected Core selection (171 passed) and the affected BFF selection
  including cart/refresh regressions (144 passed). A separate wider
  BFF run exposed five additional redirect-argument test-double failures in
  `bgg-shop-bff/tests/test_services_graphql_contract.py` and
  `bgg-shop-bff/tests/test_services_graphql_contract_more.py`, outside this
  task's authorized edit surfaces. At T010 close, these and the wider Core
  credit-checkout failures were deferred to T011 below; they do not represent
  failures in T010's seven-node verified selection.

- [X] T011 Correct the additional five BFF GraphQL request-double failures and
  21 Core credit-checkout failures within the authorized test/documentation
  surfaces only. Preserve production redirect protection, checkout contracts,
  financial transaction semantics, and all pre-existing worktree changes. Use
  explicit `allow_redirects=False` expectations in BFF doubles. For Core,
  reproduce failures against an isolated in-memory SQLite fixture, apply the
  real catalog-event outbox schema/migration to that fixture, and add regression
  coverage that successful checkout emits exactly one event, idempotent retry
  emits no additional event, and rollback emits no event or financial changes
  before a successful retry emits one. Update this evidence ledger only with
  observed commands/results. Authorized 2026-11-09; local-only, no commits,
  branches, shared database writes, service restarts, or source changes.
  Verification: focused Core checkout tests and the specified related Core and
  BFF suites; run each complete backend suite once only after confirming safe
  local test configuration. Risk: high because checkout financial semantics
  are covered; perform independent verification and parent spot-check before
  marking complete. Route: delegated direct, one bounded writer, no nested
  agents. Independent review confirmed the outbox/financial rollback assertions
  and reran all 52 checkout tests successfully. The parent also reran these 52
  tests and executed the complete BFF suite using its service virtualenv:
  912 passed. The isolated Core full suite passed 609 tests, with 221 explicitly
  PostgreSQL-gated skips. No service source or canonical contract changed.

## Dependencies and execution

T002 precedes T003/T004/T006. T003 precedes T004; T004 precedes final T006
integration. T005 and T007 are independent regressions but share existing files,
so keep a single writer. T010 and T011 are separate baseline corrections
authorized 2026-11-09. T008 follows all behavior changes; T009 closes only
observed results.

Implementation route: one bounded writer across service contracts, backend,
and frontend; no nested agents. Risk: high (public interfaces, authentication,
and order privacy). Use meaningful deterministic RED → GREEN tests before
behavior changes; contract/docs structural changes are exempt. Independent verification completed: the separate QA review identified the
transient-refresh defect, the scoped correction passed focused checks, and
the parent reran the affected BFF checks. A separate isolated integration run
validated the public catalog through PostgreSQL, BFF HTTP, and Chromium.

## Verification commands

From `bgg-shop-core/`:

```sh
python3 -m pytest tests/test_graphql_products.py tests/test_007_catalog_data_contracts.py tests/test_graphql_orders.py tests/test_catalog_events.py tests/test_015_catalog_publishers.py tests/test_015_order_history.py -q
```

From `bgg-shop-bff/`:

```sh
PYTHONPATH=. .venv/bin/python -m pytest tests/test_products.py tests/test_catalog_cache.py tests/test_services_cart_product_contract.py tests/test_orders.py tests/test_services_wishlist_orders_contract.py tests/test_catalog_events.py tests/test_015_catalog_publishers.py tests/test_015_orders.py -q
```

From `bgg-shop-frontend/`:

```sh
npm run generate:types
npm run test -- --run src/App.test.tsx src/App.admin-navigation.test.tsx src/App.checkout.test.tsx src/App.015-catalog.test.tsx src/App.015-session.test.tsx src/catalog/urlState.test.ts src/auth/AuthScreens.test.tsx src/auth/adminCapabilities.test.tsx src/lib/apiClient.test.ts
npm run build
```

Include any new focused tests in the same runner invocation. Normalization and
type generation precede final functional verification. Missing dependencies may
be restored only following an observed missing-dependency failure.

## Evidence and recovery

- Core focused tests: `tests/test_015_catalog_publishers.py` and
  `tests/test_015_order_history.py` — 9 passed.
- Core affected suite: 168 passed, 3 failed. Existing failures are canonical
  schema drift and review tests expecting `APPROVED` while implementation uses
  `ACCEPTED`.
- BFF focused feature-015 tests: 23 passed. Affected suite: 107 passed, 4
  failed. Three older test doubles reject the existing `allow_redirects`
  argument; cart mutation also references undefined `op_key`. These unrelated
  existing issues were not changed.
- Frontend focused regression command: 142 passed; `npm run build` passed.
  `src/auth/session.test.ts` is absent, so session behavior is covered by the
  feature and app-level tests instead.
- Canonical OpenAPI YAML and Core GraphQL SDL parse; publisher endpoint/filter
  schema shapes were asserted. Frontend types generated successfully.
- `git diff --check` passed in root and all three services. Existing unrelated
  root changes and frontend `.pytest-tmp/` were preserved.
- Local integrated-browser checks and independent high-risk review completed;
  see the final integration ledger in `quickstart.md`. The originally reported
  browser `500` was not reproduced; the deterministic BFF service-fixture
  failure is established.
- No commit, remote publication, deployment, or live-account access was
  performed.
