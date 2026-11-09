# Research: Admin Navigation and Discoverability

This document records the pre-implementation research baseline and the resulting implementation decisions. The endpoint design was promoted to the canonical BFF contract and implemented; this feature made no Core contract/source changes. The approved fragment remains a non-canonical design copy. Current implementation and verification evidence are in [quickstart.md](quickstart.md).

## Decision 1 — Reuse existing administrative workflows

- **Decision**: The feature adds discoverability, shared navigation/layout, and consistent styling across all eight existing admin modules; it does not implement replacement CRUD.
- **Rationale**: `bgg-shop-frontend/src/admin/AdminRouter.tsx:1-27` already routes products, coupons, users, and other operational modules. The existing product form handles `/admin/products/new`; the coupon panel provides administrator listing/create/edit/deactivate flows; the user panel manages the existing privilege flags. The storefront header in `src/App.tsx:708-724` has no admin entry. The root-only administration links are in `AdminRouter.tsx:30-34`.
- **Alternatives considered**: Add new create-game, coupon, or role-management screens. Rejected because they duplicate existing workflows and are not needed to solve the discovery gap.

## Decision 2 — Use current server role data, not token presence or cached flags

- **Decision**: The Frontend needs a current server response before displaying admin navigation or protected panel content. The approved design response contains only `is_staff` and `is_superuser`.
- **Rationale**: `src/App.tsx:74-80, 889` currently uses access-token presence to gate admin routes, while Core's canonical SDL already exposes `Query.me` and `User.isActive`, `User.isStaff`, and `User.isSuperuser` (`bgg-shop-core/specs/schema.graphql:427-429, 554-561`). BFF login's `AuthUser` includes `is_active` but not staff/superuser flags (`bgg-shop-bff/specs/openapi.yaml:3764-3785`); the BFF has an existing current-principal Core query pattern in `src/proxy.py:1187-1218`.
- **Alternatives considered**: Read role flags from token presence or browser storage; rejected because current authorization can change and these are not role claims. Query Core directly from the browser; rejected because BFF OpenAPI is the Frontend REST contract boundary. Expand login response; rejected as the primary mechanism because a login-time role snapshot can become stale and would broaden the login projection.

## Decision 3 — Approve one minimal additive BFF capability endpoint design

- **Decision**: The user approved the design for `GET /api/v1/auth/me` on 2026-11-09: bearer authenticated, returning only `is_staff` and `is_superuser` with `Cache-Control: no-store`. Reuse Core `Query.me`; do not add a Core SDL field or endpoint.
- **Rationale**: This gives the Frontend a role-aware response at its existing BFF boundary without adding persistence or duplicate identity semantics. The endpoint must read current account state and be independent of operation-key-only sessions.
- **Alternatives considered**: Add a Core query; rejected because the required active/staff/superuser fields already exist. Add endpoint-specific role data to every login/logout response; rejected as more coupled and potentially stale. Omit a current-user API and display admin links to every authenticated user; rejected because role-specific discoverability is required.
- **Contract status**: **Canonical and implemented.** T006 promoted the approved design to `bgg-shop-bff/specs/openapi.yaml`; T007/T008 added tests and implementation. The endpoint uses active bearer identity, returns only the two role booleans, maps missing/invalid/inactive identities to `401`, sanitizes Core-resolution failures as `502`, applies `Cache-Control: no-store` to every outcome, rejects operation-key-only access, and leaves each operation's backend authorization authoritative. `contracts/admin-session.openapi.yaml` is retained only as a non-canonical design copy. See [quickstart.md](quickstart.md) for observed checks and their scope.

## Decision 4 — Keep existing authorization policy unchanged

- **Decision**: Staff and Superadmins retain existing broad operational access. The “Usuarios” destination is visible only to Superadmins; this Frontend visibility rule does not replace backend enforcement.
- **Rationale**: Feature 012 explicitly establishes independent `is_staff` and `is_superuser` flags and reserves personnel/privilege management for an active Superadmin, including a Superadmin with `is_staff=false`. Existing product/coupon and other operational modules are already established and must not be narrowed in an entry-point feature.
- **Alternatives considered**: Restrict all admin operations to Superadmins or define per-module roles; rejected because neither is needed or authorized.

## Decision 5 — Fail closed and clear transient role state

- **Decision**: Keep role data in memory only. Do not render administration links or protected panels until successful role resolution. Invalidate the snapshot on logout/session changes and observed authorization denial; re-resolve on admin route entry.
- **Rationale**: The current app already publishes a session-change event (`bgg-shop-frontend/src/auth/session.ts`). Admin route and role state must not outlive the session or server denial.
- **Alternatives considered**: Persist role flags in local/session storage or optimistically render from a token; rejected because stale privilege state may expose navigation or protected UI.

## Decision 6 — Extend storefront identity to every admin screen

- **User authorization**: The user requested admin screen styling and granted visual discretion, with questions if real uncertainty arises. The implementation uses scoped CSS and existing UI patterns; no exact mockup or new design-system dependency was introduced.
- **Proposed design**: Warm neutral backgrounds, dark readable text, terracotta accents, existing body/heading typography, rounded card surfaces, and a common spacing/control treatment extending the storefront. Reuse current values/patterns with scoped shared admin CSS; adjust contrast where necessary. Do not add a UI/font dependency, token framework, or design-system architecture.
- **Evidence**: `bgg-shop-frontend/src/index.css` declares DM Sans/Playfair and a warm base with visible focus; `src/App.css` also declares Inter/system and Georgia headings, neutral cards, terracotta buttons, `purchase-form` and focus patterns. These are existing declarations, not proof of a single computed token set or contrast compliance; T013 must inspect the cascade.
- **All-module inventory**:

| Existing module and source under `bgg-shop-frontend/src/admin/` | Future styling coverage |
|---|---|
| `products/ProductsList.tsx`, `ProductForm.tsx`, `StockAdjustmentForm.tsx` | Filter/table/pagination, product create/edit, inventory inputs and recovery/status feedback. |
| `promotions/PromotionsPanel.tsx`, `PromotionForm.tsx` | Listing, create/edit, price preview, validation/save feedback. |
| `coupons/CouponsPanel.tsx`, `CouponForm.tsx` | Table and existing create/edit/activation controls, field/status messages. |
| `giftcards/GiftCardForm.tsx` | Amount form, generation/loading/error, generated code/copy/result actions. |
| `audit/AuditPanel.tsx` | Filters, table, pagination, retry/loading/error/empty states. |
| `sales/SalesPanel.tsx`, `SalesPanel.css` | Existing panel/header/cards, filters, summaries, locally wrapped tables, revenue chart and no-data/error states. |
| `reviews/ReviewsPanel.tsx` | Queue/list cards, existing moderation actions and status/error/empty states. |
| `users/UserManagementPanel.tsx`, `UserManagementPanel.css` | Existing bounded panel/header, search/list/load-more, privilege editor and save/error states; unchanged Superadmin boundary. |

- **Cross-cutting surfaces**: Shared route layout/navigation, headings, cards, buttons, labelled fields, tables/lists, existing confirmations and feedback/loading/error/empty states wherever present. Preserve current Spanish labels and action semantics; do not invent confirmations or CRUD to fill a checklist.
- **Responsive evidence and choice**: `playwright.config.ts` declares a 1280×720 base viewport and a Desktop Chrome project preset. Future checks explicitly override to 1280×720, 768×1024, 375×812, and 320×720; 320px matches `src/index.css`'s body minimum width. Require no clipped actions/page-wide overflow; wide tables can scroll in labelled keyboard-accessible local containers.
- **Acceptance**: Shared presentation on all eight routes and their subflows, keyboard-visible unobscured focus and labels, non-color status cues, normal-text contrast 4.5:1, large-text contrast 3:1, and required non-text UI contrast 3:1. Record actual pairs/ratios and local visual evidence, not assumed compliance from existing colors.
- **Gates**: T013–T015 completed the presentation work without new API/persistence or Core/BFF tasks. Protected navigation depends on T006–T011; T012's scoped isolated service-path verification is recorded in [quickstart.md](quickstart.md).
- **Alternative rejected**: A new admin UI library or replacement design system would add dependency/architecture cost without solving an authorized domain need.

## Verified planning baseline

The following observations describe the repository before implementation and explain the design decisions; they are not claims about the current runtime.

- `bgg-shop-frontend/src/admin/AdminRouter.tsx:1-27` maps existing product, promotion, coupon, gift-card, audit, sales, review, and user routes. Its local navigation is rendered only by the `/admin` fallback at lines 29-34, not as a shared shell on each panel route.
- `bgg-shop-frontend/src/App.tsx:708-724` renders storefront navigation and account actions without an administration entry. `src/App.tsx:880-889` treats an access token as sufficient to render any `/admin` route.
- Existing administrative components include `src/admin/products/ProductForm.tsx`, `src/admin/coupons/CouponsPanel.tsx`, `src/admin/coupons/CouponForm.tsx`, and `src/admin/users/UserManagementPanel.tsx`.
- BFF's canonical OpenAPI is `bgg-shop-bff/specs/openapi.yaml`; Core's canonical SDL is `bgg-shop-core/specs/schema.graphql`. Frontend generated API types come from `npm run generate:types`.
- Existing local runners are declared by `bgg-shop-frontend/package.json`: Vitest (`npm run test`), build/typecheck (`npm run build`), type generation, and local Playwright (`npm run test:e2e:opkey`). Python services use pytest; focused existing auth and role tests are in their repository `tests/` directories.

## Evidence consulted

- `.agents/ponytail.md` and `.specify/memory/constitution.md`: reuse, minimal change, contract ownership, traceability, security, and sanitized public errors.
- `specs/012-manage-users-permissions/spec.md` and `tasks.md`: staff operational access, Superadmin-only personnel/privilege boundary, independent flags, and no new role model.
- `specs/007-manage-catalog-inventory/tasks.md`: existing catalog administration behavior and cross-service ownership.
- `bgg-shop-frontend/src/App.tsx`, `src/auth/session.ts`, and `src/admin/AdminRouter.tsx`: storefront entry, current token-only route check, session event, route map, and root-only navigation.
- Existing Frontend product, coupon, and user management components and their tests: workflows are already implemented.
- `bgg-shop-bff/specs/openapi.yaml` and `bgg-shop-core/specs/schema.graphql`: canonical contract boundaries and role fields.
- `bgg-shop-bff/src/proxy.py` and `bgg-shop-core/saleor/graphql/api.py`: existing BFF identity query and Core `Query.me` resolver.

The design is grounded in local code and canonical project artifacts. The public [Web Interface Guidelines](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md) were consulted for future semantic controls, focus, forms, feedback, and overflow checks; no private repository content was transmitted. This is a styling plan, not a completed UI compliance audit.
