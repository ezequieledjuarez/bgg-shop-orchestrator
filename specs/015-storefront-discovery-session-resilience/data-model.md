# Data Model: Storefront Discovery and Session Resilience

## Persistence impact

No persistent data model change or migration is proposed. The feature reuses the existing product catalog, user session, and purchase-order data. Catalog selection belongs in client-side route state.

## Existing entities and state

### Catalog selection

| Attribute | Meaning | State source |
|---|---|---|
| `category_name` | Exact category-name filter supported by the catalog endpoint. | URL query and existing BFF query parameter. |
| `search` | Existing broad, case-insensitive product-name or publisher text search. It is not exact publisher selection. | URL query and existing BFF query parameter. |
| `publisher` | Exact publisher selector represented by the trimmed stored publisher value; matching is case-sensitive after trimming the request. | URL query and additive BFF query parameter. |
| Pagination and existing filters | Current page and the existing search, year, player-count, and price criteria. | Existing catalog URL/request state as adopted by the feature. |

Publisher, category, and broad search criteria combine with AND semantics. Unknown or invalid filter inputs fall back to the unfiltered catalog rather than selecting a different criterion. Valid but unknown publisher values produce an empty product result. No standalone publisher entity or database migration is introduced.

### Publisher facet

| Attribute | Meaning |
|---|---|
| `publisher` | Stable identity and display name: the stored publisher string with surrounding whitespace trimmed. Exact duplicate values after trimming collapse; case variants remain distinct. |
| `product_count` | Nonnegative count of distinct eligible public catalog game IDs (`bggId`) assigned to that publisher, not inventory units, SKUs, or rows from a paginated response. |
| Eligibility | Same rows the existing public `products` query exposes, independent of active search, category, other filters, or pagination. Public catalog products with zero inventory remain counted. |
| Ordering | Case-insensitive ascending publisher name, with exact spelling as a deterministic tie-breaker. |
| Empty values | Null, empty, and whitespace-only publisher names are omitted from facets. A publisher with no eligible games is not listed. |
| Availability | Full list, without pagination or client-side truncation. Invalid/unavailable Core responses become an explicit sanitized BFF failure; stale counts are not returned as success. |

This design uses the existing required publisher string field and introduces no publisher entity. The exact string and case behavior should be confirmed against the canonical persistence model before implementation.

### Account session and permission snapshot

| State | Meaning | Required interpretation |
|---|---|---|
| Unresolved | Session or current-user validation is pending. | Do not render protected admin controls based on stale flags. |
| Authenticated | Server has validated a current user/session. | Display account state appropriate to the verified result. |
| Unauthenticated | Server confirmed missing, invalid, expired, or inactive identity (`401`). | Clear only this account session and remove its protected UI. |
| Permission denied | A valid request was denied (`403`). | Deny that operation; do not infer logout from the denial alone. |
| Unavailable | Current-user or upstream validation failed (`502`/network error). | Keep authority unresolved, withhold admin UI, and show safe retry/error feedback. |

The permission snapshot is a presentation hint, not an authorization grant. Backend authorization remains authoritative. Clearing account state must not delete unrelated anonymous cart data. Reuse the current session storage/event conventions; do not introduce a new token type or refresh protocol.

### Purchase history

| Attribute | Meaning | Owner |
|---|---|---|
| Authenticated user identity | Owner used to select visible orders. | Existing Core authentication context. |
| `orders` | The authenticated user’s ordered purchase list; empty list is valid. | Existing Core `myOrders` resolver and BFF order response. |
| Load outcome | Success, empty success, authentication failure, or explicit service failure. | Existing BFF response and frontend order screen. |

Staff/superuser status does not widen order ownership. Existing order and invoice entity fields remain unchanged.
