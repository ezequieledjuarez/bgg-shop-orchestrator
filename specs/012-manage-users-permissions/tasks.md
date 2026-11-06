# Tasks: Manage Users and Permissions (CU-A04)

**Input**: [spec.md](spec.md), [requirements checklist](checklists/requirements.md)
**Status**: T004–T021 are complete, including local PostgreSQL GREEN verification, test-first evidence, independent BFF authorization verification, the full frontend suite/build, and nine isolated local Chromium scenarios. T013's broader Core checks had three unrelated existing failures, which are recorded.
**Branch**: `012-manage-users-permissions` in the orchestrator and all three service repositories.
**Scope**: Local environments and disposable test data only. No staging, production, CI, remote validation, or real personal data.

## Delivery strategy

- **Strategy**: `ask-on-risk`; the user selected `stacked-to-main` as the chain strategy on 2026-11-06 after the projected authored feature diff exceeded approximately 400 lines.
- **PR slicing**: Slice boundaries are not established yet. No push or PR creation is authorized.

## Work-unit commits

- **Contracts and T010 validation**: Core `7ee655e`, BFF `93d761a`, orchestrator docs `35e8fa3`.
- **T011 Core tests / expected RED**: Core `d8247f2`; orchestrator evidence `dcac07e`.
- **Feature implementation and initial integration evidence**: Core `73cae83`, BFF `110af16`, Frontend `48df07d`, orchestrator `2e1edce`.
- **T021 concurrent full-stack E2E proof**: Frontend `501aa6a`; orchestrator harness and evidence `6f1af5a`.

## Backlog status and gates

The three decision tasks are complete as records of explicit user approvals only; they are not implementation or test evidence. T004–T006 are complete read-only investigations, with evidence recorded below. T007 is complete as a technical planning artifact only. T008/T009 are complete as approved canonical contract work using the exact user-approved decisions recorded below. T010 passed independent validation. T011's tests are authored and their expected RED was independently reproduced against disposable PostgreSQL. T012 implementation and the dedicated PostgreSQL regression file are locally verified; T013's broader Core check results, including unrelated failures, are recorded below. T014 and T018 have authored tests with expected RED observed; T017 generated API types from the approved OpenAPI. T019/T020 frontend implementation and checks passed. T015/T016 BFF behavior and independent authorization checks passed; T021's full-stack integration scenarios, including concurrent revocations, passed in the isolated local harness.

The applicable canonical contracts remain Core `bgg-shop-core/specs/schema.graphql` and BFF `bgg-shop-bff/specs/openapi.yaml`; both contain the approved CU-A04 contract and passed structural and independent cross-contract validation. The Frontend generates types from the BFF OpenAPI using the existing `npm run generate:types` command; generated types now include both approved user-admin endpoints. Core runtime implementation and PostgreSQL tests are locally verified for T012; frontend implementation passed the focused tests/lint/typecheck and broader 228-test suite/build. BFF authorization now delegates directly to Core and maps Core `UNAUTHENTICATED`/`FORBIDDEN` errors to 401/403; its independent regression run passed 83 tests. The isolated local E2E runner passed all nine Chromium scenarios covering flag persistence, staff authorization and operational access, same-bearer denial after self-demotion, missing and invalid authentication, operation-key-only and inactive-user denial, last-active-Superadmin denial with 409 and unchanged state, and concurrent self-demotions with exactly one 200, one `LAST_ACTIVE_SUPERUSER` 409, preserved rejected-actor flags, and exactly one active Superadmin. The race test was added first and observed RED (eight passed, one failed because race fixtures were absent); after adding two synthetic seed actors the exact harness command passed all nine. Cleanup verified owned processes exited, the unique tmpfs PostgreSQL container/database were removed, and the run directory was deleted. T013's three unrelated broader Core failures remain recorded; no other T021 scenario remains pending.

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
| T012 | Core | DONE — implementation and PostgreSQL regressions locally verified | T011, T010 | FR-001–FR-008, FR-011; US1–US3 |
| T013 | Core | DONE — checks run; unrelated failures recorded | T012 | SC-001–SC-007 |
| T014 | BFF | DONE — tests authored, expected RED observed | T007, T010 | FR-001–FR-006, FR-008–FR-009, FR-011; US1–US3 |
| T015 | BFF | DONE — implementation and independent review passed | T014, T012 | FR-001–FR-006, FR-008–FR-009, FR-011; US1–US3 |
| T016 | BFF | DONE — independent regression verification | T015 | SC-001–SC-007 |
| T017 | Frontend | DONE — generated types | T010 | FR-003–FR-009; US1–US3 |
| T018 | Frontend | DONE — tests authored, expected RED observed | T007, T017 | FR-003–FR-009; US1–US3 |
| T019 | Frontend | DONE — implementation and focused checks passed | T018, T012, T015 | FR-003–FR-009, FR-011; US1–US3 |
| T020 | Frontend | DONE — local suite and build passed | T019 | SC-003, SC-005–SC-007 |
| T021 | Orchestrator | DONE — nine isolated local E2E scenarios passed, including concurrent revocations | T013, T016, T020 | FR-001–FR-011; SC-001–SC-007 |

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
- [x] **T012 [Core] [DONE — implementation and PostgreSQL regressions locally verified]** After T011's expected RED and T010 approval, preserve the approved Core contract: enforce active bearer Superadmin authority independently of `is_staff`, preserve the untouched flag, retain atomic last-active-superuser protection and subsequent-request privilege freshness, and leave operational staff access unchanged. Serialize every `is_superuser` privilege write with a transaction-scoped PostgreSQL advisory lock before materializing the active-superuser set; the subsequent READ COMMITTED query observes committed updates. Catch `DatabaseError` outside failed atomic transactions (and narrowly around list evaluation), log only static messages, and return generic safe `SERVER_ERROR` results without exception details or success-shaped fallbacks. **Evidence**: On a disposable loopback PostgreSQL 15 container started with `--pull=never`, the three focused regressions passed (3 passed, 21 deselected), the full `python -m pytest -q tests/test_user_permissions_postgres.py` passed (24 passed), and `python -m py_compile saleor/graphql/api.py` passed. The first implementation attempt found a missing import (one focused regression failed); it was corrected before the green rerun. Trace: FR-001–FR-008, FR-011; US1–US3.
- [x] **T013 [Core] [DONE — checks run; unrelated failures recorded]** Run applicable Core checks for flag updates, Superadmin authorization, last-superuser concurrency, and session freshness. **Evidence**: `python -m pytest -q tests/test_graphql_auth.py tests/test_graphql_products.py` returned 55 passed and 3 failed. The failures were outside T012: one pre-existing review SDL description mismatch, and two product-review SQL assertions expecting `APPROVED` while the implementation uses `ACCEPTED`. Runtime behavior changed in `bgg-shop-core/saleor/graphql/api.py` during T012; the canonical reference SDL `bgg-shop-core/specs/schema.graphql` was unchanged. Neither broader-check test file (`bgg-shop-core/tests/test_graphql_auth.py`, `bgg-shop-core/tests/test_graphql_products.py`) was modified. Dedicated T012 regressions are in `bgg-shop-core/tests/test_user_permissions_postgres.py`. Checks used only a disposable loopback PostgreSQL 15 database. Trace: SC-001–SC-007.

