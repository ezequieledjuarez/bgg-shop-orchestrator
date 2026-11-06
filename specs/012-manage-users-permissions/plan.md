# Implementation Plan: CU-A04 — Manage Users and Permissions

**Feature dir**: `specs/012-manage-users-permissions` | **Date**: 2026-11-06

**Status**: T011 expected RED was observed; T012 implementation and the dedicated PostgreSQL regression file are locally verified. The broader Core auth/products command recorded three unrelated existing failures; see `tasks.md`.

## Summary

Add Superadmin-only personnel selection and independent updates to the existing `is_staff` and `is_superuser` flags for existing accounts. Preserve the broad staff-or-superuser access to operational administration. Ordinary self-registration remains unchanged; no employee onboarding, new role model, account lifecycle changes, migration, or dependency is in scope.

## Technical Context and Current-State Evidence

- **Core identity**: `bgg-shop-core/saleor/graphql/api.py::_authenticated_user` decodes the bearer token's subject and fetches the current Django `User` by primary key with `is_active=True` on each GraphQL request. Its delegated operation-key branch is separate and can return an active staff or superuser, so new personnel operations must explicitly reject operation-key-only requests.
- **Core authorization and registration**: Existing operational GraphQL guards generally allow `is_staff OR is_superuser`. The regular `Register` mutation uses `User.objects.create_user` without privilege inputs. There is no current Core personnel-list or privilege-update operation.
- **Core persistence**: The affected identity is `django.contrib.auth.models.User`; the existing Core application uses Django ORM and PostgreSQL. Existing Core code uses `transaction.atomic` and `select_for_update` for transactional row coordination (for example `bgg-shop-core/opkeys/views.py`). No global-user-role lock or last-superuser invariant currently exists.
- **BFF authorization**: `bgg-shop-bff/src/auth.py::admin_required` authorizes a bearer token through the existing broad `check_admin` path or a validated operation-key session. There are no personnel/privilege routes. New management routes need a distinct bearer-only, active-Superadmin guard; do not tighten the shared operational `admin_required` behavior.
- **Frontend**: `bgg-shop-frontend/src/admin/AdminRouter.tsx` routes the existing operational modules and has no personnel-management route. The existing admin shell is reached through the current token-presence gate; this is not an authorization boundary and must not be used to protect user data or updates.
- **Existing tests/patterns**: `bgg-shop-core/tests/test_admin_sales_metrics_postgres.py` is an opt-in disposable-PostgreSQL test pattern and verifies the existing staff-or-superuser policy; `bgg-shop-bff/tests/test_admin_sales_metrics.py` verifies that the BFF operational path accepts both roles. Frontend component tests use Vitest, Testing Library and MSW; `src/admin/audit/AuditPanel.test.tsx` exercises admin routing and accessible roles.
- **Project constraints**: `.github/copilot-instructions.md` requires local-only checks and contract approval before service-interface behavior. The reference plan `specs/010-sales-metrics-reports/plan.md` also uses contract-first implementation and disposable local PostgreSQL validation.

## Approved Scope and Fixed Semantics

The approved business policy in `specs/012-manage-users-permissions/spec.md` is unchanged:

1. Only an authenticated, active `is_superuser=true` user may list/select accounts or change either privilege. `is_staff` is not additionally required.
2. The privileges remain independent. Every update identifies one flag and one desired boolean value, changes only that column, and leaves the other flag untouched. Granting superuser does not grant staff.
3. Any existing account may be selected, including an inactive account or an existing Superadmin; credentials, password hashes, tokens, and authentication secrets are never returned.
4. Ordinary self-registration continues without privilege inputs. No employee creation/invitation, deactivation/deletion, new role system, or role/module matrix is introduced.
5. Staff keeps existing operational access. Only the new personnel listing and privilege-management actions are excluded from staff-only access.
6. Revoking superuser is allowed only if at least one other active superuser remains after the update. This includes self-demotion. Concurrent requests must preserve the invariant and leave denied requests without partial writes.
7. A saved change must affect the next authorization check, including requests made with an already-issued bearer token.

