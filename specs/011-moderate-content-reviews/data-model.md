# Data Model: CU-A03 Moderate Content and Reviews

This is a planning-level view of existing data plus proposed moderation semantics. It does not change Core persistence or contract files.

## Customer Review

**Existing storage**: `product_review` in root `import_catalog.sql`.

| Field | Existing type / rule | Planned meaning |
|---|---|---|
| `id` | `BIGSERIAL PRIMARY KEY` | Stable review identifier; draft REST path uses this identifier. |
| `bgg_id` | `INTEGER NOT NULL`, FK to `product_boardgame(bgg_id)` with cascade on product deletion | Related game identifier. Queue includes enough game context to identify the review. |
| `user_id` | `INTEGER NOT NULL`, FK to `auth_user(id)` with cascade on user deletion | Buyer identity; internal only and omitted from the proposed moderation response. |
| `rating` | `SMALLINT NOT NULL`, check 1–5 | Review rating. |
| `body` | `VARCHAR(2000) NOT NULL`, trimmed length 1–2000 | Written review content. |
| `status` | Current check allows `PENDING`, `APPROVED`, `HIDDEN`, `DELETED` | Persist exactly `PENDING`, `ACCEPTED`, or `REJECTED`; soft-delete does not introduce another status. |
| `is_deleted` | Not present in the current table | New `BOOLEAN NOT NULL DEFAULT FALSE`; separates soft-deletion from moderation status. No deletion timestamp is required. |
| `created_at` | `TIMESTAMPTZ NOT NULL` | Submission timestamp; queue order is `created_at DESC, id DESC`. |
| `updated_at` | `TIMESTAMPTZ NOT NULL` | Existing row update timestamp; update on a persisted moderation-state or soft-delete change. Same-state idempotent actions need not create a state change. |

### Approved reversible storage migration

The future Core migration must preserve each legacy row and map it deterministically:

| Legacy `status` | New `status` | New `is_deleted` |
|---|---|---|
| `PENDING` | `PENDING` | `false` |
| `APPROVED` | `ACCEPTED` | `false` |
| `HIDDEN` | `REJECTED` | `false` |
| `DELETED` | `REJECTED` | `true` |

The forward migration adds `is_deleted` with a false default, performs the mapping, replaces the status check with the three-value check, and replaces the approved-only index with an accepted-and-not-deleted public-review index. It must run transactionally where the migration framework/database permits and preserve all existing row IDs and relationships.

The rollback is also deterministic because the separate marker preserves deletion independently of the current status: any row with `is_deleted=true` maps to legacy `DELETED`; otherwise `PENDING→PENDING`, `ACCEPTED→APPROVED`, and `REJECTED→HIDDEN`. Restore the legacy constraint/index and remove `is_deleted` only after values have been mapped back. This also handles a newly soft-deleted accepted review. The migration must not introduce a deletion timestamp.

### Relationships and existing invariants

- Each review belongs to one game and one buyer.
- A unique constraint prevents more than one review per `(user_id, bgg_id)`.
- Current public detail reads records with `status = 'APPROVED'`, orders by creation time descending, and derives both count and average from those rows at query time. After migration, public eligibility is `status = 'ACCEPTED' AND is_deleted = FALSE`.
- New buyer submissions are stored as `PENDING` and public detail excludes them.
- Product and user foreign-key deletion cascades exist in the current DDL; this feature does not alter those established constraints.

### Confirmed moderation semantics

| Current effective state | Action | Result |
|---|---|---|
| `PENDING` | `ACCEPT` | `ACCEPTED`, public |
| `PENDING` | `REJECT` | `REJECTED`, not public |
| `ACCEPTED` | `ACCEPT` | `ACCEPTED`, idempotent success |
| `ACCEPTED` | `REJECT` | `REJECTED`, not public |
| `REJECTED` | `REJECT` | `REJECTED`, idempotent success |
| `REJECTED` | `ACCEPT` | `ACCEPTED`, public |
| Any non-deleted state | `DELETE` | Set `is_deleted=true`; retain the row and its status; not public and excluded from queue/count/average |
| Already soft-deleted | `DELETE` | Idempotent success |
| Any state | Return to `PENDING` | Not an exposed action; no transition is allowed |

No separate suspicion marker is introduced. The planning SDL represents a soft-deleted record with `deleted: true` and its retained moderation status; soft-deleted rows are omitted from ordinary queue results.

### Queue and action consistency

- Queue filtering accepts zero or one status. Pagination is one-based, defaults to page 1 and page size 50, and caps page size at 100. Sort by `created_at DESC, id DESC`.
- The action API is one `POST /api/v1/admin/reviews/{review_id}/actions` with one `action` value: `ACCEPT`, `REJECT`, or `DELETE`.
- Core serializes actions by locking the selected review row and applying each action to the latest committed state; the last serialized action is final. A stale queue view alone is not a conflict.
- Unknown IDs return 404. Any non-delete action on a soft-deleted record returns 404. Repeated DELETE and same-state ACCEPT/REJECT return success. 409 is reserved for an actually invalid transition, not for idempotent or concurrent actions.
- Queue and action require an authenticated active staff/superuser identity in both BFF and Core. Operation-key-only context is insufficient.

## Moderation Action

The proposed API action is an operation on a Customer Review, not a separate persisted entity. Its inputs are a review identifier and one of `ACCEPT`, `REJECT`, or `DELETE`; its result states whether the operation succeeded and whether the review is deleted/public. No actor, reason, or action history table is proposed because CU-A03 does not establish those fields or retention policy. If audit history is required, approve it explicitly before implementation.

## Public Review Summary

The existing Core detail result includes `approvedReviewCount` and nullable `averageRating`. The feature's accepted/non-deleted set is the source for public review list, count, and average. An empty set yields count zero and no average. The BFF caches full game-detail results; after a Core commit, the BFF invalidates the shared catalog generation. If invalidation remains pending after bounded retries, the action still reports committed success and sets `cache_refresh_pending=true`; temporary public-detail staleness may exist until retry succeeds.

## Validation and error cases

- Reject invalid action/status filters and out-of-range pagination as field-level `INVALID`.
- Require an authenticated active staff/superuser identity at Core even if the BFF rejects earlier; an operation key without an active identity is insufficient.
- Unknown review IDs and non-delete actions on soft-deleted records return 404. Repeated DELETE and same-state ACCEPT/REJECT are successful idempotent operations.
- Use 409 only when Core identifies a genuinely invalid transition. Concurrency is serialized under a row lock; a stale state is not itself a conflict.
- If Core fails before commit, report failure and do not claim new public state. If Core commits but cache refresh is pending, report success and expose `cache_refresh_pending`; do not turn committed mutation into failure.
