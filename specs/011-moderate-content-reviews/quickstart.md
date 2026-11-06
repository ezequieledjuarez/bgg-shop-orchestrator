# Local Quickstart: CU-A03 Moderate Content and Reviews

This guide preserves contract-validation evidence and records the observed local US1–US3 integration results. The contract commands below are documented baseline checks, not checks rerun for the T015 update. All runtime evidence is local-only; no CI, staging, production, deployment, or remote service was used.

## Contract checks

From the repository root:

```bash
python -c 'import yaml; from pathlib import Path; p=Path("specs/011-moderate-content-reviews/contracts/bff-openapi.yaml"); d=yaml.safe_load(p.read_text()); assert d["openapi"] == "3.2.0"; assert set(d["paths"]) == {"/api/v1/admin/reviews", "/api/v1/admin/reviews/{review_id}/actions"}; q=d["paths"]["/api/v1/admin/reviews"]["get"]; assert q["parameters"][0]["name"] == "status"; assert q["parameters"][1]["schema"]["default"] == 1; assert q["parameters"][2]["schema"]["default"] == 50 and q["parameters"][2]["schema"]["maximum"] == 100; a=d["paths"]["/api/v1/admin/reviews/{review_id}/actions"]["post"]; assert a["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith("/ModerateReviewRequest"); assert "cache_refresh_pending" in d["components"]["schemas"]["ModerateReviewResponse"]["properties"]; print("PASS: YAML parses and confirmed draft contract fields are present")'
```

```bash
python -c 'import yaml; from pathlib import Path; from openapi_spec_validator import validate_spec; validate_spec(yaml.safe_load(Path("specs/011-moderate-content-reviews/contracts/bff-openapi.yaml").read_text())); print("PASS: OpenAPI validator accepted draft")'
```

```bash
cd bgg-shop-core && python -c 'from graphql import parse; from pathlib import Path; p=Path("../specs/011-moderate-content-reviews/contracts/core-review-moderation.graphql"); parse(p.read_text()); print("PASS: Core SDL draft parses")'
```

The YAML/OpenAPI commands validate the draft document and local references; the GraphQL command parses the SDL syntax. These checks do not prove compatibility with the actual BFF/Core runtime, and do not replace service contract suites.

The action response must include `cache_refresh_pending`. T012 implements and tests the bounded retry through the existing catalog-cache invalidation mechanism: when Core has committed a mutation but invalidation remains pending, return success with `cache_refresh_pending: true` rather than representing the committed change as failed. Public detail can be temporarily stale until invalidation succeeds. T015 observed the live ACCEPT cache-refresh success path (`cache_refresh_pending=false`) only; T029 below records the mocked cache-pending coverage for ACCEPT, REJECT, and DELETE.

## Approved service contracts and compatibility decisions

The canonical interface owners remain `bgg-shop-core/specs/schema.graphql` (Core GraphQL) and `bgg-shop-bff/specs/openapi.yaml` (BFF REST/OpenAPI). They contain the approved moderation definitions and were validated before behavior was implemented. The frontend types are generated from the BFF OpenAPI contract. T029–T031 do not change these service interfaces.

- Persist only `PENDING`, `ACCEPTED`, and `REJECTED`; preserve the legacy mapping `PENDING→PENDING`, `APPROVED→ACCEPTED`, `HIDDEN→REJECTED`, and `DELETED→REJECTED` with `is_deleted=true`.
- Keep soft-delete independent from moderation status in `is_deleted BOOLEAN NOT NULL DEFAULT FALSE`; retain the row and its status, and add no deletion timestamp. Rollback maps any marked row to `DELETED`; unmarked `PENDING`, `ACCEPTED`, and `REJECTED` map to `PENDING`, `APPROVED`, and `HIDDEN`.
- `GET /api/v1/admin/reviews` and `POST /api/v1/admin/reviews/{review_id}/actions` require an active staff/superuser identity, are `no-store`, and exclude deleted reviews from the queue. Same-state ACCEPT/REJECT and repeated DELETE are idempotent; non-delete actions on deleted reviews return 404.
- Core public detail and its count/average use accepted, non-deleted reviews only. After a Core commit the BFF tries cache-generation invalidation at most twice; if both attempts fail, the response remains successful with `cache_refresh_pending=true`. Buyer submission remains unchanged and new reviews are pending.