## Technical Design Decisions

### Independent updates and coherent outcomes

- Treat each privilege update as a single-field command: identify the target, identify exactly one privilege, and provide its new boolean value. Never accept a full user object and write both flags from a stale client snapshot.
- In Core, load and lock the target row, verify it still exists, and assign/save only the requested field. Return the saved user projection only after the transaction succeeds. A missing target or a rejected invariant returns a clear failure and no changed state.
- For an `is_staff` update, perform the target-row write atomically. For any operation that can change `is_superuser`, use the shared serialization procedure below, including grants, so concurrent grants and revocations observe an ordered active-superuser set.
- The UI displays server-confirmed values; while a change is pending, it must not optimistically present the requested value as saved. On failure it retains the last confirmed state and shows an accessible error.

### Last-active-superuser invariant and PostgreSQL strategy

- Define the invariant count as users where `is_active=true AND is_superuser=true`. Inactive Superadmins do not satisfy the invariant; changing `is_staff` never changes this count.
- Implement each superuser-flag mutation in one Django `transaction.atomic` block on the `User` model's configured database. Before any superuser-flag write, materialize PostgreSQL row locks on all currently active superusers in stable primary-key order using `select_for_update().filter(is_active=True, is_superuser=True).order_by("pk")`. Every grant and revocation must use this same lock sequence, then lock/reload the target as needed. Derive the pre-update count from the locked set and the post-update count from the requested one-flag transition before writing the target flag.
- If the requested operation would make the active-superuser count zero, return a domain-level denial before writing. Otherwise update only `is_superuser`; the transaction commits the decision and field change together. Do not rely on an application-process mutex, a pre-transaction count, or a database check constraint over multiple rows.
- This is a PostgreSQL row-locking strategy, not an already-existing feature. Validate it with real parallel transactions in the future opt-in local PostgreSQL test. If that test cannot demonstrate serialization/re-evaluation under the configured database isolation, keep implementation blocked and revise the strategy; do not weaken the invariant or add a migration as a workaround.
- Lock the active-superuser set in deterministic order for all superuser mutations to serialize revocations and concurrent promotions and to reduce deadlock risk. Lock the target row within the same transaction so the target cannot disappear or change between validation and save. Under PostgreSQL's normal `READ COMMITTED` behavior, a `SELECT ... FOR UPDATE` that waits on a concurrent update must use the current qualifying row version; verify this with the required parallel-transaction test rather than assuming it.
- Any rejected last-superuser operation must complete without writes. Tests must reread every affected flag after both success and failure.

### Authorization freshness and operation-key boundary

- Reuse Core's bearer subject resolution, which retrieves the active Django user row for each request; authorize from the freshly loaded `is_superuser` value rather than token-embedded role claims. Do not cache an authorization decision in the browser or BFF.
- The new Core resolver must require a bearer-authenticated active user and explicitly reject the operation-key-delegated identity path before accepting the actor. Then require `is_superuser=true` without requiring `is_staff=true`.
- Add a dedicated BFF Superadmin guard for these endpoints. It must require a bearer authorization header, deny operation-key-only sessions, and check current Core identity/authorization for every request. Keep `admin_required`/`check_admin` unchanged for operational routes, which intentionally allow staff and superusers.
- Subsequent requests made with the same still-valid bearer token must observe saved DB flags. A staff revocation must remove staff operational authorization on the next check; a superuser revocation must remove privilege-management authorization on the next check. A self-demotion response may complete under the actor's pre-update authorization, but the actor's next request must be denied.

### Preserve operational staff parity

- Do not change existing operational Core guards, BFF `admin_required`, operational endpoints, or their UI navigation/visibility as part of this feature.
- Add only a separate users/permissions route or panel and a separate Superadmin-only server boundary. The UI may hide the new route/control from staff, but the Core and BFF must independently deny staff-only callers.
- Keep the existing operational staff-or-superuser tests passing. The absence of a users route today is a feature gap; it is not evidence that operational staff access should be narrowed.

