# Tasks: CU-A03 — Moderate Content and Reviews

**Input**: `specs/011-moderate-content-reviews/{spec,plan,research,data-model,quickstart}.md` and the two planning drafts in `contracts/`.
**Planning status**: T001–T015 are recorded complete below, including T012 independent review and the isolated T015 local journey. T006's PostgreSQL migration integration tests previously passed against an isolated disposable loopback database. T008–T010 tests were authored and their expected RED was observed; T011's focused Core review tests now pass. T016–T031 remain pending, with T016 next. The approved Core and BFF definitions are promoted and locally validated.
**Scope**: Local project only. Do not run staging, production, CI, or remote validation.
**Tests**: Included because the specification and quickstart require independent functional evidence.

Tasks are dependency-ordered and grouped by user story. Project ownership is stated in each task. `[P]` indicates that the task can run in parallel with other marked tasks in its group after its listed prerequisites.

## Phase 1: Setup — Confirmed Design and Engineering Evidence

**Purpose**: The user decisions are resolved. Establish the bounded cache-retry integration before BFF implementation; do not treat this as a user-approval gate.

- [x] T001 [P] bgg-shop-bff: Inspect existing local retry/background/event integration points for shared catalog-cache invalidation; document the concrete bounded retry path, terminal pending behavior, and relevant test seam in `specs/011-moderate-content-reviews/plan.md`. The documented engineering default is at most two synchronous calls to the existing generation invalidation helper (initial call plus one immediate retry); no new service or background/outbox work. If both calls fail after Core commits, return committed success with `cache_refresh_pending=true`. Structural documentation readback only; no tests or implementation were run.

## Phase 2: Foundational — Approved Contracts and Shared Prerequisites

**Purpose**: Promote the confirmed planning drafts into owning service contracts and establish the reversible storage migration before story implementation.

- [x] T002 [P] Shared/Contracts: Promote the confirmed Core review queue, action, authorization, error, and public aggregation definitions from `specs/011-moderate-content-reviews/contracts/core-review-moderation.graphql` into `bgg-shop-core/specs/schema.graphql`.
- [x] T003 [P] Shared/Contracts: Promote the confirmed BFF queue/action routes, request/response shapes (including `cache_refresh_pending`), authorization, error mapping, and `Cache-Control: no-store` definitions from `specs/011-moderate-content-reviews/contracts/bff-openapi.yaml` into `bgg-shop-bff/specs/openapi.yaml`.
- [x] T004 Shared/Contracts: Validate the updated canonical SDL and OpenAPI contract using the Core GraphQL parser and BFF OpenAPI validator; both accepted the promoted definitions (depends on T002 and T003).
- [x] T005 [P] bgg-shop-core: Add migration-focused tests for the exact reversible mapping `PENDING→PENDING`, `APPROVED→ACCEPTED`, `HIDDEN→REJECTED`, and `DELETED→REJECTED` plus `is_deleted=true`, including deterministic rollback and public eligibility, in `bgg-shop-core/tests/test_graphql_reviews.py` (depends on T004; write before T006). The focused run observed the expected RED because the target migration is absent; the three database-backed tests skipped because `CREDIT_TEST_POSTGRES_DSN` is not set.
- [x] T006 bgg-shop-core: Implement the reversible status migration, separate `is_deleted BOOLEAN NOT NULL DEFAULT FALSE`, three-status constraint, accepted/non-deleted public index, and Core query filters in `import_catalog.sql`, `bgg-shop-core/saleor/graphql/api.py`, and a numbered migration under `bgg-shop-core/saleor/graphql/migrations/`. Rollback maps any marked row→`DELETED`; unmarked `PENDING→PENDING`, `ACCEPTED→APPROVED`, and `REJECTED→HIDDEN`; no deletion timestamp is added (depends on T005). Focused review tests and all three PostgreSQL migration integration tests passed locally.
- [x] T007 [P] bgg-shop-frontend: Regenerate API types from the approved canonical BFF OpenAPI contract into `bgg-shop-frontend/src/types/generated/bff-api.d.ts` with `cd bgg-shop-frontend && npm run generate:types` (depends on T004). Generation and the TypeScript no-emit check passed; the generated diff contains only moderation API definitions.

