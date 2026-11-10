# Phase 1 — Data model and state transitions

Proposed Core-owned PostgreSQL schema only. No database or migration was executed. Reuse existing `auth_user` proven by source, not a conventional Saleor account model. Schema metadata must be verified in the isolated database before choosing concrete FK types; see [research](research.md).

## Account and verification state

Existing User retains password hash, username/email, names, `is_active`, staff/superuser and sessions. No existing columns, roles or hashes are rewritten.

Proposed `account_email_verification`:

| Field | Constraint / meaning |
|---|---|
| `user_id` | PK and FK to actual `auth_user.id`, ON DELETE CASCADE |
| `state` | required `LEGACY_EXEMPT`, `PENDING`, `VERIFIED`; no default exemption |
| `verified_at` | timestamptz, null except VERIFIED |
| `created_at` | required timestamptz; policy-record creation, not historic ownership |

CHECK: VERIFIED iff verified_at is nonnull. Existing customers, staff and superusers become LEGACY_EXEMPT with null verified_at, including disabled users. Login authorization requires `is_active AND state IN (VERIFIED, LEGACY_EXEMPT)`; privileges still require existing authorization. A missing sidecar after rollout is not exemption.

State transitions:

```text
pre-cutover existing user -> LEGACY_EXEMPT (never fake VERIFIED)
new register -> PENDING
PENDING + current valid explicit proof -> VERIFIED
PENDING + resend / send failure / invalid proof -> PENDING
LEGACY_EXEMPT -> unchanged; VERIFIED -> unchanged on resend
any verification state + administrative disablement -> login denied
```

Confirmation of a pending disabled account may prove its email but NEVER changes `is_active`; subsequent login is still denied. No flow changes the registered email or grants privileges.

## Current challenge and delivery attempt

Proposed `email_verification_challenge` (one-to-one current challenge, not plaintext history):

| Field | Constraint / meaning |
|---|---|
| `user_id` | PK/FK to sidecar, cascade |
| `token_digest` | unique 64-hex SHA-256 of `email-verification:v1:` + raw proof |
| `email_normalized` | registered trimmed/casefold email at issuance; bounded by actual existing schema |
| `issued_at` | authoritative timestamptz from database clock after locks |
| `expires_at` | same issuance timestamp + exactly 3600 seconds |
| `consumed_at` | nullable timestamptz; nonnull only on successful confirmation |
| `delivery_status` | `UNCONFIRMED`, `SUBMITTED`, `FAILED`; internal sanitized classification |
| `delivery_finished_at` | nullable timestamptz; no provider error string |

CHECK expires_at = issued_at + interval '3600 seconds'; CHECK consumed_at, when nonnull, is >= issued_at and < expires_at. Digest unique index supports lookup; PK enforces one current proof/account. Current normalized User email must equal the bound email during verification; no account identifier supplied by a caller can override binding. Replacement overwrites the row under lock, making every old digest unusable. Do not keep a second usable challenge or restore an old digest after delivery failure.

Delivery attempt is metadata on the current challenge, not a new job entity. `UNCONFIRMED` includes not attempted and unknown outcome after crash/timeout; public registration maps FAILED/unknown to UNCONFIRMED. SUBMITTED means the transport accepted submission, not inbox receipt. Update outcome only if current digest still matches the attempted issuance. No raw proof, email body, password, SMTP exception or reusable transport credentials are stored in operational records.

## Durable rolling limits

Proposed `email_verification_limit_bucket`:

- `(scope, subject_digest)` composite primary key. Scope is `RESEND_CALLER`, `RESEND_RECIPIENT` or `INVALID_CONFIRM_CALLER`.
- Subject is a 64-hex purpose-prefixed hash of normalized peer address or normalized recipient. Recipient normalization is exactly the same Core normalization as registration/login.
- Bucket row exists even for a nonexistent recipient when needed to serialize attempts; it is not a membership record. INSERT ON CONFLICT followed by SELECT FOR UPDATE serializes concurrent workers.

Proposed `email_verification_limit_event`:

- `id` bigint generated PK, `scope`, `subject_digest`, `occurred_at` timestamptz.
- Composite FK to bucket, cascade; index `(scope, subject_digest, occurred_at, id)`.
- Caller resend events for all well-formed accepted caller attempts (including recipient-suppressed and absent-account requests).
- Recipient events only for committed replacement issuances (including failed/unknown delivery). Initial registration does not insert a resend event.
- Invalid confirmation events only for rejected unusable proofs after the caller gate; a success is not an invalid attempt.

Rolling window is `(now - window, now]`: at the exact oldest-event-plus-window instant that event no longer counts. Read `clock_timestamp()` once after the relevant lock acquisition for each gate; never use different application clocks. For recipient eligibility, use the challenge's latest issued_at plus 120s AND at most two recipient events in the last 3600s. Exact cooldown boundary is eligible. Confirm valid only strictly before expires_at.

Caller gate checks before input proof/account lookup. Resend attempt 11/hour and confirmation attempt after ten invalid events/900s return RATE_LIMITED before any send/consume. The tenth invalid confirmation is itself rejected with the generic invalid result; attempt eleven is throttled. `retry_after_seconds = max(1, ceil(oldest_blocking_event + window - now))`; if multiple caller restrictions ever apply, take their maximum, not a recipient wait. No public recipient-specific retry or count. Public malformed token requests still reach the invalid-confirm counter with a bounded nonmatching sentinel; do not let local input rejection bypass the attempt gate.

Delete expired events opportunistically under bucket lock (all windows <=3600s), not an unrelated retention system. Keep empty buckets for correctness initially; do not invent a background cleanup service. No application-instance local counters, clock rounded fixed windows, or failed-open fallback.

## Serialization and failure invariants

Use one consistent locking order: caller bucket, recipient bucket when applicable, User, sidecar, challenge. Registration takes its normalized-email advisory lock before creating rows and never acquires rate buckets afterward. The email uniqueness lock is supplemental to existing username uniqueness, not a replacement for DB constraints. Re-read all eligibility/digest predicates after row locks. Do not acquire a bucket in a post-commit delivery callback.

- Two confirms: only one commits VERIFIED/consumed. Second returns unusable.
- Resend versus confirm: if confirm wins, resend is neutral with no issuance; if replacement wins, old confirm fails. A new replacement may later be confirmed.
- Two resends: only one can satisfy the immediate cooldown; all caller requests still count.
- Account/challenge/quota mutations commit together; expected invalid/suppression outcomes commit relevant limit events. Database errors roll them back and fail closed.
- Delivery is outside all locks. Post-commit failure cannot rollback the account, refund a committed issuance or restore an old challenge.

## Migration/backfill and rollback

Future filename proposal: `bgg-shop-core/saleor/graphql/migrations/0021_email_verification.py`, after current `0020_chat_conversations`; verify the then-current head instead of assuming 0021 remains free. Reuse Core's SQL migration pattern (RunSQL, explicit reverse SQL and swappable auth dependency); place domain operations in a small `saleor/email_verification.py` helper rather than introducing a new app/model tree solely for this feature.

1. In a disposable PostgreSQL instance, verify actual User table/PK/lengths/indexes and applied migration state. Standard User tests create the Django auth schema, while other review/credit fixtures deliberately create a skeletal `auth_user(id)`; do NOT use those skeletal fixtures for registration/migration tests.
2. Pause registration across the schema/backfill cutover, create sidecar/challenge/limit tables with FK types matching verified metadata, and insert LEGACY_EXEMPT for every existing user with no verified_at. Use a migration transaction; duplicate/backfill rerun must not overwrite an existing PENDING/VERIFIED row.
3. Assert user-count equals policy-row count at cutover, exempt verified_at is null, and no existing activation, role, password, JWT/session or cart data changed.
4. Deploy atomic pending registration and all eligibility gates together before reopening registration. No interval where new accounts lack the marker or obtain ungated credentials.
5. Test migration from the actual isolated baseline, repeated deployment safety and rollback on failure. Reversal drops only feature-owned tables, but **operational rollback must keep registration closed and verification gates effective for post-cutover pending users**. Dropping policy data and running old ungated code would grant access and is unsafe. Do not present destructive reverse SQL as a safe live rollback.

No live schema discovery, data backfill, historical verification or broad cleanup is authorized by this planning run.
