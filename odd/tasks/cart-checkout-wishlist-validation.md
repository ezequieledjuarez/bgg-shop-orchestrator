# Cart, Checkout, and Wishlist Integration Validation

## Objective and scope

Validate the combined 004, 005, and 006 buyer flow locally: guest cart merge,
authenticated Wishlist, simulated payment, order, stock, invoice, cart cleanup,
and purchased Wishlist cleanup. Use synthetic data and disposable PostgreSQL;
do not mutate the active database or contact a payment provider. Keep each
spec's separate limitations and record only observed evidence.

## Tasks

- [x] T001 Run existing focused Core, BFF, and Frontend tests and record results.
- [x] T002 Restore and verify the missing Wishlist schema and correct the
  overly broad Core schema test before relying on clean-database validation.
- [x] T003 Run the integrated browser and service flow with a locally simulated
  provider and verify database effects in disposable PostgreSQL.
- [x] T004 Record results and remaining limitations in the affected specs and
  tasks; do not close a feature based solely on mocked tests.

## Evidence (2026-10-30)

- Core: `/home/eze/.pyenv/versions/3.12.8/bin/python -m pytest -q tests/test_graphql_cart.py tests/test_graphql_orders.py tests/test_graphql_wishlist.py` from `bgg-shop-core`: 94 passed, 1 failed, 1 warning. The failure is `test_wishlist_operations_are_exposed_without_client_user_id`: it checks the whole schema, which now includes unrelated administrative `userId` arguments. Core's `.venv` has no pytest.
- BFF: `.venv/bin/python -m pytest -q tests/test_cart.py tests/test_orders.py tests/test_wishlist.py` from `bgg-shop-bff`: 76 passed, 101 warnings.
- Frontend: `npm run test -- --run --reporter=dot src/App.cart.test.tsx src/App.checkout.test.tsx src/App.wishlist.test.tsx` from `bgg-shop-frontend`: 89 passed. MSW reported unhandled product-category requests.
- Disposable PostgreSQL: `/home/eze/.pyenv/versions/3.12.8/bin/python -m pytest -q tests/test_graphql_credit_postgres.py -k test_confirmation_uses_verified_merchant_order` from `bgg-shop-core`: 3 passed, 95 deselected, 1 warning. The test uses a simplified test schema, simulated provider responses, and checks invoice and stock for verified and unverified preferences. It does not validate the application Wishlist DDL or the browser flow.
- The focused unit tests listed above use mocks or fakes and do not independently
  establish cross-service browser behavior. No real payment request or
  active-database mutation was made.
- The previously missing `wishlist_entry` DDL was added to `import_catalog.sql`.
  A disposable, network-isolated PostgreSQL verified repeated creation, duplicate
  handling, foreign keys, and cascades. The active database was not changed;
  `IF NOT EXISTS` does not repair an existing incompatible table.
- After the Wishlist schema-test correction, the same focused Core command
  passed 95 tests with one warning. See
  `bgg-shop-core/specs/006-wishlist/spec.md` and its T010/T011 tasks.
- On 2026-10-30, `E2E_OPKEY_ISOLATED=true C04_C06_DISPOSABLE_E2E=true npx playwright test tests/e2e/cart-wishlist-purchase.spec.ts --project=chromium --reporter=line --output=/tmp/bgg-cart-wishlist-purchase-e2e` passed twice from `bgg-shop-frontend`. It used locally isolated BFF/Core and disposable PostgreSQL with selected real commercial DDL, all GraphQL migrations, synthetic data, and a simulated payment provider. It verified guest persistence and login merge, authenticated Wishlist save, payment confirmation, PDF download, cart cleanup, and purchased-item removal while preserving an unpurchased Wishlist item.
- The browser command requires the temporary BFF marker endpoint, Core payment
  stubs, and synthetic database prepared for this run; the command alone does
  not recreate that environment. The temporary services were not permanent
  application configuration.
- The final database check showed two paid orders, two invoices, stock 5 to 3, no purchased items in either cart or Wishlist, and both unpurchased entries retained. The first two E2E attempts failed due to test-selector and response-capture issues; both were corrected before the successful runs.
- Core: `python -m pytest -q tests/test_graphql_credit_postgres.py` with the isolated DSN: 99 passed, one warning; the focused cart/order/Wishlist suite: 95 passed, one warning. Frontend: the three focused Vitest files passed 89 tests; `npm run lint -- tests/e2e/cart-wishlist-purchase.spec.ts` passed without warnings.
- This is not a real provider round trip, a complete `import_catalog.sql` bootstrap, or active-database verification. The browser case merges into a new account cart; merging into an existing account cart is separately covered by the PostgreSQL test.
- Engram mirror pending: memory tools are unavailable in this session.

## Next step

The 004 and 006 specs are closed for the local scope with the limitations in
their canonical specs. Applying the Wishlist DDL to the active database requires
separate authorization. The 005 checkout spec is also closed for local,
non-production scope with the accepted second-payment exception; its corrective
Core task remains open.