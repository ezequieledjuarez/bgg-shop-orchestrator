# Local Quickstart and Verification Plan

All checks in this document are local. Use synthetic fixtures only; do not use production, staging, remote services, real credentials, or deployment steps.

## Local functional matrix

1. **Catalog navigation and URL state**
   - Open the homepage and activate “Catálogo”, “Ver todo”, and “Explorar catálogo”; each must reach `/catalogo`.
   - Load the complete publisher list; verify every displayed count against distinct eligible public catalog games, including products with zero stock that remain visible in the catalog.
   - Select an exact publisher and verify that a game whose name contains the publisher text but has a different publisher is excluded. Combine publisher, category, and broad search; verify all criteria apply together.
   - Verify publisher counts do not change with search, category, page, or other filters. Exercise publisher-list loading, explicit failure, and retry; do not display stale or page-derived counts as a successful complete list.
   - Verify category, broad-search, and exact-publisher filters via direct-link reload, browser back/forward, and clearing filters.
   - Open the legacy homepage fragments `#catalogo`, `#categorias`, and `#editorial`; confirm they remain usable and the Editoriales UI link does not require an `/editorial` route.
   - Exercise category loading/error/retry, catalog loading/error/retry, empty results, keyboard navigation, and narrow viewport layout.

2. **Session and permissions**
   - With local synthetic accounts/fixtures, separately exercise a valid buyer, valid staff/superuser, confirmed `401`, operation-level `403`, and unavailable (`502` or network-failed) identity validation.
   - Confirm a temporary `403` or unavailable check is not reported as logout, an unresolved check does not show protected admin UI, and a valid superuser retains existing privileges after current validation.
   - Confirm session cleanup does not remove anonymous/cart data and does not create a repeated refresh loop.

3. **Order history**
   - For a valid account with zero own purchases, verify `GET /api/v1/orders` returns `200 { "orders": [] }` and the existing empty state.
   - For a buyer and a staff/superuser with existing purchases, verify each response contains only that account’s orders and existing invoice behavior remains intact.
   - Separately test missing/invalid bearer authentication and a real simulated upstream failure; neither may be presented as an empty successful list.
   - Distinguish deterministic local regression evidence from reproduction of the originally reported browser `500`; retain sanitized failure details only.

4. **Refresh pipeline**
   - Verify `POST /api/v1/auth/refresh` uses the configured frontend API base,
     normalizes trailing slashes, preserves relative bases, and includes cookies.
   - Core `401` for an invalid/expired refresh token is terminal; missing local
     refresh credentials also return `401`. Transport errors, Core `5xx`/other
     non-`200` responses, redirects, and malformed JSON/token shapes return
     sanitized `502` without clearing the refresh cookie.
   - Verify every refresh response is `Cache-Control: no-store`; a stale refresh
     success or rejection cannot modify a session that changed while pending.
   - After a temporary unavailable refresh, retry only after the user explicitly
     retries permission validation. A newly refreshed token rejected with `401`
     remains a bounded terminal outcome.

## Observed local commands

Core tests used the available global pytest because the Core `.venv` does not
contain pytest. The final scoped BFF refresh run used global `python3` because
`bgg-shop-bff/.venv/bin/python` was absent; frontend checks used the
repository's existing npm dependencies.

```sh
cd bgg-shop-core
python3 -m pytest tests/test_015_catalog_publishers.py tests/test_015_order_history.py -q
python3 -m pytest tests/test_graphql_products.py tests/test_007_catalog_data_contracts.py tests/test_graphql_orders.py tests/test_catalog_events.py tests/test_015_catalog_publishers.py tests/test_015_order_history.py -q

cd bgg-shop-bff
PYTHONPATH=. .venv/bin/python -m pytest tests/test_015_catalog_publishers.py tests/test_015_orders.py -q
PYTHONPATH=. .venv/bin/python -m pytest tests/test_products.py tests/test_catalog_cache.py tests/test_services_cart_product_contract.py tests/test_orders.py tests/test_services_wishlist_orders_contract.py tests/test_catalog_events.py tests/test_015_catalog_publishers.py tests/test_015_orders.py -q

cd bgg-shop-frontend
npm run generate:types
npm run test -- --run src/App.015-session.test.tsx src/lib/api.test.ts src/auth/AuthScreens.test.tsx src/App.admin-navigation.test.tsx src/App.015-catalog.test.tsx src/App.checkout.test.tsx src/App.test.tsx src/catalog/urlState.test.ts src/auth/adminCapabilities.test.tsx src/lib/apiClient.test.ts
npm run build
node_modules/.bin/oxlint src/lib/api.ts src/App.tsx
```

Final scoped correction commands:

