# Implementation Plan: CU-A03 — Moderate Content and Reviews

**Branch**: `011-moderate-content-reviews` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)
**Status**: Planning draft. No service source, authoritative service contract, or test file was changed.

## Summary

Provide a staff/superuser-only moderation queue for buyer reviews, with accept, reject, and soft-delete actions. Preserve the existing review submission flow and update Core public-detail visibility and its accepted-review count/average after every committed moderation action. The BFF invalidates cached detail; if refresh remains pending after retry, it reports committed success and possible temporary staleness. The REST and GraphQL documents in `contracts/` are planning drafts; they are not replacements for the BFF OpenAPI or Core SDL source of truth.

## Technical Context

- **Languages/runtime**: Python (Django/Graphene Core; Flask BFF), TypeScript/React frontend.
- **Primary dependencies**: Existing Core GraphQL schema and BFF REST/proxy stack; existing authentication and staff/superuser checks; existing shared Redis-backed BFF catalog cache.
- **Storage**: PostgreSQL `product_review` table from root `import_catalog.sql`; reviews reference `product_boardgame` and `auth_user`.
- **Testing**: Core pytest/GraphQL tests, BFF pytest/controller and OpenAPI tests, Frontend Vitest and local browser tests where changed. Planning verification is limited to structural parsing of the new drafts and local artifact checks; no feature tests or runtime behavior are claimed.
- **Target platform**: Local project services only.
- **Project type**: Cross-service feature spanning Core GraphQL, BFF REST, and the admin frontend.
- **Performance goals**: No new latency or throughput target is specified. The moderation queue is bounded and paginated: one-based `page/pageSize`, default page size 50, maximum 100, ordered `createdAt DESC, id DESC`.
- **Constraints**: Do not alter the buyer review flow. Enforce an authenticated active `is_staff` or `is_superuser` identity at both service boundaries; an operation key alone is insufficient. Persist only `PENDING`, `ACCEPTED`, `REJECTED` and represent soft-delete separately with a boolean marker. Public product details show accepted, non-deleted reviews only. Moderation responses are non-cacheable. No staging, production, CI, or remote validation.
- **Scale/scope**: One review type (written review plus rating); one moderation queue; three actions; no standalone comment entity, suspicion flag, reason workflow, appeal workflow, or notification feature.

## Constitution Check

**Pre-design gate: PASS.** The status migration, queue, action, concurrency, authorization, and cache-outcome decisions listed in this plan are confirmed; there are no outstanding user-decision gates.

1. **Preserve established behavior**: buyer creation remains authenticated, one review per buyer/game, rating 1–5, nonempty body up to 2,000 characters, and `PENDING`; public pages expose only accepted, non-deleted reviews. A reversible migration maps legacy statuses as specified in the data model.
2. **Keep contracts and ownership explicit**: Core owns review state/persistence and exposes GraphQL; BFF owns the REST boundary and sanitized errors; Frontend types remain generated from the BFF source contract. Drafts here are not edits to those source-of-truth contracts.
3. **Trace changes**: the plan links CU-A03, the feature spec, current Core/BFF behavior, drafts, future tests, and local checks. Record only checks actually run.
4. **Protect customers and service boundaries**: require an authenticated active staff/superuser identity; omit buyer identity from the proposed queue response; sanitize upstream errors; exclude soft-deleted, pending, and rejected content from public pages and summaries. Operation-key-only context cannot authorize moderation.
5. **Smallest safe change**: reuse `product_review`, current admin authorization conventions, existing BFF proxy path, and the catalog cache-generation invalidation pattern; do not introduce independent comment storage or automated moderation.

No constitution violation is identified. The approved migration reconciles persisted statuses with the confirmed lifecycle in future implementation; this planning update does not change source contracts.

## Project Structure

```text
specs/011-moderate-content-reviews/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── bff-openapi.yaml
    └── core-review-moderation.graphql

bgg-shop-core/
├── specs/schema.graphql           # authoritative Core contract; not edited
├── saleor/graphql/api.py          # Core behavior owner; not edited
└── tests/                         # future scoped tests; not edited

bgg-shop-bff/
├── specs/openapi.yaml             # authoritative BFF contract; not edited
├── src/controllers/               # future REST controller; not edited
├── src/proxy.py                   # future GraphQL delegation; not edited
└── tests/                         # future scoped tests; not edited

bgg-shop-frontend/
└── src/admin/                     # future moderation UI; not edited
```

**Structure Decision**: Cross-service feature using existing Core → BFF → Frontend boundaries. Contract-first implementation must copy approved definitions into each owning service's canonical contract, then trace behavior and tests there; the planning drafts under this feature directory remain non-authoritative.

## Scope and Confirmed Design

### In scope

- List non-deleted reviews in `PENDING`, `ACCEPTED`, or `REJECTED` state with game name/id, body, rating, creation time, and state.
- Accept pending/rejected reviews; accepting an already accepted review is a successful no-op.
- Reject pending/accepted reviews; rejecting an already rejected review is a successful no-op.
- Soft-delete a review, retain the database record, and exclude it from public visibility/count/average.
- Ensure a committed state change is reflected by Core's next public detail read and invalidate the BFF's shared catalog cache generation. If refresh remains pending after bounded retry, report success and disclose possible temporary staleness.
- Require the existing active staff/superuser gate; do not add a separate seller/role policy.

