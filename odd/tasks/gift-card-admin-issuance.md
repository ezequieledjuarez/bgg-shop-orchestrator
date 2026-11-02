# Admin Gift Card Issuance

## Objective

Allow an authenticated administrator to issue a single-use gift card, display its code once, and persist only its verifier. Scope is issuance only; redemption, account credit, and credit checkout remain separate work.

## Constraints

- Use existing Core GraphQL, BFF REST, and React admin boundaries; no provider calls or public domain.
- Preserve existing uncommitted changes and do not commit.
- Generate high-entropy codes in Core; never persist or log the raw code or authorization headers. Restrict issuance to staff/superusers in Core.
- Do not claim existing seed data or the active database was migrated; only apply an explicitly safe additive table change if required for local use.
- The code is returned once on successful creation. An interrupted response is not automatically retried because the original code cannot be recovered.

## Tasks

- [x] Define admin issuance contracts and tests: REST OpenAPI and Core SDL added; targeted SDL comparison passed.
- [x] Implement Core issuance with authorization and protected persistence: 11 focused tests passed.
- [x] Implement BFF issuance with sanitized errors and secret-safe logging: 14 focused tests passed; Core checks administrator privileges.
- [x] Add the admin screen and one-time display: three focused UI tests passed; generated types use the updated REST contract.
- [ ] Verify focused tests, contract alignment, and local behavior; record limitations.

## Verification

- Core: authorized and unauthorized issuance, amount bounds, stored hash and returned code, errors and schema.
- BFF: authentication, validation, upstream failure, no token/code logs, and no-store responses.
- Frontend: admin navigation, input validation, generated-code display, no automatic retry, and errors.
- Local database validation must avoid running the full destructive catalog import.
- The complete Core SDL comparison currently fails because five existing admin mutations are absent from the reference SDL; the new issuance mutation and its types match Graphene.
- Local PostgreSQL issuance was checked with a rolled-back transaction; the stored hash matched the generated code. Browser validation with an invalid token returned 401 and `Cache-Control: no-store`.
- Administrator browser E2E: the user signed in as an active superuser and issued a card for 20,000 ARS. The endpoint returned 201 with `no-store`, the displayed code matched the response, and PostgreSQL contained its matching hash and an unused card. The one-time test code was discarded without recording it; redemption and credit checkout are not yet implemented.
- Frontend suite: 68 passed. Core issuance plus checkout: 29 passed before adding two additional issuance tests; latest issuance-only run: 11 passed. BFF issuance: 14 passed; related BFF tests: 44 passed and two preexisting invalid-route failures.
- Frontend build remains blocked by the existing TypeScript configuration/version mismatch; project lint remains blocked by preexisting duplicate imports. Focused lint and component type check passed.
- For local validation, frontend runs on `http://127.0.0.1:3001` with a proxy to the updated BFF on port 5001; the preexisting services on ports 3000 and 5000 were not stopped.