```sh
cd bgg-shop-bff
PYTHONPATH=. python3 -m pytest tests/test_refresh_proxy.py tests/test_refresh_integration.py tests/test_015_refresh.py tests/test_015_catalog_publishers.py tests/test_015_orders.py -q

cd bgg-shop-frontend
npm run test -- --run src/App.015-session.test.tsx src/lib/api.test.ts src/auth/AuthScreens.test.tsx src/App.admin-navigation.test.tsx src/App.015-catalog.test.tsx src/App.checkout.test.tsx src/App.test.tsx src/catalog/urlState.test.ts src/auth/adminCapabilities.test.tsx src/lib/apiClient.test.ts
npm run build
node_modules/.bin/oxlint src/lib/api.ts src/App.tsx
```

## Evidence ledger

| Check | Observed result |
|---|---|
| Canonical BFF OpenAPI and Core SDL contract validation | Passed locally before implementation; endpoint/schema shapes validated and frontend types regenerated with `npm run generate:types`. |
| Test-first Core publisher facet/filter behavior | New tests first failed because fields were absent from SDL; then 6 facet tests passed. Combined Core feature-015 tests: 9 passed. |
| Core affected regression suite | 168 passed, 3 failed. Failures are existing schema-reference drift and two review-status expectations (`APPROVED` vs source `ACCEPTED`); feature-015 tests passed. |
| Test-first BFF publisher endpoint/filter | New tests first failed because route/filter behavior was absent; then 18 publisher tests passed. Combined feature-015 publisher/order tests: 23 passed. |
| BFF affected regression suite | 107 passed, 4 failed. Three older `requests.post` test doubles reject the existing `allow_redirects` argument; a separate existing cart-mutation path references undefined `op_key`. These unrelated issues were not changed. |
| Deterministic order-history regression | Local BFF fixture reproduced failure from undefined `op_key` passed by `get_orders()` into `_graphql_request`; removing the invalid argument fixed it. Core empty own-order results and staff own-only scope passed. This is not a reproduction of the original browser incident. |
| Frontend feature catalog/session tests | The final targeted command passed 153 tests across catalog, session, refresh API, URL-state, capabilities, API-client, admin-navigation, checkout, and authentication screens. No standalone `src/auth/session.test.ts` exists. |
| Frontend build | `npm run build` passed. |
| Browser/integrated-service flow | Passed in a fresh Chromium context: home CTAs route to `/catalogo`; real publisher/category/search filtering returns `Editorial Almanac`; URL survives reload/back/forward; facets remain global; keyboard and 375px layout checked; no final console/runtime/request errors. |
| Independent high-risk review | Completed: independent QA inspected contracts/authentication and reproduced transient-refresh logout; the scoped correction passed 41 BFF and 153 frontend tests. The parent independently reran the 41 BFF tests successfully. A separate QA run completed the isolated PostgreSQL/HTTP/browser checks below. |
| Protected worktree state | Existing unrelated root changes and frontend `.pytest-tmp/` were preserved; no commits or remote actions were made. |
| Refresh regression tests (RED → GREEN) | New BFF/frontend refresh regressions failed before the correction; final affected BFF suite passed (41 tests) and frontend suite passed (153 tests). |
| Refresh implementation checks | Frontend build and focused oxlint passed. BFF refresh behavior preserves cookies on upstream failures, clears only on terminal `401`/missing token, validates response shape, disables redirects, and marks responses no-store. |
| Refresh pipeline contract evidence | Core `saleor/auth_refresh.py` returns `401` for invalid/expired tokens and `400` only when the token is missing; the BFF requires a token before calling Core. BFF OpenAPI defines refresh `401`/`502` outcomes. |


### Feature-015 final isolated integration (2026-11-09)

- Environment: local disposable `docker.io/library/postgres:15` (observed
  PostgreSQL 15.19), bound only to `127.0.0.1:55433`, no volume; actual Core
  `schema.execute`, Django GraphQL HTTP server `127.0.0.1:8001`, actual BFF
  controller/service/proxy on `127.0.0.1:5001`, Vite on `127.0.0.1:3001`, and
  installed Playwright 1.64.1 / Chromium 1248. Container and all attached
  processes were stopped; `--rm` removed the database. Reserved/shared ports
  and services were not used.
- Synthetic fixture: 7 product rows, 7 distinct BGG IDs; publisher variants
  `  Northstar  ` / `Northstar`, case variant `northstar`, blank publisher,
  stock 0, and a product whose name contains “Editorial” under a different
  publisher. During the facet edge probe a temporary permissive row also had
  `NULL` publisher; the actual resolver excluded NULL/blank facets. For the
  full product-list/browser run the NULL row was normalized to a non-NULL
  synthetic publisher and duplicate BGG ID was made unique, matching
  `import_catalog.sql` (`publisher NOT NULL`, `bgg_id UNIQUE`). The table was a
  minimal feature fixture, not a full migration deployment.
