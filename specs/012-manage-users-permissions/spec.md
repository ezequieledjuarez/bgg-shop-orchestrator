# Feature Specification: Manage Users and Permissions

**Feature Branch**: `012-manage-users-permissions`
**Created**: 2026-11-06
**Status**: Implementation and repository-recorded local checks are complete
per [tasks.md](tasks.md). The additional privilege grant/revoke smoke test is
owner-reported on 2026-11-10; no command or log for that smoke test is recorded.
T013's unrelated broader Core failures remain documented in the task ledger.
**Input**: CU-A04, “Administrar Usuarios y Permisos”: an active Superadmin manages the staff and superuser privileges of existing users so operational access follows the approved authority rules.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Manage privileges for an existing user (Priority: P1)

An active Superadmin finds any existing user and independently grants or removes that user's staff or superuser privilege. Each change applies only to the selected privilege, preserves the other privilege, and takes effect for subsequent authorization checks.

**Why this priority**: Privilege assignment and revocation are the purpose of CU-A04; account creation and role-management authority must remain separate.

**Independent Test**: As an active Superadmin, including one with `is_staff=false`, assign and remove each privilege on existing users, verify the untouched flag is preserved, and verify authorization reflects the saved state. Attempt to remove the last active superuser's privilege and race concurrent revocations; neither may leave the system without an active superuser or partially apply a denied change.

**Acceptance Scenarios**:

1. **Given** an active Superadmin and any existing user, including an existing Superadmin, **When** the Superadmin grants or removes only `is_staff`, **Then** that flag changes and `is_superuser` remains unchanged.
2. **Given** an active Superadmin and any existing user, including an existing Superadmin, **When** the Superadmin grants or removes only `is_superuser`, **Then** that flag changes and `is_staff` remains unchanged; granting superuser does not automatically grant staff.
3. **Given** a target active Superadmin and at least one other active Superadmin, **When** the acting Superadmin removes the target's superuser privilege, including when acting on their own account, **Then** the change succeeds and another active Superadmin remains.
4. **Given** removing a target's superuser privilege would leave no active Superadmin, **When** the change is submitted, **Then** it is denied with no partial updates.
5. **Given** concurrent requests that could remove the last active Superadmin privileges, **When** both requests are processed, **Then** the invariant is preserved and any denied request makes no partial update.
6. **Given** a requested change fails, **When** the result is shown, **Then** the prior saved privileges remain displayed and the failure is clear.

### User Story 2 - Use operational modules with staff access (Priority: P1)

An active staff user can use the same administrative operational modules as a superuser, except that personnel listing/selection and assigning or removing staff/superuser privileges remain Superadmin-only. Existing broad operational staff access is intentional and is not narrowed by CU-A04.

**Why this priority**: CU-A04 adds a protected privilege-management capability without disrupting the existing staff operational experience.

**Independent Test**: Verify staff can perform the same applicable operational actions as a superuser, but cannot access personnel listing/selection or assign/remove privileges. Confirm the UI and backend both enforce the role-management boundary.

**Acceptance Scenarios**:

1. **Given** an active staff user, **When** they use an administrative operational module that a Superadmin can use, **Then** they retain the same operational access.
2. **Given** an active staff-only user, **When** they request personnel listing/selection or attempt to assign/remove either privilege, **Then** the request is denied and no personnel data or configuration is changed.
3. **Given** a privilege change is saved, **When** the affected user performs a subsequent authorized operation in an already active session, **Then** the operation reflects the saved privilege state without relying solely on UI or cached token flags.

### User Story 3 - Protect privilege administration (Priority: P1)

Privilege-management data and actions are available only to an authenticated, active Superadmin, regardless of what the interface displays.

**Why this priority**: Unauthorized access to personnel selection or privilege changes could expose user information or grant administrative authority.

**Independent Test**: Attempt listing/selection and privilege changes as unauthenticated, inactive, active staff-only, and operation-key-only callers; verify denial without protected data or state changes. Verify an active Superadmin with `is_staff=false` is allowed.

