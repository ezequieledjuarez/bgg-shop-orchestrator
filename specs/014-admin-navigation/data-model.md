# Data Model: Admin Navigation and Discoverability

This feature introduces no database entity, migration, persisted role, or new authorization model. The Frontend retains only an in-memory projection of existing account flags, loaded from implemented `GET /api/v1/auth/me`. Its canonical contract is [BFF OpenAPI](../../bgg-shop-bff/specs/openapi.yaml); [the approved design fragment](contracts/admin-session.openapi.yaml) is a non-canonical copy. See [verification evidence and scope](quickstart.md).

## Presentation-only Extension

US6 / FR-014–FR-017 style the existing products, promotions, coupons, gift cards, audit, sales, reviews, and users screens and their common layout. Colors, typography, spacing, cards, controls, tables/lists, existing confirmations and feedback/loading/error/empty states are presentation concerns, not new domain entities or persisted preferences. Reuse storefront patterns and existing panel classes; no backend payload, API contract, database, or browser-storage change is required for styling.

Existing routes, Spanish UI labels, operations, role policy, and data flows below remain unchanged. T013–T015 delivered the presentation without bypassing canonical-contract promotion or protected-navigation dependencies. Common styled-shell integration passed T011/T012; see [verification evidence](quickstart.md).

## Existing Account and Privileges

**Existing source**: Core `User` in `bgg-shop-core/specs/schema.graphql:554-561` and the existing authenticated account.

| Existing field | Type | Use in this feature |
|---|---|---|
| `isActive` | Boolean | An inactive account cannot obtain operational admin UI access. The BFF current-user endpoint maps inactive bearer identity to `401`. |
| `isStaff` / REST `is_staff` | Boolean | Grants discoverability of existing operational modules under existing backend policy. |
| `isSuperuser` / REST `is_superuser` | Boolean | Grants operational module discoverability and the existing user/privilege management destination, regardless of `isStaff`. |

These are independent flags. This feature does not coerce, combine, backfill, or persist role values. The implemented endpoint maps an inactive bearer identity to `401`.

## Current-User Capability Snapshot — Implemented Contract

**Persistence**: None. Retain only in Frontend memory for the active page/session; clear it when the session changes, the user logs out, or an authorization denial is observed.

| Proposed property | Type | Meaning |
|---|---|---|
| `is_staff` | Boolean | Current server-side operational staff flag. |
| `is_superuser` | Boolean | Current server-side Superadmin flag. |

`GET /api/v1/auth/me` requires an active bearer identity and uses the existing Core `Query.me` projection. A successful response represents an active identity and returns only `is_staff` and `is_superuser`. Missing, invalid, or inactive identity maps to sanitized `401`; failed Core identity resolution maps to sanitized `502`. Every outcome uses `Cache-Control: no-store`; operation-key-only access is rejected. The response does not include credentials, tokens, unrelated personal data, or user-list data. T006 promoted and validated the contract in canonical BFF OpenAPI; focused and isolated integration evidence is in [quickstart.md](quickstart.md).

### Navigation visibility mapping

| Current server result | Storefront administration entry | Existing operational links | Existing “Usuarios” link |
|---|---:|---:|---:|
| Active `is_staff=true`, any `is_superuser` | Yes | Yes, existing policy | Only if `is_superuser=true` |
| Active `is_staff=false`, `is_superuser=true` | Yes | Yes, existing policy | Yes |
| Active `is_staff=false`, `is_superuser=false` | No | No | No |
| Unauthenticated or inactive | No | No | No |
| Pending, malformed, or failed capability response | No | No | No |

The UI mapping does not authorize requests. Core/BFF authorization remains authoritative, and existing feature/API security rules are unchanged.

## Existing Administrative Destinations

These routes and modules already exist and are reused:

| Destination | Existing route | Existing behavior reused |
|---|---|---|
| Products | `/admin/products` | Product listing and existing create/edit flows. |
| Create product/game | `/admin/products/new` | Existing product form; no second form is proposed. |
| Coupons | `/admin/coupons` | Administrator listing and create/edit/activate/deactivate paths. Buyer coupon redemption is unrelated. |
| Gift cards | `/admin/gift-cards` | Existing operational module. |
| Promotions | `/admin/promotions` | Existing operational module. |
| Audit history | `/admin/audit` | Existing operational module. |
| Sales | `/admin/sales` | Existing operational module. |
| Reviews | `/admin/reviews` | Existing operational module. |
| User privileges | `/admin/users` | Existing Feature 012 panel; Superadmin-only discoverability and existing server authorization. |

## Data Flow

1. The Frontend requests the BFF current-user capability endpoint with the current bearer token.
2. The BFF resolves the current Core principal through existing `Query.me`, projects only role flags, and returns a non-cacheable response.
3. The Frontend stores the result in memory, renders only links allowed by the mapping, and clears it on session change or observed denial.
4. Existing panels continue calling their existing APIs. Every backend independently enforces its existing authorization policy.

No user search/list response is used to infer the signed-in user's role. No capability snapshot is written to browser storage.
