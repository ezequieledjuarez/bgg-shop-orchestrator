# Feature Specification: Customer Authentication (As-Built)

**Feature Branch**: `not applicable — retrospective specification`
**Created**: 2026-10-21
**Status**: As-built / retrospective
**Input**: CU-C01, implemented customer registration, login, and local logout in the orchestrator repository.

> This document records the buyer-facing behavior evidenced in the current repository. It is not a proposal or a requirement to implement excluded behavior. “MUST” statements below describe the observed baseline.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create a customer account (Priority: P1)

A visitor creates an account using their name, email address, and password so they can later sign in as a buyer.

**Why this priority**: Account creation is the implemented entry point for buyers who do not yet have an account.

**Independent Test**: Submit a valid registration and verify that account creation is confirmed and the visitor is directed to login without being signed in.

**Acceptance Scenarios**:

1. **Given** a visitor with valid registration details, **When** they submit the registration form, **Then** the account is created, a success state is shown, and the visitor is directed to login without an authenticated session.
2. **Given** an email address already registered, **When** the visitor submits that address, **Then** registration is rejected as a duplicate and the visitor remains able to correct the form.
3. **Given** invalid or incomplete form data, **When** the visitor submits it, **Then** validation feedback is shown and no account is reported as created.

### User Story 2 - Sign in and sign out (Priority: P1)

A registered buyer signs in with email and password, sees the authenticated navigation state, and can sign out locally.

**Why this priority**: Sign-in establishes the buyer context required by authenticated actions elsewhere in the implemented store.

**Independent Test**: Exercise valid and invalid sign-in, inspect the visible navigation state, then sign out and verify the visitor state returns.

**Acceptance Scenarios**:

1. **Given** an existing account and valid credentials, **When** the buyer signs in, **Then** an authenticated session is stored for the current browser tab and the buyer returns to the catalog with authenticated navigation.
2. **Given** invalid credentials, **When** the visitor attempts to sign in, **Then** the attempt is rejected with a generic credential error that does not disclose whether the email exists.
3. **Given** an authenticated browser session, **When** the buyer signs out, **Then** the local session is removed and visitor navigation is shown.

### Edge Cases

- Registration with an already-used email is rejected; the duplicate is reported without creating a second account.
- Invalid, malformed, or missing form fields are surfaced as validation feedback rather than a success state.
- Unexpected service failures are shown as user-facing errors without exposing internal infrastructure details.
- Local logout does not revoke already-issued tokens server-side; it only clears the browser's local session.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: As built, the system MUST allow a visitor to register with first name, last name, email, and password.
- **FR-002**: As built, the system MUST reject duplicate email registration and provide validation or error feedback for invalid submissions.
- **FR-003**: As built, successful registration MUST confirm account creation and direct the visitor to login without automatically signing them in.
- **FR-004**: As built, the system MUST authenticate a registered buyer using email and password and present a generic error for invalid credentials.
- **FR-005**: As built, a successful login MUST establish the browser session and update the visible navigation to the authenticated state.
- **FR-006**: As built, logout MUST clear the browser's local session and restore visitor navigation.
- **FR-007**: Passwords and internal service errors MUST NOT be shown in user-facing success or error responses.

### Key Entities

- **Customer account**: A buyer identity with a name, email address, and password credential; the password is not exposed in user-facing account data.
- **Browser session**: The local authenticated state used by the buyer until it is cleared or otherwise no longer valid.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 3 registration acceptance scenarios produce their stated success, duplicate, or validation outcome.
- **SC-002**: All 3 sign-in/sign-out acceptance scenarios produce the stated authentication and navigation outcome.
- **SC-003**: In the invalid-credential scenario, the user-facing result does not distinguish an unknown email from a wrong password.
- **SC-004**: After local logout, the browser has no stored local session and shows visitor navigation.

## Assumptions

- The feature is for buyer accounts using local email-and-password credentials.
- A registration does not automatically sign in the new account.
- Login state is local to the browser tab; the current implementation uses session storage.
- Social login, email confirmation, password recovery/change, roles, administrative permissions, refresh-token rotation/revocation, and server-side logout are not part of implemented CU-C01.

### As-Built Status, Limitations, and Evidence

- **Verified in source/tests**: Registration and login flows, local session handling, validation, and user-visible session state are represented by the linked implementation and tests.
- **Reported, not rerun for this documentation change**: The implementation note records Core, BFF, and Frontend automated test results and successful HTTP checks. Browser automation was not run there; no browser or live-stack test was run as part of this specification work.
- **Known security limitation**: Browser session data is accessible to same-origin JavaScript, and local logout does not revoke tokens on the server. Production session-hardening and token lifecycle behavior remain outside the implemented flow.
- **Evidence references**:
  - Use case and implementation record: [CasosDeUso.md](../../CasosDeUso.md), [CU-C01 authentication notes](../../docs/CU-C01-AUTHENTICATION-CHANGES.md).
  - Contracts: [BFF OpenAPI](../../bgg-shop-bff/specs/openapi.yaml), [Core GraphQL schema](../../bgg-shop-core/specs/schema.graphql).
  - Implementation: [Frontend authentication screens](../../bgg-shop-frontend/src/auth/AuthScreens.tsx), [Frontend session handling](../../bgg-shop-frontend/src/auth/session.ts), [Core GraphQL implementation](../../bgg-shop-core/saleor/graphql/api.py), [BFF authentication controller](../../bgg-shop-bff/src/controllers/auth_controller.py).
  - Tests: [Frontend authentication tests](../../bgg-shop-frontend/src/auth/AuthScreens.test.tsx), [BFF authentication tests](../../bgg-shop-bff/tests/test_auth.py), [Core authentication tests](../../bgg-shop-core/tests/test_graphql_auth.py).
