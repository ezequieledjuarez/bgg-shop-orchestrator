# Phase 0 — Repository evidence and decisions

**Status:** planning only, 2026-11-09. No runtime tests, database inspection, network requests or email sends. All technical choices below are proposed implementation decisions, not claims about current behavior. Product decisions Q1–Q3 are already approved in [spec](spec.md).

## 1. Ownership and compatibility

**Decision:** Core Django/Graphene owns verification, persistence, deadlines and limits. The live Flask BFF adapts errors/JSON and supplies trusted caller context. React calls only BFF. Reuse existing Python standard library, Django transactions/mail and PostgreSQL; no provider framework, worker, queue or new dependency.

**Evidence:** `bgg-shop-core/requirements.txt` specifies Django 4.2.x, Graphene >=3.3, graphene-django >=3.1.5, psycopg2, PyJWT and Redis; BFF requirements specify Flask >=3, requests and PyYAML. Frontend package.json declares React 19.2, TypeScript ~5.4 and Vite 5.4. The live BFF is root `bgg-shop-bff/app.py`, started by its Dockerfile, not the unrelated FastAPI stub `src/app.py`. Existing auth history is in `docs/CU-C01-AUTHENTICATION-CHANGES.md`; the current source takes precedence over its stale statements about refresh/roles.

**Rationale:** minimal changes in established service boundaries. **Alternatives considered:** BFF-owned verification (duplicates Core truth), standalone auth service/provider abstraction (unnecessary), frontend-only gate (bypass).

## 2. Identity schema and legacy semantics

**Decision:** do not change `is_active`, replace User, or assume a Saleor account table. Use a Core-owned sidecar keyed by the actual `auth_user.id`, backfill explicit `LEGACY_EXEMPT` with null `verified_at`, and create `PENDING` alongside every new registration in one transaction. Absence of a sidecar after rollout fails closed; deployment must complete the backfill before enabling the gate.

**Evidence:** `saleor/graphql/api.py:2734–2815` imports `django.contrib.auth.models.User`, uses `create_user(username=email,email=email,...)`, `strip().casefold()` and `email__iexact`; `authenticate` and `is_active` are checked before `_merge_guest_cart` and `_auth_tokens`. `saleor/settings.py` installs `django.contrib.auth` and no `AUTH_USER_MODEL` override was found. `opkeys/models.py` uses `settings.AUTH_USER_MODEL`; existing domain SQL references `auth_user(id)` with integer FKs, e.g. `saleor/graphql/migrations/0020_chat_conversations.py`. `tests/test_user_permissions_postgres.py:155–159` creates real Django User/Group/Permission/ContentType tables in an isolated schema. `import_catalog.sql` seeds an existing admin in `auth_user`; it is not the authoritative auth-table DDL and must not be used as a verification migration.

**Schema limitation:** no live DB schema was inspected. Current code demonstrates standard User usage, not proof that every local DB matches it. Before future migration, introspect only schema metadata in the disposable DB: actual PK type, username/email lengths, unique/index constraints, auth migration history and table ownership. Existing Django username uniqueness is not an email uniqueness constraint; do not silently add an unrelated global email constraint. Existing BFF allows email length 254, while conventional Django username is 150; retain this pre-existing compatibility issue as a migration/test preflight, not a feature-driven schema rewrite. Exercise the database's actual bounds and preserve sanitized failures.

**Rationale:** exemption is not historic verification, and activation remains separate. **Alternatives considered:** `is_active=False` for pending (conflates administrative state), backfill `verified_at` (false historical claim), missing-row-means-exempt (fail-open on registration bugs), new custom User model (migration risk).

## 3. Token persistence, atomicity and delivery

**Decision:** generate 32 random bytes with `secrets.token_urlsafe(32)` (43 base64url characters). Persist only SHA-256 of a purpose-prefixed proof; keep registered normalized email and account binding in the challenge. One current challenge row/account; replacement overwrites its digest/deadline and clears consumed state, so all older proofs become unresolvable. Store an authoritative database issuance timestamp and `expires_at = issued_at + 3600 seconds`; use database wall-clock time after acquiring locks, not transaction-start `CURRENT_TIMESTAMP`, for deadline checks after lock waits.

