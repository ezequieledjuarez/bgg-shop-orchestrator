# Plan: CU-A01 — Manage Catalog, Inventory & Promotions (Overall)

Feature branch: CU-ADM-01
Feature dir: specs/007-manage-catalog-inventory

## Goal
Deliver a production-ready admin flow to manage products, stock, promotions and coupons with safe business rules (no oversell, atomic coupon counters, controlled stacking of promos).

## Phases & Milestones
1. Design & Contracts (2 days)
   - Complete API contract Core↔BFF (schemas, errors)
   - Approve DB migration plan
2. Core Implementation (6-12 days)
   - Models, migrations, business logic (stock reservations, promotions, coupons)
   - Events and audit
   - Concurrency tests
3. BFF Integration (4-8 days)
   - Admin endpoints, validation, error mapping, cache invalidation
   - Contract tests with Core
4. Frontend Admin (4-8 days)
   - Product list, create/edit forms, stock controls, promotions UI, audit view
   - E2E tests
5. Verification & CI (2-4 days)
   - Add CI jobs for contract tests and E2E
   - Run full verification in staging
6. Rollout & Monitoring (1-2 days)
   - Gradual roll-out, monitor error rates, verify metrics

## Owners
- Core: `bgg-shop-core` team (models, migrations, business rules)
- BFF: `bgg-shop-bff` team (API façade, validation, cache)
- Frontend: `bgg-shop-frontend` team (admin UI, UX)

## Deliverables per Phase
- API contract (OpenAPI or JSON schemas)
- DB migrations + migration runbook
- Unit/integration tests for business rules
- Admin endpoints + contract tests
- Admin UI + E2E tests
- CI pipeline updates

## Risks & Mitigations
- Concurrency (coupon redemptions, stock): mitigate with DB-level atomic counters and integration tests.
- Cache inconsistency: use event-driven invalidation and short TTL.
- Image upload/storage: test with S3 emulator or local storage driver in CI.

## Acceptance Criteria
- All ACs in component specs pass (Core/BFF/Frontend specs).
- Contract tests green and E2E admin flows pass in CI on `CU-ADM-01`.

## Timeline (rough)
Total ~3–5 weeks depending on parallel work and reviews.

## Next Steps
- Finalize API contract (Task X-1)
- Start Core models & migrations (Task C-1)
