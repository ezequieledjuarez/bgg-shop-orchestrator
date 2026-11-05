# ODD Task: CU-A03 — Moderate Content and Reviews

## Objective

Implement `specs/011-moderate-content-reviews` across Core, BFF, and Frontend, preserving the existing buyer review flow and exposing only accepted, non-deleted reviews publicly.

## Problem and Why

The approved feature specification defines a staff/superuser moderation queue and accept, reject, and soft-delete actions. The service contracts, storage migration, authorization, cache invalidation outcome, UI, and local functional evidence must stay aligned.

## Scope and Constraints

- Follow `specs/011-moderate-content-reviews/tasks.md` in dependency order; its T001–T031 are the detailed checklist.
- Local project only. No CI, staging, production, remote validation, or new service.
- Require an active staff/superuser identity at Core and BFF; an operation key alone is insufficient.
- Preserve the confirmed reversible review-status mapping and separate boolean soft-delete marker.
- Report a committed Core mutation as success with `cache_refresh_pending=true` if bounded BFF cache refresh remains pending.
- Preserve pre-existing working-tree changes; do not stage or commit unrelated paths.
- Delivery strategy: `feature-branch-chain` (user-selected). Estimated authored changes exceed 400 lines; keep the work on this feature branch in slices. Do not push or create PRs without explicit authorization.
- Engram task mirror: pending because the memory tools are unavailable in this session.

## Acceptance Criteria

- Canonical Core GraphQL and BFF OpenAPI contracts are updated and locally validated before behavior changes.
- Migration is reversible with the specified legacy mapping and public query eligibility.
- Core, BFF, and Frontend moderation behavior and negative authorization/error tests match the spec.
- Local functional verification is recorded only when actually executed; no non-local checks are run.

## Tasks

- [x] T001: Document the bounded cache-generation retry path, terminal committed-success behavior, and test seam in the plan.
- [x] T002: Promote the confirmed Core review queue/action definitions, authorization/error semantics, and accepted non-deleted public aggregation rules into the canonical SDL.
- [x] T003: Promote the confirmed moderation routes, schemas, authorization/error mapping, cache-refresh outcome, and no-store requirements into canonical OpenAPI.
- [x] T004: Validate both canonical contracts locally; the Core SDL parser and BFF OpenAPI validator passed.
- [x] T005: Add migration-focused Core compatibility tests and observe the expected RED.
- [x] T006: Implement reversible storage/query migration; focused Core tests and disposable PostgreSQL forward/rollback/public-eligibility tests passed.
- [x] T007: Regenerate frontend API types from the canonical BFF OpenAPI contract; generated output and TypeScript no-emit check passed.
- [x] T008: Author Core queue/action/public-review tests and observe the expected RED.
- [x] T009: Author BFF moderation tests and observe the expected RED.
- [x] T010: Author frontend moderation queue and acceptance UI tests and observe the expected RED.
- [ ] T011: Core queue/accept implementation and writer self-check passed, but the required independent review is pending because agent model routing is unavailable.
- [ ] T012: Implement the BFF queue/action adapter (US1).
- [x] T013: Implement the frontend review queue and acceptance action (US1).
- [x] T014: Register the frontend moderation route and navigation entry (US1).
- [ ] T015: Locally verify the complete queue-to-accept integration (US1).
- [ ] T016–T022: Implement and locally verify rejection and restoration (US2).
- [ ] T023–T029: Implement and locally verify soft deletion (US3).
- [ ] T030–T031: Complete local documentation and focused functional validation.

## Progress and Verification

- Initial exploration: the current branch is `011-moderate-content-reviews`; the existing untracked and modified worktree contents were preserved.
- Existing tree has unrelated modifications and untracked files; they will be preserved.
- T001 documentation is complete: the selected engineering default is at most two synchronous calls to `invalidate_catalog_cache` (initial attempt plus one immediate retry); exhaustion preserves committed success and reports `cache_refresh_pending=true`.
- The existing BFF cache helper itself has no retry loop. This milestone documents the bounded moderation request path and monkeypatch test requirements; no executable code or tests were changed or run.
- T002–T003 are complete: the confirmed definitions were promoted to `bgg-shop-core/specs/schema.graphql` and `bgg-shop-bff/specs/openapi.yaml`. No runtime behavior or frontend generated types were changed.
- T004 is complete: both canonical validators passed after promotion. The root `.gitignore` excludes `bgg-shop-core/` and `bgg-shop-bff/`, so root Git status does not show these contract edits; no files were staged or committed.
- T005 is complete as test authoring only: tests cover the four legacy status mappings, deterministic rollback (including a newly soft-deleted accepted row), and accepted/non-deleted public eligibility. No migration or runtime code was changed.
- T005 focused command: `cd bgg-shop-core && python -m pytest tests/test_graphql_reviews.py`
  - Exact result: `1 failed, 17 passed, 3 skipped, 1 warning in 1.95s`.
  - Expected RED output: `FAILED tests/test_graphql_reviews.py::test_review_status_compatibility_migration_is_registered - ModuleNotFoundError: No module named 'saleor.graphql.migrations.0019_review_status_compatibility'`; the target migration is not present before T006.
  - The three PostgreSQL migration behavior tests were skipped because `CREDIT_TEST_POSTGRES_DSN` is not set. Their fixture accepts only a disposable loopback `credit_test_<uuid>` PostgreSQL database and drops its per-test schema.