### Out of scope

- New buyer review submission behavior, standalone comments, suspicion classification, moderation reasons, appeals, notices, role management, or hard deletion.
- Changing any authoritative service contract or service implementation as part of this planning run.
- CI, staging, production, or remote validation.

### Confirmed BFF REST surface (planning draft)

The draft contract records:

- `GET /api/v1/admin/reviews?status={PENDING|ACCEPTED|REJECTED}&page=1&page_size=50`
  - Requires bearer-authenticated active staff/superuser identity; `status` is optional and single-valued; omitted status returns all three non-deleted states. An operation-key-only context does not satisfy this user-identity authorization requirement.
  - Order is `created_at DESC, id DESC`; pagination is one-based, page defaults to 1, page size defaults to 50 and has maximum 100.
  - `200` returns `{items, page, page_size, total, total_pages}`; an empty queue returns `items: []`.
  - Always `Cache-Control: no-store`.
- `POST /api/v1/admin/reviews/{review_id}/actions`
  - JSON body: `{"action":"ACCEPT"|"REJECT"|"DELETE"}`.
  - Requires the same active staff/superuser identity as the queue.
  - `200` returns the review identifier, retained moderation status, `deleted`, `publicly_visible`, and required boolean `cache_refresh_pending`.
  - Same-state ACCEPT/REJECT and repeated DELETE are idempotent success. Unknown ID and non-delete action on a soft-deleted review return 404. Core serializes actions under a row lock; the last serialized action is final. A stale queue view or concurrency is not a 409; use 409 only for a genuinely invalid transition.
  - Always `Cache-Control: no-store`. After Core commits, synchronously call the existing `catalog_cache.invalidate_catalog_cache(event_id)` request-path helper to increment the shared BFF catalog cache generation. Make at most two total calls (initial attempt plus one immediate retry) if the first call raises. This two-attempt limit is the explicit engineering default for this feature; do not add a service, background task, or outbox work. The generation increment is monotonic, so retrying the invalidation is safe. If both calls fail, preserve the committed Core mutation as HTTP 200 success and set `cache_refresh_pending: true`; disclose possible temporary public-detail staleness. If the first or second call succeeds, set `cache_refresh_pending: false`.
- Error shapes follow existing admin conventions: field errors use `{"errors":[{"code":"INVALID","field":"action","message":"..."}]}`; authorization/not-found/upstream errors use `{"error":"..."}`. HTTP mapping: 400 invalid input, 401 unauthenticated, 403 forbidden, 404 unknown ID or non-delete action on soft-deleted record, 409 only genuinely invalid transition, and 502 sanitized Core failure before a commit.

### Confirmed Core GraphQL surface (planning draft)

- `adminReviews(status, page, pageSize): AdminReviewPage!`, gated to an authenticated active staff/superuser identity; optional single status filter, one-based page, default page size 50/max 100, order `createdAt DESC, id DESC`.
- `moderateReview(reviewId, action): ModerateReviewPayload!`, using enums for `PENDING|ACCEPTED|REJECTED` and `ACCEPT|REJECT|DELETE`; payload reports success, retained status and separate soft-delete state. Core rechecks active user authorization, locks the row, and serializes actions.
- Unknown ID and non-delete action on soft-deleted row map to 404; only a genuinely invalid transition maps to 409. Same-state actions and repeated DELETE are idempotent success.
- Public `productBySlug`/`productByBggId` calculates visible reviews and summary from accepted, non-deleted records only.

The concrete draft schemas and examples are in `contracts/`. The drafts reflect confirmed decisions, but remain non-authoritative and must not replace the owning service contracts during this planning-only update.

## Work Sequence (tracked authoritatively in `tasks.md`)

1. Promote the reviewed Core and BFF drafts into their owner-maintained canonical contracts, then validate those canonical contracts.
2. Add Core migration and behavior tests before implementation; migrate legacy states reversibly and enforce active identity authorization.
3. Add BFF route/service/auth/cache tests before implementation. The moderation action calls the existing cache-generation invalidation helper synchronously at most twice; this bounded request-path retry does not introduce a service or background/outbox work. Wire the endpoint and report committed success with cache-refresh-pending only if both calls fail.
4. Implement the admin UI from generated BFF types; verify loading, empty, error, and action outcomes without creating a separate client-side source contract.
5. Run proportionate local Core/BFF/Frontend checks and the relevant local end-to-end flow; record exact commands and observed results. Do not run external environments.

## Contracts & Endpoints Gate

**Planning gate: DRAFTS CONSISTENT; user decisions are resolved.** The feature changes external API surfaces, so future implementation must promote the draft REST and Core GraphQL details into the owning service contracts and validate them before behavior changes. OpenAPI includes paths, schemas, security, response codes, errors, and examples; Core SDL includes the query/mutation and typed results/errors. `quickstart.md` lists structural checks and future functional evidence. These planning drafts do not replace canonical contracts or establish runtime behavior.