## Functional evidence required after contract approval and implementation

Run only against local services and a disposable/local test database:

1. Core pytest: active staff/superuser allowed; unauthenticated, inactive, non-admin, and operation-key-only/no-user contexts rejected; pending→accepted/rejected; accepted↔rejected; no return to pending; same-state actions and repeated DELETE are idempotent; unknown IDs and non-delete actions on deleted rows return 404; row-lock concurrency produces last-serialized-action-wins.
2. Core migration tests: verify the exact `PENDING→PENDING`, `APPROVED→ACCEPTED`, `HIDDEN→REJECTED`, and `DELETED→REJECTED` plus `is_deleted=true` forward mapping, and the deterministic reverse mapping. The deleted marker is a boolean; no deletion timestamp is introduced.
3. Core product detail tests: only accepted/non-deleted reviews appear; count and average update for acceptance, rejection, and soft-delete, including empty set.
4. BFF pytest: request validation, active bearer-user staff/superuser gate, a negative operation-key-only authorization case, route/service/auth wiring, sanitized 400/401/403/404/409/502 outcomes, `Cache-Control: no-store`, and post-commit cache invalidation behavior. On invalidation failure after Core commit, assert successful response with `cache_refresh_pending: true`, retry behavior, and no false mutation failure.
5. Frontend Vitest: queue states, status visibility, action outcomes, and refresh after success.
6. Local end-to-end: submit a buyer review (still pending), moderate it through the BFF, and verify public game detail and summary after invalidation; repeat for reject and soft-delete. Use disposable fixtures and clean them afterward.

No CI, staging, production, or remote checks are part of this project workflow.

## T015a / T015 local evidence — 2026-11-05

**Status: T015a and T015 complete.** This evidence covers only the authorized local disposable setup and the US1 queue-to-accept journey. The spec is `specs/011-moderate-content-reviews/spec.md`; implementation references are `bgg-shop-core/saleor/graphql/api.py`, `bgg-shop-bff/src/controllers/reviews_controller.py`, and `bgg-shop-frontend/src/admin/reviews/ReviewsPanel.tsx`; the focused test is `bgg-shop-frontend/tests/e2e/product-reviews.spec.ts`.

### Isolated local setup (T015a)

- The separate `podman-compose.reviews-isolated.yaml` configuration parsed successfully with the observed command:

  ```bash
  podman-compose -f /home/eze/develop/boardgame-app/podman-compose.reviews-isolated.yaml config >/dev/null
  ```

- The isolated setup reused local images only and started isolated, healthy containers: DB `bgg_reviews_test_db` at `127.0.0.1:55432`, Redis `bgg_reviews_test_redis` at `127.0.0.1:56379`, Core `bgg_reviews_test_api` at `127.0.0.1:18001`, and BFF `bgg_reviews_test_bff` at `127.0.0.1:5001`. The Frontend ran locally at `127.0.0.1:3000`.
- Core GraphQL `POST { __typename }`, BFF `/health`, and the Frontend each returned HTTP 200.
- The default Compose stack was not used: no default `saleor_db` container, volume, port, or network was used. Only the disposable `review_test` database was accessed. The local Admin fixture was corrected inside that disposable database because its username differed from its email, while Core authentication uses email as the username. No credentials or password are included here.

### Queue-to-accept journey (T015)

Exact focused command:

```bash
cd bgg-shop-frontend && env -u VITE_API_BASE_URL E2E_OPKEY_ISOLATED=true C03_DISPOSABLE_REVIEW_E2E=true npx playwright test tests/e2e/product-reviews.spec.ts --grep "moderator accepts" --project=chromium --workers=1
```

Result: **1 passed (8.5s)** in the independent runner; the parent spot-check also observed **1 passed (8.5s)**.

The flow submitted a buyer review in `PENDING`, loaded it in the moderator queue, accepted it, and observed `status=ACCEPTED`, `publicly_visible=true`, and `cache_refresh_pending=false`. Public detail then included the review, and the accepted count and average increased. Unique fixture data and baseline-derived aggregate assertions make reruns repeatable.

