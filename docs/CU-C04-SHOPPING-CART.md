# CU-C04: Shopping cart

## Implemented flow

```text
Frontend React → BFF Flask REST → Core Django/GraphQL → PostgreSQL
```

Buyers see each game's stock (`quantity`), add, update and remove items, and
see the recalculated total. Guests and logged-in users both have a persistent,
server-side cart. Editing the cart never reserves or decrements stock; stock is
only decremented when a purchase is paid (see CU-C05).

## Persistence

`import_catalog.sql` (idempotent DDL):

- `product_boardgame.quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0)`.
  The development seed sets 10 units per game; this is not a production
  inventory policy.
- `shopping_cart`: one cart per authenticated user or per opaque guest UUID.
- `shopping_cart_line`: one line per game, `quantity > 0`.

Prices and subtotals are not stored in the cart. They are recalculated from the
current product price on every read.

## Cart identity

- Guests: the BFF issues an opaque UUID in an HttpOnly cookie. The Frontend
  never sees or sends it.
- Authenticated users: identity comes from the validated bearer token, never
  from a client-provided user id.
- On login the BFF forwards the guest cart id and the Core merges it into the
  account cart: same-game quantities are summed and capped to current stock;
  lines with zero stock are removed.

## Core GraphQL

- Query: `cart(cartId)`.
- Mutations: `addToCart`, `updateCartQuantity`, `removeFromCart`.
- Products expose `quantity`.
- Requests above stock are capped to the available stock and answered with an
  `INSUFFICIENT_STOCK` warning (exception flow 1a of the use case), not rejected.

## BFF REST

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/cart` | Read the cart |
| POST | `/api/v1/cart/items` | Add a game (`bgg_id`, `quantity`) |
| PATCH | `/api/v1/cart/items/{bgg_id}` | Change the quantity |
| DELETE | `/api/v1/cart/items/{bgg_id}` | Remove the game |

Each response carries `lines` (`bgg_id`, `name`, `unit_price`, `quantity`,
`subtotal`, `available_stock`), `total` and `warnings`. Inputs are validated in
the BFF, including integer bounds (a GraphQL `Int` overflow used to surface as
a 502 and is now a validation error). Product list and detail DTOs include
`quantity`. The contract is in `bgg-shop-bff/specs/openapi.yaml`.

## Frontend behavior

- The catalog shows stock and disables "add" when stock is 0.
- The cart view handles loading, error, empty and success states, quantity
  changes, removal and stock warnings. The total comes from the BFF response.
- Cart and login requests send cookies; cart calls add the bearer token when a
  session exists. Copy is Spanish, in the existing messages module.

## Validation performed

Automated (final suites for this use case):

- Core: 31 passed.
- BFF: 36 passed.
- Frontend: 22 passed, `npm run build` OK, `npm run lint` with one
  pre-existing `set-state-in-effect` warning in the catalog loading effect.
- Independent reviews (high risk: stock, identity, persistent data): Core no
  findings; BFF one finding (Int overflow), fixed.

Live, against the rebuilt dev containers with DDL and seed applied to
`saleor_db`:

- `/products` returns `quantity` 10.
- Adding 3 × 90000 and 2 × 186000 gives total 642000.
- Requesting 99 units caps to 10 with an `INSUFFICIENT_STOCK` warning.
- Removing a line recalculates the total.
- Stock stays 10 after cart edits (no reservation).
- The cart persists through the guest cookie.

## Pending verification

- Frontend in a real browser (covered only by MSW tests).
- Guest → account cart merge on login against the live stack.
- Login → load cart → purchase: depends on CU-C05 and is tracked in
  [CU-C05-PURCHASE.md](./CU-C05-PURCHASE.md).
- `import_catalog.sql` on a clean PostgreSQL from scratch.

## Related commits (branch `CU-04`, merged)

- Core `e453f2d` — inventory and persistent cart.
- BFF `5185928` — cart endpoints and stock in products.
- Frontend `3fbc776` — stock display and cart view.
- Orchestrator `fa68fe0` — feature document and docs.
