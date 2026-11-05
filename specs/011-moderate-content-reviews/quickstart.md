# Local Quickstart: CU-A03 Moderate Content and Reviews

This guide preserves contract-validation evidence and records the observed local US1 integration result. The contract commands below are documented baseline checks, not checks rerun for the T015 update. All runtime evidence is local-only; no CI, staging, production, deployment, or remote service was used.

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

The action response must include `cache_refresh_pending`. T012 implements and tests the bounded retry through the existing catalog-cache invalidation mechanism: when Core has committed a mutation but invalidation remains pending, return success with `cache_refresh_pending: true` rather than representing the committed change as failed. Public detail can be temporarily stale until invalidation succeeds. T015 observed the ACCEPT cache-refresh success path (`cache_refresh_pending=false`) only; REJECT, RESTORE, and DELETE cache-refresh checks remain pending with their US2/US3 work.

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

These are local observations only. No deployment, external service, persistent/default Saleor database, CI, staging, production, reject/restore, or soft-delete check is claimed. T016–T031 remain pending; T016 is next.