**Checkpoint**: T001–T007 are complete; implementation may proceed to User Story 1. This ledger does not authorize implementation beyond its tracked tasks.

## Phase 3: User Story 1 — Review the Queue and Accept a Review (Priority: P1, MVP)

**Goal**: An active staff/superuser can inspect a bounded moderation queue and accept a pending review; the accepted review and public summary refresh without exposing other states publicly.

**Independent Test**: With local fixtures, verify the moderator-only queue includes game, review body, rating, and status; an empty queue is clear; accepting a pending review makes it visible in public detail and updates the accepted-only count/average after cache invalidation.

### Tests — write before implementation

- [x] T008 [P] [US1] bgg-shop-core: Add tests for active staff/superuser identity authorization (including rejection of operation-key-only/no-user context), queue fields/filter/pagination, empty results, pending acceptance, and accepted-only public detail aggregation in `bgg-shop-core/tests/test_graphql_reviews.py` (depends on T006).
  - Verification: `cd bgg-shop-core && python -m pytest tests/test_graphql_reviews.py` — **13 failed, 19 passed, 3 skipped, 1 warning** (35 collected; 2.89s). Expected RED: Core runtime schema validation reports unknown `ReviewModerationStatus` and missing `Query.adminReviews`, or missing `Mutation.moderateReview`; the accepted/non-deleted public-detail test passes. The three migration tests skipped because `CREDIT_TEST_POSTGRES_DSN` was unset. No resolver/schema/DB behavior was implemented.
- [x] T009 [P] [US1] bgg-shop-bff: Add tests for queue/action contract mapping, route registration and service wiring, active Authorization-user staff/superuser gate, a negative operation-key-only moderation check, validation, `no-store`, sanitized Core errors, and post-commit cache retry/pending-success behavior in `bgg-shop-bff/tests/test_reviews.py` (depends on T001 and T004).
  - Verification: `cd bgg-shop-bff && PYTHONPATH=. pytest -q tests/test_reviews.py` — **19 failed, 17 passed, 33 warnings in 2.93s**. Expected RED: moderation routes are not registered (requests return 405), and queue/action runtime behavior is absent. No dependency or environment blocker; no runtime behavior was changed.
- [x] T010 [P] [US1] bgg-shop-frontend: Add queue and acceptance UI tests for loading, empty, error, review context, and successful refresh in `bgg-shop-frontend/src/admin/reviews/ReviewsPanel.test.tsx` (depends on T007).
  - Verification: `cd bgg-shop-frontend && npm test -- --run src/admin/reviews/ReviewsPanel.test.tsx` — expected RED; Vitest could not resolve `./ReviewsPanel` because the planned component is not implemented. Five behavior tests were authored; no production component or stub was added.

### Implementation

- [x] T011 [P] [US1] bgg-shop-core: Implement the authenticated active staff/superuser-only, bounded `adminReviews` query and pending-to-accepted action, with row-lock serialization and accepted/non-deleted public review/count/average aggregation in `bgg-shop-core/saleor/graphql/api.py` (depends on T008). Writer and independent focused checks passed; reject/restore/delete transitions remain intentionally assigned to T019/T026.
- [x] T012 [P] [US1] bgg-shop-bff: Implement the confirmed admin queue/action REST adapter, route registration, Core delegation, active user-identity staff/superuser gate that rejects operation-key-only contexts, input validation, sanitized errors, `no-store` responses, and bounded post-commit cache retry with success plus `cache_refresh_pending` when needed. Wire `bgg-shop-bff/app.py`, `bgg-shop-bff/src/services.py`, `bgg-shop-bff/src/auth.py`, `bgg-shop-bff/src/controllers/reviews_controller.py`, `bgg-shop-bff/src/proxy.py`, and `bgg-shop-bff/src/catalog_cache.py` (depends on T001, T009, and T004). Route: delegated direct (multi-file writer); trigger: five non-trivial BFF source files. Risk tier: high because the task adds an authorization gate and post-commit behavior. Writer checks passed; independent review found no significant issues.
  - Implementation: added the no-store admin queue and action routes, Core query/mutation adapters, request validation, an active staff/superuser check that requires Authorization-backed `me` identity, fixed public error mapping, and ACCEPT-only cache invalidation with one immediate retry. A second invalidation success clears `cache_refresh_pending`; two failures preserve the committed 200 response. REJECT/DELETE business behavior remains with T020/T027. Existing buyer `createReview` behavior is unchanged.
  - Verification: `cd bgg-shop-bff && PYTHONPATH=. pytest -q tests/test_reviews.py` — **37 passed, 34 warnings in 2.88s**. `PYTHONPATH=. pytest -q tests/test_admin.py tests/test_admin_audit.py tests/test_opkey_middleware.py` — **75 passed, 37 warnings in 1.18s**. `python -m py_compile app.py src/auth.py src/services.py src/controllers/reviews_controller.py src/proxy.py` and `git diff --check` passed. The warnings are existing `datetime.utcnow()` deprecations in `app.py` and `proxy.py`.
  - Independent review evidence: **37 focused review tests, 85 admin/auth tests, and 11 contract/cache tests passed**, with no significant issues reported. BFF commit: `c4358ed`.
  - BFF commit: `c4358ed` (`feat(bff): add review moderation queue and accept adapter`), containing only the six T012 BFF source/test files.