**Rationale:** a high-entropy opaque proof needs no JWT claims, extra signing key or plaintext token storage. **Alternatives considered:** signed stateless links (cannot revoke/consume atomically), reuse OpKeys/JWT (wrong purpose), historic plaintext-token log (secrecy violation).

**Transaction decisions:**

- Registration serializes same-normalized-email attempts with a PostgreSQL transaction advisory lock, rechecks `email__iexact`, creates User + PENDING + challenge, and commits before delivery. Convert only identified username-uniqueness conflicts to DUPLICATE_EMAIL; rollback all state on creation failure.
- Confirmation first locks/checks the caller bucket, then discovers the candidate digest without trusting it and locks User → sidecar → challenge, re-reads proof/email/state and checks the deadline. The winning transaction updates VERIFIED and consumes the challenge together. A queued loser gets INVALID_VERIFICATION_TOKEN.
- Resend locks caller bucket → recipient bucket → User → sidecar → challenge, then checks eligibility again and commits replacement + quota before sending. Confirmation and resend have the same account lock ordering; old-email delivery arriving after a replacement remains harmless.
- A SQL/Django failure rolls back issuance and allowance updates together. Invalid-attempt records must commit on expected domain rejection (do not raise an exception that rolls them back).

Use a bounded synchronous Django mail submission **after commit** (`transaction.on_commit`, with a result holder if needed), never inside a DB lock and never an automatically retried task. New local timeout proposal: 3 seconds, shorter than existing BFF `_auth_request` 10-second HTTP timeout. Register returns 201 with SUBMITTED only if submission was acknowledged; otherwise UNCONFIRMED. Resend always returns its neutral 202 for a committed valid request, including submission failure. The UI never claims inbox delivery.

Crash after commit/before submission leaves pending state and an unconfirmed challenge. Timeout may mean accepted-but-unknown delivery; do not retry automatically or restore old proof. User recovery is an explicit resend after cooldown. Update delivery metadata only with a digest/version predicate, so an old callback cannot overwrite a newer challenge. Raw proof exists only in short-lived memory, the intended email and the minimum confirmation exchange. Do not retain it in a durable outbox. A process crash can lose a message; approved recoverability, not guaranteed delivery, is the design target.

## 4. Abuse ownership, caller identity and topology

**Decision:** durable PostgreSQL rolling-window events owned by Core, with row-locked buckets and per-request database time. Do not reuse the existing fixed-window or in-process chatbot limiter as-is. Proposed tables and exact windows are in [data model](data-model.md). Count committed resend issuances, including failed delivery, toward recipient limits; initial issuance starts cooldown but is not a resend. Count every well-formed resend request toward caller quota, even nonexistent/suppressed recipients.

**Topology evidence:** root compose publishes BFF `5000:5000`, Core only `127.0.0.1:8000:8000`, and frontend receives `VITE_API_BASE_URL=http://localhost:5000/api/v1`. `bgg-shop-frontend/vite.config.ts` has no dev proxy. Browser therefore calls Flask directly in current local topology. Container port forwarding/NAT can group callers; no supported reverse-proxy identity chain is established. The isolated compose differs from the main stack and must not be assumed to run the frontend/BFF identically.

At BFF, normalize `request.remote_addr` with Python `ipaddress`, including IPv4-mapped IPv6; never take identity from body, cookies, user-agent, Forwarded, X-Forwarded-For, X-Real-IP or browser-supplied internal headers. Compute SHA-256 of UTF-8 `email-verification:caller:v1:` plus the normalized peer address as a 64-hex caller key; use that same algorithm for both operations. Missing/unparseable peer identity fails closed with 503, not a random/new caller identity. Do not persist/log the raw address. IP grouping behind loopback/NAT is a documented conservative demo limitation, not a reason to trust spoofable headers. No ProxyFix is introduced. If a reverse proxy is later required, explicitly review its overwrite behavior, exact trusted peers and hop count first.

