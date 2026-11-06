# Research: CU-A03 Moderate Content and Reviews

## Decision 1 — Preserve Core ownership of review lifecycle and public aggregation

- **Decision**: The Core service owns moderation state, authorization checks, persistence, and which records contribute to public detail. The BFF is a REST adapter and sanitizes errors; the Frontend consumes generated BFF types.
- **Rationale**: The root constitution names Core GraphQL and BFF OpenAPI as their respective source-of-truth boundaries. Current Core `saleor/graphql/api.py` writes buyer reviews into `product_review`, queries only the current approved state for public details, and calculates count/average in Core. The BFF's current review controller delegates to Core.
- **Alternatives considered**: Implement moderation in BFF or Frontend. Rejected because neither owns persistence/domain state and it would split review rules across service boundaries.

## Decision 2 — Apply the confirmed moderation policy without adding suspicion classification

- **Decision**: Expose `PENDING`, `ACCEPTED`, and `REJECTED`; pending can be accepted or rejected, accepted/rejected can switch, and no transition returns to pending. Only accepted, non-deleted reviews are public and included in count/average. Delete is soft-delete and excludes the record from public detail and summary.
- **Rationale**: These are explicit user-confirmed decisions. The feature spec also explicitly excludes a separate suspicion marker.
- **Alternatives considered**: A `SUSPICIOUS` status or automated flag; a hard delete; restoring an accepted/rejected item to pending. Excluded by the confirmed scope and retention/lifecycle requirements.

## Decision 3 — Keep the existing active staff/superuser authorization gate

- **Decision**: Require an authenticated active user with `is_staff` or `is_superuser` for the queue and every action, with checks at the BFF and Core boundaries.
- **Rationale**: The user confirmed this gate. Existing Core admin resolvers use active staff/superuser checks; BFF admin endpoints use an admin guard. A validated operation key is not a replacement for Core authorization.
- **Alternatives considered**: Introduce a seller role mapping or action-specific permissions. Not authorized or needed for this feature.

## Decision 4 — Use the confirmed queue and action contracts

- **Decision**: The BFF queue accepts one optional `status`, one-based `page` and `page_size` (default 50, maximum 100), ordered by `createdAt DESC, id DESC`. The single action endpoint is `POST /api/v1/admin/reviews/{review_id}/actions` with `{action: ACCEPT|REJECT|DELETE}`. Both operations are non-cacheable.
- **Rationale**: These are now-confirmed user decisions and fit the existing Core→BFF boundary.
- **Alternatives considered**: Multi-status filters, alternate pagination, separate action routes, or PATCH/DELETE action methods; not selected.

## Decision 5 — Migrate stored review status and preserve legacy meaning

- **Decision**: Persist exactly `PENDING`, `ACCEPTED`, and `REJECTED`, with a separate boolean `is_deleted` marker defaulting to false. In a reversible migration map `PENDING→PENDING`, `APPROVED→ACCEPTED`, `HIDDEN→REJECTED`, and `DELETED→REJECTED` plus `is_deleted=true`. Do not add a deletion timestamp.
- **Rationale**: This preserves every legacy row's effective state while making soft-delete independent from moderation status. The rollback can restore legacy values deterministically: any `is_deleted=true` row→`DELETED`; otherwise pending→pending, accepted→approved, and rejected→hidden.
- **Alternatives considered**: Retain the legacy storage vocabulary and translate in API code; rejected in favor of the explicitly approved stored vocabulary. Adding deletion time is unnecessary and unapproved.

## Decision 6 — Make mutation and authorization outcomes deterministic

- **Decision**: Same-state ACCEPT/REJECT and repeated DELETE are successful and idempotent. Unknown IDs and non-delete actions on soft-deleted reviews return 404. Actions serialize under a row lock; the last serialized action is final. Return 409 only for a genuinely invalid transition, not for a stale view or concurrent action. Require an active staff/superuser identity at both BFF and Core; an operation key alone is not that identity.
- **Rationale**: This matches the user's confirmed retry/concurrency and authorization requirements. Local evidence shows `bgg-shop-bff/src/auth.py:18-19` allows `op_session_valid` without an Authorization header; the moderation-specific guard must close that path. Core must independently verify an active user identity and staff/superuser flags.
- **Alternatives considered**: Fail repeated requests as conflicts, use optimistic stale-state conflicts, or treat a validated operation key as moderator identity; rejected.

## Decision 7 — Preserve success after commit and expose cache refresh state

- **Decision**: If the Core mutation committed, the BFF reports success even when cache generation invalidation cannot complete. The success payload includes `cache_refresh_pending`; it is true when invalidation remains pending. Retry invalidation through a bounded integration with an existing local mechanism, and state that public detail may remain temporarily stale until refresh succeeds.
- **Rationale**: BFF details are cached by `catalog_response("game-detail", ...)`; `invalidate_catalog_cache` increments the shared Redis generation. The existing cache invalidation endpoint returns 503 when that increment fails, but no review-action retry path or established local background retry integration was found. A bounded evidence task must identify/reuse a local integration; do not add a new service.
- **Alternatives considered**: Treat a committed mutation as failed or rely solely on cache TTL; rejected. Adding an unverified queue/service is out of scope.

## Decision 8 — Keep service-owned contracts authoritative

- **Decision**: Keep OpenAPI and Core SDL draft files under this feature's `contracts/` directory. They are to be promoted only by future owning-service tasks; this planning update does not edit canonical service contracts.
- **Rationale**: The user limited the edit surface to planning artifacts and the root constitution identifies the service contracts as authoritative.
- **Alternatives considered**: Edit `bgg-shop-bff/specs/openapi.yaml` or `bgg-shop-core/specs/schema.graphql`; prohibited for this work.

## Evidence consulted

- `CasosDeUso.md`, CU-A03: Administrator/Seller panel, review/comment evaluation, approve/hide/delete, immediate visibility and rating-average adjustment.
- `specs/011-moderate-content-reviews/spec.md`: user scenarios, acceptance scenarios, explicit lifecycle/authorization/deletion decisions, and local-only scope.
- Root `.specify/memory/constitution.md` and `.agents/ponytail.md`: source-of-truth contracts, traceability, privacy/security, and minimal-change principles.
- `import_catalog.sql`: `product_review` columns, foreign keys, uniqueness/rating/body checks, current status constraint and approved-review index.
- `bgg-shop-core/saleor/graphql/api.py`, `bgg-shop-core/specs/schema.graphql`, and `bgg-shop-core/tests/test_graphql_reviews.py`: current public aggregation and pending buyer-submission behavior; no moderation API is present.
- `bgg-shop-bff/src/controllers/reviews_controller.py`, `bgg-shop-bff/src/controllers/admin_audit_controller.py`, `bgg-shop-bff/src/controllers/admin_sales_controller.py`, and `bgg-shop-bff/specs/openapi.yaml`: existing REST validation, auth/error patterns, `no-store`, and API contract conventions.
- `bgg-shop-bff/src/catalog_cache.py`, `bgg-shop-bff/src/services.py`, `bgg-shop-bff/app.py`: current shared generation cache and invalidation integration.
- `bgg-shop-bff/src/auth.py:18-19`: `admin_required` currently permits an operation-key-validated session without an Authorization header; future moderation wiring must require and validate an active user identity. `bgg-shop-core/saleor/graphql/api.py` has active staff/superuser checks that provide the Core-side pattern.

No external research was necessary: technology choices and integration patterns were verified from the local project. The cache retry integration remains an engineering evidence item, not an unresolved user policy decision. No research agent or external/remote validation was used.
