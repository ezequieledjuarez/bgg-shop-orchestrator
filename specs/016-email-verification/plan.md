# Implementation Plan: Token-Based Registration Email Verification

**Branch**: `016-email-verification` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

**Status**: Planning complete; implementation and runtime acceptance NOT performed.

**Input**: `specs/016-email-verification/spec.md`, full [checklist](checklists/requirements.md), root constitution, Ponytail rules, current service contracts/code, CU-C01 notes and feature 011 planning context.

## Summary

Require mailbox verification for newly registered customers before password login. Preserve existing accounts as explicitly **LEGACY_EXEMPT**, without fabricated verification timestamps, and keep administrative activation independent. Reuse Core PostgreSQL transactions for state, one current hashed challenge and durable rolling limits; use existing Flask BFF for REST mapping and trusted caller derivation; add a small explicit-confirmation React journey using BFF only. Submit email once after commit with local capture/fake delivery, not a worker or retry queue.

The drafts were promoted into the canonical `bgg-shop-bff/specs/openapi.yaml` and `bgg-shop-core/specs/schema.graphql` (canonical_per_service) and removed; [mapping/acceptance cases](contracts/README.md) are traceability only.

## Technical Context

| Area | Resolved choice |
|---|---|
| Language/Version | Python; Core requirements Django >=4.2.10,<5 and Graphene >=3.3; BFF Flask >=3; frontend React 19.2, TypeScript ~5.4/Vite 5.4. Runtime Python version not pinned by this feature; use existing supported project interpreter, not an upgrade. |
| Primary Dependencies | Existing Django auth/transactions/mail, Graphene, PostgreSQL/psycopg2, requests, Python secrets/hashlib/ipaddress; existing frontend fetch/History API. No new package, OAuth SDK, router, provider abstraction or queue. |
| Storage | Actual `auth_user` plus four feature-owned tables: sidecar, current challenge, limit bucket, limit event. Do not reuse the auxiliary in-memory refresh store as verification persistence. |
| Testing | Installed PyYAML/OpenAPI validator/graphql-core for draft checks; future Core pytest + real isolated PostgreSQL, BFF mocked-controller/contract pytest, frontend Vitest and local browser capture flow. |
| Target Platform | Local Linux project stack; disposable PostgreSQL only for destructive tests, locmem/fake mail first, optional isolated Mailpit later. |
| Project Type | Cross-service web feature: React → Flask BFF → Django/Graphene Core → PostgreSQL. |
| Performance Goals | No invented throughput SLA. One account-serialized proof transition, indexed limit lookups, no SMTP under DB locks; proposed mail timeout 3s under current BFF upstream timeout 10s. No guaranteed inbox delivery. |
| Constraints | Exactly 3600s token lifetime; single-use/replacement atomicity; 120s cooldown, 2 recipient resends/rolling hour, 10 caller resend requests/rolling hour, 10 invalid confirmations/rolling 900s. Explicit POST only; no auth/cart side effects while pending. |
| Scale/Scope | Local acceptance with ten captured messages; future separately authorized Gmail demo around ten messages. No SMTP/network execution, credential reads, installs, implementation, commits or pushes in this run. |

No unresolved technical clarification marker remains. Repository evidence, rejected alternatives and limits of evidence are in [research](research.md). The checklist's remaining runtime outcome (15/16 checked) is accepted as a planning-only boundary, not waived acceptance.

## Constitution Check

**Pre-design gate: PASS for planning.**

1. **Preserve established behavior:** only approved new-registration access changes; existing active customers/staff/superusers and their sessions remain eligible, disabled users stay disabled. Duplicate registration stays 409, email/password login remains, no auto-login.
2. **Contract ownership:** canonical sources remain `bgg-shop-core/specs/schema.graphql` and `bgg-shop-bff/specs/openapi.yaml`; frontend types generated from BFF only. Feature-local drafts were removed after promotion.
3. **Traceability:** requirement/acceptance IDs map to contracts, implementation seams, tests and measurable evidence below. No task completion or parser result represents runtime success.
4. **Customer/service protection:** Core authoritative gate, atomic proof consumption, secret-free logs/errors, neutral resend, trustworthy caller identity, no caching or guest-cart merge on denial.
5. **Smallest safe change:** native primitives and existing boundaries; no custom User migration, background provider layer or auth/session redesign. Four small feature tables coordinate persistence and rates in one transaction boundary.

No constitution exception is required. Canonical contract promotion and validation were completed before behavior.

## Project Structure