BFF constructs fresh internal headers, authenticating with existing `X-Internal-Secret` / `OPKEY_INTERNAL_SECRET` and supplying `X-Verification-Caller`. Reuse `opkeys.utils.has_internal_secret` for constant-time service authentication; do not reuse an OpKey as proof. New Core confirm/resend mutations reject absent/invalid service context (FORBIDDEN), making direct loopback Core calls unable to invent unlimited caller keys. Secret values are never read in planning. Internal authentication configuration is a future prerequisite; fail closed if unavailable. Existing public Core register/login access is not silently removed.

**Alternatives considered:** Redis sorted sets/Lua (available, but would create a second coordination/durability boundary with account transactions), local memory (worker/restart bypass), client identifier/localStorage (reload/spoof bypass), blind forwarded-header trust (spoofing). Existing Redis remains unchanged. PostgreSQL events and bucket locks work across processes and restarts without a new dependency.

**Non-enumeration:** equivalent well-formed inputs have the same 202 body/status/header profile regardless of membership, recipient suppression or SMTP errors. Never expose recipient cooldown/remaining quota. Avoid account-specific response fields or error branches. Bounded synchronous delivery can still affect latency; no perfect timing-indistinguishability claim is made. Local tests compare response equivalence and inspect latency for obvious provider-error leaks; timing hardening must not introduce a queue/automatic retry or make a delivery claim.

## 5. Complete credential gate, without session redesign

**Evidence and decision:**

| Existing file / surface | Required minimal reuse/change |
|---|---|
| `saleor/graphql/api.py::LoginMutation` | Gate after correct password/active check, before guest merge, `_auth_tokens` and optional privileged OpSession creation. Return EMAIL_NOT_VERIFIED only to correct-password active pending users. |
| `api.py::_authenticated_user` | Gate both JWT access and delegated OpKey branches against active + VERIFIED/LEGACY_EXEMPT. All buyer/admin resolvers using this helper inherit the gate; `me` must not leak pending identity. |
| `api.py::_auth_tokens` | Defense-in-depth eligibility check at issuance, not merely at its current caller. |
| `saleor/auth_refresh.py` and `saleor/urls.py` | Real `/api/v1/auth/refresh` uses an in-memory **opaque** store; it is NOT rotation of GraphQL login's JWT refresh. Gate `_issue_tokens`/`issue_for_user`, stored subject in `_consume_refresh`, and refresh response issuance. Preserve existing wire protocol and lifetime behavior; do not implement a new JWT refresh design. |
| `opkeys/views.py::op_create, op_validate` | Under the existing service-secret requirement, deny issuance/validation of user-bound keys for pending/inactive/missing subjects; preserve separate active staff/superuser requirement for admin delegation. Null-user service keys remain service keys, never buyer identity. |
| `opkeys/middleware.py::OpKeyAuthMiddleware` | Check eligibility before touching/delegating a user-bound key; retain existing allow-list and service-secret checks. |
| `bgg-shop-bff/app.py::login` | Already deletes guest cookie only on 200; keep it so 403 does not lose the guest cart. |
| `src/proxy.py::_auth_result`, `src/dtos/auth.py`, `src/controllers/auth_controller.py` | Preserve metadata currently dropped by DTOs; explicitly map EMAIL_NOT_VERIFIED rather than collapsing it to 502. Add operation-specific confirmation/resend mapping, never pass raw upstream error text. |

`api.py` has other JWT decoding for admin-error classification and authenticated chatbot identity; the latter delegates access to `_authenticated_user`. Check all raw `request.user`, Django session and JWT consumers during implementation; a verification token is accepted by none. Scope is bypass prevention, not retroactive revocation of eligible legacy sessions or fixing the pre-existing opaque/JWT refresh mismatch.

