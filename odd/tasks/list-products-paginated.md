# List Products Paginated

## Objective
Expose the board-game catalog through `GET /api/v1/products` in the BFF, backed by a paginated GraphQL query in Core.

## Problem and rationale
The current Core only exposes a health-style GraphQL field and the BFF only exposes health. The storefront needs a stable REST product contract while Saleor/Core remains the GraphQL boundary.

## Scope
- Add the Core GraphQL product type and paginated `products` query backed by `product_boardgame`.
- Add the BFF REST endpoint and GraphQL adapter.
- Validate pagination inputs and propagate upstream failures as explicit HTTP errors.
- Add focused tests for GraphQL mapping and REST pagination/error behavior.

## Constraints
- Preserve the existing Flask/Django stack and minimal Ponytail design.
- Keep `min_age` as the API field name because it is the persisted SQL column.
- Split the persisted comma-separated category into `category: [String!]!`.
- Do not expose Core's GraphQL endpoint to the frontend.

## Tasks
- [x] core-products-graphql: implement product fields, pagination, and SQL-backed resolver.
- [x] bff-products-rest: implement REST adapter, validation, mapping, and errors.
- [x] endpoint-tests: cover contract mapping, pagination, and upstream failures.

## Acceptance criteria
- `GET /api/v1/products?page=1&page_size=20` returns `{items, page, page_size, total, total_pages}`.
- Product items expose the requested fields with `category` as a list.
- Invalid pagination returns HTTP 400.
- GraphQL or transport failures return an explicit HTTP 502.
- Existing `/health` behavior remains unchanged.

## Verification
- `python -m pytest` from each Python service.
- `python -m compileall` for changed Python files.

## Progress
- Status: implemented; functional test runner unavailable in the environment
- Route: delegated direct writer; two non-trivial service surfaces require coordinated changes.
- Verification evidence: `python3 -m compileall -q` passed; `python3 -m pytest` unavailable because pytest is not installed; Django/Graphene/Flask are also unavailable in the system interpreter.
- Next step: install service requirements and run both pytest suites.