- T010 frontend tests are authored in `bgg-shop-frontend/src/admin/reviews/ReviewsPanel.test.tsx` for loading, empty/error states, review context, and accepting a review followed by queue and public-detail refresh. They use the generated BFF review/action/product types and MSW fixtures; no production component or stub was added.
- T010 focused command: `cd bgg-shop-frontend && npm test -- --run src/admin/reviews/ReviewsPanel.test.tsx`
  - Exact result: **1 failed suite, 0 tests collected**. This is the expected RED: Vite could not resolve `./ReviewsPanel` because the planned component does not exist yet; there was no unrelated dependency or environment failure.
- T006 independent review found the forward/reverse mapping and public query filter align with the data model. The first focused run reported 18 passed and 3 skipped because no DSN was configured; a later disposable local PostgreSQL run reported 21 passed, 0 skipped, 1 warning. Python compile checks passed.
- The disposable PostgreSQL verification used the locally cached `postgres:15-alpine` image with `--pull=never`, a unique `credit_test_<uuid>` database/user, and a loopback-only ephemeral port. The container was removed after the test run; no source files were changed by the verification action.
- T007 generated types with `cd bgg-shop-frontend && npm run generate:types` (passed). `cd bgg-shop-frontend && npx tsc --noEmit -p tsconfig.app.json` passed; `git -C bgg-shop-frontend diff --check` passed. Only `src/types/generated/bff-api.d.ts` changed (238 additions).

## Contract Validation Evidence (2026-11-05)

Draft baseline checks, run before promotion:

- Command: `python -c 'import yaml; from pathlib import Path; p=Path("specs/011-moderate-content-reviews/contracts/bff-openapi.yaml"); d=yaml.safe_load(p.read_text()); assert d["openapi"] == "3.2.0"; assert set(d["paths"]) == {"/api/v1/admin/reviews", "/api/v1/admin/reviews/{review_id}/actions"}; q=d["paths"]["/api/v1/admin/reviews"]["get"]; assert q["parameters"][0]["name"] == "status"; assert q["parameters"][1]["schema"]["default"] == 1; assert q["parameters"][2]["schema"]["default"] == 50 and q["parameters"][2]["schema"]["maximum"] == 100; a=d["paths"]["/api/v1/admin/reviews/{review_id}/actions"]["post"]; assert a["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith("/ModerateReviewRequest"); assert "cache_refresh_pending" in d["components"]["schemas"]["ModerateReviewResponse"]["properties"]; print("PASS: YAML parses and confirmed draft contract fields are present")'`
  - Result: **PASS** — `PASS: YAML parses and confirmed draft contract fields are present`.
- Command: `python -c 'import yaml; from pathlib import Path; from openapi_spec_validator import validate_spec; validate_spec(yaml.safe_load(Path("specs/011-moderate-content-reviews/contracts/bff-openapi.yaml").read_text())); print("PASS: OpenAPI validator accepted draft")'`
  - Result: **PASS** — `PASS: OpenAPI validator accepted draft`.
- Command: `cd bgg-shop-core && python -c 'from graphql import parse; from pathlib import Path; p=Path("../specs/011-moderate-content-reviews/contracts/core-review-moderation.graphql"); parse(p.read_text()); print("PASS: Core SDL draft parses")'`
  - Result: **PASS** — `PASS: Core SDL draft parses`.

Canonical validation, run after promotion:

- Command: `cd bgg-shop-core && PYTHONDONTWRITEBYTECODE=1 python -c 'from pathlib import Path; from graphql import build_schema; build_schema(Path("specs/schema.graphql").read_text()); print("SDL valid")'`
  - Result: **PASS** — `SDL valid`.
- Command: `PYTHONDONTWRITEBYTECODE=1 python -c 'import yaml; from pathlib import Path; from openapi_spec_validator import validate_spec; p=Path("bgg-shop-bff/specs/openapi.yaml"); spec=yaml.safe_load(p.read_text()); validate_spec(spec); print("OpenAPI valid")'`
  - Result: **PASS** — `OpenAPI valid`.

## Next Step
T011 Core queue/accept implementation and its focused checks are complete. Proceed with T012–T015 only; do not treat the skipped migration integration cases as validation in the T011 test run.

