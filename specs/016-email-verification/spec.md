# Feature Specification: Token-Based Registration Email Verification

**Feature Branch**: `016-email-verification`
**Created**: 2026-11-09
**Status**: Specification clarified — ready for contract-first planning; not implemented.
**Input**: User request to specify email verification with a token. Retain email/password login, discard Google login, and support a future academic local demo using Gmail SMTP for approximately ten emails.

> Proposal only. Nothing in this document asserts that email verification, delivery, or new contract operations exist today. This authoring run changes specification artifacts only and authorizes no network connections, email sends, implementation, commits, or pushes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Register and verify ownership before login (Priority: P1)

A visitor registers with the existing name, email, and password fields, receives verification instructions, confirms ownership of the registered mailbox, and then signs in with email and password.

**Why this priority**: A newly registered account must not obtain authenticated access before mailbox ownership is verified.

**Independent Test**: Using local captured email and a fresh account, register, attempt login before verification, confirm the email, and then log in. Check both visible outcomes and the absence of authenticated credentials before verification.

**Acceptance Scenarios**:

1. **US1-A1 — Pending registration**: **Given** a fresh email and valid existing registration fields, **When** registration succeeds, **Then** exactly one account is pending verification, instructions explain that email verification is required, a verification message is submitted to the configured delivery channel, and no authenticated session or credentials are issued.
2. **US1-A2 — Login blocked**: **Given** a newly registered pending account, **When** correct credentials are submitted, **Then** login is denied without creating a session, issuing access/refresh/operation credentials, or merging a guest cart; the user can reach verification recovery instructions.
3. **US1-A3 — Confirm and log in**: **Given** a pending account and its current, unused, unexpired token, **When** the user explicitly confirms verification, **Then** that account alone becomes verified, the token becomes unusable, and a success screen directs the user to email/password login without automatic sign-in; subsequent valid login follows existing behavior.
4. **US1-A4 — Separate account restrictions**: **Given** an account disabled for another reason, **When** its mailbox is verified, **Then** verification does not remove that restriction or enable login.
5. **US1-A5 — No unintended activation**: **Given** an email preview, link scanner, or ordinary page load, **When** it opens the verification link without the user's confirmation action, **Then** the account is not verified and the token is not consumed.

### User Story 2 - Recover safely from an unusable or missing message (Priority: P1)

A visitor whose verification message did not arrive or whose link is unusable can request another message without creating another account or exposing account membership.

**Why this priority**: Delivery problems and expired links must not permanently strand a registration.

**Independent Test**: With locally seeded pending, verified, and nonexistent identities, exercise resend and invalid-link outcomes using a controlled clock and captured delivery; compare public responses and account transitions.

**Acceptance Scenarios**:

1. **US2-A1 — Invalid link**: **Given** a missing, malformed, tampered, unknown, expired, used, or superseded token, **When** confirmation is attempted, **Then** no account state changes or credentials are issued, and the same safe unusable-link outcome offers login or resend without disclosing the token's owner or the precise failure reason.
2. **US2-A2 — Resend**: **Given** an eligible pending account whose cooldown has elapsed and whose approved quotas are not exhausted, **When** a new message is requested, **Then** no duplicate account is created, a new expiring token is issued, and all prior verification tokens for that account become unusable.
3. **US2-A3 — Non-enumeration**: **Given** a syntactically valid pending, verified, or nonexistent email, **When** resend is requested under equivalent caller-limit conditions, **Then** the public acknowledgment has the same status, structure, and neutral text; only an eligible pending account can receive a new message, and neither verification state nor mailbox existence is disclosed.
4. **US2-A4 — Abuse limits**: **Given** requests at the approved cooldown and quota boundaries, including repeated invalid confirmation attempts, **When** another request is made, **Then** the approved recipient and caller limits suppress excess delivery or attempts, return the specified safe response, and do not verify or duplicate an account.
5. **US2-A5 — Delivery failure**: **Given** a locally simulated delivery rejection or timeout after account creation, **When** registration or resend completes, **Then** the account remains pending, no authenticated access is granted, no confirmed-delivery claim is shown, and recovery remains available under the approved limits. A lost response or repeated registration must not create another account.

### User Story 3 - Preserve existing accounts under an approved transition policy (Priority: P2)

An existing customer can understand whether verification applies to their account without an unapproved lockout, privilege change, or misleading claim that historic email ownership was checked.

**Why this priority**: Introducing verification must not silently decide the access policy for existing customers, staff, or local demonstration accounts.

**Independent Test**: Use local fixtures for existing active customers, staff/superusers, disabled accounts, and newly registered pending accounts; verify that existing access is preserved, disabled accounts remain disabled, and only new accounts require verification.

**Acceptance Scenarios**:

1. **US3-A1 — Transition policy**: **Given** an existing customer, staff member, or superuser, **When** verification is introduced and login is attempted, **Then** the account is exempt from the new verification requirement, existing sessions retain their current behavior, disabled accounts remain disabled, and no account is silently marked as having proved mailbox ownership.
2. **US3-A2 — No scope expansion**: **Given** the proposed registration/login journey, **When** a visitor follows its available actions, **Then** login remains email/password only, there is no Google sign-in option, and verification never behaves as password reset or passwordless login.

### Edge Cases

- At the exact expiry instant the token is invalid; validity requires confirmation strictly before its deadline.
- Two simultaneous confirmations of one valid token allow at most one successful state transition; the other receives the safe unusable-link outcome.
- A token cannot verify another account or a different email address, even when a caller supplies another identifier.
- A resend racing confirmation must have one consistent result: either verification completes and no further effective token is issued, or the replacement wins and the older token is rejected.
- Resend failure leaves the account pending and recoverable; no previously revoked token is silently restored. The user can retry after the approved cooldown.
- Duplicate registration retains existing email-uniqueness rules and the current duplicate-email rejection; it does not implicitly resend or bypass resend limits. Registration non-enumeration is not newly promised by this feature.
- Existing email normalization applies consistently to registration, login, and resend; alternate casing does not create another account or reset recipient quotas.
- A verification message may be delayed or filtered. Submission is not proof of inbox delivery; the screen does not promise guaranteed delivery.
- Browser back/refresh, copied links, service outages, or an already authenticated browser must not consume tokens merely by loading a page, switch identities, or silently sign the user in.
- The destination of a verification link is the approved local application, not a caller-controlled redirect. Analytics, referrers, browser history after capture, application/proxy logs, and errors must not retain raw verification tokens.
- Email verification is separate from administrative activation. No existing meaning of `isActive`/`is_active` is redefined without explicit contract review.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Registration MUST preserve existing required fields, validation, normalization, and uniqueness rules while creating new customer accounts in a pending-verification state.
- **FR-002**: Pending new accounts MUST be denied authenticated access at authoritative service boundaries, not only in the interface. Registration, confirmation, and resend MUST NOT issue authenticated credentials or create a login session. Blocked login MUST NOT trigger guest-cart merge.
- **FR-003**: The system MUST provide verification instructions and a mailbox-ownership confirmation action associated exclusively with the registered account and email. Merely loading or previewing a link MUST NOT verify the account.
- **FR-004**: A verification token MUST be unpredictable, purpose-bound to email verification, account/email-bound, expiring, and single-use. Confirmation MUST atomically consume its validity and verify at most one account. Verification tokens MUST NOT be accepted as login, password-reset, access, refresh, or operation credentials.
- **FR-005**: Invalid, expired, reused, superseded, or otherwise unusable tokens MUST receive one sanitized public outcome, with no identity disclosure, state change, credential issuance, or raw token echo.
- **FR-006**: Eligible pending users MUST be able to request another verification message. Issuing a replacement MUST invalidate all prior verification tokens for that account; verified and nonexistent accounts MUST receive no verification message.
- **FR-007**: Resend MUST return a neutral acknowledgment for well-formed email submissions, without revealing account existence or verification state. Malformed input MAY receive field validation. Caller-level throttling MAY have a distinct safe response independent of account membership; recipient-specific suppression MUST preserve the neutral acknowledgment.
- **FR-008**: Resend MUST enforce a 120-second per-recipient cooldown, at most two resends per normalized recipient in any rolling hour, and at most ten resend requests per caller in any rolling hour. Invalid confirmations MUST be limited to ten attempts per caller in any rolling 15-minute window. Caller identity MUST be enforced server-side and remain consistent across page reloads; its trusted derivation MUST be defined in contract-first planning. Recipient-specific suppression MUST retain the neutral acknowledgment. Caller throttling MUST return safe retry guidance using the time until the applicable quota permits another attempt, rounded up to whole seconds. A resend is eligible only when cooldown and all applicable quotas allow it. Local acceptance tests MUST cover just-before, exact, and just-after cooldown/window boundaries, alternate email casing, and page reloads.
- **FR-009**: Successful confirmation MUST direct the user to ordinary email/password login; verification MUST NOT bypass password checks, administrative disablement, or any separate authorization requirement.
- **FR-010**: Delivery failure MUST leave an existing pending account recoverable without duplicate creation or authenticated access. User-facing text MUST distinguish submission from guaranteed delivery and MUST NOT disclose provider errors, account existence through resend failures, or infrastructure details.
- **FR-011**: Raw verification tokens MUST be disclosed only in the intended verification message and the minimum confirmation exchange. They MUST NOT appear in ordinary account responses, error payloads, logs, analytics, persistent browser history after capture, or reusable plaintext token records. Passwords, credential material, and internal errors MUST never be exposed in these surfaces. Verification exchanges MUST be non-cacheable.
- **FR-012**: Existing accounts MUST be exempt from the new verification requirement without being represented as having proved mailbox ownership. Existing access and session behavior MUST be preserved for customers, staff, and superusers; disabled accounts MUST remain disabled. Verification is required only for accounts registered after this feature takes effect.
- **FR-013**: Each token MUST expire exactly one hour (3,600 seconds) after issuance, use one authoritative deadline, and reject confirmation at or after expiry.
- **FR-014**: All future changed service interfaces MUST be defined and validated in their owning canonical contracts before corresponding behavior is implemented. Feature-local proposals MUST be labeled non-authoritative; see Contract Requirements below.
- **FR-015**: Google login MUST be excluded from this proposed CU-C01 scope; email/password login MUST remain. Password reset/change, magic-link login, email-address change, and unrelated session/role redesign MUST NOT be added.
- **FR-016**: Local verification MUST use captured messages and simulated delivery failures without external connections. A future, separately authorized Gmail SMTP demo may submit approximately ten real verification emails; configuring or sending them is outside this authoring run and MUST NOT become a prerequisite for local validation.

