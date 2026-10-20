# CU-C04 Shopping Cart

## Objective

Implement CU-C04 across Core, BFF, and Frontend. Buyers can see each game's inventory `quantity`, add or remove items from a persistent cart, and see the correct recalculated total.

## Problem and why

The current services do not expose inventory or cart operations. The Core uses raw SQL against `product_boardgame`; the BFF has no cart persistence; the Frontend has no product/cart flow. This feature adds the minimum required behavior while preserving the existing service boundaries.

## Scope

- Add product inventory column `quantity` to the existing games table and expose it through Core GraphQL, BFF REST, and Frontend.
- Provide server-persisted carts for anonymous and authenticated buyers.
- Support cart read, add, update quantity, and remove; recalculate line subtotals and cart total from current product prices.
- Validate requested quantities against inventory; do not reserve or decrement inventory until checkout.
- On login, merge the anonymous cart into the account cart by summing same-game quantities and capping to current inventory.
- Update focused tests and service documentation/contracts.
- Defer integrated login → cart load → purchase validation until CU-C05 is implemented.

## Constraints and decisions

- Inventory `quantity` and cart-line requested quantity are distinct concepts.
- Anonymous identity must be an opaque server-issued identifier, transported with an HttpOnly cookie. Authenticated identity must come from validated authentication, never a client-provided user ID.
- Core owns cart persistence and business behavior; BFF adapts REST and validates inputs; Frontend consumes only BFF.
- Do not add a migration framework solely for this change. First identify the authoritative schema/bootstrap mechanism and make the smallest compatible update.
- Cart edits do not reserve/decrement stock. Checkout changes are out of scope.
- Use 10 units per game only for development seed data; do not treat this as a production inventory policy.
- Preserve pre-existing untracked files (`CasosDeUso.md`, `README.MD`, and `bgg-shop-frontend/`) and unrelated user changes.

## Checklist

- [x] **inventory-and-core-cart** — Persist and expose inventory `quantity`; implement Core cart read/add/update/remove, stock validation, totals, anonymous/account association, login merge, and focused tests.
- [x] **bff-cart-contract** — Add validated BFF cart REST endpoints, anonymous cookie and account flows, OpenAPI schemas, integration tests, and docs. Depends on Core cart operations.
- [x] **frontend-cart-flow** — Display inventory; add/remove items and show the correct cart total through BFF; cover loading/error/empty/success and stock feedback. Depends on BFF contract.
- [x] **cu-c04-verification-docs** — Verify the requested checks: stock visibility, cart add/remove, and displayed total; finish related documentation. Depends on Frontend flow.
- [ ] **cu-c05-flow-validation (deferred/blocked)** — After CU-C05 purchase is implemented, verify login → account cart load → execute purchase. This does not block CU-C04.

## Acceptance criteria

- Inventory `quantity` is stored and visibly presented in the product UI.
- Development catalog seed data starts each game at `quantity = 10`.
- Anonymous and authenticated buyers can add, inspect, update, and remove cart items end-to-end.
- Cart totals reflect line quantity × current price after add/remove/update.
- Requested cart quantities are stock-validated, with clear feedback when stock limits the request.
- Cart edits do not reserve or decrement stock.
- Login merges guest quantities into the account cart and caps merged lines to current inventory.
- The deferred CU-C05 purchase-flow validation is explicitly pending until that feature exists.

## Verification

- Core: focused product and cart GraphQL tests; then Core suite if practical.
- BFF: focused cart/controller/OpenAPI tests; then BFF suite if practical.
- Frontend: focused cart tests, `npm test -- --run`, `npm run build`, and `npm run lint`.
- CU-C04 functional checks: inventory is visible; cart add/remove works; the correct total is displayed.
- Deferred: login → load cart → purchase after CU-C05 is implemented.
- Risk tier: high, because this includes stock, persistent cart data, identity, and cross-service contracts. Require writer verification and independent verification.

## Implementation routing

