# Feature Specification: Wishlist (As-Built)

**Status**: Closed for the local scope with limitations on 2026-10-30.
**Input**: CU-C06, authenticated Wishlist behavior across Frontend, BFF, and Core.

## Scope and Closure

Authenticated buyers can save, list, remove, and add saved games to their cart.
Adding to the cart does not remove a saved game. On successful payment
confirmation, Core removes the purchased owner's matching entries; unpaid and
stock-conflict outcomes do not remove them.

The authenticated save and purchase cleanup passed in an isolated browser,
BFF, Core, and disposable PostgreSQL flow with a simulated payment provider.
The database check confirmed purchased entries were removed and an unpurchased
entry was retained. The [integration record](../../odd/tasks/cart-checkout-wishlist-validation.md)
contains commands, observed results, and setup limitations.

Wishlist DDL was tested in disposable PostgreSQL but was not applied or checked
against the active database. Applying it there requires separate authorization;
`IF NOT EXISTS` does not repair an existing incompatible table. Full database
bootstrap and a real payment-provider round trip were not verified.

## Traceability

- Service specs: [Core](../../bgg-shop-core/specs/006-wishlist/spec.md), [BFF](../../bgg-shop-bff/specs/006-wishlist/spec.md), [Frontend](../../bgg-shop-frontend/specs/006-wishlist/spec.md).
- Contracts: [Core GraphQL SDL](../../bgg-shop-core/specs/schema.graphql), [BFF OpenAPI](../../bgg-shop-bff/specs/openapi.yaml).
- Implementation: [Core Wishlist](../../bgg-shop-core/saleor/graphql/wishlist.py), [order confirmation](../../bgg-shop-core/saleor/graphql/orders.py), [BFF controller](../../bgg-shop-bff/src/controllers/wishlist_controller.py), [Frontend view](../../bgg-shop-frontend/src/wishlist/WishlistScreen.tsx), [DDL](../../import_catalog.sql).
- Tests: [Core Wishlist](../../bgg-shop-core/tests/test_graphql_wishlist.py), [Core PostgreSQL](../../bgg-shop-core/tests/test_graphql_credit_postgres.py), [BFF Wishlist](../../bgg-shop-bff/tests/test_wishlist.py), [Frontend Wishlist](../../bgg-shop-frontend/src/App.wishlist.test.tsx), [browser E2E](../../bgg-shop-frontend/tests/e2e/cart-wishlist-purchase.spec.ts).