**Rationale:** denying only login leaves auxiliary credential paths unsafe. **Alternatives considered:** unrelated refresh redesign/role redesign (out of scope), broad JWT revocation (breaks approved legacy policy).

**Error-secrecy decision:** the current URL mounts GraphQLView with GraphiQL enabled, and Core settings include Graphene debug middleware. Ordinary resolver payload sanitization does not protect GraphQL variable-coercion errors, which can include rejected input. Add a narrow verification-aware GraphQLView adapter in proposed `saleor/graphql/views.py`, wired through `saleor/urls.py`, to format validation/execution errors without raw variables, tokens, traces or debug data for these exchanges. Include aliased/multi-operation documents in detection tests; authenticate trusted context before dispatching verification behavior. Keep unrelated operation contracts unchanged. Prefer this small boundary adapter over global exception/debug behavior changes. Direct Core malformed nested token variables and BFF timeout/error paths both belong in leakage tests.

## 6. Link, UI and mail configuration

**Decision:** email link uses the explicitly configured application origin plus `/verify-email#token=<proof>`, not a query/path token and never a caller-controlled redirect. Application bootstrap captures the fragment into ephemeral memory and immediately `history.replaceState`s `/verify-email` **before** analytics/other telemetry can execute. No token in local/session storage, URL query, logs or React effect-triggered network call. Show an explicit confirmation button; POST only in its submit handler, with in-flight button suppression. A refresh after capture intentionally loses proof; offer reopening the email or resend. An existing login session is neither replaced nor created by confirmation.

**Evidence:** `src/auth/AuthScreens.tsx` currently manages auth with native History API, submits to BFF, persists session only on login and redirects registration to login after 900ms. `src/App.tsx`, `src/routing/routes.ts`, `src/ui/messages.ts`, `src/auth/session.ts` are the integration points. Reuse that routing/form pattern; no router or auth SDK. Future confirmation bootstrap belongs before application render in `src/main.tsx` (verify the existing bootstrap order when implementing).

Existing compose declares `EMAIL_URL`, `DEFAULT_FROM_EMAIL` and Mailpit. Core settings currently do not map those to Django mail settings. Proposed future configuration: map `EMAIL_URL` with django-environ mail parsing; set `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `EMAIL_USE_SSL`, `EMAIL_TIMEOUT=3`, and `DEFAULT_FROM_EMAIL`. Reference the user-reported `MEEPLE_APP_SMTP_PASSWORD` only as a password override during a separately authorized Gmail setup; never embed it in URLs or artifacts. Use existing `FRONTEND_URL` but validate the explicitly configured origin against the actual local frontend port; its current default must not silently decide the recipient link.

Local tests inject Django locmem backend or a fake sender. Optional later Mailpit testing must use only a dedicated local capture port with no relay. Gmail credentials, sender identity and connectivity are deferred operational setup outside this plan's execution; they are not required for local acceptance. No Google OAuth, password reset, email-change or magic-link feature.

## Resolution record

- `skill_resolution`: `.atl/skill-registry.md` absent. Loaded installed `vercel-react-best-practices` at `/home/eze/.agents/skills/vercel-react-best-practices` before frontend analysis. Apply event-handler mutation, ephemeral state and no extra dependency guidance; no frontend code was changed. No separate customization skill needed because agent-context edits are prohibited.
- Research dispatch: one bounded topology/isolated-test exploration and one narrow correction of its incorrect FastAPI/ASGI inference. Corrected live Flask entrypoint evidence is used above, not the obsolete stub.
- Explicit feature selection worked through `SPECIFY_FEATURE_DIRECTORY`; selector file was not rewritten. Agent-context script/marker update deliberately skipped (outside allowed surfaces). No tasks.md generated.
- No consequential unresolved product decision remains. Future runtime prerequisites (isolated DB schema preflight, configured service authentication and local sender/origin) are implementation gates, not product assumptions. Canonical contract approval remains required.
