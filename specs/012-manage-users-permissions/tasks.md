# Tasks: Manage Users and Permissions (CU-A04)

**Input**: [spec.md](spec.md), [requirements checklist](checklists/requirements.md)
**Status**: T004–T011 are complete through the observed Core test-first RED. T012, T014 and T017 are ready; later tasks remain pending their prerequisites.
**Branch**: `012-manage-users-permissions` in the orchestrator and all three service repositories.
**Scope**: Local environments and disposable test data only. No staging, production, CI, remote validation, or real personal data.

## Delivery strategy

- **Strategy**: `ask-on-risk`; the user selected `stacked-to-main` as the chain strategy on 2026-11-06 after the projected authored feature diff exceeded approximately 400 lines.
- **PR slicing**: Slice boundaries are not established yet. No push or PR creation is authorized.

## Work-unit commits

- **Contracts and T010 validation**: Core `7ee655e`, BFF `93d761a`, orchestrator docs `35e8fa3`.
- **T011 Core tests / expected RED**: Core `d8247f2`.

## Backlog status and gates

The three decision tasks are complete as records of explicit user approvals only; they are not implementation or test evidence. T004–T006 are complete read-only investigations, with evidence recorded below. T007 is complete as a technical planning artifact only. T008/T009 are complete as approved canonical contract work using the exact user-approved decisions recorded below. T010 passed independent validation. T011's tests are authored and their expected RED was independently reproduced against disposable PostgreSQL; T012, T014 and T017 are now ready, while later tasks remain pending their listed prerequisites. No service behavior has been changed yet.

The applicable canonical contracts remain Core `bgg-shop-core/specs/schema.graphql` and BFF `bgg-shop-bff/specs/openapi.yaml`; both contain the approved CU-A04 contract and passed structural and independent cross-contract validation. The Frontend generates types from the BFF OpenAPI using the existing `npm run generate:types` command; generation has not run. No runtime implementation, tests, or generated types were changed.

## Task format and distribution

Global task IDs are stable across the master and service documents. Each ID has exactly one owner. Service documents contain only their service's assigned tasks; cross-service and project-coordination work remains here. A completed decision task records user approval only. Every future implementation or verification task remains unchecked until its outcome and applicable local evidence are recorded.

| ID | Owner | Status | Depends on | Trace |
|---|---|---|---|---|
| T001 | Orchestrator | DONE — approved policy decision | — | FR-005, FR-007, FR-010; US1–US2 |
| T002 | Orchestrator | DONE — approved account-creation boundary | — | FR-004; US1 |
| T003 | Orchestrator | DONE — approved privilege authority and invariant | — | FR-001–FR-003, FR-011; US1, US3 |
| T004 | Core | DONE — investigation only | — | FR-001–FR-008, FR-011; US1–US3 |
| T005 | BFF | DONE — investigation only | — | FR-001–FR-009, FR-011; US1–US3 |
| T006 | Frontend | DONE — investigation only | — | FR-003–FR-009; US1–US3 |
| T007 | Orchestrator | DONE — planning artifact | T004–T006 | All FRs; SC-001–SC-007 |
| T008 | Core | DONE — approved canonical contract | T007 | FR-001–FR-008, FR-011; US1–US3 |
| T009 | BFF | DONE — approved canonical contract | T007 | FR-001–FR-006, FR-008–FR-009, FR-011; US1–US3 |
| T010 | Orchestrator | DONE — independent contract validation | T008, T009 | FR-001–FR-011; SC-001–SC-007 |
| T011 | Core | DONE — tests authored, expected RED observed | T007, T010 | FR-001–FR-009, FR-011; US1–US3 |
| T012 | Core | READY — Core implementation | T011, T010 | FR-001–FR-008, FR-011; US1–US3 |
| T013 | Core | BLOCKED — Core behavior | T012 | SC-001–SC-007 |
| T014 | BFF | READY — tests first | T007, T010 | FR-001–FR-006, FR-008–FR-009, FR-011; US1–US3 |
| T015 | BFF | BLOCKED — tests and Core behavior | T014, T012 | FR-001–FR-006, FR-008–FR-009, FR-011; US1–US3 |
| T016 | BFF | BLOCKED — BFF behavior | T015 | SC-001–SC-007 |
| T017 | Frontend | READY — generated types | T010 | FR-003–FR-009; US1–US3 |
| T018 | Frontend | BLOCKED — plan and generated types | T007, T017 | FR-003–FR-009; US1–US3 |
| T019 | Frontend | BLOCKED — tests and service behavior | T018, T012, T015 | FR-003–FR-009, FR-011; US1–US3 |
| T020 | Frontend | BLOCKED — UI behavior | T019 | SC-003, SC-005–SC-007 |
| T021 | Orchestrator | BLOCKED — all service checks | T013, T016, T020 | FR-001–FR-011; SC-001–SC-007 |

