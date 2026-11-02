# Checkout Local Remediation

## Objective

Advance CU-C05 locally: distinguish cancelled results, verify rejection, stock
conflict and repeated confirmations with simulated payments, and review the
documented duplicate/late-payment risks. Do not contact payment providers,
change the active database, or claim provider-backed verification.

## Tasks

- [x] T001 Add a failing cancelled-result test, correct the UI, and rerun it.
- [x] T002 Check existing local coverage and add focused tests where it does not
  prove rejection, stock-conflict, and repeated-confirmation behavior.
- [x] T003 Review current handling of duplicate and late payments against the
  existing credit follow-up, recording evidence and remaining limitations.
- [x] T004 Update CU-C05 specifications and tasks with observed results and
  leave closure subject to the remaining documented scope limitations.

## Constraints

Use simulated payment responses and disposable PostgreSQL when needed. Preserve
existing changes. Engram mirror pending: memory tools are unavailable.

## Evidence (2026-10-30)

- Frontend cancelled-result regression failed before implementation and passed
  afterward. `npm run test -- --run --reporter=dot src/App.checkout.test.tsx src/checkout/navigation.test.ts` passed 82 tests; focused lint and `npm run build` passed.
- Core `/home/eze/.pyenv/versions/3.12.8/bin/python -m pytest -q tests/test_graphql_orders.py tests/test_graphql_credit_postgres.py` with the exclusive disposable DSN: 182 passed, one strict expected failure, one warning. Four new PostgreSQL cases cover repeated rejected, pending, stock-conflict, and paid confirmations and their stock, invoice, cart, and Wishlist effects.
- BFF `.venv/bin/python -m pytest -q tests/test_orders.py`: 48 passed, 57 warnings.
- The strict expected failure exposes an approved second payment with a different
  ID but the same preference returning no `PAYMENT_REQUIRES_REVIEW` error after
  the first payment. Running the same test with `--runxfail` failed at that
  assertion; no real provider payment was made. Existing Core tests cover review
  for older preferences and credit-guarded late payments; [the 009 follow-up](../../specs/009-gift-card-credit/follow-up.md) retains reconciliation as deferred.
- No active database or payment provider was touched. The user accepted the
  second-payment risk as an explicit exception for local, non-production
  closure; the corrective Core task T010 remains open.

## Browser Reproduction (2026-10-30)

- `E2E_OPKEY_ISOLATED=true C04_C06_DISPOSABLE_E2E=true C05_DUPLICATE_PAYMENT_E2E=true npx playwright test tests/e2e/cart-wishlist-purchase.spec.ts --project=chromium --reporter=line --output=/tmp/bgg-double-payment-e2e` from `bgg-shop-frontend` failed as intended: the second distinct simulated approved payment for the same preference returned HTTP 200, not the expected 409. The UI showed a successful paid result rather than a review alert.
- The isolated database retained the first payment ID and had no review record.
  Across three reproduction runs and one normal baseline run, four orders had
  four invoices, stock decreased from five to one, and none had a review record.
- The normal E2E without `C05_DUPLICATE_PAYMENT_E2E` passed; focused lint and
  TypeScript checks passed. The test needs a temporary BFF marker, Core payment
  stubs, and a synthetic database; the command alone does not set them up.
- The provider was simulated. The E2E establishes application behavior for the
  injected responses, not that an external provider would issue two charges.