**Acceptance Scenarios**:

1. **Given** an unauthenticated, inactive, staff-only, or operation-key-only caller, **When** they request privilege-management data or submit a privilege change, **Then** the backend denies the request without revealing protected data or applying a change.
2. **Given** an authenticated active user with `is_superuser=true` and `is_staff=false`, **When** they request privilege-management data or submit an otherwise valid privilege change, **Then** they are not denied solely because `is_staff` is false.
3. **Given** a public or buyer-facing view, **When** it is accessed, **Then** it does not expose privilege-management data or credentials.

### Edge Cases

- The acting user is unauthenticated, inactive, staff-only, or an active Superadmin with `is_staff=false`; only the last is authorized.
- The target no longer exists or its active/privilege state changes before the requested update is applied; the system must not claim an unsaved or stale change succeeded.
- The target is an existing Superadmin, or the actor is changing their own privileges; apply the same independent-flag rules and last-active-superuser invariant.
- Concurrent superuser revocations race; at least one active superuser must remain, and a denied operation must not partially change either privilege.
- A privilege change narrows access while the target has an active session; subsequent authorization checks must use the saved privileges, not only UI or cached token state.
- Staff attempts to access the privilege-administration listing or selection; do not return user-selection data even though staff retains operational-module access.
- Public or buyer-facing callers request credentials or privilege data; none may be returned.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Only an authenticated, active user with `is_superuser=true` MUST be authorized to list/select users for privilege administration or assign/remove privileges. `is_staff=true` MUST NOT be additionally required.
- **FR-002**: The backend MUST deny unauthenticated, inactive, staff-only (`is_staff=true`, `is_superuser=false`), and operation-key-only callers for privilege-management listing/selection and privilege changes. Denial MUST NOT disclose protected user data or change privilege state.
- **FR-003**: An authorized Superadmin MUST be able to locate and select any existing user, including users who already have staff or superuser privileges. Listings MUST NOT return credentials or authentication secrets. Staff-only users MUST NOT receive or access this listing/selection data.
- **FR-004**: A person creates their own account through the existing ordinary registration flow, the same as a buyer. CU-A04 MUST NOT introduce Superadmin-created employee accounts, invitations, temporary credentials, onboarding, or first-use credential steps. Account registration itself MUST NOT assign staff or superuser privileges.
- **FR-005**: An authorized Superadmin MUST be able to independently grant or remove the existing staff and superuser privileges on any existing user, including an existing Superadmin. Changing one privilege MUST preserve the other; superuser status does not require staff status. The system MUST NOT automatically enable, coerce, or mutually exclude these privileges.
- **FR-006**: Each privilege change MUST be saved coherently and its outcome reported clearly. A failed or denied change MUST NOT be presented as active or partially applied.
- **FR-007**: Staff MUST retain the same access as superusers in administrative operational modules, except for personnel listing/selection and assigning or removing staff/superuser privileges. Existing broad operational staff access is intentional; CU-A04 MUST NOT narrow or broaden unrelated operational-module behavior.
- **FR-008**: A saved privilege change MUST affect subsequent authorization checks, including checks from sessions that were already active. The system MUST NOT rely solely on UI restrictions or cached client/token privilege flags. The technical mechanism is deferred to planning.
- **FR-009**: Public and buyer-facing views MUST NOT expose privilege-management data, user credentials, or authentication secrets.
- **FR-010**: This feature MUST NOT deactivate or delete accounts and MUST NOT introduce a new module-specific role model or role/module permission matrix.
- **FR-011**: The system MUST NOT remove superuser privilege from an active user when doing so would leave zero active superusers. This includes self-demotion: it is allowed if another active superuser remains and denied otherwise. A denied operation MUST make no partial updates, and concurrent revocations MUST NOT bypass the invariant.

### Key Entities