## Phase 4: BFF

- [x] **T014 [BFF] [DONE — tests authored, expected RED observed]** After T007 and T010, author deterministic BFF tests first for Superadmin-only listing and privilege changes, identity propagation, independent flag updates, inactive and operation-key-only contexts, last-superuser denials, and public errors that exclude upstream details, exceptions, traces, internal URLs, and credentials. **Evidence**: `PYTHONPATH=. pytest tests/test_admin_users.py -q` from `bgg-shop-bff/` returned 11 failed; all requests reached expected-status assertions and returned 405 because user-admin routes are not implemented. The BFF virtualenv could not collect because `redis` is missing, so system pytest was used. Trace: FR-001–FR-006, FR-008–FR-009, FR-011; US1–US3.
- [x] **T015 [BFF] [DONE — implementation and independent review passed]** After T014 failures and T010 approval, implement the approved OpenAPI-backed BFF operations and Core delegation. The personnel routes send bearer credentials directly to Core; Core's structured `UNAUTHENTICATED` and `FORBIDDEN` errors map to HTTP 401 and 403 respectively. Operation-key forwarding remains disabled for these endpoints, independent flag updates and safe projection are preserved, and public errors are sanitized. **Evidence**: independent review found no significant issue; focused and broader BFF suites passed (15 and 83 tests respectively); `py_compile` and `git diff --check` passed. Trace: FR-001–FR-006, FR-008–FR-009, FR-011; US1–US3.
- [x] **T016 [BFF] [DONE — independent regression verification]** Run and record applicable BFF checks for active Superadmin with `is_staff=false`, staff-only and other unauthorized negatives, independent flag updates, last-superuser denial, and error non-disclosure. **Evidence**: independent `PYTHONPATH=. pytest tests/test_admin_users.py tests/test_admin.py tests/test_admin_error_mapping.py tests/test_opkey_admin.py -q` returned 83 passed; `python -m py_compile src/auth.py src/controllers/admin_users_controller.py` and `git diff --check` passed. 71 existing datetime deprecation warnings were emitted. Trace: SC-001–SC-007.

## Phase 5: Frontend