### Key Entities

- **Customer account**: Existing identity and credential record with an explicit proposed mailbox-verification state. Administrative activation and permissions remain distinct.
- **Verification challenge**: Proof associated with one account, registered email, purpose, issue time, expiry, and consumed/revoked status. Raw proof is not ordinary account data.
- **Delivery attempt**: A submission outcome sufficient to support sanitized recovery and local evidence, without retaining credentials or raw tokens in operational records.
- **Abuse-limit state**: Recipient and caller allowances over approved time windows; independent of browser reloads and not a public account lookup.

### Contract Requirements — proposal, not canonical definitions

The canonical sources remain [Core SDL](../../bgg-shop-core/specs/schema.graphql) and [BFF OpenAPI](../../bgg-shop-bff/specs/openapi.yaml). Existing operations include Core `register`/`login` and BFF `POST /api/v1/auth/register` and `POST /api/v1/auth/login`; neither source currently defines this verification flow. No operation names, new paths, status codes, or payload fields for verification are approved by this spec.

Before future behavior changes, planning must produce reviewable draft definitions covering:

1. Registration's pending-verification outcome and delivery-submission semantics, with no authentication credentials; login denial before verification and unchanged behavior after eligible verification.
2. Confirmation and resend requests/results, input bounds, public access rules, error codes, HTTP mappings, retry guidance, non-cacheable responses, neutral resend acknowledgments, and sanitized delivery failures.
3. Agreement on token consumption, replacement, expiry, and concurrency semantics across Core and BFF; examples using placeholders only. No raw token is part of the ordinary account representation.
4. Core ownership of account state and proof validation, BFF adaptation and sanitization, and frontend consumption of BFF only. Browser code must not contact Core directly or become the authoritative source of verification state.
5. Representation of pending versus verified state separately from existing administrative activation; treatment of refresh or operation credentials that might otherwise bypass the new-account restriction; approved legacy policy from Q1.
6. Compatibility review of existing registration and login response shapes and duplicate-email behavior; existing clients must not interpret “registered” as “verified.”
7. Local contract checks and test cases mapped to the requirements and acceptance IDs below. Draft validation does not establish runtime implementation or email delivery.

Feature-local drafts were promoted into the canonical service contracts and removed; `contracts/README.md` is acceptance/traceability only.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In all local new-account tests, zero sessions or authenticated credentials are issued before verification, and zero guest carts are merged on blocked login.
- **SC-002**: In ten local captured-message trials with valid current tokens, all ten accounts can be verified and then signed in using their passwords; verification itself signs in zero accounts.
- **SC-003**: Every tested missing, malformed, tampered, unknown, expired, consumed, and superseded token is rejected without account changes; two simultaneous uses produce at most one successful verification.
- **SC-004**: All pending/verified/nonexistent resend comparison cases have equivalent public acknowledgments under equal caller-limit conditions; all approved cooldown and quota boundary cases suppress excess sends or attempts.
- **SC-005**: In a local usability walkthrough, at least four of five participants identify the next action after pending registration, successful verification, and unusable-link feedback without assistance.
- **SC-006**: Every local delivery-failure case leaves the account pending and recoverable, with zero exposed raw tokens, passwords, SMTP credentials, or provider diagnostics in inspected non-email responses and operational records.
- **SC-007**: Every existing-account class passes its local access-preservation test, no exempt account is falsely marked verified, and no separate administrative restriction is removed by verification.

These are future acceptance targets, not observed test results. The ten-message local capture target does not authorize ten external sends.

## Assumptions

### Confirmed scope and dependencies

