# Interface acceptance and traceability

**Not a contract.** The only authoritative definitions are `bgg-shop-bff/specs/openapi.yaml` (BFF REST) and `bgg-shop-core/specs/schema.graphql` (Core GraphQL). The feature-local drafts were promoted into them and removed (canonical_per_service); this file keeps only acceptance and traceability and holds no shadow schemas. Frontend types are generated from the canonical OpenAPI only (`npm run generate:types`).

## Contract-first gate (done)

Promoted, structurally validated (OpenAPI validator; full Core SDL `build_schema`/`validate_schema`) and types regenerated before any behavior change.

Compatibility: registration keeps HTTP 201 and `user` but adds `verification` metadata and returns no `session`. Existing `is_active: true` never means email verified. Core keeps nullable `RegisterPayload.tokens` as always-null compatibility field and `LoginPayload` has no verification field. Only correct-password pending login adds 403. Duplicate email remains 409/EMAIL_EXISTS (Core DUPLICATE_EMAIL). No automatic HTTP retry for these mutations.

### Mapping

| Core result | BFF |
|---|---|
| registration success + metadata | 201 `{user, verification}` |
| DUPLICATE_EMAIL / EMAIL_EXISTS / UNIQUE | 409 existing EMAIL_EXISTS |
| login INVALID_CREDENTIALS / inactive | 401 existing credentials error |
| login EMAIL_NOT_VERIFIED | 403, no user/session/cookie/cart mutation |
| confirm verified=true | 200 `{verified:true,message}` |
| INVALID_VERIFICATION_TOKEN | 400 one generic unusable-link error |
| resend neutral success | 202 `{message}` even when no delivery occurs |
| INVALID resend email | 400 bounded field error |
| RATE_LIMITED | 429 `{errors,retry_after_seconds}` and matching Retry-After |
| storage failure / missing internal caller context at BFF | 503 VERIFICATION_UNAVAILABLE |
| direct Core FORBIDDEN service-context rejection | GraphQL payload error, never a successful mutation |
| network/invalid Core response on new operations | 502 UPSTREAM_FAILURE; no raw GraphQL error forwarding |

All BFF outcomes, including errors and 405, receive `Cache-Control: no-store`; confirmation pages and exchanges also use `Referrer-Policy: no-referrer`. Strip foreign upstream headers/messages. No cookies are issued by registration, resend or confirmation.

## Request examples (see canonical contracts for shapes)

Public browser request: `POST /api/v1/auth/email-verification/confirm`, JSON `{"token":"<VERIFICATION_TOKEN>"}`. No email, user ID, redirect, Authorization or OpKey is needed.

Core operations are sent only by the BFF with server-derived service context; their exact documents live in the BFF service module and the canonical SDL.

## Negative and compatibility acceptance cases

| ID | Input / race | Required observation | Trace |
|---|---|---|---|
| C01 | fresh and mixed-case duplicate registration; response loss/retry | one user; 201 metadata/no session; repeated registration 409, no resend | FR-001, FR-010; US1-A1, US2-A5 |
| C02 | correct password pending, with guest cookie; bad password; inactive pending | pending 403; bad/inactive 401; no JWT, refresh, OpKey, DB/Django session, cart merge or cookie deletion | FR-002; US1-A2 |
| C03 | current proof, explicit POST, then password login | one verified state, no automatic authentication, normal subsequent login | FR-003, FR-009; US1-A3 |
| C04 | missing, null, malformed, oversize, tampered, unknown, used, replaced proof | identical 400 code/message; no owner, token, state write or credentials | FR-004, FR-005, FR-011; US2-A1 |
| C05 | expiry minus 1µs / exact / plus 1µs | valid / invalid / invalid from one authoritative DB deadline | FR-013; SC-003 |
| C06 | two connections confirming together | exactly one winner, one generic invalid; verify another account impossible | FR-004; SC-003 |
| C07 | confirmation versus replacement, and parallel resends | serialized state; old proof invalid if replacement wins; no effective new proof if confirm wins; quotas atomic | FR-004, FR-006; US2-A2 |
| C08 | pending, verified, exempt, absent; recipient exhausted; SMTP failure | same 202 exact acknowledgment; only eligible pending account sends | FR-006, FR-007, FR-010; US2-A3 |
| C09 | 120s cooldown, 2/recipient/hour, 10/caller/hour; mixed casing/reload | before/exact/after boundaries; initial issue starts cooldown, not resend count; no quota reset by UI | FR-008; US2-A4 |
| C10 | 10 invalid confirmations/900s; attempt 11; valid proof while exhausted | tenth invalid 400, eleventh 429; ceiling Retry-After; no consumption until allowed | FR-008; US2-A4 |
| C11 | fake Forwarded/XFF/caller JSON/internal headers, bearer or OpKey | public headers cannot choose caller; direct Core rejects untrusted verification context | FR-002, FR-008 |
| C12 | page GET/HEAD, scanner preview, React remount, back/refresh, double click | zero automatic POST/state changes; explicit action only; no proof in history/storage/telemetry | FR-003, FR-011; US1-A5 |
| C13 | send rejection/timeout/crash after commit/response loss | pending preserved, no old-token restoration; quota spent only after committed issuance; safe recovery | FR-010; US2-A5 |
| C14 | legacy customer/staff/superuser/session and disabled fixtures | EXEMPT with verified_at null; old eligible access unchanged; disabled stays disabled | FR-012; US3-A1 |
| C15 | forged access/opaque refresh/OpSession for pending subject | denied by Core identity/rotation/issue/validate/delegation boundaries | FR-002, FR-004 |
| C16 | inspect response, logs, direct Core malformed/nested token variables, aliased/multi-operation GraphQL errors, captured proxy traffic and browser storage | no raw proof except email/request; sanitize framework coercion/debug errors too; no credential/provider detail; no cache | FR-011; SC-006 |
| C17 | Core/storage outage; repeated request after unknown success | fail closed; no automatic replay/send; explicit resend follows quota; confirm replay safely invalid | FR-005, FR-010 |
| C18 | complete UI journey | email/password only; no Google, reset or magic login; BFF only | FR-015; US3-A2 |

Use independent database connections and barriers for races, not SQLite or mocked row locks. Negative tests must also assert absence of side effects, not only status codes. See [quickstart](../quickstart.md) for prerequisites and evidence boundaries.
