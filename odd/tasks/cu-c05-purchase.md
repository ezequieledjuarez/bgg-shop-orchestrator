# CU-C05 Process Purchase and View Invoice

Branch: `CU-05` in all repos (created from merged `CU-04`). Plan: session `plan.md`, section "CU-C05".

## Objective

A logged-in buyer with cart items pays through Mercado Pago (test/sandbox only), gets a persisted order, decremented stock and a downloadable PDF invoice, and sees past orders under "Mis Compras".

## Scope

- Persist `purchase_order`, `purchase_order_line` (price/name snapshot) and `invoice`; decrement `product_boardgame.quantity` once on payment approval; clear the cart after payment.
- Core (GraphQL, authenticated only): `checkout`, `confirmPayment`, `myOrders`, `myOrder`; PDF invoice endpoint with ownership check.
- BFF REST: `POST /api/v1/checkout`, `POST /api/v1/checkout/confirm`, `GET /api/v1/orders`, `GET /api/v1/orders/{id}`, `GET /api/v1/orders/{id}/invoice`.
- Frontend: "Proceder al Pago", address and shipping mode form, MP redirect, return route `/compra/resultado`, retry on rejection, "Mis Compras", invoice download.
- Out of scope: real payments, webhooks, refunds, address book, shipping costs.

## Constraints and decisions

- Mercado Pago Python SDK, Checkout Pro, test credentials only. Token `MP_ACCESS_TOKEN` (prefix `APP_USR-`) from env, never committed; Core requires `MP_SANDBOX=true` to create payments. Token only reaches the `api` container.
- Currency: `COUNTRY_MONEY_CODE=AR` maps to `ARS` (or `MP_CURRENCY_ID`).
- Return URLs: `http://localhost:3000/compra/resultado` (success, failure, pending); no `auto_return`.
- `confirmPayment` verifies the payment with the MP API (never trusts the browser), checks `external_reference`, owner and amount; idempotent; DB transaction with row locks; stock decremented exactly once.
- Totals and prices come from the server snapshot, never from the client.
- Shipping: address stored in the order, modes `standard` / `pickup`, no cost.
- Additive idempotent DDL in `import_catalog.sql`; no migration framework.
- Preserve untracked `CasosDeUso.md`, `README.MD`, `bgg-shop-frontend/` (own repo) and unrelated changes.
- Delivery: commits only on `CU-05`; no push, no merge.

## Checklist

- [x] **cu-c05-order-schema** — DDL in `import_catalog.sql`.
- [x] **cu-c05-core-checkout** — Core checkout/confirm/orders/invoice, SDL, tests with MP mocked, compose and `.env.example`.
- [ ] **cu-c05-bff-contract** — BFF endpoints, OpenAPI, tests.
- [ ] **cu-c05-frontend-flow** — Frontend flow and tests.
- [ ] **cu-c05-docs-verification** — READMEs, suites, evidence.
- [ ] **cu-c05-flow-validation** — Live sandbox: login -> guest cart merge -> checkout -> MP payment -> order, stock, invoice.

## Acceptance criteria

- Order, lines and invoice persisted; stock decremented once even if confirm runs twice.
- Only the owner reads an order or invoice; anonymous checkout rejected.
- Rejected payment shows the reason and allows retry; cart and stock untouched until approval.
- Core, BFF and Frontend suites, build and lint pass; contracts and docs updated.

## Verification

- Core tests with MP mocked (approved, rejected, pending, double confirm, stock conflict, ownership); BFF and Frontend suites; frontend build and lint.
- Live sandbox run with the MP test buyer.

## Implementation routing

Per task: one delegated writer per layer, spot checks by the parent, independent review (high risk: payments, stock, identity).

## Progress and evidence

Route: delegated writer (Core layer); risk tier: high.

Core evidence: idempotent order, line snapshot, and invoice DDL added; GraphQL purchase operations and PDF invoice route implemented; SDL synchronized with Graphene. Verification: `cd bgg-shop-core && PATH=/home/eze/.pyenv/versions/3.12.8/bin:$PATH python -m pytest -q` — 47 passed, 0 failed; generated-schema introspection comparison passed without SDL drift. Added 14 test functions (16 cases), with Mercado Pago calls mocked. Focused auth/product suite also passed: 7 passed. No live database or payment request was used; BFF and frontend checks remain pending.

## Next step

Implement the BFF contract, then complete cross-service verification.
