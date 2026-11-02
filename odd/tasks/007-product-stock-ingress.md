# Product Stock Ingress

## Historical Record

This document records an earlier stock-intake-only work unit. Its checkboxes,
contract assumptions and verification are historical and are not additional
open tasks in the overall 007 count. The current UUID-based IN/OUT contract,
retry recovery and subsequent test evidence are tracked in
`specs/007-manage-catalog-inventory/tasks.md`. Earlier independent-verification
limitations remain historical evidence and do not establish later coverage.

## Objective

Implement the planned product-level incoming-stock contract. Each edition is
an independent product; `new_stock` / `newStock` adds non-negative incoming
units to its existing quantity.

## Scope and constraints

- Align Core GraphQL and the BFF endpoint with the approved contracts.
- Protect authorization and validate direct GraphQL and REST requests.
- Use an atomic database update; do not modify the active database or perform
  migrations. Keep public error responses free of upstream details.
- Product editing, stock reductions, reservations, retries and idempotency
  remain separate unresolved decisions.
- Preserve existing local changes. Do not create commits or branches.

## Tasks

- [ ] T001 Implement product-level stock ingress and focused Core/BFF tests.
  Route: delegated writer, because changes span multiple non-trivial files.
  Risk: high; authorization, inventory integrity and public contracts.
- [x] T002 Record observed verification and update related contract evidence.
- [ ] T003 Correct invalid JWT handling and enforce the delegated stock
  operation boundary before GraphQL execution. Route: delegated writer;
  risk: high because shared authorization and mutation execution are affected.
- [ ] T004 Independently verify the fixes and record observed results.

## Acceptance

- The BFF and Core expose the planned product-level operations without requiring
  a variant identifier. An increment of 20 against stock 10 results in 30.
- Invalid inputs, unauthorized requests, missing products and upstream errors
  are covered; concurrent increments do not overwrite each other.
- Local checks are reported with observed results and limitations. Real
  PostgreSQL concurrency is not claimed without a disposable database test.

## Verification

- Core: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m pytest -p no:cacheprovider tests/test_graphql_products.py tests/test_opkeys_internal.py::test_graphql_delegation_requires_trusted_secret_and_allowed_operation -q`: 41 passed, one Django warning. This includes SDL/runtime parity.
- BFF: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. .venv/bin/python -m pytest -p no:cacheprovider tests/test_admin_validation.py -q -k product_stock`: 39 passed, one deselected, 40 deprecation warnings.
- BFF: `PYTHONDONTWRITEBYTECODE=1 python3 -m openapi_spec_validator specs/openapi.yaml`: passed.
- Independent checks of the wider BFF suite found failures in unrelated product-create tests using legacy paths and in cart/coupon mocks. The larger run reported 74 passed and nine failed; no pre-change baseline was recorded for all failures.
- No PostgreSQL concurrency test or active database access was performed. The SQL update adds stock atomically, but the acceptance criterion remains unverified against real PostgreSQL.
- Earlier independent checks found invalid JWTs returning 403 and OpKey delegation allowing a different GraphQL mutation when the internal secret was available. Subsequent code changes revalidate JWT identity and bind delegated routes, operations and identifiers before resolver execution; independent verification of those changes is pending because the verifier tool failed.
- The old variant-based stock route and Core mutation were removed. Existing consumers must migrate to the product-level operations.

## Authorization Follow-up

- Core: `DATABASE_URL=sqlite:///:memory: PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m pytest -p no:cacheprovider tests/test_graphql_products.py tests/test_opkeys_internal.py -q`: 155 passed, one Django warning. The tests cover route/operation binding and rejection before resolver execution.
- BFF: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. .venv/bin/python -m pytest -p no:cacheprovider tests/test_admin_validation.py tests/test_opkey_middleware.py tests/test_opkey_admin.py tests/test_admin_gift_cards.py -q`: 119 passed, one failed, 74 warnings. The failing product-create test calls the legacy `/admin/products` route.
- The independent verifier failed to launch twice due to tool errors. T003 and T004 remain open; the broader authorization change must not be treated as independently approved.
- The BFF attempts some operations absent or incompatible with the current Core schema, including product lookup, coupon preview and the promotions list fields; end-to-end compatibility is not established.