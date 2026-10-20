# CU-C05 Process Purchase and View Invoice

Branch: `CU-05` in all repos (created from merged `CU-04`). Plan: session `plan.md`, section "CU-C05".

## Objective

A logged-in buyer with cart items pays through Mercado Pago (test/sandbox only), gets a persisted order, decremented stock and a downloadable PDF invoice, and sees past orders under "Mis Compras".

## Scope

- Persist `purchase_order`, `purchase_order_line` (price/name snapshot) and `invoice`; decrement `product_boardgame.quantity` once on payment approval; clear the cart after payment.
- Core (GraphQL, authenticated only): `checkout`, `confirmPayment`, `myOrders`, `myOrder`; PDF invoice endpoint with ownership check.
- BFF REST: `POST /api/v1/checkout`, `POST /api/v1/checkout/confirm`, `GET /api/v1/orders`, `GET /api/v1/orders/{id}`, `POST /api/v1/orders/{id}/retry-payment`, `GET /api/v1/orders/{id}/invoice`.
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
- [x] **cu-c05-bff-contract** — BFF endpoints, OpenAPI, tests.
- [x] **cu-c05-frontend-flow** — Frontend flow and tests.
- [x] **cu-c05-docs-verification** — READMEs, suites, evidence.
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

Core evidence: idempotent order, line snapshot, and invoice DDL added; GraphQL purchase operations and PDF invoice route implemented; SDL synchronized with Graphene. Verification: `cd bgg-shop-core && PATH=/home/eze/.pyenv/versions/3.12.8/bin:$PATH python -m pytest -q` — 47 passed, 0 failed; generated-schema introspection comparison passed without SDL drift. Added 14 test functions (16 cases), with Mercado Pago calls mocked. Focused auth/product suite also passed: 7 passed. No live database or payment request was used; BFF implementation and tests are complete, with frontend and cross-service verification pending.

BFF evidence: delegated writer; risk tier: high (payment identity and invoice access). Implemented checkout, confirmation, retry, authenticated order list/detail, and protected PDF invoice streaming; added DTO validation, Core user-error mapping, OpenAPI schemas, README guidance, and 18 purchase test functions (30 parameterized test cases). Authored BFF diff: 1,289 changed lines (1,285 additions, including 549 new-file lines, plus 4 deletions). Verification: `cd /home/eze/develop/boardgame-app/bgg-shop-bff && .venv/bin/python -m pytest -q` — 66 passed, 0 failed. Invoice requests validate the UUID before URL construction and verify the bearer with Core before forwarding it to the invoice endpoint; no Mercado Pago access token is used in the BFF. OpenAPI YAML parser validation was unavailable because neither PyYAML nor Ruby is installed; the spec paths and refs were reviewed structurally. No live payment or Core request was made.

Frontend evidence: route: delegated writer (frontend layer); risk tier: high (payment identity, order ownership, and invoice access). Implemented the authenticated checkout form and Mercado Pago redirect, return-state confirmation/retry flows, authenticated order history/detail, and bearer-authenticated invoice download. Added 13 focused CU-C05 test cases (including parameterized error mapping); complete Frontend suite: 35 passed, 0 failed. Authored frontend diff: 711 additions and 6 deletions; generated OpenAPI contract update: 554 lines. `npm run generate:types` succeeded against `../bgg-shop-bff/specs/openapi.yaml`. Verification: `npm test -- --run` — 35 passed; `npm run build` — TypeScript and Vite build passed; `npm run lint` — passed with the single pre-existing `src/App.tsx:355` set-state-in-effect warning and no new warnings. No live payment, order, or invoice request was made.

Independent reviews (high risk): Core found three issues, all fixed with tests: retry could overwrite a concurrently paid order (now a conditional UPDATE refusing non-payable states), live-mode payments were not rejected (confirm now refuses `live_mode: true`), and approval cleared the whole cart (now only purchased quantities are removed). BFF review: no findings. Frontend review: unvalidated `init_point` redirect, fixed with an https Mercado Pago host allowlist plus tests.

Final suites: Core 50 passed; BFF 66 passed; Frontend 43 passed, build OK, lint 1 pre-existing warning. Commits on `CU-05` (not pushed or merged): Core `7fe630f`, BFF `375d5cf`, Frontend `fe4ae1e`, orchestrator `42da91c` and `cc9b36f`.

Not verified: the new DDL on PostgreSQL (not applied to `saleor_db`; `FOR UPDATE OF p`, the invoice sequence and `ON CONFLICT` are untested against a real DB), a real Mercado Pago sandbox payment, the live browser flow, the `live_mode` field behavior with test users, and a second approved payment on an already paid order (the stock is protected, but the money would be taken twice; sandbox only, refunds are out of scope).

## Next step

Run the live sandbox validation (`cu-c05-flow-validation`): apply the DDL, set `MP_SANDBOX=true`, restart containers, and walk login -> guest cart merge -> checkout -> MP test buyer payment -> confirmation, stock and invoice.
