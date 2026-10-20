# CU-C03 Product Reviews

## Objective

Expose product details by public slug and allow authenticated users to submit
one pending review per game through the Core GraphQL API and BFF REST API.

## Scope

- Core GraphQL detail and review mutation.
- BFF slug-based detail/review DTOs, controllers, and services.
- Frontend detail route, review form, filter ordering, and Spanish copy.
- Focused tests and contract documentation.

## Checklist

- [x] Define and implement the Core GraphQL contract and behavior.
- [x] Implement the BFF REST contract and layered integration.
- [x] Implement the Frontend detail and review flow.
- [x] Add focused integration tests and update documentation.

## Persistence

`import_catalog.sql` was updated and committed in `ece3221`. PostgreSQL parser
validation remains pending because `psql` is unavailable in the environment.

## Current progress

The GraphQL contract is defined for slug-based product detail, approved review
aggregation, and authenticated pending review creation. Implementation starts
with the Core.

## Verification evidence

- Core existing GraphQL suite passed with 6 tests.
- BFF existing suite passed with 19 tests.
- Frontend Vitest suite passed with 15 tests; OpenAPI types regenerated.
- Frontend lint completed with one warning in the catalog loading effect;
  production build passed.
- Documentation added at `docs/CU-C03-REVIEWS.md`.

## Commits

- `ece3221` — review persistence schema.
- `38aae5c` — Core GraphQL contract and behavior.
- `a6e3f9b` — BFF review endpoints.
- Pending — Frontend detail/review flow and CU-C03 documentation.
