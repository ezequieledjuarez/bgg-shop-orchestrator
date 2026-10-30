# Contract Remediation Plan

## Scope

Plan the observed Core GraphQL and BFF REST discrepancies. This document does not authorize contract changes. Preserve the existing data and run integration tests with synthetic users and isolated services.

## Findings And Work

1. **Invoice delivery:** The BFF now requests Core's `/invoices/{id}/` route and the proxy test checks the trailing slash. An isolated browser test downloaded a PDF for a synthetic paid order and observed HTTP 401 without authentication. Additional real-service tests for a missing invoice, invalid ID, and ownership remain pending.
2. **Credit idempotency and 400 responses:** The BFF returns `INVALID` for local address validation and maps Core's persisted `ADDRESS_REQUIRED` to `ADDRESS_REQUIRED_RECORDED`. The frontend releases an uncertain attempt only for the new code; the old `ADDRESS_REQUIRED` remains ambiguous. Core tests cover replay, changed payload conflicts, and a new key in SQLite and PostgreSQL; frontend tests cover lost responses and mixed versions. An isolated HTTP test covered BFF, Core, and PostgreSQL using a replay to simulate a lost response. OpenAPI and generated types are updated. An actual network interruption remains untested.
3. **Address constraints:** Both checkout flows, OpenAPI, and frontend use limits of 250, 500, 150, 32, and 50 Unicode characters for recipient, street, city, postal code, and phone. BFF checks supplied lengths before trimming, rejects explicit nulls, and preserves credit input for idempotency. Core validates both GraphQL checkouts. Boundary tests passed in BFF, Core, frontend, and PostgreSQL; the browser flow also used a 500-character Unicode street.
4. **Mercado Pago retry errors:** `PENDING_PAYMENT` maps to HTTP 409 and is documented in OpenAPI. The frontend explains that review is required and disables another retry on that screen. Core's existing concurrent retry tests passed with a simulated provider. An audited reconciliation mechanism and proof against previously issued provider preferences remain pending.
5. **Core GraphQL schema drift:** Graphene now honors the existing SDL default of 50 for `products.pageSize`; the BFF's public catalog continues to send its own default of 20. The SDL now includes existing user fields and administrative operations. The complete schema-introspection comparison passed.
6. **BFF routing tests:** Flask now returns HTTP exceptions rather than re-raising them. Tests distinguish invalid UUIDs (400), missing routes (404), and traversal-like paths matched only by the OPTIONS catch-all (405), without upstream calls.
7. **Refresh contract:** OpenAPI now documents the existing refresh route, cookie rotation, optional body token, and 200/401/502 responses. Route tests cover a synthetic token and missing token with Core mocked.

## Verification

- Run Core's `python -m pytest -q -p no:cacheprovider tests/test_graphql_products.py tests/test_graphql_orders.py tests/test_graphql_credit_checkout.py` and the isolated PostgreSQL credit tests.
- Run BFF's `python -m pytest -q -p no:cacheprovider tests/test_orders.py tests/test_credit.py tests/test_refresh_integration.py` and OpenAPI contract validation.
- Run frontend type generation, focused tests, lint, and build; review generated type differences rather than editing generated types manually.
- Repeat the isolated browser flow from login through redemption, payment, idempotent retry, order details, and successful PDF download. Inspect balance, inventory, order, invoice, and cart in the disposable database.

## Current Evidence

- Before correction, Core schema comparison and two BFF order-path tests failed, and invoice download returned 404.
- After correction, 124 BFF tests, 120 Core tests, 28 isolated PostgreSQL tests, and 125 frontend tests passed. The schema comparison, OpenAPI validation, generated-type check, and frontend build passed.
- An isolated browser run completed login, cart, gift-card redemption, credit checkout with a 500-character Unicode street, idempotent replay, order details, and PDF download. PostgreSQL confirmed one redemption, one paid order, one credit payment, one invoice, balance 7500.00 ARS, stock 2 from 3, an empty cart, and a 500-character stored street. No provider payment was made.
- For credit error recovery, 76 BFF tests, 76 Core checkout and order tests, 18 isolated PostgreSQL tests, and 63 frontend checkout tests passed. OpenAPI validation, generated-type synchronization, and the frontend build passed. A separate isolated HTTP run verified persisted 400 replay, changed-payload 409, local `INVALID`, a new-key payment, and paid replay; PostgreSQL contained one recorded rejection and one payment. It simulated a lost response by replaying the request rather than interrupting the connection.
- This plan does not resolve previously issued provider preferences, ambiguous provider attempts, or frontend recovery across closed tabs; those remain separate outstanding risks.