# Feature Specification: Storefront Discovery and Session Resilience

**Feature Branch**: `015-storefront-discovery-session-resilience`
**Created**: 2026-11-09
**Status**: Implementation complete. Local checks and remaining exceptions are
recorded in [tasks.md](tasks.md) and [quickstart.md](quickstart.md); the
unrelated Core/BFF baseline failures and the limitation that the original
browser incident was not reproduced remain part of that evidence.
**Input**: User-reported storefront navigation and order-history failures, plus uncertainty about an expired administrator session.

## Clarifications

### Session 2026-11-09

- Q: Should publisher game counts reflect the entire public catalog or the active search/category filters? → A: Global counts across the public catalog, independent of active search, category, other filters, and pagination.

## User Scenarios & Testing

### User Story 1 — Browse the complete catalog (Priority: P1)

A visitor can reach a dedicated catalog page from the storefront, browse publishers with their game counts, and narrow displayed games by category or exact publisher. The homepage remains a selected-games experience.

**Why this priority**: Current catalog links land on a home-page section rather than a complete discovery destination, and the category navigation reportedly does nothing.

**Independent Test**: From the homepage, activate each catalog entry point and verify that it reaches `/catalogo`; compare publisher counts with the public catalog, select an exact publisher and category, reload, and use browser back/forward to verify that the displayed selection follows the URL.

**Acceptance Scenarios**:

1. **Given** a visitor is on the home page, **When** they activate “Catálogo”, “Ver todo”, or “Explorar catálogo”, **Then** they reach the canonical `/catalogo` page rather than only scrolling to the home games section.
2. **Given** the visitor selects a category or publisher, **When** the selection is applied, **Then** the catalog results reflect that selection and its shareable URL state.
3. **Given** the visitor follows “Categorías” or “Editoriales”, **When** navigation completes, **Then** the catalog page is shown with the relevant filter area available; these links do not lead to unimplemented standalone pages.
4. **Given** the visitor is on the catalog page, **When** they return to the homepage, **Then** its selected-games section remains available and is not replaced by the full-catalog page.
5. **Given** publisher facets load successfully, **When** the visitor opens the publisher selector, **Then** it shows each eligible publisher exactly once with the count of distinct public catalog games attributed to that publisher.
6. **Given** the visitor selects a publisher, **When** the catalog loads, **Then** only products with that exact publisher value match; product-name substring matches do not count as publisher matches.
7. **Given** the visitor combines publisher, category, or search criteria, **When** results load, **Then** all active criteria are combined with AND semantics and `search` retains its existing broad product-name-or-publisher behavior.
8. **Given** publisher counts are displayed, **When** the visitor changes search, category, or pagination without a catalog data change, **Then** each publisher count remains the same global total rather than the number of matching filtered results.

### User Story 2 — Understand and recover from authentication and authorization outcomes (Priority: P1)

A shopper or administrator sees account state that reflects validated server responses. Temporary permission or service failures do not falsely confirm logout or grant administrative access.

**Why this priority**: A reported expired-session symptom is unverified, and stale account UI can mislead users or expose protected controls.

**Independent Test**: Locally exercise valid, expired/invalid, missing, and permission-denied sessions; verify public storefront recovery, protected UI removal, and preservation of unrelated cart data.

**Acceptance Scenarios**:

1. **Given** a session is missing, expired, or invalid and the server confirms authentication failure (`401`), **When** the application handles the response, **Then** it clears only that account session, removes account-protected controls, and offers a safe path to sign in again.
2. **Given** a valid authenticated user receives a forbidden response (`403`), **When** the application handles it, **Then** it withholds the denied operation and protected content without treating the response alone as proof that the user is logged out.
3. **Given** session or permission validation is pending or unavailable, **When** the application renders, **Then** it does not present stale role flags as current authority, falsely confirm logout, or expose administrative controls; it provides an appropriate retry/error state.
4. **Given** a valid superuser session, **When** current permissions are successfully verified, **Then** existing superuser privileges continue to function; frontend visibility is not authorization.
5. **Given** the account session is cleared, **When** unrelated anonymous/cart data exists, **Then** that data is preserved.

### User Story 3 — View own purchase history, including an empty history (Priority: P1)

An authenticated shopper can view their own orders, or a clear empty state if they have not purchased. Staff users are also limited to their own purchase history.

**Why this priority**: A `500` was reported for an administrator with no purchases; a valid empty collection must not be presented as a server error or as another customer’s orders.

**Independent Test**: Locally request order history for an authenticated account with no orders, one with existing orders, and a staff/superuser account; separately simulate invalid authentication and an actual upstream failure.

**Acceptance Scenarios**:

1. **Given** an authenticated account has no purchases, **When** it requests `GET /api/v1/orders`, **Then** the response is `200` with `{ "orders": [] }` and the UI presents the existing empty-history state.
2. **Given** an authenticated account has purchases, **When** it requests its order history, **Then** existing order and invoice behavior remains unchanged and only its own orders are returned.
3. **Given** a staff or superuser has no purchases, **When** they request their purchase history, **Then** the empty response remains `200`; elevated privileges do not broaden the result to all customers’ orders.
4. **Given** Core or another upstream dependency actually fails, **When** order history is requested, **Then** the failure remains an explicit sanitized error and is not converted into a success-shaped empty collection.
5. **Given** the bearer credential is invalid or absent, **When** order history is requested, **Then** the established authentication failure remains distinguishable from an empty collection.

## Edge Cases

- Unknown, repeated, malformed, or unsupported catalog query values must not crash the page or silently select a different filter; the unfiltered catalog remains a safe baseline.
- Publisher facet counts use the same product eligibility as the public catalog, count distinct games rather than inventory units, and do not vary with search, category, pagination, or other active filters.
- Empty/null/whitespace publisher values are not listed as selectable publishers; counts are not inferred from a truncated product page or replaced with stale counts after an upstream failure.
- Existing `#catalogo`, `#categorias`, and `#editorial` URLs must not become broken. The observed `#editorial` anchor is not evidence that an `/editorial` route exists.
- Direct navigation, reload, browser back/forward, and clearing filters must keep URL and selected filter state coherent.
- Empty catalog results, category/publisher load failure, catalog load failure, and retrying each failure must have distinct, accessible UI states.
- A `403` for one operation must not erase a valid session or cause a refresh loop; only a validated authentication failure may invalidate that session.
- Failure to validate permissions must not be mistaken for a validated denial or for successful administrator status.
- Logging out or invalidating one account must not erase unrelated anonymous cart state.
- An actual upstream order failure must never fall back to `200 { "orders": [] }`.
- Existing nonempty order, invoice, checkout, wishlist, and admin workflows remain unchanged.

## Requirements

### Functional Requirements

- **FR-001**: The storefront MUST provide `/catalogo` as the canonical route for browsing the complete catalog.
- **FR-002**: The “Catálogo”, “Ver todo”, and “Explorar catálogo” entry points MUST navigate to `/catalogo`.
- **FR-003**: The homepage MUST retain its selected-games experience independently of the complete catalog page.
- **FR-004**: “Categorías” and “Editoriales” MUST lead to the catalog discovery experience with category or publisher filtering available, not an unimplemented standalone page.
- **FR-005**: The catalog MUST expose category filtering and broad text search through the existing `category_name` and `search` criteria, and MUST expose exact publisher filtering through an additive `publisher` criterion. The existing `search` behavior remains a case-insensitive match over product name or publisher and is not a substitute for exact publisher selection.
- **FR-006**: Applied catalog filters MUST be represented in navigable URL state, including the exact selected `publisher`, so direct links, reload, back, and forward reproduce the selected state. Unknown or invalid query parameters MUST preserve the unfiltered baseline without failure.
- **FR-007**: Catalog entry points, publisher selectors, and other filter controls MUST be keyboard accessible, have meaningful accessible names, and expose loading, error, empty-results, and retry states accessibly.
- **FR-008**: Account-session UI MUST distinguish validated unauthenticated responses (`401`) from permission denial (`403`) and from unavailable validation/upstream services.
- **FR-009**: The application MUST NOT treat a transient permission or network failure as proof of logout or as proof of administrative authority.
- **FR-010**: Current server-validated permissions MUST remain the basis for showing protected administrative UI; the UI MUST NOT substitute for backend authorization.
- **FR-011**: When a session is confirmed invalid, the application MUST clear only that account session, remove its protected UI, and avoid refresh loops while preserving unrelated anonymous/cart data.
- **FR-012**: `GET /api/v1/orders` MUST return `200` with `{ "orders": [] }` for a valid authenticated user with no purchases.
- **FR-013**: Order history MUST be scoped to the authenticated user, including staff and superusers; it MUST NOT expose other customers’ orders.
- **FR-014**: Genuine upstream or network failures MUST remain explicit, sanitized failures and MUST NOT be converted into a successful empty order list.
- **FR-015**: Existing nonempty order, invoice, checkout, wishlist, and administrative behavior MUST be preserved except for the navigation, session-resilience, and empty-history corrections specified here.
- **FR-016**: The reported order-history `500` and suspected expired-session behavior MUST be investigated locally during implementation; neither cause may be stated as confirmed before reproducible evidence exists.
- **FR-017**: The public catalog MUST provide a complete, unpaginated publisher-facet list containing each eligible nonblank publisher once and a nonnegative count of distinct public catalog games. Counts MUST be global, independent of active catalog filters and pagination, and MUST NOT be derived from a partial product page.
- **FR-018**: Publisher facet identity MUST be the trimmed, stored publisher name because the current catalog has no separate publisher entity or identifier. Identical trimmed values are one option; case variants remain distinct, display spelling is preserved, matching is exact and case-sensitive after trimming the request, and blank publisher values are excluded.
- **FR-019**: The additive BFF publisher-facet and exact-product-publisher interfaces and their corresponding Core GraphQL surfaces MUST be specified and validated before implementation. This planning package does not modify the canonical service contracts or implement those interfaces.

