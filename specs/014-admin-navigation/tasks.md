# Tasks: Admin Navigation and Discoverability

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), and [approved contract design draft](contracts/admin-session.openapi.yaml)<br>
**Status**: T001–T015 complete for the scoped feature slice; T012 passed isolated local Frontend→BFF→Core verification. Evidence and limits are in [quickstart.md](quickstart.md).<br>
**Branch**: `014-admin-navigation`<br>
**Scope**: Local environments only. BFF and Frontend implementation/contracts/tests changed; Core source and contract did not. A disposable local PostgreSQL database was used for isolated auth-path verification and destroyed afterward. No commit is claimed for the observed checks.

## Delivery and contract gates

- **Delivery strategy**: Local feature commits authorized by the user on 2026-11-09 after validation; no push or pull request is authorized.
- **Local service commits**: BFF `3c8500f` (T006–T008), Frontend `5fce047` (T009–T015), Core `8d8446b` (T001 documentation only). All use branch `014-admin-navigation`; verification evidence predates packaging and is recorded in [quickstart.md](quickstart.md).
- **Canonical contracts**: Core SDL remains unchanged. T006 promoted the approved BFF endpoint design to canonical OpenAPI and locally validated it before endpoint implementation. Styling creates no new backend contract or persistence requirement.
- **Test-first**: T007 observed the deterministic BFF tests fail before implementation; T008 now passes them. Frontend T010 also recorded RED before T011 implemented the role-aware navigation; see [quickstart.md](quickstart.md) for before/after evidence.
- **Implementation evidence**: BFF T006–T008 and Frontend T009–T015 are complete. T012's integration evidence is limited to the auth/capability path and explicitly does not certify full admin CRUD or full Core migration bootstrap; see [quickstart.md](quickstart.md).
- **Local-only verification**: Use repository-local pytest, Vitest/build, and the existing local Playwright wrapper. Do not use staging, production, CI, remote APIs, or real personal data.
- **Public error hygiene**: Any future public error must omit upstream response bodies, exceptions, traces, internal URLs, and credentials; add negative assertions for these cases.
- **Styling scope and discretion**: US6 extends current storefront identity to products, promotions, coupons, gift cards, audit, sales, reviews, and users. Exact pixels are design choices, not user-approved mockups. No mandatory mockup sign-off or new UI dependency/design-system architecture; ask only about genuine uncertainty. Preserve Spanish labels, routes, CRUD, and role policy.
- **Presentation and integration tracks**: T013–T015 cover local browser presentation checks. T012 additionally passed a live isolated Frontend→BFF→Core capability-path check with synthetic accounts and no API mocks on `/auth/me`; this is not full-module live CRUD or full Core migration validation.

## Backlog status and ownership

Global task IDs, status, owner, and dependencies are identical in the master and service task documents. Cross-repository dependencies refer to these global IDs.

| ID | Owner | Status | Depends on | Trace |
|---|---|---|---|---|
| T001 | Core | DONE — investigation only | — | FR-002, FR-011; US4 |
| T002 | BFF | DONE — investigation only | — | FR-001–FR-002, FR-008, FR-011–FR-012; US1, US4 |
| T003 | Frontend | DONE — investigation only | — | FR-001–FR-010, FR-013; US1–US5 |
| T004 | Orchestrator | DONE — planning artifact | T001–T003 | All FRs; SC-001–SC-008 |
| T005 | Orchestrator | DONE — design approval recorded 2026-11-09 | T001–T004 | FR-001–FR-002, FR-008–FR-012; US1, US3–US4 |
| T006 | BFF | DONE — canonical contract | T005 | FR-001–FR-002, FR-008, FR-011–FR-012; US1, US4 |
| T007 | BFF | DONE — RED observed | T006, T002 | FR-001–FR-002, FR-008, FR-011–FR-012; US1, US4 |
| T008 | BFF | DONE — implementation | T007, T006 | FR-001–FR-002, FR-008, FR-011–FR-012; US1, US4 |
| T009 | Frontend | DONE — generated types | T006 | FR-001–FR-002, FR-008, FR-011; US1, US3–US4 |
| T010 | Frontend | DONE — tests observed RED/GREEN | T009, T003 | FR-001–FR-010, FR-013; US1–US5 |
| T011 | Frontend | DONE — implementation | T010, T008 | FR-001–FR-010, FR-013; US1–US5 |
| T012 | Frontend | DONE — scoped local integration verified | T011, T008, T015 | FR-001–FR-017; US1–US6; SC-001–SC-012 |
| T013 | Frontend | DONE — styling inventory and assertions | T003 | FR-014–FR-017; US6; SC-009–SC-012 |
| T014 | Frontend | DONE — shared and panel styling | T013 | FR-014–FR-017; US6; SC-009–SC-012 |
| T015 | Frontend | DONE — local visual and accessibility verification | T014 | FR-014–FR-017; US6; SC-009–SC-012 |