- [x] **T017 [Frontend] [DONE — generated types]** After T010 approves the BFF contract, generate Frontend API types with the existing `npm run generate:types`; do not hand-edit generated contract types. **Evidence**: `npm --prefix bgg-shop-frontend run generate:types` passed with openapi-typescript 7.13.0, adding the approved `/api/v1/admin/users` and `/api/v1/admin/users/{user_id}/privileges` paths and schemas to `src/types/generated/bff-api.d.ts`; `git diff --check -- src/types/generated/bff-api.d.ts` passed. No UI behavior was implemented. Trace: FR-003–FR-009; US1–US3.
- [x] **T018 [Frontend] [DONE — UI tests authored, expected RED observed]** After T007 and T017, author deterministic UI tests first for user listing/search/selection, independent staff and superuser controls, grant/revoke and failure states, operational navigation, and no employee-onboarding flow. **Evidence**: `npm --prefix bgg-shop-frontend test -- --run src/admin/users/UserManagementPanel.test.tsx` returned 4 expected failures because `/admin/users` does not yet render the panel/error state; imports resolved and no runtime UI code changed. The frontend session contract does not expose actor roles, so the tests do not claim client-side role hiding is authorization. Trace: FR-003–FR-009; US1–US3.
- [x] **T019 [Frontend] [DONE — implementation and focused checks passed]** Implement the CU-A04 interface using generated BFF types. Provide user selection and independent privilege updates only after the backend permits listing; preserve visible operational access for staff; clearly distinguish saved from failed changes and never expose credentials or personnel selection data to staff. The frontend session contract does not expose roles, so rely on the server response rather than inventing client-side role claims. **Evidence**: focused Vitest passed 4/4; focused ESLint passed with 0 warnings/errors; `tsc -b bgg-shop-frontend/tsconfig.app.json` passed; `git diff --check` passed. No full build was run. Trace: FR-003–FR-009, FR-011; US1–US3.
- [x] **T020 [Frontend] [DONE — local suite and build passed]** Run and record remaining applicable Frontend npm tests/build checks from T007. **Evidence**: `npm --prefix bgg-shop-frontend test -- --run` passed (22 files, 228 tests); two MSW unhandled-request warnings were emitted. `npm --prefix bgg-shop-frontend run build` passed (TypeScript and Vite); `git -C bgg-shop-frontend diff --check` passed. Trace: SC-003, SC-005–SC-007.

## Phase 6: Local integration and evidence

- [x] **T021 [Orchestrator] [DONE — nine isolated local E2E scenarios passed]** Coordinate local integration checks after all service checks. **Test-first RED**: after adding the concurrent-revocation Playwright case but before adding its seed actors, `bash scripts/run-spec012-local-e2e.sh` returned exit 1 with eight scenarios passing and the new case failing because the two race accounts were absent. **GREEN**: after adding only two synthetic active non-staff Superadmin seed accounts, the same exact command passed all nine Chromium scenarios: (1) active non-staff Superadmin changes both flags independently and persistence is checked; (2) staff receives 403 without personnel data and retains an operational route; (3) self-demotion denies the next request using the identical bearer; (4) missing authentication receives 401; (5) an invalid bearer receives 401; (6) a fake operation-key-only request receives 403; (7) an inactive user with a valid bearer receives 403; (8) revoking the last active Superadmin is denied with 409 and state unchanged; and (9) two independently authenticated remaining Superadmins concurrently self-demote, producing exactly one HTTP 200 and one HTTP 409 with `LAST_ACTIVE_SUPERUSER`; the successful actor loses superuser, the rejected actor retains both original flags, and exactly that rejected actor remains an active Superadmin verified with its still-active bearer. Setup uses an existing synthetic Superadmin to revoke other synthetic active Superadmins before relinquishing its own role, so unrelated fixtures are not authorization survivors. The runner used only synthetic accounts, a unique loopback-only tmpfs PostgreSQL container, random loopback service ports, isolated Playwright state and cached Chromium. GREEN cleanup verified owned Core/BFF/Frontend/Playwright processes exited, the PostgreSQL container/database were removed without volumes, and the unique temporary run directory was deleted. The test is repeatable in the serial harness; no timing-only assertion is used. Trace: spec `specs/012-manage-users-permissions/spec.md` (FR-001–FR-011; SC-001–SC-007); implementation `bgg-shop-core/saleor/graphql/api.py`, `bgg-shop-bff/src/controllers/admin_users_controller.py`; E2E test `bgg-shop-frontend/tests/e2e/admin-users.spec.ts`; harness `scripts/run-spec012-local-e2e.sh`.

## Dependency and execution rules

- T004–T006 are complete, independent read-only investigations. T001–T003 are complete records of explicit user decisions; no business-policy decision blocks planning.
- T007 depends on the three current-state investigations. T008/T009 depend on T007 and update the canonical owning contracts. T010 independently validated both contracts; T011–T013 are complete, while T014 and T017 are ready for their ordered work.
- Within each service, author deterministic tests before behavior when a clear runnable expected result exists; observe failing tests before implementation. Use existing Core pytest, BFF pytest, and Frontend npm test/build tooling. T007 must identify exact files, selectors, and commands.
- Core and BFF must each enforce the active authenticated `is_superuser=true` requirement. A staff-only identity is denied; `is_staff=true` is not additionally required for an active Superadmin. UI hiding is not an authorization boundary.
- Staff operational parity is intentional. Investigate existing behavior and change operational modules only if a verified gap directly violates the approved parity requirement.
- Independent flags, last-active-superuser safety, immediate subsequent-check effectiveness, and sanitized public errors must follow this specification. Any technical implementation mechanism is a planning/contract decision, not an open business-policy choice.
- Use only local environments and disposable test data. Record checks actually run; decision approval is not functional verification.