## Phase 1: Approved decisions and current-state investigation

- [x] **T001 [Orchestrator] [DONE — user decision only]** Record the approved privilege policy: `is_staff` and `is_superuser` remain independent existing booleans; staff retains broad operational access except privilege administration; no module-role matrix, backfill, or cutover is in scope. **Evidence**: explicit user approval in the request dated 2026-11-06. This completion is not implementation or test evidence. Trace: FR-005, FR-007, FR-010; US1–US2.
- [x] **T002 [Orchestrator] [DONE — user decision only]** Record the approved account-creation boundary: users create their own accounts through existing ordinary registration, like buyers; CU-A04 adds no employee creation or credential-onboarding process. **Evidence**: explicit user approval in the request dated 2026-11-06. This completion is not implementation or test evidence. Trace: FR-004; US1.
- [x] **T003 [Orchestrator] [DONE — user decision only]** Record the approved authority and lifecycle boundary: only an authenticated active `is_superuser` can assign/remove either privilege on any existing user; protect the last active superuser under concurrent revocations; deactivation, deletion, and a new role model are out of scope. **Evidence**: explicit user approval in the request dated 2026-11-06. This completion is not implementation or test evidence. Trace: FR-001–FR-003, FR-011; US1, US3.
- [x] **T004 [Core] [DONE — investigation only]** Inventory current Core identity and active-account checks, GraphQL authorization paths, user/privilege data, account registration behavior, and relevant operational staff authorization. Do not edit contracts, schema, or behavior. **Evidence**: `bgg-shop-core/saleor/graphql/api.py` resolves bearer subjects to the current `is_active=True` Django user, has a separate operation-key-delegated branch, applies the existing operational `is_staff OR is_superuser` checks, and registers users without privilege inputs. No personnel listing/update operation exists. The existing staff-or-superuser test policy is exercised in `bgg-shop-core/tests/test_admin_sales_metrics_postgres.py`. No code or schema was changed. Trace: FR-001–FR-008, FR-011; US1–US3.
- [x] **T005 [BFF] [DONE — investigation only]** Inventory BFF authentication/context propagation, operation-key-only paths, existing user/personnel routes, flag representations, error sanitization, and existing session/token behavior. Do not design or change an interface. **Evidence**: `bgg-shop-bff/src/auth.py` shows `admin_required` accepts authenticated users through the broad admin check and validated operation-key sessions; existing staff/superuser parity is exercised in `bgg-shop-bff/tests/test_admin_sales_metrics.py`. No personnel/privilege route exists. No contract or behavior was changed. Trace: FR-001–FR-009, FR-011; US1–US3.
- [x] **T006 [Frontend] [DONE — investigation only]** Inventory admin navigation, existing user search/selection, privilege controls, generated API types, and operational UI visibility for staff and superusers. Do not assume a role matrix or edit UI/types. **Evidence**: `bgg-shop-frontend/src/admin/AdminRouter.tsx` routes existing operational modules and has no user-management route or personnel-selection UI; the existing admin shell is reached via token-presence gating and does not provide authorization. `bgg-shop-frontend/src/admin/audit/AuditPanel.test.tsx` demonstrates the local accessible admin-routing/component-test pattern. No UI or generated type was changed. Trace: FR-003–FR-009; US1–US3.