## Post-design Constitution Check

**PASS.** The design keeps canonical ownership with Core and BFF, proposes no frontend-maintained contract, preserves current buyer behavior, excludes private buyer identity from the queue, specifies sanitized BFF errors and no-store admin responses, and calls out the existing Redis-backed product-detail cache. User decisions are resolved, so the task ledger is appropriate and is maintained as a pending future plan. The exact local retry integration remains an engineering evidence task, not a policy approval gate. No implementation or authoritative contract file was modified.

## Planning Artifact Verification (2026-11-05)

- Command: `python -c 'import yaml; from pathlib import Path; p=Path("specs/011-moderate-content-reviews/contracts/bff-openapi.yaml"); d=yaml.safe_load(p.read_text()); assert d["openapi"] == "3.2.0"; assert set(d["paths"]) == {"/api/v1/admin/reviews", "/api/v1/admin/reviews/{review_id}/actions"}; q=d["paths"]["/api/v1/admin/reviews"]["get"]; assert q["parameters"][0]["name"] == "status"; assert q["parameters"][1]["schema"]["default"] == 1; assert q["parameters"][2]["schema"]["default"] == 50 and q["parameters"][2]["schema"]["maximum"] == 100; a=d["paths"]["/api/v1/admin/reviews/{review_id}/actions"]["post"]; assert a["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith("/ModerateReviewRequest"); r=d["components"]["schemas"]["ModerateReviewResponse"]; assert "cache_refresh_pending" in r["properties"] and "cache_refresh_pending" in r["required"]; print("PASS: YAML parses and confirmed draft contract fields are present")'`
  - Result: **PASS** — YAML parsed and the confirmed route, queue, and action response fields were present.
- Command: `python -c 'import yaml; from pathlib import Path; from openapi_spec_validator import validate_spec; validate_spec(yaml.safe_load(Path("specs/011-moderate-content-reviews/contracts/bff-openapi.yaml").read_text())); print("PASS: OpenAPI validator accepted draft")'`
  - Result: **PASS** — OpenAPI validator accepted the draft.
- Command: `cd bgg-shop-core && python -c 'from graphql import parse; from pathlib import Path; p=Path("../specs/011-moderate-content-reviews/contracts/core-review-moderation.graphql"); parse(p.read_text()); print("PASS: Core SDL draft parses")'`
  - Result: **PASS** — Core SDL draft parsed.
- Command: `git diff --check -- specs/011-moderate-content-reviews/spec.md specs/011-moderate-content-reviews/plan.md specs/011-moderate-content-reviews/research.md specs/011-moderate-content-reviews/data-model.md specs/011-moderate-content-reviews/quickstart.md specs/011-moderate-content-reviews/tasks.md specs/011-moderate-content-reviews/contracts/bff-openapi.yaml specs/011-moderate-content-reviews/contracts/core-review-moderation.graphql` followed by `git diff --no-index --check -- /dev/null <each of the eight planning files>`
  - Result: **PASS** — no whitespace diagnostics. The `--no-index` checks returned the expected exit status 1 for each file because each differs from `/dev/null`; no-index checking covers the untracked planning directory.
- Command: Local Python consistency assertions over the plan, research, data model, tasks, quickstart, BFF OpenAPI, and Core SDL.
  - Result: **PASS** — confirmed decision vocabulary, authorization/cache semantics, file ownership, and all-pending task state agree.
- These are draft structure and documentation checks only. No functional tests or runtime behavior were run or are claimed.

## T001 Retry Evidence and Test Seam

- The existing BFF cache helper in `bgg-shop-bff/src/catalog_cache.py:90-91` increments `catalog:v1:generation`; public cache keys include that generation (`catalog_cache.py:63-74`). Repeating the increment is safe because it only advances the generation and makes older-generation entries unreachable.
- The moderation action's post-commit refresh path uses that existing helper synchronously. It makes no more than two total calls: one initial invalidation and, only if that raises, one immediate retry. If both raise, Core's already-committed mutation remains a successful action response with `cache_refresh_pending: true`; do not retry Core or turn the committed result into an error.
- The focused test seam is monkeypatching `src.catalog_cache.invalidate_catalog_cache` in the BFF moderation action tests (`bgg-shop-bff/tests/test_admin.py`). Cover first-call failure followed by retry success (two helper calls, committed success, pending false) and both-call failure (exactly two helper calls, committed success, pending true). Assert the Core action service is called only once in either case. Existing generation behavior is independently covered in `bgg-shop-bff/tests/test_catalog_cache.py:51-64`; the existing internal event test demonstrates the BFF helper monkeypatch seam and retryable failure response in `bgg-shop-bff/tests/test_catalog_events.py:167-199`.
- Buyer review submission remains unchanged: `bgg-shop-bff/src/services.py:45-46` forwards directly to `proxy.create_review`, and `bgg-shop-bff/src/controllers/reviews_controller.py:18-22` returns its existing `201` response.

No new architectural layer is proposed. The bounded attempt count and inline retry are explicit engineering defaults for the moderation action; implementation and the specified focused tests remain future tasks.