- Core resolver: `productPublishers` returned `Northstar: 2`, `northstar: 1`,
  `Other Press: 1` during the initial NULL/blank probe; final schema-valid data
  returned `Northstar: 3`, `northstar: 1`, `Fixture Press: 1`, `Other Press: 1`.
  Exact case-sensitive filters returned 3 vs. 1 item; trimmed publisher +
  `categoryName=Juegos Familiares` + `search=Editorial` returned only BGG ID
  `150005` (`Editorial Almanac`, quantity 0). Unknown publisher returned 0;
  whitespace publisher produced the documented GraphQL validation error.
- BFF HTTP: `GET /api/v1/product-publishers` and categories returned 200;
  combined filtered `GET /api/v1/products?...` returned 200 / total 1; lowercase
  case-variant returned total 1; unknown publisher returned 200 / empty items;
  whitespace publisher returned 400. UI-emitted product request was
  `GET /api/v1/products?page=1&page_size=100&search=Editorial&category_name=Juegos+Familiares&publisher=Northstar`
  and returned 200.
- Persistence: final read used separate `feature015_ro` role granted SELECT
  only and a read-only transaction. `SELECT` observed 7 rows / 7 distinct BGG
  IDs / 1 blank-publisher row and facets
  `Fixture Press:1`, `northstar:1`, `Northstar:3`, `Other Press:1`; blank was
  excluded from facets. No real/shared database was queried.
- Browser: three homepage CTAs (`Catálogo`, `Ver todo`, `Explorar catálogo`)
  reached `/catalogo`; category/editorial controls applied exact URL filters;
  publisher counts stayed global; the one expected heading was visible after
  keyboard-submitted search; reload/back/forward preserved URL state; search,
  category, and editorial controls remained visible at 375×812 and Tab reached
  `Buscar`. Final browser errors: none. No route mocks or pre-existing storage
  state were used.
- Harness boundaries: BFF catalog cache was bypassed in the BFF process only;
  a test-only CORS origin was added for Vite port 3001 because the configured
  local allowlist is ports 3000/localhost. This does not validate production
  CORS configuration. Full migrations (`python manage.py migrate --noinput`)
  were not run; Core used a minimal disposable table for the feature resolver.
  A full migration run requires a fresh disposable database seeded with the
  documented catalog schema first. Auth/opkey middleware and authenticated
  flows were not exercised. The broad Core/BFF regression failures recorded
  above remain unchanged; they were not attributed to this isolated feature
  flow.
- Startup command forms (ephemeral password/DSN intentionally omitted):
  `podman run --pull=never --rm --name feature015-integration-pg -p 127.0.0.1:55433:5432 docker.io/library/postgres:15`;
  `DATABASE_URL=<ephemeral isolated DSN> python manage.py runserver 127.0.0.1:8001 --noreload`;
  `SALEOR_GRAPHQL_URL=http://127.0.0.1:8001/graphql/ python -c <BFF app with test-only cache/CORS harness>`;
  `VITE_API_BASE_URL=http://127.0.0.1:5001/api/v1 npm run dev -- --host 127.0.0.1 --port 3001 --strictPort`.
  Browser used the installed Playwright/Chromium via a one-off `node -e` check;
  no repository test/config files were added or modified.

### Baseline correction results (2026-11-09)

- RED observed before implementation: Core schema parity and the two SQL
  status assertions failed (3 failures); the BFF cart/product and
  wishlist/order test set plus the new cart-context regression failed (5
  failures), including the undefined cart `op_key`.
- Focused GREEN: `python3 -m pytest tests/test_graphql_products.py -q` passed
  (56 tests); BFF `tests/test_services_cart_product_contract.py`,
  `tests/test_services_wishlist_orders_contract.py`, and `tests/test_cart.py`
  passed (19 tests). The cart regression verifies guest cart IDs, bearer
  forwarding, no operation-key forwarding on cart requests, and redirect
  blocking. Redirect protection remains enabled.
- A separate wider Core run reported 588 passed, 221 skipped, and
  21 failures in `tests/test_graphql_credit_checkout.py` cases. At the time,
  these failures had not yet been diagnosed; the subsequent T011 investigation
  and correction are recorded below.
- A separate wider BFF run reported 907 passed and 5 failures.
  All five are additional request doubles that reject `allow_redirects=False`:
  four in `tests/test_services_graphql_contract.py` and one in
  `tests/test_services_graphql_contract_more.py`. The scoped T011 correction
  below addresses these separate follow-up failures.