- [x] T013 [P] [US1] bgg-shop-frontend: Implement the typed review queue, status/context display, loading/empty/error states, and accept action using generated API types in `bgg-shop-frontend/src/admin/reviews/ReviewsPanel.tsx` (depends on T010 and T007).
- [x] T014 [US1] bgg-shop-frontend: Register the moderation panel route and navigation entry in `bgg-shop-frontend/src/admin/AdminRouter.tsx` (depends on T013).
- [x] T015a [US1] Local-only prerequisite (user-authorized, 2026-11-05): Add and validate a disposable isolated service/DB setup in `podman-compose.reviews-isolated.yaml`, without reusing the default stack, its containers, ports, network, or persistent volumes (depends on T011, T012, and T014; prerequisite for T015). The isolated Compose config parsed successfully; local images were reused and isolated resources/services started successfully. No default `saleor_db` container, volume, port, or network was used; only the disposable `review_test` database was accessed. The local Admin fixture was corrected in that disposable DB because its username differed from its email while Core authentication uses email as username. No secret or test password is recorded. See the observed evidence in `specs/011-moderate-content-reviews/quickstart.md` and `odd/tasks/011-moderate-content-reviews.md`.
- [x] T015 [US1] Local integration: Verify the queue-to-accept journey and public-detail refresh against local Core/BFF/Frontend services, including the pending buyer-submission behavior, using disposable fixtures; record actual commands and results in `specs/011-moderate-content-reviews/quickstart.md` (depends on T011, T012, T014, and T015a). Spec: `specs/011-moderate-content-reviews/spec.md`; implementation: `bgg-shop-core/saleor/graphql/api.py`, `bgg-shop-bff/src/controllers/reviews_controller.py`, `bgg-shop-frontend/src/admin/reviews/ReviewsPanel.tsx`; test: `bgg-shop-frontend/tests/e2e/product-reviews.spec.ts`. Focused Playwright run passed: **1 passed (8.5s)**.

## Phase 4: User Story 2 — Reject or Restore an Accepted Review (Priority: P1)

**Goal**: A moderator can reject a pending/accepted review or restore a rejected review to accepted; accepted/rejected may switch, and neither returns to pending.

**Independent Test**: In local tests, reject an accepted review and verify it disappears from the public list and accepted-only summary; accept a rejected review and verify it reappears; verify neither action reports a false success.

### Tests — write before implementation

- [ ] T016 [P] [US2] bgg-shop-core: Add tests for pending-to-rejected, accepted-to-rejected, rejected-to-accepted, same-state idempotent success, no return to pending, and concurrent row-lock serialization/last-serialized-action-wins in `bgg-shop-core/tests/test_graphql_reviews.py` (depends on T015).
- [ ] T017 [P] [US2] bgg-shop-bff: Add tests for reject/restore mapping, idempotent success, 404/409 mapping (409 only for a genuinely invalid transition), sanitized errors, and post-commit cache retry/pending-success behavior in `bgg-shop-bff/tests/test_reviews.py` (depends on T015).
- [ ] T018 [P] [US2] bgg-shop-frontend: Add tests for reject and restore actions, resulting status display, failure feedback, and refreshed public-state indication in `bgg-shop-frontend/src/admin/reviews/ReviewsPanel.test.tsx` (depends on T015).