## Completed planning investigations

- [x] **T001 [Core] [DONE — investigation only]** Confirm whether Core already exposes active/staff/Superadmin state for the authenticated principal. **Evidence**: `bgg-shop-core/specs/schema.graphql:427-429, 554-561` exposes `Query.me` and `User.isActive/isStaff/isSuperuser`; `bgg-shop-core/saleor/graphql/api.py:1460-1464` resolves `me` through `_authenticated_user`. No Core SDL or runtime change is planned. **Trace**: FR-002, FR-011; US4.
- [x] **T002 [BFF] [DONE — investigation only]** Identify the current BFF identity projection and an existing Core role lookup pattern. **Evidence**: `bgg-shop-bff/specs/openapi.yaml:3764-3785` defines login `AuthUser` with `is_active` but not staff/superuser flags; `bgg-shop-bff/src/proxy.py:1175-1218` contains the existing `me` role-check pattern. T005 later records approval of the additive endpoint design; T006/T008 subsequently promote and implement it. **Trace**: FR-001–FR-002, FR-008, FR-011–FR-012; US1, US4.
- [x] **T003 [Frontend] [DONE — investigation only]** Inventory storefront role visibility, admin route shell, and reusable tasks. **Evidence**: `bgg-shop-frontend/src/App.tsx:708-724` lacks an admin entry; `src/App.tsx:880-889` gates admin routes by token presence; `src/admin/AdminRouter.tsx:1-34` has existing admin destinations but renders its links only at `/admin`. Product, coupon, and user panels already exist. **Trace**: FR-001–FR-010, FR-013; US1–US5.
- [x] **T004 [Orchestrator] [DONE — planning artifact]** Create the feature spec, research, plan, data model, draft BFF contract, quickstart, and master/service task documents; update only the Spec Kit plan marker. **Evidence**: Planning deliverables in this directory and the three service task files; no runtime source or canonical contract changed. Structural checks are recorded in the completion response. **Trace**: All FRs; SC-001–SC-008.

## Completed planning decision

- [x] **T005 [Orchestrator] [DONE — design approval recorded 2026-11-09]** Record the user's approval of the `GET /api/v1/auth/me` design: only `is_staff` and `is_superuser` from current Core state; active bearer identity; `401` for missing, invalid, or inactive identity; sanitized `502` for failed Core identity resolution; `Cache-Control: no-store` on all outcomes; operation-key-only access rejected; owning backends continue authorizing each operation. **Historical evidence**: At approval time this was design-only; T006/T007/T008 subsequently promoted the contract, observed RED, and implemented the endpoint. **Evidence**: Q/A in [spec.md](spec.md#clarifications), research decision, and draft contract metadata. **Trace**: FR-001–FR-002, FR-008–FR-012; US1, US3–US4.