- **Existing user account**: An account created through the existing ordinary registration flow. CU-A04 manages its existing privilege flags; it does not create employee accounts.
- **Staff privilege (`is_staff`)**: An existing independent boolean privilege that grants access to administrative operational modules, but not privilege-management listing or actions.
- **Superuser privilege (`is_superuser`)**: An existing independent boolean privilege that authorizes privilege administration only when the account is active and authenticated; staff status is not a prerequisite.
- **Active Superadmin**: An authenticated, active user with `is_superuser=true`, whether or not `is_staff=true`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In all tested listing/selection and privilege-change paths, 100% of unauthenticated, inactive, staff-only, and operation-key-only attempts are denied, with zero unauthorized changes or protected user data returned.
- **SC-002**: 100% of tested active Superadmin attempts are not denied solely because `is_staff=false`.
- **SC-003**: 100% of tests changing one privilege preserve the other privilege; granting superuser does not implicitly grant staff or coerce either flag.
- **SC-004**: In all tested concurrent revocations, at least one active superuser remains; every denied last-superuser revocation makes no partial update.
- **SC-005**: In all tested operational modules, staff retains the same operational access as superusers except for personnel listing/selection and privilege assignment/removal.
- **SC-006**: After a privilege change, 100% of subsequent authorization checks—including checks made through already-active sessions—reflect the saved state.
- **SC-007**: Public and buyer-facing views disclose zero credentials, authentication secrets, or privilege-management data.

## Assumptions

- CU-A04 manages the existing `is_staff` and `is_superuser` privileges for existing user accounts; it does not create a new role system.
- Ordinary self-registration remains the existing flow used by buyers. Users acquire staff or superuser privileges only through authorized administration of their existing account.
- Existing broad staff access to operational modules is desired. Only privilege-management personnel data/actions are Superadmin-only.
- The project has established authentication, registration, and user-account behavior that planning should inspect and reuse where applicable.
- Applicable service contracts are owned by Core and BFF. Their exact request/response semantics, independent flag-update shape, and technical enforcement mechanism are deferred to the planned contract-first workflow.
- All verification is local and uses disposable fixtures; no real personal data or secrets are required.

## Approved Decision Record

Business decisions below were explicitly approved by the user on **2026-11-06**. No business-policy decision remains open; technical planning and canonical contract approval remain pending.

1. **Account creation**: Users create their own account through existing ordinary registration, like any buyer. CU-A04 adds no employee creation, invitations, temporary passwords, onboarding, or first-use credential system.
2. **Privilege authority**: An authenticated active `is_superuser` can assign and remove staff or superuser privileges on any existing user, including existing superusers. `is_staff` alone cannot manage privileges; `is_superuser=true, is_staff=false` is sufficient.
3. **Operational access**: Staff retains all superuser operational access except privilege assignment/removal. No Seller/Moderator/Warehouse roles, module permission matrix, or backfill/cutover policy is introduced. Privilege-management personnel listing/selection remains Superadmin-only.
4. **Independent privileges and last-superuser protection**: Staff and superuser are independent booleans. A change to one preserves the other; do not auto-enable staff when granting superuser, coerce flags, or make the privileges mutually exclusive. Removing superuser is allowed, including self-demotion, only while another active superuser remains. Denial must be atomic, and concurrent revocations cannot bypass the invariant.
5. **Lifecycle, model, and enforcement boundary**: Account deactivation/deletion and a new module-specific role model are out of scope. Privilege changes affect subsequent authorization checks even in existing sessions; the mechanism is deferred to planning and cannot rely solely on UI or cached token flags.

**Scope boundary**: This specification records approved business behavior only. It does not define or modify API contracts, schemas, implementation, or the technical enforcement mechanism. The plan must resolve technical semantics and validate applicable Core GraphQL and BFF OpenAPI contracts before behavior implementation.

**Source**: CU-A04 in `CasosDeUso.md` (source text begins at line 249 in the supplied read-only attachment).