- Target users are customers using existing email/password registration and login. Google sign-in is discarded; use of Gmail SMTP is transport only, not Google authentication.
- All application services and validation remain local. Mailpit is already declared in [podman-compose.yaml](../../podman-compose.yaml) as a local capture channel; no configuration is changed or runtime readiness claimed.
- The requested later delivery goal is Gmail SMTP for approximately ten academic demo messages. Local capture does not prove Gmail delivery. Any external connectivity check or actual send requires separate explicit authorization.
- The user reports the root `.env` is ignored and contains `MEEPLE_APP_SMTP_PASSWORD`. That report is not independently verified; `.env` is never read for this work. Refer to the variable name only. Future sender identity, connection settings, and delivery setup belong to later authorized planning; this spec includes no credential value.
- Product choices Q1, Q2, and Q3 are approved. Replacement-token revocation and explicit confirmation rather than page-load consumption are proposed security requirements in this specification.
- There is no cleanup/retention redesign, retroactive session revocation, account deletion, or migration implementation in this feature specification.

### Resolved product decisions

- **Q1 — Existing-account policy (approved: A)**: Existing accounts are exempt. Preserve existing customer, staff/superuser, and session access without claiming historical mailbox verification. Disabled accounts remain disabled.
- **Q2 — Token lifetime (approved: 1 hour)**: Each token expires 3,600 seconds after issuance. Confirmation at or after that deadline is rejected.
- **Q3 — Abuse and resend policy (approved: B)**: Enforce a 120-second resend cooldown, two resends per recipient per hour, ten resend requests per caller per hour, and ten invalid confirmations per caller per 15 minutes. Apply rolling windows and allow retry only when every applicable restriction has elapsed; caller-level retry guidance reports that remaining wait without exposing recipient state.

All three product decisions are approved by the user. Contract-first planning must still resolve exact operation shapes, public error mappings, trusted caller identity, and compatibility details before implementation; this specification does not approve unspecified interface definitions.

### Current evidence and narrowly proposed CU-C01 alignment

- [Authentication as-built spec](../001-authentication-as-built/spec.md) and [CU-C01 authentication notes](../../docs/CU-C01-AUTHENTICATION-CHANGES.md) explicitly exclude email confirmation and social login. Registration currently directs users to login without automatic sign-in. These documents remain historical/current-baseline evidence, not proof of this proposal.
- [CasosDeUso.md, CU-C01](../../CasosDeUso.md) still describes Google and immediate session creation during registration. The proposed replacement removes its Google alternative and separates registration → pending verification → confirmation → password login. It does not claim that replacement is implemented. That file is unchanged because it is outside the allowed edit surface.
- The current canonical Core SDL includes user activation, registration, login, and authentication credentials; the BFF contract includes existing registration, login, refresh, and logout. Historical authentication notes are not a substitute for these canonical interfaces.
- [Moderation plan](../011-moderate-content-reviews/plan.md) establishes the repository's distinction between feature-local drafts and owning service contracts; this proposal preserves that distinction.
- [.agents/ponytail.md](../../.agents/ponytail.md) was read: keep the feature minimal without weakening validation, error handling, or security. No new framework, queue, provider abstraction, or dependency is selected here.
- `skill_resolution`: `.atl/skill-registry.md` was absent; no installed skill is applicable to pure specification authoring.
- Workflow scope exception: `.specify/feature.json` already has user changes and is outside the allowed edit surface. It is not overwritten or repointed. Downstream commands must explicitly select `specs/016-email-verification` until a separately authorized metadata update is made.

### Requirement and acceptance traceability

| Requirements | Acceptance coverage | Measurable outcomes |
| --- | --- | --- |
| FR-001, FR-002 | US1-A1, US1-A2; duplicate/normalization edge cases | SC-001 |
| FR-003, FR-009 | US1-A3, US1-A4, US1-A5 | SC-002, SC-005, SC-007 |
| FR-004, FR-005, FR-013 | US2-A1; exact-expiry, cross-account, concurrency edge cases; Q2 | SC-003 |
| FR-006, FR-007, FR-008 | US2-A2, US2-A3, US2-A4; resend race; Q3 | SC-004 |
| FR-010, FR-011 | US2-A1, US2-A5; leakage and redirect edge cases | SC-006 |
| FR-012 | US3-A1; Q1 policy table | SC-007 |
| FR-014 | Contract Requirements 1–7; future owning-contract validation and cross-boundary acceptance cases | SC-001 through SC-004, SC-006 |
| FR-015 | US3-A2; review of proposed journey actions | SC-002 |
| FR-016 | US1/US2 local captured-message and failure tests; authorization boundary review | SC-002, SC-006 |

### Authoring verification boundary

Only documentation readback, requirement traceability, marker counts, local link checks, whitespace checks, and Git branch/status inspection are applicable now. No functional, browser, contract-schema, SMTP, or delivery test has run for this proposed feature. The checklist records remaining readiness failures rather than marking unresolved policy as passed.