```text
specs/016-email-verification/
├── spec.md                              # existing; unchanged
├── checklists/requirements.md            # existing; unchanged
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── README.md                        # acceptance/traceability only (C01–C18)
```

### Future source seams (NOT edited)

| Owner | Existing files / proposed additions |
|---|---|
| Core contracts | `bgg-shop-core/specs/schema.graphql`; document the existing Core refresh route and new trusted GraphQL context in service auth specs as part of later canonical review |
| Core behavior | `saleor/graphql/api.py`, `saleor/auth_refresh.py`, `saleor/urls.py`, `opkeys/views.py`, `opkeys/middleware.py`, `saleor/settings.py`; proposed `saleor/email_verification.py` and a narrowly scoped `saleor/graphql/views.py` error-sanitizing GraphQLView; reuse `opkeys/utils.py::has_internal_secret` |
| Core migration | proposed `saleor/graphql/migrations/0021_email_verification.py` after current `0020_chat_conversations` (recheck head); explicit auth dependency and real-schema preflight |
| Core tests | existing `tests/test_graphql_auth.py`, `test_auth_refresh.py`, `test_auth_refresh_integration.py`, `test_user_permissions_postgres.py`, `test_opkeys_internal.py`; proposed `tests/test_email_verification.py`, `test_email_verification_postgres.py`, `email_verification_settings.py` |
| BFF | `bgg-shop-bff/specs/openapi.yaml`, root `app.py` (not FastAPI stub), `src/services.py`, `src/proxy.py`, `src/dtos/auth.py`, `src/controllers/auth_controller.py`; extend existing auth seams instead of generic auth framework |
| BFF tests | `tests/test_auth.py`, `test_auth_current_user.py`, `test_refresh_proxy.py`, `test_refresh_integration.py`, `test_services_openapi_contract.py`; proposed `tests/test_email_verification.py`, `test_services_email_verification_contract.py` |
| Frontend | `src/main.tsx`, `src/App.tsx`, `src/routing/routes.ts`, `src/auth/AuthScreens.tsx`, `src/ui/messages.ts`, generated `src/types/generated/bff-api.d.ts`; proposed `src/auth/EmailVerificationScreen.tsx` and `.test.tsx`, extend `AuthScreens.test.tsx` |
| Shared docs/evidence later | `docs/CU-C01-AUTHENTICATION-CHANGES.md`, relevant auth service specs, CU-C01 in `CasosDeUso.md`; future `odd/tasks/016-email-verification.md` with sanitized reports, never tokens |

**Structure Decision:** keep domain state and counters together in Core, presentation/mapping in existing BFF/frontend seams. This workflow does not generate `tasks.md`; `/speckit.tasks` is the next separate approved step.

## Contracts & Endpoints Gate (MANDATORY)

**Planning gate: PASS. Owning-contract gate: PASSED (promoted to canonical contracts, structurally validated, types generated). Runtime gate: see implementation evidence.**

| REST endpoint | Auth / request | Success | Negative / compatibility |
|---|---|---|---|
| POST `/api/v1/auth/register` | public; existing email/password/first_name/last_name | 201 `{user,verification:{state:PENDING,delivery_status,message}}`; no session/cookies | 400 existing validation, 409 EMAIL_EXISTS, existing sanitized 502; post-commit delivery failure remains 201/UNCONFIRMED |
| POST `/api/v1/auth/login` | public password check; optional existing guest cookie | unchanged 200 `{user,session}` for eligible users | NEW 403 EMAIL_NOT_VERIFIED after valid password, before cart/credentials; existing 401 for bad password/inactive, 400/502 unchanged |
| POST `/api/v1/auth/email-verification/confirm` | public; `{token}` only | 200 `{verified:true,message}`, no user/tokens | generic 400 INVALID_VERIFICATION_TOKEN, 429 caller limit, 502 invalid/unreachable Core, 503 unavailable state/limit service |
| POST `/api/v1/auth/email-verification/resend` | public; `{email}` only | neutral 202 `{message}` for pending/verified/exempt/absent/suppressed/send-failure | 400 malformed email, 429 caller-only retry, 502/503 infrastructure failure independent of lookup |
| POST `/api/v1/auth/refresh` | existing cookie/body refresh credentials | unchanged 200/cookie protocol | stored subject must be eligible; existing sanitized 401 detail/cookie clear, 502 unchanged |
| GET `/api/v1/auth/me` | existing Bearer access | existing safe capability projection | same current-user unauthorized outcome for pending/missing/inactive subject; no new projection fields |