## T008 Core Test Evidence (2026-11-05)
- Added focused GraphQL tests in `bgg-shop-core/tests/test_graphql_reviews.py` for active staff and superuser identities; unauthenticated, inactive, non-admin, and operation-key-only/no-user rejection; status filtering; bounded pagination; stable order and game/review context; empty queues; pending acceptance; and accepted/non-deleted public detail aggregation.
- Command: `cd bgg-shop-core && python -m pytest tests/test_graphql_reviews.py`
- Result: **13 failed, 19 passed, 3 skipped, 1 warning** (35 collected; 2.89s). This is the expected RED before resolver implementation: `ReviewModerationStatus` is unknown and `Query.adminReviews` is absent; the mutation reports `Mutation.moderateReview` absent. The public accepted/non-deleted detail test passed.
- The three skips are the existing PostgreSQL migration integration tests; `CREDIT_TEST_POSTGRES_DSN` was unset, so no database was accessed. No resolver, schema, or database behavior was changed for T008.

## T009 BFF Test Evidence (2026-11-05)
- Extended `bgg-shop-bff/tests/test_reviews.py` with canonical OpenAPI checks; queue Core-to-REST field and pagination mapping; ACCEPT action mapping; route and service registration; active bearer staff/superuser access and inactive, non-staff, missing-user, and validated operation-key-only rejection; query/action validation; `Cache-Control: no-store`; sanitized upstream errors; and retry-success/retry-exhaustion behavior asserting one Core mutation and the appropriate `cache_refresh_pending` value.
- Command: `cd bgg-shop-bff && PYTHONPATH=. pytest -q tests/test_reviews.py`
- Result: **19 failed, 17 passed, 33 warnings in 2.93s**; no skips or dependency/environment blocker. This is the expected RED because the moderation REST routes and their runtime behavior are absent: requests returned `405 METHOD NOT ALLOWED`, and the registration assertion failed. The canonical contract test and existing buyer-review tests passed.
- All 33 warnings are the existing `datetime.datetime.utcnow()` deprecation warning from `bgg-shop-bff/app.py:148`. No route, auth, controller, proxy, service, or cache implementation was changed for T009.

## T006 Implementation Progress (2026-11-05)
- Confirmed the existing T005 tests in `bgg-shop-core/tests/test_graphql_reviews.py`: migration registration, all four legacy state mappings, deterministic rollback including a newly soft-deleted accepted review, and accepted/non-deleted public eligibility. The recorded T005 RED was the expected missing-module failure for `0019_review_status_compatibility`.
- Added `bgg-shop-core/saleor/graphql/migrations/0019_review_status_compatibility.py` after 0018. It adds `is_deleted` with a false non-null DB default, maps statuses forward, replaces the status check and approved-only partial index, and reverses the status mapping before dropping the marker. It does not add a deletion timestamp.
- Updated `import_catalog.sql` to describe the post-migration status check, soft-delete marker, and accepted/non-deleted partial index. Updated Core public review selection to require `ACCEPTED` and `is_deleted = FALSE`; aggregation remains derived from the same selected rows.
- Independent local validation: `cd bgg-shop-core && python -m pytest tests/test_graphql_reviews.py` — **18 passed, 3 skipped**. Python compile checks for the migration and touched Core file passed. No correctness issue was found in independent review.
- The disposable PostgreSQL run covered forward mapping, deterministic rollback, and accepted/non-deleted public eligibility; all three integration tests passed without skips.

## T011 Core Implementation Evidence (2026-11-05)
- Implemented the runtime moderation status/action enums, admin queue/page and moderation payload/error types, `Query.adminReviews`, and `Mutation.moderateReview` in `bgg-shop-core/saleor/graphql/api.py`.
- The queue enforces active authenticated staff/superuser identity, rejects missing/inactive/non-admin users and operation-key contexts without a user, applies optional status and non-deleted filtering with parameterized SQL, validates one-based pagination with a 100-row maximum, and orders by `created_at DESC, id DESC`.
- The mutation locks the selected review row, accepts pending reviews, returns idempotent success for already-accepted reviews, and does not implement reject, restore, or delete behavior. Public detail aggregation remains based on accepted, non-deleted rows as implemented in T006.
- Command: `cd bgg-shop-core && python -m pytest tests/test_graphql_reviews.py`
- Result: **32 passed, 3 skipped, 1 warning in 1.83s** (35 collected). The three skipped cases are the PostgreSQL migration integration tests because `CREDIT_TEST_POSTGRES_DSN` was unset; this run did not validate migration behavior against a database.
- Command: `cd bgg-shop-core && python -m py_compile saleor/graphql/api.py`
- Result: **PASS** (exit code 0).
- Runtime schema check: moderation type fields/enums and `adminReviews`/`moderateReview` fields and arguments matched `bgg-shop-core/specs/schema.graphql`; no canonical contract file was edited.
- Independent verification for T011 could not start: the code-review agent failed before execution with `Auto routing is unavailable; server-discovered preferences require the /auto endpoint`. T011 remains unchecked until independent review is available.
- T012 delegated writer likewise failed before execution with the same agent-routing error. No BFF runtime files were changed; its T009 test-only RED remains recorded.
- Next step: resume T011 independent verification and T012 through delegated workers when agent model routing is available. Do not replace required multi-file delegation with inline implementation.
