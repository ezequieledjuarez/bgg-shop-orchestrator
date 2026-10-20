# CU-C05: Purchase and invoice

## Implemented flow

```text
Frontend React → BFF Flask REST → Core Django/GraphQL → PostgreSQL
                                        └→ Mercado Pago (sandbox only)
```

1. The logged-in buyer fills the checkout form (shipping mode and address) and
   the Frontend calls `POST /api/v1/checkout`.
2. The Core snapshots the cart into a `pending_payment` order and creates a
   Mercado Pago Checkout Pro preference. The Frontend redirects to the returned
   `init_point`.
3. After paying, Mercado Pago sends the buyer to
   `http://localhost:3000/compra/resultado`. The Frontend calls
   `POST /api/v1/checkout/confirm` with the order and payment ids.
4. The Core fetches the payment from Mercado Pago (it never trusts the browser)
   and, if approved, marks the order `paid`, decrements stock, creates the
   invoice and clears the purchased quantities from the cart.
5. "Mis Compras" lists past orders and downloads the PDF invoice.

Scope: development/sandbox only. No real payments, webhooks, refunds, address
book or shipping costs.

## Persistence

`import_catalog.sql` section 5 (additive, idempotent):

- `purchase_order`: status, total, currency, shipping mode and address, payment
  status and detail, `paid_at`. Status is one of `pending_payment`, `paid`,
  `rejected`, `cancelled`, `paid_stock_conflict`.
- `purchase_order_line`: name and unit price snapshot, quantity, subtotal.
- `invoice` and `purchase_invoice_number_seq`: one invoice per paid order.
- `product_boardgame.quantity` is decremented once, on approval.

The file cannot be re-run whole on a populated database because of its seed
INSERTs. Apply section 5 on its own:

```bash
sed -n '165,$p' import_catalog.sql | podman exec -i saleor_db psql -U saleor -d saleor
```

## Security and consistency rules

- Totals and prices come from the server-side snapshot, never from the client.
- `confirmPayment` verifies with the Mercado Pago API: `external_reference`,
  amount, currency and order owner. Payments with `live_mode: true` are
  rejected (`PAYMENT_NOT_VERIFIED`).
- Confirmation is idempotent. Stock is decremented in a transaction with
  `SELECT … FOR UPDATE OF p`. If stock ran out meanwhile the order becomes
  `paid_stock_conflict`.
- `retryPayment` uses a conditional UPDATE, so a concurrently paid order is
  never overwritten (`ORDER_NOT_PAYABLE`).
- Approval removes only the purchased quantities from the cart.
- Order and invoice access is limited to the owner.
- The Frontend only redirects to `https` Mercado Pago hosts (allowlist in
  `src/checkout/navigation.ts`). The invoice is fetched with the bearer token
  and downloaded as a blob.
- `MP_ACCESS_TOKEN` reaches only the `api` container. The Core refuses to create
  payments unless `MP_SANDBOX=true`.

## Configuration

Set in `.env` (git-ignored; placeholders in `.env.example`):

| Variable | Purpose |
|----------|---------|
| `MP_ACCESS_TOKEN` | Sandbox seller credentials |
| `MP_PUBLIC_KEY` | Sandbox public key |
| `MP_SANDBOX` | Must be `true` to enable payments (default `false`) |
| `COUNTRY_MONEY_CODE` | Country (`AR`) or currency (`ARS`) code |
| `MP_CURRENCY_ID` | Optional explicit currency override |
| `FRONTEND_URL` | Base for return URLs (default `http://localhost:3000`) |

`podman-compose.yaml` passes them to the `api` service only. The Core also needs
`mercadopago` and `reportlab` (`requirements.txt`); inside an existing
container run `pip install -r requirements.txt` or rebuild the image.

## Core GraphQL

Mutations: `checkout`, `retryPayment`, `confirmPayment`. Queries: `myOrders`,
`myOrder`. The PDF invoice is served at `GET /invoices/<uuid>/` with an
ownership check.

## BFF REST

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/checkout` | Create the order and the payment preference |
| POST | `/api/v1/checkout/confirm` | Verify and confirm a payment |
| POST | `/api/v1/orders/{id}/retry-payment` | New preference for a rejected order |
| GET | `/api/v1/orders` | Order history |
| GET | `/api/v1/orders/{id}` | Order detail |
| GET | `/api/v1/orders/{id}/invoice` | PDF invoice (bearer required) |

All require authentication. Contract: `bgg-shop-bff/specs/openapi.yaml`.

## Frontend behavior

- Checkout form with shipping mode (`standard` / `pickup`) and address.
- `/compra/resultado` confirms the payment and offers retry on rejection.
- `/mis-compras` lists orders and downloads invoices.

## Validation performed

Automated: Core 51 passed, BFF 66 passed, Frontend 43 passed, build OK, lint
with the single pre-existing warning (`App.tsx:355`). Mercado Pago is mocked in
the tests.

Independent reviews (high risk: payments, stock, identity):

- Core, three findings, fixed with tests: `retryPayment` race, live-mode payments
  not rejected, approval clearing the whole cart.
- BFF: no findings.
- Frontend: unvalidated `init_point` redirect, fixed with the host allowlist.

Live, sandbox:

- Order DDL applied to `saleor_db`; re-running it is a no-op.
- A registered, logged-in user added 2 units to the cart and called
  `POST /api/v1/checkout` (pickup): a `pending_payment` order of 180000.00 ARS
  was stored, a Mercado Pago sandbox `init_point` came back, and stock stayed
  at 10.
- The live test exposed a bug: `COUNTRY_MONEY_CODE=ARS` was rejected with
  `PAYMENTS_DISABLED`. The Core now accepts a country or a currency code.

## Pending verification

To finish `cu-c05-flow-validation`:

1. Log in at `http://localhost:3000`, load the cart, press checkout, pay on
   Mercado Pago with the sandbox test buyer and land on `/compra/resultado`.
2. Confirm the order is `paid`, stock decreased, the invoice row exists, the PDF
   downloads from "Mis Compras" and the purchased lines left the cart.
3. Guest cart merge on login against the live stack (login → guest cart →
   account cart → checkout).

Also unverified: `live_mode` behavior for sandbox test-user payments, the full
`import_catalog.sql` on a clean PostgreSQL, the `Secure` cookie flag under
HTTPS.

## Known limitations

- Without webhooks, a buyer who pays and never returns stays `pending_payment`.
- A second approved payment on an already paid order does not touch stock, but
  the money would be taken twice (sandbox only; refunds out of scope).

## Related commits (branch `CU-05`, not pushed or merged)

- Core `7fe630f` — checkout, orders, invoice PDF; `1a1d66a` — currency code fix.
- BFF `375d5cf` — purchase endpoints.
- Frontend `fe4ae1e` — checkout, payment result and purchase history views.
- Orchestrator `42da91c`, `cc9b36f`, `8c83a33` — DDL, compose, `.env.example`,
  feature document and docs.