## Approved Contract Decisions

The user explicitly approved these exact Core GraphQL and BFF OpenAPI details on 2026-11-06. Both canonical contracts record them; T010 independently validated their structure and agreement.

1. **Core GraphQL surface**: `adminUsers(search, cursor, limit)` and `adminUpdateUserPrivilege(userId, privilege, enabled)`. The safe projection is exactly `id`, `email`, `firstName`, `lastName`, `isActive`, `isStaff`, and `isSuperuser`; no credentials or authentication secrets.
2. **BFF REST surface**: `GET /api/v1/admin/users` and `PATCH /api/v1/admin/users/{user_id}/privileges` with JSON `{privilege, enabled}`. The response projection uses the corresponding snake-case fields.
3. **Search and paging**: search is a case-insensitive substring over email, first name, and last name. Pages use stable user-ID ascending order and an opaque cursor; `limit` defaults to 50 and has a maximum of 100.
4. **Privilege discriminator**: values are exactly `is_staff` and `is_superuser` in both Core GraphQL and BFF JSON. Each update changes only the selected boolean and preserves the other.
5. **Authorization and errors**: require bearer-only, current active-superuser authorization on every request; do not authorize from token role flags or operation keys. Preserve existing staff operational access. The public mappings are 401/403/404/400/409; Core last-active-superuser denial code is exactly `LAST_ACTIVE_SUPERUSER` and maps to HTTP 409. Public errors remain sanitized.
6. **Frontend authorization boundary**: no separate current-role endpoint is approved or needed. The users route is server-gated, and the UI must not trust token role flags as authority.

No contract decision remains unresolved. T010 passed the independent SDL/OpenAPI structure and cross-contract agreement gate; behavior implementation may now begin under the test-first task sequence.

## Work Plan (Contract First, Then Implementation)

1. **T008/T009 — Approve both canonical contracts**: record the approved personnel listing and single-flag update semantics, authorization, safe projection, search/paging, discriminator, and sanitized error mapping in Core `bgg-shop-core/specs/schema.graphql` and BFF `bgg-shop-bff/specs/openapi.yaml`. These contract tasks are complete; no runtime behavior was changed.
2. **T010 — Independently validate before behavior work (complete)**: the independent review found no high-confidence blockers; Core SDL and BFF OpenAPI structural validation passed, and the parent spot-check passed. Evidence is recorded in `tasks.md`.
3. **T011/T012 — Core tests then implementation (complete locally)**: author the PostgreSQL-backed tests below first; verify expected failures; implement only approved operations with active bearer Superadmin enforcement, per-request DB permissions, field-specific writes, and transactional locking. T012's focused regressions and full test file passed against a disposable loopback PostgreSQL 15 container.
4. **T014/T015 — BFF tests then implementation**: test identity propagation and denials first; implement dedicated bearer-only Superadmin routes and sanitized errors without changing operational guards.
5. **T017/T018/T019 — Generated types and UI**: regenerate types from the approved OpenAPI with the existing command; write panel/routing tests; add the route/panel only after the tests and generated types. Preserve operational navigation for staff.
6. **T013/T016/T020/T021 — Local verification**: run the exact focused suites listed below, then applicable local integration/E2E checks against disposable data. Record only commands actually run and outcomes. No CI, staging, production, remote validation, or real personal data.

## Test Plan: Files and Selectors

The Core test file and selectors below have been authored. On 2026-11-06, the suite ran against a dedicated disposable local PostgreSQL database: 20 tests failed as expected because the runtime operations are absent, and the registration test passed. An independent verifier reproduced the result. This is test-first RED evidence only, not functional implementation evidence; runs without the DSN skip the suite.

### Core — `bgg-shop-core/tests/test_user_permissions_postgres.py`