These are local observations only. No deployment, external service, persistent/default Saleor database, CI, staging, production, reject/restore, or soft-delete check is claimed in this T015 evidence. See T022 below for the separate US2 reject/restore result. At the time this T015 record was written, T023–T031 were pending. T016's guarded PostgreSQL migration and concurrency tests were later run successfully as part of T019; see the task tracker.

## T022 US2 reject/restore local integration — 2026-11-05

Traceability: `specs/011-moderate-content-reviews/spec.md` User Story 2; action contract `specs/011-moderate-content-reviews/contracts/bff-openapi.yaml` (`POST /api/v1/admin/reviews/{review_id}/actions`); implementation in `bgg-shop-core/saleor/graphql/api.py`, `bgg-shop-bff/src/controllers/reviews_controller.py`, and `bgg-shop-frontend/src/admin/reviews/ReviewsPanel.tsx`; E2E test `bgg-shop-frontend/tests/e2e/product-reviews.spec.ts`.

Run from `bgg-shop-frontend` against the isolated local stack:

```bash
env -u VITE_API_BASE_URL E2E_OPKEY_ISOLATED=true C03_DISPOSABLE_REVIEW_E2E=true npx playwright test tests/e2e/product-reviews.spec.ts --grep "moderator accepts" --project=chromium --workers=1
```

Final observed result: **1 passed (8.3s)**. The flow submitted a pending review, accepted it and confirmed public visibility plus count/average increase, rejected it and confirmed it disappeared while the summary returned to baseline, then restored it and confirmed public visibility plus count/average returned. Each action response reported `cache_refresh_pending=false`.

The initial attempt showed stale public detail after rejection because the running isolated BFF had not reloaded the edited controller source. Restarting only `bgg_reviews_test_bff` reloaded it; `/health` then returned `{"status":"healthy"}`. The passing result is the rerun after this restart; the initial attempt is not reported as passing.

The observed stack was Core `127.0.0.1:18001`, BFF `127.0.0.1:5001`, Frontend `127.0.0.1:3000`, with disposable PostgreSQL inside `bgg_reviews_test_db`. No default/shared `saleor_db` or remote environment was used. This confirms US2 reject/restore only; it is not evidence that US3 soft-delete is verified. Frontend E2E test commit: `85f2631` (`test(e2e): verify review rejection and restoration`).

## T029 US3 soft-delete local integration — 2026-11-06

Traceability: User Story 3 in `specs/011-moderate-content-reviews/spec.md`; Core implementation/tests `bgg-shop-core/saleor/graphql/api.py` and `bgg-shop-core/tests/test_graphql_reviews.py`; BFF action `POST /api/v1/admin/reviews/{review_id}/actions`; Frontend action `bgg-shop-frontend/src/admin/reviews/ReviewsPanel.tsx`; E2E `bgg-shop-frontend/tests/e2e/product-reviews.spec.ts`.

The isolated database, Redis, Core, and BFF were healthy on loopback ports 55432, 56379, 18001, and 5001. To avoid the occupied port 3000, the local Vite frontend ran on port 3001:

```bash
cd bgg-shop-frontend && VITE_API_BASE_URL=http://localhost:3001/api/v1 npm run dev -- --host 127.0.0.1 --port 3001
```

The preview returned HTTP 200. Core GraphQL `POST { __typename }` and BFF `/health` also returned HTTP 200. No default database/API or remote environment was used.

Exact Playwright command:

```bash
cd bgg-shop-frontend && VITE_API_BASE_URL=http://localhost:3001/api/v1 E2E_OPKEY_ISOLATED=true C03_DISPOSABLE_REVIEW_E2E=true npx playwright test tests/e2e/product-reviews.spec.ts --grep "moderator accepts" --project=chromium --workers=1
```