## Phase 2: Planning and authoritative contract gates

- [x] **T007 [Orchestrator] [DONE — planning artifact]** After T004–T006, create the technical plan from the approved decisions and current-state evidence. Specify independent flag-update semantics that preserve the untouched flag, the last-active-superuser invariant and concurrency strategy, authorization freshness for already-active sessions, existing operational staff parity, exact future test files/selectors, and local-only checks. **Evidence**: [plan.md](plan.md) records these choices, and now reflects the approved Core/BFF wire details and T010 independent-validation gate. It identifies exact future test files/selectors and local-only commands. No business decision was reopened; no implementation, dependencies, migrations, tests, or other service files were changed. Trace: all FRs and SCs.
- [x] **T008 [Core] [DONE — approved canonical contract]** Finalize `bgg-shop-core/specs/schema.graphql` with `adminUsers(search, cursor, limit)`, `adminUpdateUserPrivilege(userId, privilege, enabled)`, the safe seven-field `User` projection, case-insensitive substring search over email/firstName/lastName, ascending user-ID cursor order, default limit 50/max 100, exact `is_staff` and `is_superuser` privilege values, and `LAST_ACTIVE_SUPERUSER` for the HTTP 409 domain denial. Require current bearer-authenticated active-superuser authority and reject operation-key-only authority; preserve existing staff operational access. **Approval/evidence**: the user explicitly approved these exact details in the request dated 2026-11-06; the canonical SDL records them at `AdminUserPage`, `Query.adminUsers`, `AdminUserPrivilege`, and `Mutation.adminUpdateUserPrivilege`. Credentials and authentication secrets are excluded. No Core behavior or tests changed in this contract task. Trace: FR-001–FR-008, FR-011; US1–US3.
- [x] **T009 [BFF] [DONE — approved canonical contract]** Finalize `bgg-shop-bff/specs/openapi.yaml` with `GET /api/v1/admin/users`, `PATCH /api/v1/admin/users/{user_id}/privileges` and `{privilege, enabled}`, the matching snake-case safe projection and search semantics, ascending user-ID cursor order, default limit 50/max 100, exact privilege values `is_staff` and `is_superuser`, and `LAST_ACTIVE_SUPERUSER` mapped to HTTP 409. Require current bearer-authenticated active-superuser authority; token role flags and operation keys are not authority; preserve staff operational behavior and sanitized 400/401/404/409 responses. **Approval/evidence**: the user explicitly approved these exact details in the request dated 2026-11-06; the canonical OpenAPI records them at both admin-user paths, `AdminUpdateUserPrivilegeRequest`, and `UserManagementLastSuperuser`. No credentials or authentication secrets are exposed. No BFF behavior or tests changed in this contract task. Trace: FR-001–FR-006, FR-008–FR-009, FR-011; US1–US3.
- [x] **T010 [Orchestrator] [DONE — independent contract validation]** Independently validate the Core SDL and BFF OpenAPI against each other and the approved plan before behavior implementation. **Acceptance**: operation names/routes, safe field projections, case-insensitive substring search fields, ascending user-ID cursor semantics, default/max limits, exact privilege values, bearer-only current authorization, independent flag updates, sanitized error/status mapping including `LAST_ACTIVE_SUPERUSER` to 409, and operational staff parity agree. **Evidence**: the independent reviewer found no high-confidence blockers and confirmed agreement across the contracts, plan and specification. From the orchestrator root, both validators passed:
  - Core SDL command:
    ```sh
    python - <<'PY'
    from pathlib import Path
    from graphql import build_schema, validate_schema
    schema = build_schema(Path('bgg-shop-core/specs/schema.graphql').read_text())
    errors = validate_schema(schema)
    for error in errors:
        print(error)
    assert not errors, f'{len(errors)} SDL structure errors'
    print('PASS: Core SDL parsed, built and validated; 0 schema errors')
    PY
    ```
    Output: `PASS: Core SDL parsed, built and validated; 0 schema errors`.
  - BFF OpenAPI command:
    ```sh
    python - <<'PY'
    from pathlib import Path
    import yaml
    import openapi_spec_validator
    from openapi_spec_validator import validate
    spec = yaml.safe_load(Path('bgg-shop-bff/specs/openapi.yaml').read_text())
    print('OpenAPI validator version:', openapi_spec_validator.__version__)
    print('Document version:', spec['openapi'])
    validate(spec)
    print('PASS: BFF OpenAPI parsed and validated')
    PY
    ```
    Output: validator `0.9.0`, document `3.2.0`, `PASS: BFF OpenAPI parsed and validated`.
  - The parent reran the BFF validation using `python - <<'PY'` with `yaml.safe_load(Path('bgg-shop-bff/specs/openapi.yaml').read_text())` and `openapi_spec_validator.validate`; it passed. No separate current-role endpoint or token-role authority was introduced. No runtime behavior was changed. Trace: all FRs and SCs.
  - Parent spot-check reran the BFF OpenAPI validator successfully. No separate current-role endpoint or token-role authority was introduced. No runtime behavior was changed. Trace: all FRs and SCs.

