# Unifying feature specification ownership

## Objective

Establish one canonical cross-service feature specification under the
orchestrator's root `specs/` directory, while keeping only service-owned
execution evidence and contracts in Core, BFF, and Frontend repositories.

## Problem and rationale

Features 001–006 currently repeat full `spec.md` definitions across service
repositories alongside canonical root as-built specs. This creates competing
sources of truth. Service `plan.md` and `tasks.md` files contain layer-specific
plans and execution history that should remain local and should not be mistaken
for canonical requirements.

## Scope and constraints

- Replace duplicate service `spec.md` content for features 001–006 with concise
  pointers to the matching root canonical spec.
- Add a root `specs/README.md` describing the ownership and layout convention.
- Preserve service-local `plan.md` and `tasks.md` evidence, canonical contracts,
  service-specific design/implementation notes, backups, and unrelated changes.
- Do not move or delete files in this work unit; preserve paths and references.
- Local-only work; no push or pull request.

## Allowed edit surfaces

- `specs/README.md`
- `bgg-shop-core/specs/001-authentication/spec.md`
- `bgg-shop-core/specs/002-catalog-search-filters/spec.md`
- `bgg-shop-core/specs/003-product-detail-reviews/spec.md`
- `bgg-shop-core/specs/004-shopping-cart/spec.md`
- `bgg-shop-core/specs/005-checkout-orders-invoice/spec.md`
- `bgg-shop-core/specs/006-wishlist/spec.md`
- `bgg-shop-bff/specs/001-authentication/spec.md`
- `bgg-shop-bff/specs/002-catalog-search-filters/spec.md`
- `bgg-shop-bff/specs/003-product-detail-reviews/spec.md`
- `bgg-shop-bff/specs/004-shopping-cart/spec.md`
- `bgg-shop-bff/specs/005-checkout-orders-invoice/spec.md`
- `bgg-shop-bff/specs/006-wishlist/spec.md`
- `bgg-shop-frontend/specs/001-authentication/spec.md`
- `bgg-shop-frontend/specs/002-catalog-search-filters/spec.md`
- `bgg-shop-frontend/specs/003-product-detail-reviews/spec.md`
- `bgg-shop-frontend/specs/004-shopping-cart/spec.md`
- `bgg-shop-frontend/specs/005-checkout-orders-invoice/spec.md`
- `bgg-shop-frontend/specs/006-wishlist/spec.md`
- `odd/tasks/unify-feature-specs.md`

## Acceptance criteria

- [x] Each duplicate service `spec.md` points to the exact canonical root spec.
- [x] None of the duplicate service spec files retain a competing feature definition.
- [x] Service plans/task ledgers and authoritative OpenAPI/GraphQL contracts remain
  unchanged.
- [x] The root layout policy explains canonical feature docs, service-owned
  evidence, contracts, and service-only notes.
- [x] All canonical links resolve locally and each repository's scoped diff passes
  whitespace checks.

## Verification

- [x] Structurally read back all 18 pointer files and root `specs/README.md`.
- [x] Check every pointer target exists.
- [x] Run `git diff --check` in the orchestrator and three service repositories.

## Progress

- Authorized by the user after recommendation of one canonical root feature
  spec and service-local implementation/evidence artifacts.
- Replaced the 18 service feature definitions with pointers and added
  `specs/README.md`. Canonical sources are
  `specs/001-authentication-as-built/spec.md`,
  `specs/002-catalog-search-filters-as-built/spec.md`,
  `specs/003-product-detail-reviews-as-built/spec.md`,
  `specs/004-shopping-cart-as-built/spec.md`,
  `specs/005-checkout-orders-invoice-as-built/spec.md`, and
  `specs/006-wishlist-as-built/spec.md`.
- The service-local `plan.md` and `tasks.md` files and owning service contracts
  remain unchanged. No runtime code changed; no functional tests were run, as
  requested for this documentation-only task.
- Feature branches created locally: `docs/unify-feature-specs` in the root and
  each of Core, BFF, and Frontend. Existing worktree changes are preserved.
- Work-unit commits:
  - Core: `1861fd0` — `docs(core): point feature specs to canonical definitions`
  - BFF: `78542d0` — `docs(bff): point feature specs to canonical definitions`
  - Frontend: `f314eb6` — `docs(frontend): point feature specs to canonical definitions`
- Risk tier: passive documentation; structural verification and link checking
  are proportionate.
- Structural readback confirmed each of the 18 pointers uses its exact
  `../../../specs/<feature>-as-built/spec.md` target and that every target
  exists. Read back the root layout guide at `specs/README.md`.
- `git diff --check` passed in the orchestrator root, `bgg-shop-core`,
  `bgg-shop-bff`, and `bgg-shop-frontend`. No additional project code or test
  paths apply to this documentation-only change.
