# Storefront Navigation and Session Behavior

This document defines the Frontend-facing behavior for the feature. The authoritative REST and GraphQL interfaces are [the BFF OpenAPI contract](../../../bgg-shop-bff/specs/openapi.yaml) and [the Core SDL](../../../bgg-shop-core/specs/schema.graphql). The feature-local [REST reference](bff-openapi.yaml) and [GraphQL delta](core-catalog-publishers.graphql) summarize the additions for traceability.

## Routes and entry points

| Entry | Destination |
|---|---|
| Main “Catálogo” link | `/catalogo` |
| “Ver todo” | `/catalogo` |
| “Explorar catálogo” | `/catalogo` |
| “Categorías” | `/catalogo` with category-filter access |
| “Editoriales” | `/catalogo` with exact publisher selector access |
| Homepage logo/home link | Existing homepage selected-games experience |

`/catalogo` is the canonical full-catalog route. The homepage retains its selected-games section. Category and publisher navigation are filters, not separate category/editorial pages. No `/editorial` route is implied.

## URL filter state

- `category_name` carries an exact category name from `GET /api/v1/product-categories`.
- `search` carries broad text sent to existing `GET /api/v1/products?search=...`; the BFF search remains case-insensitive over both product name and publisher.
- `publisher` carries the exact selected publisher value sent to additive `GET /api/v1/products?publisher=...`. Matching is exact and case-sensitive after trimming surrounding whitespace; it cannot match a publisher name merely appearing in a product title.
- The publisher selector is populated by the additive `GET /api/v1/product-publishers` facet list. Each item has `publisher` and `product_count`; the full list is unpaginated and counts distinct eligible public catalog games. Counts are global across search, category, other filters, and pages. Publisher, category, and broad search criteria combine with AND semantics.
- The facet identity is the trimmed stored publisher string, because there is no separate publisher entity/ID in the existing model. Exact duplicates after trimming are grouped; case variants remain distinct and display spelling is preserved. Blank publisher strings are omitted. Counts include products with zero inventory if they remain in the public catalog.
- Existing supported catalog parameters remain governed by the BFF contract. Unknown or invalid query parameters do not cause failure or silently select a different filter; the unfiltered catalog is the fallback.
- Direct navigation, reload, back, and forward restore the selected filter state and matching results. Clearing filters returns to the unfiltered catalog.
- Publisher list failure is distinct from an empty successful list. The UI must not derive counts from the current product page or present stale counts as current success; it offers a safe retry/error state.

## Link and accessibility behavior

- Use native links for navigation. Each link has a meaningful accessible name and visible keyboard focus.
- Category and publisher controls are labelled and keyboard operable. Publisher choices expose both the publisher name and game count accessibly.
- Loading, empty results, failure, and retry states are distinguishable and announced through appropriate status/alert semantics.
- Keep existing homepage fragment bookmarks usable, including `#catalogo`, `#categorias`, and `#editorial`, even though the primary discovery links now navigate to `/catalogo`.

## Session and role presentation

| Result | Frontend behavior |
|---|---|
| Current user validated | Show account/admin navigation only according to the current server response and established admin rules. |
| `401` confirmed unauthenticated | Clear only that account session; remove protected UI; offer sign-in recovery. |
| `403` operation denied | Deny that operation and show safe feedback; do not infer logout from this response alone. |
| `502` or network unavailable | Keep role unresolved, withhold admin controls, and offer safe retry/error feedback without claiming logout or permission. |

Role visibility is a navigation hint only. Backend checks remain mandatory. A successful current superuser check must preserve existing superuser access. Session cleanup does not erase unrelated anonymous/cart data and must not trigger refresh loops.

## Order-history outcomes

- A valid authenticated user with no own orders receives `200 { "orders": [] }` and sees the existing empty state.
- Nonempty own orders and invoice behavior remain unchanged; staff/superusers see only their own orders.
- Invalid authentication and genuine upstream/network errors remain explicit distinct failures. An actual failure is never converted to an empty success.
