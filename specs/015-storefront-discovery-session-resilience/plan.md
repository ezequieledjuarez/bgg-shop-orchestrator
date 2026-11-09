# Implementation Plan: Storefront Discovery and Session Resilience

**Branch**: `015-storefront-discovery-session-resilience` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/015-storefront-discovery-session-resilience/spec.md`

## Summary

Add a canonical `/catalogo` page while keeping the homepage as a selected-games experience. Route the existing catalog CTAs to the full catalog, and connect category/editorial navigation to category, broad-search, and exact-publisher filters. Show a complete publisher list with counts of distinct eligible public catalog games. Separately, verify and correct locally any reproducible empty-order-history or stale-session issue: preserve `200 { "orders": [] }` for a valid user with no orders, scope orders to that user, and distinguish confirmed `401` from valid-user `403` and upstream `502`. Implementation is local; no deployment or remote validation is in scope.

Publisher facets and exact publisher filtering are additive API capabilities implemented contract-first. The canonical contracts now define `GET /api/v1/product-publishers`, an exact `publisher` filter on `GET /api/v1/products`, and the matching Core GraphQL fields. The feature-local contract files summarize these changes; service contracts remain authoritative.

## Technical Context

- **Languages/runtimes**: Python services; TypeScript/React frontend. Existing manifests specify Flask `>=3.0.0` for the BFF, Django `>=4.2.10,<5.0.0` for Core, React `^19.2.8`, and TypeScript `~5.4.0`; no new runtime is proposed.
- **Primary dependencies**: Existing BFF REST controllers and OpenAPI, Core Graphene query and schema, frontend router/state/fetch code, and existing Vitest/pytest suites.
- **Storage**: No new persistence. Orders remain in the existing purchase-order store; catalog selection is client URL state; account-session data retains its existing browser-session lifecycle.
- **Testing**: Frontend Vitest/build and local browser checks; BFF/Core pytest checks for applicable order and auth behavior. Actual command results and known unrelated failures are recorded in [quickstart.md](quickstart.md) and [tasks.md](tasks.md).
- **Target platform**: Local environments only.
- **Project type**: Existing cross-service web storefront with React frontend, Flask BFF, and Django/Graphene Core.
- **Performance goals**: No new quantitative latency or throughput target. Publisher counts come from a Core aggregation, not from paginated product results; the BFF adapts one complete facet result and the UI makes no per-publisher requests.
- **Constraints**: Preserve checkout, wishlist, nonempty order/invoice, and admin behavior; no new dependencies, migrations, or speculative authentication flow. Do not equate `403` or a service outage with confirmed logout. Never use frontend role visibility as backend authorization.
- **Scale/scope**: One dedicated catalog route, category, broad-search, and exact-publisher filters, publisher counts, three existing navigation entry points, and targeted handling/verification of order/session edge cases.

## Constitution Check

**Implementation check: PASS.**

1. **Preserve established behavior**: Keep homepage selection, existing product query behavior, nonempty order/invoice flow, and existing admin privileges; fix only confirmed behavior within this feature’s scope.
2. **Keep contracts and ownership explicit**: BFF REST is defined by `bgg-shop-bff/specs/openapi.yaml`; Core GraphQL by `bgg-shop-core/specs/schema.graphql`; frontend API types are generated from the BFF contract. Catalog publisher aggregation/filtering is owned by Core; the BFF exposes the REST shape; the frontend consumes the BFF contract.
3. **Trace changes**: Feature requirements link to local evidence, affected canonical contracts, implementation, tests, and existing service boundaries. A locally deterministic BFF orders failure was found; it is not claimed to reproduce the original browser incident.
4. **Protect customers and service boundaries**: Keep order ownership enforced by Core, preserve sanitized upstream failures, avoid leaking identity details, and require fresh server-validated permissions for protected UI.
5. **Smallest safe change**: Keep existing broad case-insensitive `search` semantics, add only the approved publisher facet and exact-match filter, and reuse existing product storage. Do not create a publisher entity, migration, independent client-derived facet calculation, or authentication abstraction.

**Post-design check: PASS.** The canonical BFF OpenAPI and Core SDL were updated and validated before the corresponding behavior. Frontend types were regenerated from canonical OpenAPI. Existing `search` remains broad and case-insensitive over product name or publisher; it is distinct from the exact-publisher filter.

## Project Structure

```text
specs/015-storefront-discovery-session-resilience/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── bff-openapi.yaml
    ├── core-catalog-publishers.graphql
    └── storefront-navigation.md

bgg-shop-frontend/
└── src/
    ├── App.tsx                         # storefront navigation and current catalog
    ├── auth/session.ts                 # session utilities and operation-key expiry
    └── checkout/OrdersScreen.tsx        # existing empty/error/order-history states