### Key Entities

- **Catalog selection**: The category, exact publisher, and/or broad-search criteria selected by a visitor, represented in the URL and applied to catalog results with AND semantics.
- **Publisher facet**: A complete public list of trimmed nonblank publisher names with global counts of distinct eligible catalog games; it is not derived from current query results or a product page.
- **Account session**: The currently validated or unvalidated authentication state for one account; it is distinct from anonymous/cart data.
- **Purchase history**: The orders owned by the authenticated account, including an empty collection when no orders exist.
- **Permission snapshot**: Server-validated current user privileges used to decide which administrative UI may be shown; never an authorization grant.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All three named catalog entry points reach `/catalogo` in 100% of local navigation checks.
- **SC-002**: Category, exact-publisher, and broad-search selections are reproducible by direct URL, reload, back, and forward in 100% of local navigation checks.
- **SC-003**: A valid account with zero purchases receives and displays `200 { "orders": [] }`; a genuine upstream failure remains a non-success response in all corresponding local checks.
- **SC-004**: In local session checks, `401`, `403`, unavailable validation, and valid superuser authorization each produce their specified distinct UI outcome without stale admin controls or refresh loops.
- **SC-005**: Clearing an account session leaves unrelated anonymous/cart state unchanged in all corresponding local checks.
- **SC-006**: Existing nonempty order and invoice scenarios continue to pass their applicable local regression checks.
- **SC-007**: Every listed publisher count equals the number of distinct eligible public catalog games for that exact publisher, including games with zero inventory when they remain in the public catalog; counts do not change with active filters or pagination.
- **SC-008**: Selecting a listed publisher returns only exact publisher matches, while the independent broad search continues to match product name or publisher; when combined, publisher, category, and search criteria all apply.

## Confirmed Product Decision

- The complete catalog is a dedicated `/catalogo` page. The homepage remains a selection of games.
- Category and publisher navigation are filters in that catalog experience, not new standalone pages. The publisher selector presents the complete publisher list with distinct-game counts and selects an exact publisher value.
- Existing shopping, checkout, wishlist, and administrative behavior is preserved except for the requested corrections.
- The publisher interface is additive and is authorized for planning; implementation and edits to canonical service contracts are not authorized by this planning-only task.

## Assumptions and Evidence Status

- The stated `500 GET /api/v1/orders` for an administrator with no purchases is a **user report**, not a locally reproduced result or established root cause.
- The expired superuser session is a **suspected explanation**, not a validated diagnosis. Visible logout UI or an earlier admin view does not prove a current valid session or current permissions.
- The source shows the existing storefront navigation uses `#catalogo`, `#categorias`, and `#editorial`; this does not establish an `/editorial` route. Runtime symptoms remain unverified.
- Existing BFF order contract uses bearer authentication, returns `200` with an `orders` array, defines `401` and `502` outcomes, and the Core `myOrders` resolver returns an empty list when the authenticated user has no own orders. The source contract and implementation are not modified by this specification.
- The existing catalog contract defines `category_name` as an exact category name, `search` as case-insensitive search over product name or publisher, and `/api/v1/product-categories` as the available category-name source. The requested publisher list/count and exact-publisher behavior are explicit additive planning decisions: draft `GET /api/v1/product-publishers`, an exact `publisher` filter on `GET /api/v1/products`, and corresponding Core GraphQL additions in the feature-local contract drafts. They do not authorize changes to the canonical contracts or service implementation.
- Existing Core catalog records store publisher as a required string with an empty-string default rather than a publisher entity. The draft therefore uses a trimmed publisher name as its stable selector identity, excludes blank values, preserves case, treats case variants as distinct, and counts distinct catalog game IDs. These normalization rules are planning defaults to validate against the current persistence model before implementation.
- The suspected session failure may require reproducing the current-user/permission check locally. Do not request or depend on a screenshot, credential, or non-local environment.