- The seven targeted failures are corrected without changing the canonical
  BFF OpenAPI, Core SDL, or public cart wire contract. Core runtime descriptions
  now match the SDL; review SQL expectations use migration-canonical
  `ACCEPTED`; the cart proxy no longer references an undefined `op_key`.
- Independent parent verification reran the original Core affected selection
  recorded above: 171 passed, with one Django deprecation warning. The BFF
  affected selection plus `tests/test_refresh_proxy.py`,
  `tests/test_refresh_integration.py`, `tests/test_015_refresh.py`, and
  `tests/test_cart.py` passed: 144 tests, with 127 `datetime.utcnow()`
  deprecation warnings. T010 is complete for the seven authorized corrections.

### Additional baseline correction results (T011, 2026-11-09)

- RED reproduced locally before test edits. Core
  `PYTHONDONTWRITEBYTECODE=1 DATABASE_URL=sqlite:///:memory: python3 -m pytest tests/test_graphql_credit_checkout.py -q --tb=no -p no:cacheprovider`
  reported **21 failed, 31 passed**: successful checkout paths returned the
  sanitized `SERVER_ERROR`. Inspection showed the in-memory checkout fixture
  omitted `catalog_event_outbox`, although checkout records a transactional
  stock event. The BFF RED command
  `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. .venv/bin/python -m pytest tests/test_services_graphql_contract.py tests/test_services_graphql_contract_more.py -q --tb=short -p no:cacheprovider`
  reported **5 failed, 1 passed** because the fakes rejected the explicit
  `allow_redirects=False` argument.
- The Core fixture now applies the real `catalog_events.0001_initial`
  migration to its in-memory SQLite connection. Regression tests verify one
  `stock.changed` event on success, no extra event on idempotent replay, no
  outbox or financial changes after an invoice-triggered rollback, and exactly
  one event and one financial result after retry. SQLite trigger callbacks
  assert that injected rollback failures reached their intended table, rather
  than failing earlier on a missing outbox schema. BFF fakes explicitly accept
  and assert `allow_redirects is False`; the checkout response double has
  `status_code=200`. No service source or canonical contract changed.
- Focused GREEN: Core checkout command above passed **52 tests**. BFF command
  above passed **6 tests**. Related Core command
  `PYTHONDONTWRITEBYTECODE=1 DATABASE_URL=sqlite:///:memory: python3 -m pytest tests/test_graphql_credit_checkout.py tests/test_graphql_products.py tests/test_007_catalog_data_contracts.py tests/test_graphql_orders.py tests/test_catalog_events.py tests/test_015_catalog_publishers.py tests/test_015_order_history.py -q --tb=short -p no:cacheprovider`
  passed **223 tests**. Related BFF command
  `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. .venv/bin/python -m pytest tests/test_services_graphql_contract.py tests/test_services_graphql_contract_more.py tests/test_services_cart_product_contract.py tests/test_services_wishlist_orders_contract.py tests/test_cart.py tests/test_015_orders.py tests/test_015_refresh.py -q --tb=short -p no:cacheprovider`
  passed **41 tests** (33 existing `datetime.utcnow()` deprecation warnings).
- Safe isolated Core full suite ran once with explicit PostgreSQL test DSNs
  unset in the runner and `DATABASE_URL=sqlite:///:memory:`:
  `env -u ADMIN_AUDIT_TEST_POSTGRES_DSN -u SALES_METRICS_TEST_POSTGRES_DSN -u CREDIT_TEST_POSTGRES_DSN -u CHAT_CONVERSATION_TEST_POSTGRES_DSN -u COUPON_ADMIN_TEST_POSTGRES_DSN -u USER_PERMISSIONS_TEST_POSTGRES_DSN DATABASE_URL=sqlite:///:memory: PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q --tb=short -p no:cacheprovider`
  passed **609 tests**, skipped **221 PostgreSQL-gated tests**, with 9 existing
  warnings, in 26.84 seconds. No PostgreSQL DSN variable was set in the
  environment inspected before the run.
- The writer deferred the full BFF run. The independent verifier's global
  interpreter could not collect the complete suite because `langchain_chroma`
  and `langchain_ollama` were unavailable there; its focused service tests passed.
  The parent then used the existing service virtualenv, without installing
  dependencies:
  `cd bgg-shop-bff && PYTHONPATH=. .venv/bin/python -m pytest tests -q --tb=short`.
  The complete BFF suite passed **912 tests**, with 749 deprecation warnings,
  in 25.38 seconds. Tests using their own temporary directories were permitted;
  no shared database was accessed.
- Independent financial-fixture review confirmed the real outbox migration,
  success/replay event assertions, and rollback failure markers, and reran the
  checkout file: **52 passed**. The parent independently reran the same checkout
  command: **52 passed**, one Django warning. T011 is complete. These corrections
  changed only tests and this evidence, not service source or API contracts.
