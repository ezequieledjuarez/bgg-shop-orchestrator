# Feature Specification: Admin Navigation and Discoverability

**Feature Branch**: `014-admin-navigation`<br>
**Created**: 2026-11-09<br>
**Status**: Implemented; local unit, browser, and isolated Frontend→BFF→Core verification passed for the scoped feature slice. See [verification ledger](quickstart.md).<br>
**Input**: Administrators need an obvious entry to existing operational tasks, including creating games/products, managing coupons, and managing personnel privileges as Superadmins. Coupon scope means administrator creation and management, not buyer redemption.

**Additional user-authorized scope**: Style all existing admin screens with visual discretion, extending the current storefront identity. The implementation and local verification are complete for the scoped feature slice; see [quickstart.md](quickstart.md). No exact mockup or pixel design has been approved or was required; ask only when a genuine unresolved decision needs user guidance.

## User Scenarios & Testing

### User Story 1 — Find the administration area (Priority: P1)

An active staff member or Superadmin can discover the existing administration area from the storefront and can navigate among existing operational modules without returning to a special root-only menu.

**Why this priority**: The required tasks already exist, but discovery is poor: the storefront has no administration entry and the admin links appear only at `/admin`.

**Independent Test**: Sign in as an active staff user and as an ordinary buyer. Verify the staff user can find the administration entry and the buyer cannot. Visit each existing admin route directly and verify the shared navigation remains available to eligible staff.

**Acceptance Scenarios**:

1. **Given** an active staff user, **When** the storefront header finishes resolving the current user's role, **Then** it exposes an accessible “Administración” link to `/admin`.
2. **Given** an ordinary buyer or signed-out visitor, **When** the storefront renders, **Then** no “Administración” entry or admin-only link is shown.
3. **Given** an authorized staff user opens `/admin/products`, `/admin/coupons`, or another existing operational admin route, **When** the page loads, **Then** the common administration navigation is present and the current panel is not replaced or duplicated.

### User Story 2 — Reach existing product and coupon tasks (Priority: P1)

An active staff user can discover the existing product creation and administrator coupon management workflows from the common administration navigation.

**Why this priority**: Creating games and managing coupons are explicit admin tasks. The current forms and endpoints exist; the missing capability is a consistent entry point.

**Independent Test**: Follow the product and coupon links from the shared admin navigation. Verify product creation opens the existing `/admin/products/new` flow and coupon administration opens `/admin/coupons` and its existing create/edit paths.

**Acceptance Scenarios**:

1. **Given** an active staff user, **When** they select “Productos” and then the existing create action, **Then** the existing product form opens at `/admin/products/new`.
2. **Given** an active staff user, **When** they select “Cupones”, **Then** they reach the existing coupon listing and can use its existing create/edit/activate/deactivate flows.
3. **Given** a buyer-facing coupon preview or checkout, **When** this feature is used, **Then** buyer coupon redemption behavior is unchanged and is not part of this feature.

### User Story 3 — Keep privilege administration Superadmin-only (Priority: P1)

An active Superadmin can discover the existing user and privilege administration panel; staff without Superadmin authority cannot discover or access it through the Frontend.

**Why this priority**: Privilege assignment is security-sensitive and already governed by Feature 012.

**Independent Test**: Test an active Superadmin with `is_staff=true` and another with `is_staff=false`; both can see the existing user-management link. Test staff-only and ordinary accounts; neither sees the link nor receives user-management panel data.

**Acceptance Scenarios**:

1. **Given** an active user with `is_superuser=true`, including one with `is_staff=false`, **When** the current role snapshot resolves, **Then** the shared navigation exposes the existing “Usuarios” route.
2. **Given** an active staff-only user, **When** the shared navigation resolves, **Then** operational modules remain available but “Usuarios” is absent.
3. **Given** a staff-only user directly opens `/admin/users`, **When** the role check completes, **Then** the Frontend displays a generic forbidden state without rendering personnel data or issuing a user-list request; backend authorization remains independently enforced.