### Implementation

- [ ] T019 [P] [US2] bgg-shop-core: Implement reject and restore transitions, idempotent same-state outcomes, unknown/deleted review errors, and last-serialized-action-wins behavior under a row lock; do not permit a transition back to pending in `bgg-shop-core/saleor/graphql/api.py` (depends on T016).
- [ ] T020 [P] [US2] bgg-shop-bff: Map reject/restore outcomes through the approved REST action contract and preserve error sanitization and post-commit invalidation behavior in `bgg-shop-bff/src/controllers/reviews_controller.py` and `bgg-shop-bff/src/proxy.py` (depends on T017).
- [ ] T021 [US2] bgg-shop-frontend: Add reject/restore controls and outcome handling to the moderation panel using generated BFF types in `bgg-shop-frontend/src/admin/reviews/ReviewsPanel.tsx` (depends on T018 and T019–T020).
- [ ] T022 [US2] Local integration: Verify reject and restore through the local BFF and confirm public detail list/count/average changes after cache invalidation; record exact commands and observed results in `specs/011-moderate-content-reviews/quickstart.md` (depends on T019, T020, and T021).

## Phase 5: User Story 3 — Soft-Delete a Review (Priority: P2)

**Goal**: A moderator can soft-delete a review while retaining it internally and removing it from Core public visibility and aggregation; the BFF reports whether cached detail refresh is still pending.

**Independent Test**: Delete an accepted review with local fixtures; verify the row remains retained with its separate soft-delete marker, the queue omits it, public detail omits it, and count/average are recalculated. Verify repeated DELETE is idempotent and concurrent actions serialize under the row lock.

### Tests — write before implementation

- [ ] T023 [P] [US3] bgg-shop-core: Add tests for retained soft-deleted records, queue exclusion, public-list exclusion, and count/average recalculation including deletion of the last accepted review in `bgg-shop-core/tests/test_graphql_reviews.py` (depends on T022).
- [ ] T024 [P] [US3] bgg-shop-bff: Add tests for repeated DELETE success, unknown-ID/non-delete-on-deleted 404, 409 only for genuinely invalid transition, sanitized failures, and cache-retry failure handling after Core commit (successful response with `cache_refresh_pending=true`) in `bgg-shop-bff/tests/test_reviews.py` (depends on T022).
- [ ] T025 [P] [US3] bgg-shop-frontend: Add tests for the delete action, success/failure feedback, and queue refresh in `bgg-shop-frontend/src/admin/reviews/ReviewsPanel.test.tsx` (depends on T022).

### Implementation

- [ ] T026 [P] [US3] bgg-shop-core: Implement soft-delete using the migrated separate boolean marker, retaining the row and its moderation status while excluding it from queue and public aggregation in `bgg-shop-core/saleor/graphql/api.py` (depends on T023).
- [ ] T027 [P] [US3] bgg-shop-bff: Implement delete response/error handling and bounded cache retry; after Core commit, never report mutation failure, and return success with `cache_refresh_pending=true` if refresh remains pending in `bgg-shop-bff/src/controllers/reviews_controller.py`, `bgg-shop-bff/src/services.py`, `bgg-shop-bff/src/auth.py`, `bgg-shop-bff/app.py`, and `bgg-shop-bff/src/catalog_cache.py` (depends on T024, T026, and T001).
- [ ] T028 [US3] bgg-shop-frontend: Add the soft-delete action and its success/failure handling to the moderation panel using generated BFF types in `bgg-shop-frontend/src/admin/reviews/ReviewsPanel.tsx` (depends on T025 and T026–T027).
- [ ] T029 [US3] Local integration: Verify soft-delete retention and rollback mapping, public removal, summary recalculation, repeated DELETE success, serialized concurrent actions, and cache-refresh-pending success through local Core/BFF/Frontend services; record exact commands and results in `specs/011-moderate-content-reviews/quickstart.md` (depends on T026–T028).

## Phase 6: Polish — Cross-Cutting Local Validation

**Purpose**: Run final local-only checks and keep the feature quickstart evidence accurate.

