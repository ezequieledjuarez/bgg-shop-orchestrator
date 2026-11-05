# Local Quickstart: CU-A03 Planning Artifacts

This guide covers structural verification of the **draft** contracts only. It does not start services, modify authoritative contracts, or claim runtime behavior.

## Draft contract checks

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

The action response must include `cache_refresh_pending`. When Core has committed a moderation mutation but shared catalog-cache invalidation is still pending after the bounded retry integration, return a successful mutation response with `cache_refresh_pending: true`; never represent the committed change as failed. Public detail can be temporarily stale until invalidation succeeds. The exact local retry integration must be established by the future BFF evidence task, reusing an existing mechanism and adding no new service.

## Functional evidence required after contract approval and implementation

Run only against local services and a disposable/local test database:

1. Core pytest: active staff/superuser allowed; unauthenticated, inactive, non-admin, and operation-key-only/no-user contexts rejected; pending→accepted/rejected; accepted↔rejected; no return to pending; same-state actions and repeated DELETE are idempotent; unknown IDs and non-delete actions on deleted rows return 404; row-lock concurrency produces last-serialized-action-wins.
2. Core migration tests: verify the exact `PENDING→PENDING`, `APPROVED→ACCEPTED`, `HIDDEN→REJECTED`, and `DELETED→REJECTED` plus `is_deleted=true` forward mapping, and the deterministic reverse mapping. The deleted marker is a boolean; no deletion timestamp is introduced.
3. Core product detail tests: only accepted/non-deleted reviews appear; count and average update for acceptance, rejection, and soft-delete, including empty set.
4. BFF pytest: request validation, active bearer-user staff/superuser gate, a negative operation-key-only authorization case, route/service/auth wiring, sanitized 400/401/403/404/409/502 outcomes, `Cache-Control: no-store`, and post-commit cache invalidation behavior. On invalidation failure after Core commit, assert successful response with `cache_refresh_pending: true`, retry behavior, and no false mutation failure.
5. Frontend Vitest: queue states, status visibility, action outcomes, and refresh after success.
6. Local end-to-end: submit a buyer review (still pending), moderate it through the BFF, and verify public game detail and summary after invalidation; repeat for reject and soft-delete. Use disposable fixtures and clean them afterward.

No CI, staging, production, or remote checks are part of this project workflow.