## Contract and implementation tasks
- [x] **T006 [BFF] [DONE — canonical contract]** Promoted the T005-approved design to canonical `bgg-shop-bff/specs/openapi.yaml`. **Evidence**: Local PyYAML parse and assertions passed for operation ID, bearer-only security, 200/401/502 responses, no-store headers on each response, and the exact two-boolean schema. Core SDL remains unchanged. **Depends on**: T005. **Trace**: FR-001–FR-002, FR-008, FR-011–FR-012; US1, US4.
- [x] **T007 [BFF] [DONE — RED observed]** Added deterministic route/proxy tests for staff, Superadmin with `is_staff=false`, buyer, strict bearer validation, operation-key-only access, inactive/null/unauthenticated Core responses, malformed payloads, role revocation, sanitized upstream errors, proxy headers/query, and non-cacheable responses. **Evidence**: Before implementation, 27 new endpoint tests failed and 17 existing auth tests passed; the failures were the unimplemented route. The endpoint/auth suite subsequently passed all 44 tests. **Depends on**: T006, T002. **Trace**: FR-001–FR-002, FR-008, FR-011–FR-012; US1, US4.
- [x] **T008 [BFF] [DONE — implementation]** Implemented `GET /api/v1/auth/me` using Core `Query.me`, current active/staff/superuser state, bearer-only authentication, sanitized 401/502 errors, operation-key bypass, and no-store responses. **Evidence**: Focused auth and operation-key regression suite passed 89 tests. **Depends on**: T007, T006. **Trace**: FR-001–FR-002, FR-008, FR-011–FR-012; US1, US4.
- [x] **T009 [Frontend] [DONE — generated types]** Ran `npm run generate:types` after T006 promoted the canonical BFF OpenAPI contract; `CurrentUserCapabilities` derives exactly `{ is_staff: boolean; is_superuser: boolean }`. Generated output was not edited manually. **Trace**: FR-001–FR-002, FR-008, FR-011; US1, US3–US4.
- [x] **T010 [Frontend] [DONE — tests observed RED/GREEN]** Added deterministic role, shared-shell, direct-route, denied-Users, loading/error/malformed/401/502/network/retry, logout/session-race/denial, and product/coupon route tests. The initial focused run observed 13 failing tests and 1 passing before implementation; all focused and full-suite tests subsequently passed. **Trace**: FR-001–FR-010, FR-013; US1–US5.
- [x] **T011 [Frontend] [DONE — implementation]** Added current-user-backed storefront entry and shared role-aware shell, fail-closed pending/error/forbidden routes, in-memory invalidation/revalidation, and guarded all admin URLs. Reused the eight existing modules without modifying service authorization. **Trace**: FR-001–FR-010, FR-013; US1–US5; layout integration with US6 / FR-016.
- [x] **T012 [Frontend] [DONE — scoped local integration verified]** Unit and browser checks verified role/session behavior, route protection, existing destinations, and all eight styled modules at the four required viewports. An independent isolated local run then exercised the live Frontend→BFF→Core `/api/v1/auth/me` path with synthetic accounts and no API mocks on that path: active staff, buyer, and superuser (including superuser with `is_staff=false`); exact role fields and no-store; missing/invalid/inactive/operation-key-only `401`; staff denial without a personnel-list request; shared operational navigation; same-bearer self-demotion on reentry; logout `204`; and read-only DB confirmation that saved flags remained active=true, staff=false, superuser=false. This accepts the feature slice, not all eight modules' live CRUD or full Core migration bootstrap. The temporary harness and disposable services/database were removed. **Evidence and limits**: [quickstart.md](quickstart.md). **Trace**: FR-001–FR-017; US1–US6; SC-001–SC-012.

## Frontend styling tasks

- [x] **T013 [Frontend] [DONE — styling inventory and tests]** Inventoried the eight existing module surfaces, forms, lists, filters, feedback and keyboard/table needs. Added deterministic shell/role/route assertions that failed before implementation; visual preferences and contrast were verified in Chromium rather than simulated as unit-test RED. **Depends on**: T003. **Trace**: FR-014–FR-017; US6; SC-009–SC-012.
- [x] **T014 [Frontend] [DONE — shared and panel styling]** Applied scoped shared administration styling and local scroll regions to all existing wide tables; preserved Spanish labels, routes, role/CRUD/request behavior, and existing confirmations. Added no dependency, storage, or endpoint. **Depends on**: T013. **Trace**: FR-014–FR-017; US6; SC-009–SC-012.
- [x] **T015 [Frontend] [DONE — local visual and accessibility verification]** Chromium assertions covered all eight modules and product/promotion/coupon forms at 1280×720, 768×1024, 375×812, and 320×720; no page-wide horizontal overflow or clipped shell was observed. Keyboard focus, current navigation, error feedback, and computed text/boundary/focus contrast were checked. **Depends on**: T014. **Trace**: FR-014–FR-017; US6; SC-009–SC-012.

## Service task documents

- [Core task document](../../bgg-shop-core/specs/014-admin-navigation/tasks.md)
- [BFF task document](../../bgg-shop-bff/specs/014-admin-navigation/tasks.md)
- [Frontend task document](../../bgg-shop-frontend/specs/014-admin-navigation/tasks.md)