The standalone OpenAPI overlay defines changed registration/login/refresh and new operations. Existing `/auth/me`, logout, cart and internal OpKey wire definitions remain in canonical contracts; only shared eligibility enforcement changes, with regression evidence required. GET/HEAD verification API requests return 405 without consuming proof. `/verify-email` is a frontend route, not a Core GET activation endpoint.

Core preserves `register`/`login` and adds `confirmEmailVerification(input)` and `resendEmailVerification(input)`, with explicit sanitized payload errors. `me` remains existing authenticated identity. BFF creates trusted internal caller headers, never forwards client-supplied ones; new Core verification mutations require existing service-secret authentication plus a bounded caller digest. See [contract mapping](contracts/README.md).

All changed auth outcomes are no-store, including errors. New confirmation responses are no-referrer. Verification proof is never an access/refresh/OpKey credential. No user/email/redirect identifier is accepted by confirmation.

## Core architecture and security invariants

- **Explicit legacy policy:** backfill LEGACY_EXEMPT, null verified_at; PENDING for new register. State gate checks `is_active` independently. Missing policy after rollout fails closed; backfill/deployment is coordinated.
- **Atomic proof:** one digest-bound challenge per account, 3600s authoritative deadline, row-lock/recheck/consume and VERIFIED in one transaction. Account email must still match. No prior proof restoration on send failure.
- **Rate ownership:** Core PostgreSQL events use rolling windows and row locks, not BFF memory or the existing fixed-window Redis chatbot limiter. Same normalized recipient for alternate casing. Initial issue starts 120s cooldown; only resends count toward the two/hour replacement quota.
- **Caller:** Flask `request.remote_addr`, normalized and hashed; ignore forwarded/client-supplied identity. Current frontend has no Vite proxy and calls BFF directly; NAT can conservatively group callers. Direct Core confirmation/resend requires authenticated BFF context so it cannot bypass caller policy.
- **Fail closed:** no send/consume when limit storage or trusted context is unavailable. Invalid outcomes commit attempt counts; storage exceptions rollback. Throttle replies return ceiling seconds until caller eligibility, never recipient status/quota.
- **GraphQL errors:** do not assume framework variable-coercion/debug errors are secret-safe. At the GraphQL HTTP view boundary, sanitize verification-operation validation/execution errors before formatting/logging, including nested or wrongly typed token variables; preserve existing unrelated operations. BFF never forwards raw GraphQL errors. Add regression tests for direct Core malformed-variable requests as well as ordinary BFF requests.
- **All auth surfaces:** shared eligibility used in login, `_auth_tokens`, `_authenticated_user` (JWT/delegated key), opaque refresh issuance/rotation, internal user-bound OpKey issue/validate and middleware delegation. Audit raw request.user/session consumers. Preserve null-user service keys without turning them into a customer identity.
- **Delivery:** commit before one bounded submission. Failed/unknown delivery keeps pending account and spent issuance allowance. No durable plaintext outbox, hidden retry, guaranteed inbox claim or provider diagnostics. Lost registration response can yield duplicate 409 on manual retry, not another account or implicit resend.
- **UI:** pending screen replaces current 900ms registration redirect; correct-password 403 offers resend/login guidance. Fragment capture + immediate history replacement before telemetry; explicit event-handler POST, never useEffect/GET consumption. Disabled button prevents double clicks; server remains authoritative. No auto-login/session replacement. Standard login route is `/iniciar-sesion` (legacy `/login` alias).

## Phase 0 — Research (completed)

[research.md](research.md) resolves stack, actual User schema evidence, legacy semantics, opaque/JWT refresh mismatch, OpKey bypass seams, service trust, transaction/delivery failure semantics, native SMTP configuration names and local tooling. Evidence does not establish a live database schema or sender readiness. No product question remains open.

## Phase 1 — Design and contracts (completed)

- [data-model.md](data-model.md): exact sidecar/challenge/limit fields, constraints, state machine, clock/window definitions, lock ordering, migration/backfill/rollback safeguards.
- [contracts/](contracts/README.md): error mapping, compatibility and C01–C18 acceptance cases (shapes live in canonical contracts).
- [quickstart.md](quickstart.md): parse-only commands, future hermetic tests/isolated DB prerequisites and measurable acceptance evidence.
- Agent-context update deliberately **skipped**: `.github/copilot-instructions.md` and update scripts fall outside allowed edits. No script was run that could alter them.

## Phase 2 — Implementation sequencing proposal (not executed)

This is dependency order for later task generation, not an executable task ledger:

1. **Approve/promote contracts first.** Review draft compatibility and service-context documentation; update owning SDL/OpenAPI, validate them locally and generate frontend types. Assert Graphene intent/BFF documents/generated types agree. Do not implement new behavior against draft-only authority.
2. **Write failing tests where runnable.** Add hermetic no-env/no-network fixtures and pure normalization/hash/window/mapping tests, then real PostgreSQL migration/concurrency fixtures. For DB/browser cases without prerequisites, record BLOCKED rather than substitutes or false green results.
3. **Build migration and Core primitive.** Schema metadata preflight, migration/backfill, transaction/locking/challenge/rolling-limit helpers and fake mail. Prove races and post-commit failure semantics before wiring HTTP/UI.
4. **Wire every Core gate and BFF mapping together.** Include refresh/OpKey/session negatives before enabling new registration. Add bounded Core input validation (not just BFF), safe error handling, trusted caller context and no-store/no-referrer coverage; do not broaden password/role/session behavior.
5. **Integrate generated frontend contract.** Pending/recovery/confirmation screens and fragment bootstrap; native accessible forms/status/errors, keyboard/focus behavior and event-only mutation. No browser-to-Core request.
6. **Run isolated local acceptance and docs alignment.** Ten captured successful journeys, race/window/legacy/security tests, failure capture, five-participant walkthrough; update affected service/shared documentation and attach sanitized evidence. Any Gmail setup/send requires a new explicit authorization.

## Traceability and measurable evidence plan

| Requirements | Scenarios / contract tests | Future evidence and threshold |
|---|---|---|
| FR-001, FR-002 | US1-A1/A2; C01/C02/C15 | SC-001: zero pre-verification sessions/access/refresh/OpKeys/cart merges; one account on retry |
| FR-003, FR-009 | US1-A3/A4/A5; C03/C12 | SC-002: 10/10 local captured proofs verify then password-login, 0 automatic logins |
| FR-004, FR-005, FR-013 | US2-A1; C04/C05/C06/C07 | SC-003: all invalid categories rejected; expiry exact rejected; at most one race winner |
| FR-006, FR-007, FR-008 | US2-A2/A3/A4; C07/C08/C09/C10/C11 | SC-004: identical neutral acknowledgments and every just-before/exact/just-after quota boundary; casing/reload/parallel/restart coverage |
| FR-010, FR-011 | US2-A5; C13/C16/C17 | SC-006: every failure remains recoverable; 0 token/password/provider/credential leaks in inspected non-email records |
| FR-012 | US3-A1; C14/C15 | SC-007: every active legacy class retains access, 0 false verification timestamps or reactivated disabled accounts |
| FR-014 | canonical promotion gate, all contract cases | parser + generated-type checks AND real mapping/integration evidence before behavior/PR claims |
| FR-015 | US3-A2; C18 | email/password only; no reset, Google or magic-link alternatives |
| FR-016 | all local mail fixtures | 0 external SMTP connections; locmem/fake first, optional isolated Mailpit only |
| UI recovery across FR-003/005/009/010 | US1/US2 walkthrough | SC-005: at least 4/5 participants identify next action unaided after pending/success/unusable feedback |

Evidence package later: exact commands/prerequisites, pytest/Vitest results, DB migration/concurrency outcomes, sanitized capture counts (not raw emails/tokens), browser route/storage/network assertions, failure matrix and anonymous walkthrough tally. Store future evidence under `odd/tasks/016-email-verification.md` only after that surface is separately authorized. No runtime target is checked off here.

## Post-design Constitution Check

**PASS for planning.** Contract ownership, legacy policy, administrative disablement, normalization/uniqueness, authenticated side effects and local-only constraints remain explicit. No unjustified architecture exception. Future gates remain: canonical approval/validation, isolated actual-schema preflight, tests-first implementation, all credential surfaces and acceptance evidence. An absent test prerequisite is not a product clarification.

## Planning workflow and verification boundary

Setup ran with explicit `SPECIFY_FEATURE_DIRECTORY=/home/eze/develop/boardgame-app/specs/016-email-verification` and `SPECIFY_FEATURE=016-email-verification`; returned the correct FEATURE_SPEC, IMPL_PLAN, SPECS_DIR and BRANCH. The dirty selector resolving 011 was not changed. Optional git pre/post hooks are not executed under the no-commit instruction.

`skill_resolution`: registry absent; `vercel-react-best-practices` loaded before frontend analysis. No implementation or agent-context update, tasks generation, installs, credentials/.env reads, runtime/database tests or network/email activity is included. Draft structural checks and final readback are recorded in [quickstart](quickstart.md).
