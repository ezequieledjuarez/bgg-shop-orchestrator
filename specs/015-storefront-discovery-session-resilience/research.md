# Research: Storefront Discovery and Session Resilience

This document records the design evidence and implementation findings. Reported symptoms remain distinct from deterministic local regression evidence; no live account or remote service was used.

## Decision 1 — Use a dedicated catalog page with counted exact-publisher selection

- **Decision**: Make `/catalogo` the canonical complete-catalog route; retain the homepage’s selected-games section. Route “Catálogo”, “Ver todo”, and “Explorar catálogo” there. “Categorías” and “Editoriales” navigate to the catalog’s category and exact-publisher filters. The publisher selector displays the complete eligible publisher list and each publisher’s distinct-game count.
- **Evidence**: The current storefront links all three main navigation items to fragments in `bgg-shop-frontend/src/App.tsx:708-713`; the hero and view-all CTAs also use `#catalogo` at `:750-763`. Category controls already exist on the home catalog section at `:787-805`; the editorial section anchor is at `:833`.
- **API capability**: Existing `GET /api/v1/products` accepts `category_name` and broad `search`; `search` matches product name or publisher case-insensitively. The canonical BFF contract now adds `publisher` and `GET /api/v1/product-publishers`; the canonical Core SDL adds `publisher` and `productPublishers`. Frontend types were regenerated from the BFF OpenAPI.
- **Tradeoff**: Broad search intentionally remains broad and may match a game name. Publisher selection uses a separate exact filter so a same-name game cannot accidentally match a publisher choice.
- **Compatibility**: Preserve current homepage fragment targets for existing bookmarks, including `#editorial`; the user report mentioning `/editorial` does not establish an existing route.

## Decision 2 — Treat exact publisher state as a navigable client selection

- **Decision**: Use URL query keys `category_name`, `search`, and additive exact `publisher`. Preserve safe unfiltered behavior for unknown/invalid query values. Keep route state synchronized across reload and browser history.
- **Evidence**: The current page builds BFF query parameters from local component state in `bgg-shop-frontend/src/App.tsx:522-538`; the existing BFF contract defines the current criteria. The additive publisher key and corresponding service contracts are feature-local drafts, not canonical changes.
- **Tradeoff**: Broad search and exact publisher are distinct controls. If both are present, as with category, all criteria combine with AND semantics. Unknown query keys are not silently interpreted as filters.

## Decision 3 — Keep empty orders, invalid authentication, and upstream failure distinct

- **Decision**: A valid user with no purchases receives `200 { "orders": [] }`. Missing/invalid bearer authentication remains `401`; an actual Core/upstream failure remains an explicit sanitized failure. Do not convert an error to an empty success.
- **Evidence**: The canonical BFF contract defines `GET /api/v1/orders` with `200`, `401`, and `502` outcomes (`bgg-shop-bff/specs/openapi.yaml:1392-1415`) and `OrderListResponse.orders` as an array (`:4879-4887`). BFF `list_orders` returns the service result inside `{orders: ...}` and maps `UpstreamError` (`bgg-shop-bff/src/controllers/orders_controller.py:21-27, 100-108`). Core `myOrders` derives the authenticated user and queries only rows with that `user_id`, returning an empty list when no rows exist (`bgg-shop-core/saleor/graphql/api.py:1921-1937`). The frontend already distinguishes empty and retryable error states (`bgg-shop-frontend/src/checkout/OrdersScreen.tsx:58-91, 108-118`).
- **Evidence status**: Core order-history tests confirm empty results for buyer and staff/superuser while retaining user scoping. A deterministic BFF service fixture reproduced a `500`: `get_orders()` passed undefined `op_key` to `_graphql_request`, causing a local failure before a successful GraphQL response could be mapped. Removing the invalid argument fixed the deterministic regression. This does not claim the original reported browser incident was reproduced.

## Decision 4 — Do not infer session validity or admin role from stale UI