### User Story 4 — Fail closed during role and session changes (Priority: P1)

The Frontend does not use token presence or stale browser-stored flags as proof of role. It waits for the current role response before displaying administration links or protected panel content.

**Why this priority**: A token only establishes a possible session; it does not prove a current administrative role. Revocation and direct navigation must not reveal protected UI.

**Independent Test**: Delay or fail the proposed role request, visit admin paths directly, change or remove the local session, and revoke an admin role. Verify that protected UI is withheld until a successful current response and disappears after a session change or authorization denial.

**Acceptance Scenarios**:

1. **Given** the current-user role request is pending, **When** the storefront or an admin route renders, **Then** no administrative links or protected panel data flash before the role decision.
2. **Given** the role request fails, returns an invalid shape, or reports an unauthenticated/inactive account, **When** the request settles, **Then** the Frontend hides admin links and data and presents a safe retry or generic access/error state.
3. **Given** the user logs out, changes session, or receives an authorization denial after role revocation, **When** the session state changes, **Then** the in-memory role snapshot is invalidated and protected UI is removed.
4. **Given** any Frontend link is visible, **When** an API operation is attempted, **Then** the owning backend remains the authorization authority; UI visibility never grants access.

### User Story 5 — Use administration accessibly across screen sizes (Priority: P2)

Staff and Superadmins can navigate the administration area using keyboard and assistive technology on desktop and mobile layouts.

**Independent Test**: Use keyboard-only navigation at desktop and mobile viewport sizes; verify landmarks, names, focus visibility, link order, and that navigation does not require hover.

**Acceptance Scenarios**:

1. **Given** an eligible user, **When** they use keyboard navigation, **Then** the storefront entry and each permitted admin destination have a visible focus indicator and meaningful accessible name.
2. **Given** a narrow viewport, **When** the admin shell is rendered, **Then** all permitted destinations remain reachable without horizontal clipping or inaccessible hover-only controls.

### User Story 6 — Use consistently styled administration screens (Priority: P2)

Staff and Superadmins can work in a coherent, readable administration area whose existing screens feel like part of the storefront, not unrelated tools.

**Why this priority**: The user explicitly requested admin screen styling, not just navigation. All eight existing modules need coverage while retaining their current workflows and Spanish UI labels.

**Independent Test**: With local fixtures or authorized local accounts, inspect products (list, create/edit, inventory), promotions, coupons, gift cards, audit, sales, reviews, and users at 1280×720, 768×1024, 375×812, and 320×720. Check shared presentation, existing states, keyboard operation, contrast, long content, and locally scrolling tables without changing access rules.

**Acceptance Scenarios**:

1. **Given** an authorized user visits any existing admin destination, including direct routes, **When** its content renders, **Then** the common admin layout and consistent colors, typography, spacing, headings, cards, buttons, forms, and tables/lists remain recognizable across routes.
2. **Given** an existing confirmation, success/validation feedback, loading, error, or empty state is shown, **When** the user reads or operates it, **Then** it is legible, consistently styled, and identified by text/semantics rather than color alone; its action semantics remain unchanged.
3. **Given** any supported test viewport or keyboard-only input, **When** the user reaches filters, row actions, forms, or existing confirmations, **Then** labels and visible unobscured focus remain available and no action is clipped; wide data tables may scroll within a labelled local container, not the entire viewport.
4. **Given** the proposed storefront-derived palette is applied, **When** contrast is measured against actual adjacent backgrounds, **Then** normal text reaches 4.5:1, large text reaches 3:1, and UI boundaries, state indicators, and focus indicators needed to identify controls reach 3:1.

## Requirements

### Functional Requirements