- [ ] T030 Local integration/docs: Document the approved compatibility and contract decisions, local setup, and functional verification commands/results in `specs/011-moderate-content-reviews/quickstart.md` without recording unrun checks as passed (depends on T029).
- [ ] T031 Local integration: Run the focused local Core tests with `cd bgg-shop-core && python -m pytest tests/test_graphql_reviews.py`, BFF tests with `cd bgg-shop-bff && python -m pytest tests/test_reviews.py tests/test_services_openapi_contract.py`, and Frontend tests/build with `cd bgg-shop-frontend && npm test -- --run src/admin/reviews/ReviewsPanel.test.tsx && npm run build`; then verify the local end-to-end moderation flow and record exact outcomes in `specs/011-moderate-content-reviews/quickstart.md` (depends on T030).

## Dependencies & Execution Order

### Phase dependencies

- **Phase 1**: T001 is bounded engineering evidence for the existing local cache-retry integration, not a user decision gate.
- **Phase 2**: T002 and T003 may proceed in parallel in separate owning contracts. T004 validates both. T005 and T007 may proceed in parallel after T004; T006 follows the migration tests. User-story work begins only after T001–T007.
- **User Story 1 (P1)**: Depends on the approved contracts, storage compatibility, and generated types. The Core, BFF, and Frontend implementation tasks can proceed in parallel after their tests are written; T015a must establish and verify disposable local isolation before T015 integrates them locally.
- **User Story 2 (P1)**: Follows the US1 increment because it extends the same moderation action path and panel. Its Core, BFF, and Frontend tests are written before implementation.
- **User Story 3 (P2)**: Follows US2 to avoid concurrent edits to the same review resolver, controller, tests, and panel. Deletion behavior is confirmed; BFF retry implementation reuses the mechanism established by T001.
- **Polish**: T030 and T031 depend on all three story checkpoints. Local-only verification; no CI, staging, production, or remote checks.

### Task dependency graph

```text
T001 ────────────────┐
T002 ─┐              ├── T009 ── T012
T003 ─┴── T004 ──┬───┘
                 ├── T005 ── T006 ──┬── US1 (T008–T015)
                 └── T007 ──────────┘
US1 T015a ── T015 ── US2 (T016–T022) ── US3 (T023–T029) ── T030 ── T031
```

### Parallel execution examples

```text
# Promote separate canonical contracts in parallel:
T002: Core SDL in bgg-shop-core/specs/schema.graphql
T003: BFF OpenAPI in bgg-shop-bff/specs/openapi.yaml

# Establish retry evidence independently; after T004, foundational work can proceed:
T001: Identify bounded retry integration for shared catalog-cache invalidation
T005: Core status compatibility tests
T007: Frontend type generation from canonical BFF OpenAPI

# Within US1, author tests in separate projects before implementation:
T008: Core tests in bgg-shop-core/tests/test_graphql_reviews.py
T009: BFF tests in bgg-shop-bff/tests/test_reviews.py
T010: Frontend tests in bgg-shop-frontend/src/admin/reviews/ReviewsPanel.test.tsx

# After US1 tests, separate project implementations can proceed in parallel:
T011: Core query/accept implementation
T012: BFF REST/proxy/cache implementation
T013: Frontend panel implementation
```

## Implementation Strategy

1. **Confirmed contracts and evidence first**: Complete T001–T007. User decisions are resolved; T001 determines/reuses the bounded local cache retry integration without creating a service.
2. **MVP**: Complete Phase 3 only, then validate the queue and pending-to-accepted flow independently using local services.
3. **Incremental delivery**: Complete and locally verify US2 reject/restore, then US3 soft-delete; each story preserves the earlier journey.
4. **Final evidence**: Complete the focused service/frontend checks and local end-to-end flow. Record only commands actually run and observed outcomes; do not use remote environments.

## T002–T004 Contract Evidence

The approved draft baseline passed syntax/structure checks before promotion. Exact baseline and canonical validator commands and observed output are recorded in `odd/tasks/011-moderate-content-reviews.md`. Both canonical validations passed. T005 tests are written and their expected RED is recorded in `odd/tasks/011-moderate-content-reviews.md`; T006–T007 and frontend type generation remain complete as recorded above. T011's focused verification and T012's independent review are recorded in `odd/tasks/011-moderate-content-reviews.md`. T015a/T015 are complete with local-only evidence; T016–T031 remain pending, with T016 next. No remote or deployment checks were performed.