- **Decision**: Treat server-validated current-user flags as a navigation hint only. Handle confirmed `401`, operation-level `403`, and `502`/network unavailability separately. Do not equate transient denial/unavailability with logout, and do not accept stale flags as admin authorization.
- **Evidence**: `/api/v1/auth/me` returns current `is_staff` and `is_superuser` flags with bearer authentication and no-store behavior; invalid/inactive identity is `401`, while inability to resolve identity is `502` (`bgg-shop-bff/specs/openapi.yaml:57-110`). The existing `014-admin-navigation` specification already requires current role resolution and backend enforcement (`specs/014-admin-navigation/spec.md`, “User Story 4”); this feature extends rather than replaces it. The home header currently bases visible logout on a sessionStorage key in `bgg-shop-frontend/src/App.tsx:715-720`. `operationKeyFor` returns no operation key for expired or invalid operation-key data but does not itself clear account session state (`bgg-shop-frontend/src/auth/session.ts:5-23`).
- **Evidence status**: Focused frontend tests use synthetic sessions and verify that a confirmed `401` permits a bounded refresh, `403` and unavailable permission checks do not clear the account session, and unresolved permissions withhold admin controls. No real account was used.

## Decision 5 — Preserve service ownership while planning additive catalog contracts

- **Decision**: No new persistence entity, migration, or dependency is proposed. Draft one additive public REST facet endpoint and an exact publisher argument, backed by Core publisher aggregation and product filtering. Keep order/auth behavior and Core `myOrders` unchanged.
- **Rationale**: The current Core product stores publisher as a required string rather than a publisher entity (`bgg-shop-core/specs/schema.graphql:13,146`; `bgg-shop-core/tests/test_admin_audit_postgres.py:33`). The BFF already exposes the catalog and category pattern. Frontend API types remain generated from the canonical BFF OpenAPI file after any future approved canonical change.
- **Contract status**: The feature-local references summarize implemented canonical interfaces. Authoritative contracts remain the BFF OpenAPI and Core SDL.

## Decision 6 — Count public catalog games at the source

- **Decision**: The publisher-facet operation returns the complete, unpaginated list of trimmed nonblank publisher strings and distinct game counts. Counts use the same rows eligible to `products`, count distinct game IDs (`bggId`) rather than stock units/SKUs, and do not depend on active filters or pagination. Public catalog products with zero quantity remain eligible when the existing catalog includes them.
- **Identity and ordering**: No publisher entity or ID exists in the current schema; the trimmed stored publisher value is the stable selector identity and display name. Exact duplicate strings after trimming collapse to one option. Case variants remain distinct; casing is preserved and matching is case-sensitive after trimming the request. Sort case-insensitively ascending, with exact spelling as tie-breaker. Null, empty, and whitespace-only publisher values are excluded.
- **Rationale**: Counts derived by the frontend from a page would be incomplete and potentially misleading; Core must aggregate across the eligible catalog and BFF must adapt the complete result without N+1 calls.
- **Failure/cache behavior**: Return a sanitized explicit upstream failure rather than stale counts or a false empty success. No new cache is proposed. If an existing shared catalog cache is reused, existing invalidation must cover product changes and publisher reassignment; do not add a separate count cache.
- **Contract status**: These semantics are represented in the canonical BFF OpenAPI and Core SDL and validated before implementation.

## Implementation findings (2026-11-09)

- Core facets aggregate across eligible public products, count distinct `bgg_id` values, group `BTRIM(publisher)`, omit blank values, preserve case variants, and sort case-insensitively with exact spelling as tie-breaker. Exact publisher filtering combines with existing criteria.
- BFF validates facet shape/counts and publisher input, maps `productCount` to `product_count`, forwards the exact filter, includes publisher in the established catalog cache key, and returns sanitized errors instead of false empty success. Facets are not cached.
- Frontend `/catalogo` has canonical URL state and independent product/category/publisher loading/error states. Category and publisher navigation are filters, not separate routes; the home page retains selected games.
- Broad affected test runs still report unrelated existing failures: Core schema/reference drift and review-status expectations; stale BFF mocked `requests.post` signatures were aligned with `allow_redirects`. Exact latest results are maintained in `quickstart.md`.
- Independent refresh-pipeline QA found that the BFF mapped every Core non-200 or request exception to terminal `401` and cleared the cookie, while the frontend sent refresh to a relative URL instead of its configured API base. Core's current refresh view returns `401` for invalid/expired tokens and `400` only when no token is supplied; the BFF handles missing credentials before calling Core.
- The final correction maps only terminal/missing-token cases to cookie-clearing `401`; transport, non-`200` upstream statuses, redirects, and invalid response payloads become sanitized, non-cacheable `502` responses that preserve the cookie. The frontend now normalizes configured URLs, ignores stale outcomes after account changes, and makes temporary refresh failure retryable only by explicit user action. Focused RED/GREEN evidence and remaining integration gaps are recorded in `quickstart.md`.