Follow the disposable, loopback-only PostgreSQL pattern used by `test_admin_sales_metrics_postgres.py`. Read only `USER_PERMISSIONS_TEST_POSTGRES_DSN`; if it is absent, skip these opt-in tests. If it is present but invalid, fail closed before connecting. Require a PostgreSQL URL whose host is exactly `127.0.0.1`, whose port is explicit, whose password is nonempty, and whose database name and username are the same `user_permissions_test_<32 lowercase hex>` value. Reject query parameters and fragments. Never fall back to Django's configured/default `saleor` database, and never create or drop a database or role.

After validating the DSN, temporarily configure Django's default connection to that exact disposable database/role, verify `current_database()` and `current_user`, then create a random per-run schema and set the connection search path to that schema. Create test tables only inside that schema and always drop only that schema in fixture cleanup, including on test failure. Do not print the DSN or credentials. Exercise real ORM row locks with separate DB connections/transactions for concurrency.

Planned pytest selectors:

- `test_user_list_requires_active_superuser_not_staff`
- `test_user_list_search_is_case_insensitive_substring_across_user_fields`
- `test_user_list_cursor_paginates_ascending_ids_with_default_and_max_limits`
- `test_user_list_invalid_search_limit_and_cursor_include_invalid_field`
- `test_user_list_and_last_superuser_errors_are_sanitized`
- `test_user_list_operational_error_is_sanitized`
- `test_privilege_update_operational_error_is_sanitized`
- `test_operation_key_only_cannot_list_or_update_users`
- `test_privilege_update_changes_only_requested_flag`
- `test_superuser_without_staff_can_list_and_update_privileges`
- `test_last_active_superuser_revocation_is_denied_without_partial_update`
- `test_last_superuser_self_demotion_requires_another_active_superuser`
- `test_concurrent_superuser_revocations_preserve_one_active_superuser`
- `test_promotion_then_concurrent_actor_revocation_refreshes_qualifying_set`
- `test_existing_bearer_token_uses_updated_privileges_on_next_request`
- `test_registration_does_not_assign_staff_or_superuser`

T012 review regressions (expected RED observed before implementation; GREEN verified locally): the promotion/revocation lock-state test and both synthetic database-error sanitization tests passed (3 passed, 21 deselected), and the complete PostgreSQL file passed (24 passed). The race regression now serializes superuser-flag writes with a transaction-scoped PostgreSQL advisory lock before reading the active-superuser set; the subsequent READ COMMITTED query sees the committed promotion. Both public database-error paths catch `DatabaseError` outside the failed write transaction (or narrowly around list evaluation), log static messages, and expose generic `SERVER_ERROR` results without exception details. An initial focused attempt exposed a missing import (one of three focused checks failed); after correction, the focused and full runs passed. The separate `python -m pytest -q tests/test_graphql_auth.py tests/test_graphql_products.py` run recorded 55 passed and 3 unrelated failures: existing review SDL description drift and two product-review SQL assertions expecting `APPROVED` while the implementation uses `ACCEPTED`. No tests or SDL were changed; these broader failures remain outside T012.

Focused invocation, from `bgg-shop-core/`, once the dedicated disposable PostgreSQL DSN is configured:

```sh
pytest -q tests/test_user_permissions_postgres.py
```

Configure the disposable test connection through `USER_PERMISSIONS_TEST_POSTGRES_DSN`; absence means the tests skip, while any present but invalid DSN is a hard failure. The fixture must not consult or use Django's configured/default database as a fallback.

### BFF — `bgg-shop-bff/tests/test_admin_users.py`

Use Flask's test client and mocked Core identity/GraphQL responses, following `tests/test_admin_sales_metrics.py`. Verify unauthenticated, inactive, staff-only and operation-key-only denials; active `is_superuser=true, is_staff=false` acceptance; request carries one flag only; sanitized failures; and no change to staff-or-superuser operational admin behavior.

Implemented pytest cases:

- `test_inactive_bearer_uses_core_forbidden_response`
- `test_user_listing_forwards_bearer_and_filters`
- `test_privilege_patch_changes_only_the_selected_flag_and_propagates_bearer`
- `test_core_denials_are_mapped_without_identity_preflight`
- `test_operation_key_alone_cannot_list_or_change_users`
- `test_last_active_superuser_error_is_conflict_and_excludes_upstream_detail`
- `test_upstream_exception_is_sanitized_for_user_listing`