bgg-shop-bff/
├── specs/openapi.yaml                  # authoritative REST contract
├── src/controllers/products_controller.py
├── src/services.py                     # GraphQL adaptation and catalog caching
└── src/proxy.py                        # Core GraphQL operations

bgg-shop-core/
├── specs/schema.graphql                # authoritative GraphQL contract
└── saleor/graphql/api.py               # catalog facets/filter and own-orders resolver
```

**Structure Decision**: Keep existing service ownership and implement in the existing Core, BFF, and frontend modules. No new persistence entity, migration, or dependency was added.

## Endpoints Availability and Contract Gate

The feature-local references below summarize the canonical service contracts. All catalog reads are public and contain only public-catalog data.

| Method and path | Request and success shape | Authorization / failures | Planned use |
|---|---|---|---|
| `GET /api/v1/products` | Existing page/player/year/price filters plus `category_name`, broad `search`, and exact `publisher`; returns paginated `ProductPage` (`items`, `page`, `page_size`, `total`, `total_pages`). `search` remains case-insensitive over product name or publisher. | Public, bearer, or operation-key security as currently defined; `400` for invalid filters, `502` for sanitized Core failures. | Full catalog; category, broad-search, and exact-publisher filters, combined with AND semantics. |
| `GET /api/v1/product-categories` | Returns a JSON array of category-name strings. | Existing public operation; `502` on unavailable/invalid Core response. | Populate category choices. |
| `GET /api/v1/product-publishers` | Public operation returning the complete, unpaginated array of `{publisher, product_count}` facets. The count is distinct eligible catalog games and global across query filters and pages. | No authentication required; `502` for unavailable/invalid Core response. Never return stale or partial success as the complete list. | Populate publisher choices and game counts without client-side counting or N+1 calls. |
| `GET /api/v1/auth/me` | Returns `{is_staff, is_superuser}`. | Bearer only; `401` for missing/invalid/inactive identity, `502` for unverified Core identity. No-store. | Current role/navigation hint; never grants access. |
| `POST /api/v1/auth/refresh` | Existing refresh-cookie or optional body-token flow; `200` returns access token and may rotate cookie. | `401` when refresh token is missing/rejected, `502` on unavailable/invalid Core response. | Preserve existing refresh behavior; do not introduce a refresh loop. |
| `GET /api/v1/orders` | Bearer-authenticated own orders as `{orders: [PurchaseOrder, ...]}`; empty is `{orders: []}`. | `401` for missing/invalid bearer; `502` for Core unavailability/invalid response. | Keep empty history distinct from upstream failure. |

**Publisher contract decision**: The Core contract exposes `productPublishers: [ProductPublisherCount!]!` and a nullable `publisher: String` argument to `products`. The BFF contract exposes `GET /api/v1/product-publishers` and a nullable `publisher` query parameter to `GET /api/v1/products`. The publisher list has no pagination because truncation would make it incomplete; an empty successful list means there are no eligible nonblank publishers. Each item uses the trimmed, stored publisher name as both stable identity and display name, with `product_count` as a nonnegative integer. Identical values after trimming are grouped; case variants remain distinct, display spelling is preserved, sorting is case-insensitive ascending with exact spelling as tie-breaker, and the request matches the trimmed publisher case-sensitively. Blank publisher values are excluded. Valid but unknown publishers return an empty product page; blank or over-250-character filter values return `400`. Publisher, category, and broad search criteria combine with AND semantics.

Counts are aggregated in Core over the same rows eligible for the public catalog, counting distinct game IDs (`bggId`) rather than stock units or SKUs. Current catalog semantics include public products even when quantity is zero; counts are not personalized and do not vary with search, category, page, or other filters. No new cache is proposed. If implementation reuses an existing shared catalog cache, product changes and publisher reassignment must participate in its established invalidation; do not introduce a separate count cache or a stale fallback.

**Unresolved contract decisions**: None. Canonical OpenAPI and Core SDL validation passed locally before behavior implementation.

The list and product-filter operations remain public and return no private/user-specific data. On invalid upstream data or unavailability, BFF returns an explicit sanitized `502`; it must not return stale counts or claim a successful empty list. `401`, operation-level `403`, and upstream unavailability remain distinct for account/order operations.

**Evidence**: Canonical OpenAPI and Core SDL shape/syntax checks and type generation passed. Focused Core publisher/order tests, BFF publisher/order tests, frontend route/session tests, and the frontend build passed. Full affected suites expose existing schema/review drift and legacy BFF mocks; details are recorded in [quickstart.md](quickstart.md). Use synthetic/local identities and fixtures only.

**Acceptance gate**: Complete local functional checks and independent review of public-contract/auth changes before declaring the feature fully verified. No check may turn an actual upstream failure into an empty success. Remote publication, deployment, and PR/MR work are out of scope.

## Complexity Tracking

No constitution violations or additional project layers are proposed.