### T008/T009 contract approval record — 2026-11-06

- **Explicit approval applied**: search is case-insensitive substring over email, first name and last name; cursor ordering is stable by user ID ascending; limit defaults to 50 and maxes at 100; privilege discriminator values are exactly `is_staff` and `is_superuser` in Core GraphQL and BFF JSON; `LAST_ACTIVE_SUPERUSER` maps to HTTP 409. The previously approved operations/routes, seven-field safe projection, one-flag mutation/body, current bearer-only authorization (not token roles or operation keys), operation-key-only denial, independent flags, and existing staff operational access are retained. Inactive actors are forbidden (403); inactive targets remain selectable. No separate current-role endpoint is approved or needed; the users route is server-gated and the UI must not trust token role flags.
- **Established conventions reused**: Core `User.id: ID!` / BFF `AuthUser.id` string; Core camel-case/BFF snake-case fields; existing cursor pagination envelope mapped as `items` plus `nextCursor`/`next_cursor`, opaque signed cursors and limit default 50/range 1–100 from administrative audit; cursor length 1–512 from that contract; optional search length 1–200 from the existing Search parameter. Mutation uses nullable saved `user` and existing `userErrors`; REST returns the safe saved user after success. Existing public `AdminErrorResponse`/`AdminFieldErrorResponse` forbid extra diagnostic properties. Existing 502 convention covers unavailable/invalid upstream responses without claiming an unknown mutation outcome was rolled back.
- **Unresolved contract decisions**: none. Cursor/filter binding is not an unresolved product/API choice: the opaque cursor advances after its last user ID while the requested search filter continues to apply.
- **Plan reconciliation**: `plan.md` records all approved details and has no unresolved contract decisions. T008/T009 are checked complete on explicit user approval and contract evidence only; T010 independent cross-contract validation remains pending. No behavior, tests, generated types, dependencies or migrations were changed; no staging/commit or auto-commit hook was executed.
- **Local structural verification**: both commands below were run after the final contract edits on 2026-11-06 using already-installed Python parsers (no package installation). Core output: `PASS: Core SDL parsed, built and validated; 0 schema errors`. BFF output: `OpenAPI validator version: 0.9.0`, `Document version: 3.2.0`, and `PASS: BFF OpenAPI parsed and validated`. These are document syntax/structure checks only; T010 independent cross-contract validation and runtime conformance remain pending.

Core SDL command, from the orchestrator root:

```sh
python - <<'PY'
from pathlib import Path
from graphql import build_schema, validate_schema
schema = build_schema(Path('bgg-shop-core/specs/schema.graphql').read_text())
errors = validate_schema(schema)
for error in errors:
    print(error)
assert not errors, f'{len(errors)} SDL structure errors'
print('PASS: Core SDL parsed, built and validated; 0 schema errors')
PY
```

BFF OpenAPI command, from the orchestrator root:

```sh
python - <<'PY'
from pathlib import Path
import yaml
import openapi_spec_validator
from openapi_spec_validator import validate
spec = yaml.safe_load(Path('bgg-shop-bff/specs/openapi.yaml').read_text())
print('OpenAPI validator version:', openapi_spec_validator.__version__)
print('Document version:', spec['openapi'])
validate(spec)
print('PASS: BFF OpenAPI parsed and validated')
PY
```

Additional observed check: `git -C bgg-shop-core diff --check -- specs/schema.graphql && git -C bgg-shop-bff diff --check -- specs/openapi.yaml` passed after the final contract edits. No feature behavior tests were run for this contract-only change.

## Phase 3: Core

- [x] **T011 [Core] [DONE — tests authored, expected RED observed]** After T007 and T010, author deterministic Core tests first for Superadmin-only listing/selection and privilege changes; positive active `is_superuser=true, is_staff=false`; negative unauthenticated, inactive, staff-only, and operation-key-only contexts; case-insensitive substring search across email, first name, and last name; stable ascending user-ID cursor pagination with next-page continuation, default limit 50, and maximum 100; invalid search, limit, and cursor inputs returning `INVALID` with `field`; grant/revoke of each flag while preserving the other; no implicit staff enablement; no partial updates when rejecting last-superuser revocation; self-demotion with another active Superadmin; concurrent revocations; active-session authorization freshness; and sanitized authorization and `LAST_ACTIVE_SUPERUSER` errors that expose no traceback, internal URL, credential/password/secret, or DSN. **Depends on**: T007, T010. **Acceptance/evidence**: all approved behaviors have focused assertions. `python -m py_compile tests/test_user_permissions_postgres.py` passed. With a fresh loopback-only disposable PostgreSQL container, `pytest -q tests/test_user_permissions_postgres.py` produced 20 expected failures because the runtime GraphQL operations are not yet implemented and 1 passing registration test; no unexpected failures or skips. An independent reviewer reproduced the same result and verified container cleanup. This is TDD RED, not implementation evidence. Trace: FR-001–FR-009, FR-011; US1–US3.
- [ ] **T012 [Core] [READY — Core implementation]** After T011 failures and T010 approval, implement only the approved Core contract and behavior. Enforce authenticated, active `is_superuser=true` independently of `is_staff`; preserve the untouched privilege; enforce the last-active-superuser invariant atomically under concurrency; and make saved changes effective for subsequent authorization checks in active sessions. Preserve already-correct operational staff access; do not introduce employee creation, a new role model, or unrelated access changes. **Acceptance**: unauthorized reads/writes and partial denied updates are absent; local disposable fixtures prove the invariant. Trace: FR-001–FR-008, FR-011; US1–US3.
- [ ] **T013 [Core] [BLOCKED]** Run and record applicable Core pytest checks from T007, including independent flag updates, positive active superuser without staff, authorization negatives, last-superuser denial/self-demotion/concurrency, and session freshness. **Acceptance**: focused local checks pass or failures are accurately recorded; no non-local environment is used. Trace: SC-001–SC-007.

## Phase 4: BFF

- [ ] **T014 [BFF] [READY — tests first]** After T007 and T010, author deterministic BFF tests first for Superadmin-only listing and privilege changes, identity propagation, independent flag updates, inactive and operation-key-only contexts, last-superuser denials, and public errors that exclude upstream details, exceptions, traces, internal URLs, and credentials. **Depends on**: T007, T010. **Acceptance**: expected failures are observed before behavior implementation; use disposable local data. Trace: FR-001–FR-006, FR-008–FR-009, FR-011; US1–US3.
- [ ] **T015 [BFF] [BLOCKED]** After T014 failures and T010 approval, implement only the approved OpenAPI-backed BFF operations and Core delegation. Enforce the identity boundary at the BFF as well as Core, do not treat UI controls or an operation key alone as authorization, preserve the unmodified privilege, and sanitize errors without exposing credentials/secrets. **Acceptance**: denied requests cause no downstream privilege change and public errors disclose no sensitive upstream details. Trace: FR-001–FR-006, FR-008–FR-009, FR-011; US1–US3.
- [ ] **T016 [BFF] [BLOCKED]** Run and record applicable BFF pytest checks from T007, including active Superadmin with `is_staff=false`, staff-only and other unauthorized negatives, independent flag updates, last-superuser denial, and error non-disclosure. **Acceptance**: focused local checks pass or failures are accurately recorded. Trace: SC-001–SC-007.