- **FR-001**: The storefront MUST provide an “Administración” entry only after a current authenticated role response confirms an active staff or Superadmin account.
- **FR-002**: The Frontend MUST NOT derive staff or Superadmin access from access-token presence, operation-key data, or stale local/session storage flags.
- **FR-003**: The common admin navigation MUST be available on the existing operational admin routes, including direct route loads.
- **FR-004**: The existing product creation flow MUST remain reachable at `/admin/products/new`; this feature MUST NOT implement a second product-creation flow.
- **FR-005**: The existing administrator coupon listing and management flow MUST remain reachable under `/admin/coupons`; buyer coupon redemption is out of scope.
- **FR-006**: Operational modules MUST remain available to active staff and Superadmins under their existing authorization rules. This feature MUST NOT narrow broad staff access or create a per-module role matrix.
- **FR-007**: The existing user/privilege management route MUST be discoverable only by active Superadmins, whether or not `is_staff` is true. Staff-only users MUST NOT receive user-list data through the Frontend.
- **FR-008**: Role-loading, malformed-response, unauthenticated, denied, and upstream-error states MUST fail closed without flashing protected links or panel data.
- **FR-009**: Logout/session changes and observed authorization denials MUST invalidate the in-memory role snapshot and remove now-protected navigation/content.
- **FR-010**: Frontend navigation MUST remain subordinate to backend authorization. This feature MUST NOT change backend authorization policy for existing operations.
- **FR-011**: The approved design for the current-user REST response MUST be minimal, non-cacheable, bearer-authenticated, derived from current Core user state, and must not expose credentials or unrelated personal data.
- **FR-012**: Public errors MUST NOT reveal upstream responses, exceptions, stack traces, internal URLs, or credentials.
- **FR-013**: Admin navigation MUST use semantic navigation landmarks, accessible names, visible keyboard focus, and a layout that remains usable at narrow viewports.
- **FR-014**: All eight existing modules—products, promotions, coupons, gift cards, audit, sales, reviews, and users—MUST receive coherent screen styling, including their existing list, create/edit, inventory, filter, pagination, summary, chart, and privilege-editor surfaces where present. Existing routes, role policy, CRUD semantics, and Spanish UI labels MUST be preserved.
- **FR-015**: Admin presentation MUST extend current storefront colors, typography, spacing, surface/card treatment, and button/form patterns through narrowly scoped shared CSS and existing panel classes. No new UI dependency, font dependency, or design-system architecture is required. Headings, cards, buttons, labelled inputs, tables/lists, existing confirmations, and feedback/loading/error/empty states MUST follow that common treatment without changing their behavior.
- **FR-016**: A common admin layout MUST persist across existing admin routes and direct loads. At 1280×720, 768×1024, 375×812, and 320×720, navigation, content, and actions MUST remain usable without page-wide horizontal overflow or clipped actions; wide data tables MAY scroll in a keyboard-reachable, accessibly labelled local container.
- **FR-017**: Styled controls MUST retain semantic labels, logical keyboard order, visible unobscured focus, and status/error announcements. Information MUST NOT rely on color alone. WCAG AA contrast MUST meet 4.5:1 for normal text, 3:1 for large text (at least 24 CSS px regular or approximately 18.7 CSS px bold), and 3:1 for required non-text UI boundaries/state/focus indicators against adjacent colors.

### Key Entities

- **Current User Capability Snapshot**: An ephemeral projection of the active user's `is_staff` and `is_superuser` flags for navigation visibility; it is not persisted.
- **Administrative Destination**: An existing admin route and panel. This feature changes its discoverability and visual presentation, not its domain behavior or API authorization.
- **Administrative Role**: Existing `is_staff` and `is_superuser` flags, which remain independent as defined by Feature 012.

## Assumptions