The first run failed because the new E2E lookup filtered for `ACCEPTED` before the review had been accepted. The test was corrected to find its unique pending review in the unfiltered queue. The final rerun passed: **1 passed (9.4s)**. Through the actual local Frontend, BFF, Core, and disposable PostgreSQL path, it submitted a pending review, accepted it, rejected it, restored it, and then soft-deleted it through the accessible UI action. The delete response retained `status=ACCEPTED`, returned `deleted=true`, `publicly_visible=false`, and `cache_refresh_pending=false`; the UI queue no longer contained the row. Public detail no longer included the review, and its count and average returned to the starting baseline. A repeated DELETE returned 200 with the same deleted state; ACCEPT on the deleted review returned the sanitized 404 response `{"error":"Review not found."}`.

Additional deterministic checks for T029, run against local fixtures:

- Core: `cd bgg-shop-core && python -m pytest -q tests/test_graphql_reviews.py -k "review_status_migration or concurrent_moderation_last_serialized_action_wins or deleting_last_accepted_review"` with `CREDIT_TEST_POSTGRES_DSN` set only to a generated guarded loopback database/role inside `bgg_reviews_test_db` — **4 passed, 41 deselected, 1 Django warning in 4.53s**. These PostgreSQL-backed cases cover forward/rollback mapping, serialized concurrent actions, and retained soft-deleted row/public aggregation. Cleanup in `finally` was verified: temporary database count 0, temporary role count 0.
- BFF: `cd bgg-shop-bff && PYTHONPATH=. python -m pytest -q tests/test_reviews.py -k retry_exhaustion_preserves_committed_success_as_pending` — **3 passed, 48 deselected, 3 existing `datetime.utcnow()` deprecation warnings in 1.18s**. This is a Flask test-client check with mocked Core and cache invalidation; it proves committed-success/pending behavior, but it does not simulate a live Redis outage or cross-service HTTP request.

The Core row-retention and rollback/concurrency evidence uses the disposable PostgreSQL test database. The BFF cache-pending case is intentionally mock-based; the end-to-end DELETE itself used the local HTTP stack and actual database.

## T031 Final focused checks — 2026-11-06

All commands below ran locally. The Core checks used a generated `credit_test_<32 hex>` user/database inside `bgg_reviews_test_db`, with the DSN restricted to `127.0.0.1:55432`.

- Core: `cd bgg-shop-core && CREDIT_TEST_POSTGRES_DSN=<guarded temporary loopback DSN> python -m pytest -q tests/test_graphql_reviews.py` — **45 passed, 0 skipped, 1 Django warning in 6.07s**. This includes migration forward/rollback, soft-delete retention/public aggregation, and row-lock concurrency coverage. The temporary database and role were dropped in `finally`; exact-name cleanup counts were both zero.
- BFF: `cd bgg-shop-bff && PYTHONPATH=. python -m pytest -q tests/test_reviews.py tests/test_services_openapi_contract.py` — **57 passed, 49 existing `datetime.utcnow()` deprecation warnings in 8.25s**.
- Frontend: `cd bgg-shop-frontend && npm test -- --run src/admin/reviews/ReviewsPanel.test.tsx && npm run build` — **12 component tests passed**; TypeScript check and Vite production build passed.
- End-to-end: `cd bgg-shop-frontend && VITE_API_BASE_URL=http://localhost:3001/api/v1 E2E_OPKEY_ISOLATED=true C03_DISPOSABLE_REVIEW_E2E=true npx playwright test tests/e2e/product-reviews.spec.ts --grep "moderator accepts" --project=chromium --workers=1` — **1 passed (8.2s)** after the focused suites. This exercised the actual local BFF/Core/database action flow and the accessible frontend delete action.

No final focused suite failed or skipped. The earlier failed E2E attempt caused by the test's premature ACCEPTED-only queue filter is retained in the T029 record above. A known unrelated Core generated-schema SDL comparison previously failed on seven description-only differences; inspection found no type/field drift, this comparison was not rerun here, and it is not claimed as passed or caused by the soft-delete change.

Cleanup: the frontend preview on port 3001 was stopped. The temporary Core role/database are absent (counts 0/0). Only the four `bgg_reviews_test_*` containers were stopped; Podman warned that the isolated BFF did not stop on SIGTERM within 10 seconds and used SIGKILL. A filtered container check observed zero remaining `bgg_reviews_test_*` running containers. No default `saleor_db`, its API, or its network was contacted or changed.