- Task 1 Core: delegated direct; preparation spans unfamiliar DB schema/bootstrap and Core GraphQL behavior.
- Task 2 BFF: delegated direct; contract and request identity/persistence integration.
- Task 3 Frontend: delegated direct; product/catalog and cart UI with focused tests.
- Task 4: delegated/direct focused verification after implementation; record all failed, unavailable, skipped, or pending checks.
- Keep one writer at a time. Exact edit surfaces are scoped per task in its delegated prompt. No implementation commit until its applicable checks pass.
- Feature delivery strategy: `ask-on-risk`; forecast is above 400 authored lines across the three services. Ask for the chain strategy before any work-unit commit if the running change count exceeds the threshold.

## Progress and evidence

- Plan approved for implementation on branch `CU-04` in Core, BFF, Frontend, and orchestrator repositories.
- Baseline repository states were clean except pre-existing untracked files listed above.
- Mapping confirmed no Core cart contract, no BFF cart routes/persistence, and no Frontend cart UI. Current catalog has no inventory field.
- User confirmed development seed stock: 10 units per game.
- The root `.atl/skill-registry.md` is unavailable; applicable service instruction files and the React best-practices skill were used.
- Core task 1 now adds `product_boardgame.quantity` with production-safe zero default and sets 10 only for the explicit development catalog seed IDs; cart tables persist opaque UUID guest carts and account carts keyed by authenticated user.
- Core GraphQL now exposes inventory, cart read/add/update/remove, current-price line subtotals/cart subtotal, stock errors, and optional guest-cart merge on authenticated login; merge sums quantities, caps to current inventory, and removes lines for zero stock. No reservation or checkout decrement was added.
- Focused Core verification: `cd bgg-shop-core && python -m pytest -q tests/test_graphql_products.py tests/test_graphql_cart.py` passes (12 passed); generated GraphQL introspection matches the normalized SDL. Full Core suite `cd bgg-shop-core && python -m pytest -q` passes (31 passed). Both report one existing Django `USE_TZ` deprecation warning.
- BFF task 2 adds validated GET/POST/PATCH/DELETE cart REST routes, guest cookie identity and login merge forwarding, Bearer propagation, stock-warning responses, and inventory quantity in product list/detail DTOs. OpenAPI and README document the contracts and cookie settings.
- BFF verification: `cd bgg-shop-bff && python -m pytest -q` passes (35 passed); `git diff --check` is clean; OpenAPI YAML parses and contains cart routes plus inventory fields.
- Initial RED evidence: the first focused run exposed the wrong `GraphQLError` import; after correcting it, the new cart tests exposed required/nullability and in-memory SQL test-double issues. These were fixed before the passing focused and full-suite runs. No dependencies were installed.
- Database DDL/bootstrap was inspected but not executed against PostgreSQL; persistent SQL behavior therefore still needs database-backed verification.


- Frontend task 3 adds inventory and stock-disabled add controls in the catalog, a local cart route with load/error/empty/success states, quantity updates and remove actions; totals use the BFF response and cart stock warnings are shown. Cart and login requests include cookies, and cart calls add the current session Bearer token when present. Spanish cart copy is kept in the existing messages module; MSW cart handlers and focused flow tests were added. No dependencies were added.
- Frontend verification: `npm run generate:types` completed from `../bgg-shop-bff/specs/openapi.yaml` (OpenAPI cart/inventory contract); `npm test -- --run` passes (22 tests), `npm run build` passes TypeScript and Vite, and `npm run lint` completes with the existing single warning in the catalog loading effect (no new warnings).

- Task 4 (live check, rebuilt dev containers, DDL/seed applied to `saleor_db`): BFF `/products` shows `quantity` 10; adding 3×90000 + 2×186000 gave total 642000; quantity 99 was capped to 10 with an `INSUFFICIENT_STOCK` warning; removal recalculated the total; stock stayed 10 (no reservation); the cart persisted via the guest cookie.
- Final suites: Core 31 passed, BFF 36 passed, Frontend 22 passed, build OK, lint 1 pre-existing warning. Independent reviews: Core no findings; BFF one finding (GraphQL Int overflow → 502), fixed.
- Capping fix: Core originally rejected over-stock; changed to cap at available stock with a warning, per CU-C04 exception flow 1a.
- Not live-verified: Frontend UI in a browser (covered by MSW tests) and guest→account merge on login.
- No commits made: the change exceeds the ~400-line forecast, so the delivery strategy is pending the user's decision.

## Next step

Choose a delivery strategy (commit per repo on `CU-04`), then implement CU-C05 and run the deferred login → cart → purchase validation.