- “Games” means existing product/catalog administration, including the current product creation form.
- “Coupon management” means administrator-side creation and management, not buyer redemption or checkout.
- Existing operations are reused. The presence of an entry-point gap is not evidence that corresponding CRUD is missing.
- The approved design was promoted by T006 to the canonical BFF OpenAPI and implemented by T007–T008. The fragment at `contracts/admin-session.openapi.yaml` remains a non-canonical design copy; see [verification evidence](quickstart.md).
- Core `Query.me` and `User` already provide `isActive`, `isStaff`, and `isSuperuser`; no Core contract or source change was needed or made.
- Visual discretion is authorized. The implementation uses storefront-derived warm neutral surfaces, dark readable text, terracotta accents, and existing typography/patterns; these are not user-approved exact pixels. Local visual checks and their limits are recorded in [quickstart.md](quickstart.md).
- Styling adds no backend contract or persistence requirement. T005 records design approval; canonical promotion is recorded by T006. Its historical approval was not itself a runtime implementation.

## Clarifications

### Session 2026-11-09

- **Q**: Approve the proposed `GET /api/v1/auth/me` design: return only `is_staff` and `is_superuser` from current Core state for an active bearer identity, disable caching, sanitize errors, and continue authorizing every operation in its owning backend?
- **A**: Approved as a design. The response is `200` with only the two role flags; missing, invalid, or inactive bearer identity maps to `401`; failed Core identity resolution maps to sanitized `502`; all outcomes use `Cache-Control: no-store`; operation-key-only access is not accepted. T006 promoted this design to the canonical BFF OpenAPI, and T007–T015 implemented the contract-backed endpoint and Frontend behavior/presentation. The approved fragment in `contracts/admin-session.openapi.yaml` remains a non-canonical design copy. Scoped local verification, including a live isolated service-path check, is recorded in [quickstart.md](quickstart.md); it does not claim full admin CRUD or full Core migration validation.

## Out of Scope

- Buyer coupon redemption, checkout, or promotion behavior.
- New product, coupon, gift-card, promotion, sales, audit, review, or user CRUD.
- A new role model, per-module permissions, account creation/invitations, migrations, or persistence.
- Changes to existing Core/BFF authorization policies or Feature 012 privilege rules.
- Replacement domain workflows, new admin modules, a new UI library/design-system architecture, or a storefront redesign. Styling existing admin screens is in scope.
- Staging, production, CI, or remote validation.

## Success Criteria

- **SC-001**: Active staff and Superadmins can reach `/admin` from the storefront in one activation of the visible “Administración” link.
- **SC-002**: All existing operational admin destinations remain reachable from the shared navigation without changing their routes or panel behavior.
- **SC-003**: Staff-only accounts see every existing operational destination except “Usuarios”; Superadmins, including `is_staff=false`, see “Usuarios”.
- **SC-004**: Buyers and signed-out users never see admin links; unauthorized direct navigation never renders protected panel data.
- **SC-005**: Pending, failed, malformed, or denied role resolution displays zero privileged navigation links and zero protected panel data.
- **SC-006**: Session changes and an observed authorization denial remove the stale in-memory capability snapshot before rendering protected navigation again.
- **SC-007**: Automated local checks cover role combinations, loading/failure, direct routes, and existing product/coupon destinations; no backend policy change is required.
- **SC-008**: Keyboard and narrow-viewport checks confirm all permitted links remain operable and accessible.
- **SC-009**: A local visual checklist covers all eight modules and each applicable surface/state listed in FR-014–FR-015, with consistent shared styles for headings, cards, controls, tables/lists, confirmations, and feedback; no module is omitted.
- **SC-010**: At all four FR-016 viewports, every existing permitted action is reachable with no clipped controls or viewport-wide horizontal overflow. Any wide table scroll is confined to its labelled local container; shared layout remains present after navigation and direct loads.
- **SC-011**: Keyboard/label checks and measured contrast evidence meet every FR-017 threshold across shared controls and module-specific states. Record foreground/background pairs and ratios; no unresolved failure may be called verified.
- **SC-012**: Existing route, CRUD, Spanish-label, role, and storefront regression checks pass after styling, with zero new UI dependencies, backend contract changes, or persistence changes attributable to styling.