Focused invocation, from `bgg-shop-bff/`:

```sh
pytest tests/test_admin_users.py tests/test_admin_sales_metrics.py
```

### Frontend — `bgg-shop-frontend/src/admin/users/UserManagementPanel.test.tsx`

Use Vitest, Testing Library and MSW, matching `src/admin/audit/AuditPanel.test.tsx`. Keep query assertions accessible by role/label. Implemented accessible selectors include the heading `Administración de usuarios`, checkboxes `Personal de administración` and `Superadministrador`, and button `Guardar cambios`.

Covered Vitest behaviors:

- `searches and selects existing users, and saves each privilege independently`
- `does not expose personnel after the listing endpoint refuses access`
- `keeps operational admin destinations in navigation and offers no employee onboarding flow`
- `shows a safe failure and preserves the saved superuser value after a rejected revocation`

Focused invocation, from `bgg-shop-frontend/`:

```sh
npm --prefix bgg-shop-frontend test -- --run src/admin/users/UserManagementPanel.test.tsx
```

### Local integration / browser check

E2E file: `bgg-shop-frontend/tests/e2e/admin-users.spec.ts`, using the isolated local harness `scripts/run-spec012-local-e2e.sh`. The harness creates a disposable loopback PostgreSQL container with tmpfs data and synthetic accounts, starts Core/BFF/Frontend on random loopback ports, disables shared Playwright login/storage state, uses the installed local Chromium without downloads, and cleans up only its own resources. The reported run passed all 8 Chromium scenarios: independent staff/superuser flag changes and persistence; staff denial/data hiding with operational access; same-bearer denial after self-demotion; missing-authentication 401; invalid-bearer 401; fake operation-key-only 403; inactive-valid-bearer 403; and last-active-Superadmin denial with 409 and unchanged state. Harness cleanup verified its owned services and Playwright processes exited, its unique tmpfs PostgreSQL container/database were removed, and its temporary run directory was deleted. Full-stack concurrent revocations remain untested.

```sh
bash scripts/run-spec012-local-e2e.sh
```

Core service-level concurrency tests are separate and do not substitute for the unrun full-stack concurrent-revocation case. Record E2E evidence only from the isolated runner above. Never use default Compose resources, ambient credentials, non-local environments, or real personal data.

## Risks and Mitigations

- **Concurrent update race**: serialize every superuser-flag write with the same PostgreSQL transaction-scoped advisory lock before materializing the active-superuser set; prove with parallel DB connections and reread the committed state.
- **Stale browser/token role state**: Core reloads the active user from DB per bearer request; each BFF management operation delegates to the Core resolver, which authorizes from current saved state. UI state is not authorization.
- **Operation-key bypass**: existing shared admin middleware permits operation-key sessions. New endpoints use a distinct bearer-only guard at BFF and reject the delegated path in Core.
- **Accidental operational regression**: leave all broad operational authorization paths unchanged and run the existing sales/admin role-parity tests.
- **Contract drift or sensitive user data**: approve and cross-check SDL/OpenAPI before behavior; explicitly exclude credentials and authentication secrets from all listing and update payloads.

## Acceptance Criteria for This Plan

- The plan reflects all approved business behavior without reopening it.
- Core/BFF authorization paths, operation-key limitation, registration behavior, current operational role parity, and frontend route gap are grounded in the inspected repository files above.
- One-flag update behavior, transactional PostgreSQL invariant strategy, and next-request authorization freshness are explicit.
- All user-approved wire decisions are explicit above and reflected in both canonical contracts; T010 independent agreement validation passed.
- Exact future test files, selectors and local-only checks are identified.
- Only the two canonical contracts and allowed plan/task records are changed; no runtime behavior, dependency, migration, test fixture, generated types, or non-allowed file is changed.