## Phase 5: Frontend

- [ ] **T017 [Frontend] [READY — generated types]** After T010 approves the BFF contract, generate Frontend API types with the existing `npm run generate:types`; do not hand-edit generated contract types. **Acceptance**: generated output corresponds to approved OpenAPI and generation/type issues are recorded; no UI behavior is implemented yet. Trace: FR-003–FR-009; US1–US3.
- [ ] **T018 [Frontend] [BLOCKED]** After T007 and T017, author deterministic UI tests first for Superadmin-only user listing/search/selection, independent staff and superuser controls, grant/revoke and failure states, and no employee-onboarding flow. Verify operational modules remain available to staff while privilege-management data/actions are hidden from staff. **Depends on**: T007, T017. **Acceptance**: tests exercise the approved contract and never treat hidden controls as an authorization control. Trace: FR-003–FR-009; US1–US3.
- [ ] **T019 [Frontend] [BLOCKED]** After T018 failures and Core/BFF behavior, implement the CU-A04 interface using generated BFF types. Provide user selection and independent privilege updates only to Superadmins; preserve visible operational access for staff; clearly distinguish saved from failed changes and never expose credentials or personnel selection data to staff. **Acceptance**: user-visible state matches server outcomes and UI restrictions supplement, but never replace, backend guards. Trace: FR-003–FR-009, FR-011; US1–US3.
- [ ] **T020 [Frontend] [BLOCKED]** Run and record applicable Frontend npm tests and build checks from T007. **Acceptance**: local checks pass or failures are recorded; generated types are not manually altered to mask contract drift. Trace: SC-003, SC-005–SC-007.

## Phase 6: Local integration and evidence

- [ ] **T021 [Orchestrator] [BLOCKED]** Coordinate local integration checks after all service checks. Verify denial for unauthenticated, inactive, staff-only, and operation-key-only callers; positive active `is_superuser=true, is_staff=false`; listing privacy; independent privilege grants/revocations and flag preservation; staff operational parity without privilege-management access; last-superuser denial and self-demotion; concurrent revocations and no partial updates; and changed authorization in existing sessions. Use disposable fixtures and exact local commands/selectors from T007. **Acceptance**: every applicable case has observed evidence, deviations are recorded, and no staging, production, CI, remote system, real personal data, or fixture secrets are used. Trace: FR-001–FR-011; SC-001–SC-007.

## Dependency and execution rules

- T004–T006 are complete, independent read-only investigations. T001–T003 are complete records of explicit user decisions; no business-policy decision blocks planning.
- T007 depends on the three current-state investigations. T008/T009 depend on T007 and update the canonical owning contracts. T010 independently validated both contracts; T011, T014 and T017 are now ready for their ordered work.
- Within each service, author deterministic tests before behavior when a clear runnable expected result exists; observe failing tests before implementation. Use existing Core pytest, BFF pytest, and Frontend npm test/build tooling. T007 must identify exact files, selectors, and commands.
- Core and BFF must each enforce the active authenticated `is_superuser=true` requirement. A staff-only identity is denied; `is_staff=true` is not additionally required for an active Superadmin. UI hiding is not an authorization boundary.
- Staff operational parity is intentional. Investigate existing behavior and change operational modules only if a verified gap directly violates the approved parity requirement.
- Independent flags, last-active-superuser safety, immediate subsequent-check effectiveness, and sanitized public errors must follow this specification. Any technical implementation mechanism is a planning/contract decision, not an open business-policy choice.
- Use only local environments and disposable test data. Record checks actually run; decision approval is not functional verification.
