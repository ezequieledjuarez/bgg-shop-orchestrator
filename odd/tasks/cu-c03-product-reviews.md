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

- [ ] Define and implement the Core GraphQL contract and behavior.
- [ ] Implement the BFF REST contract and layered integration.
- [ ] Implement the Frontend detail and review flow.
- [ ] Add focused integration tests and update documentation.

## Persistence

`import_catalog.sql` was updated and committed in `ece3221`. PostgreSQL parser
validation remains pending because `psql` is unavailable in the environment.

## Current progress

The GraphQL contract is defined for slug-based product detail, approved review
aggregation, and authenticated pending review creation. Implementation starts
with the Core.
