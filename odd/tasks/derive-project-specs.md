# Deriving project specifications from canonical use cases

## Objective

Add 15 functional project specifications, one for each canonical CU-C01–CU-C05 in Core, BFF, and Frontend, while preserving the existing technical contracts and application behavior.

## Problem and rationale

The root specifications document end-to-end buyer behavior. Core GraphQL SDL and BFF OpenAPI define technical contracts, but do not provide functional project-scoped specifications; Frontend has no standalone specs. Each new document must describe only the responsibilities evidenced in its project's code, contract, and tests, with explicit traceability to its canonical source.

## Scope and constraints

- In scope: five project specs in each of `bgg-shop-core/specs/`, `bgg-shop-bff/specs/`, and `bgg-shop-frontend/specs/`.
- Preserve root canonical specs, Core GraphQL SDL, and BFF OpenAPI unchanged.
- Do not change application code, tests, or technical contracts.
- Describe gaps and out-of-scope behavior instead of inventing behavior or silently resolving mismatches.
- Keep unrelated dirty/untracked worktree content unchanged.
- No push or pull request is authorized; local work-unit commits are on the existing `CU-05` feature branch.

## Authorized edit scope

- `odd/tasks/derive-project-specs.md`
- `bgg-shop-core/specs/001-authentication/spec.md`
- `bgg-shop-core/specs/002-catalog-search-filters/spec.md`
- `bgg-shop-core/specs/003-product-detail-reviews/spec.md`
- `bgg-shop-core/specs/004-shopping-cart/spec.md`
- `bgg-shop-core/specs/005-checkout-orders-invoice/spec.md`
- `bgg-shop-bff/specs/001-authentication/spec.md`
- `bgg-shop-bff/specs/002-catalog-search-filters/spec.md`
- `bgg-shop-bff/specs/003-product-detail-reviews/spec.md`
- `bgg-shop-bff/specs/004-shopping-cart/spec.md`
- `bgg-shop-bff/specs/005-checkout-orders-invoice/spec.md`
- `bgg-shop-frontend/specs/001-authentication/spec.md`
- `bgg-shop-frontend/specs/002-catalog-search-filters/spec.md`
- `bgg-shop-frontend/specs/003-product-detail-reviews/spec.md`
- `bgg-shop-frontend/specs/004-shopping-cart/spec.md`
- `bgg-shop-frontend/specs/005-checkout-orders-invoice/spec.md`

## Acceptance criteria

- Each project/CU pair has exactly one project spec (15 total).
- Each spec links to its root canonical spec and maps relevant behavior to project responsibilities, technical boundaries, and source/test evidence.
- Requirements stay specific to that project's layer; exclusions, limitations, and gaps are explicit.
- Existing contracts and implementation are unchanged.
- Relative references and named GraphQL/OpenAPI operations are checked against repository contents.

## Tasks and progress

### CORE — Derive Core specs

- [x] `core-specs`: Create five Core specs from the canonical specs, GraphQL SDL, resolvers, and Core tests.
- Route: completed directly by the Documentation Agent after reading the canonical specs, Core SDL, resolvers, payment adapter, and Core tests.
- Risk: passive documentation; inaccurate layer attribution is the main risk. Requirements are limited to observed Core contracts/implementation, with exclusions and test-coverage limits called out.
- Verification: PASS — structural readback confirmed all five specs, their required sections, canonical references, repository-relative evidence links, and named SDL operations. PASS — `git -C bgg-shop-core diff --cached --check` completed before commit. PASS — commit `88300a398a58db71c67615b4b78a9043a4534c54` lists only the five spec paths (`git -C bgg-shop-core show --format= --name-only 88300a398a58db71c67615b4b78a9043a4534c54`); the tracked Core worktree and index are clean (`git -C bgg-shop-core diff --exit-code` and `git -C bgg-shop-core diff --cached --exit-code`). No application tests were run because this was documentation-only work.
- Commit: `88300a398a58db71c67615b4b78a9043a4534c54` — `docs(core): derive five as-built functional specs` (nested `bgg-shop-core` repository, branch `CU-05`).

### BFF — Derive BFF specs

- [ ] `bff-specs`: Create five BFF specs mapping canonical behavior to REST/OpenAPI, Core operations, controllers/services, and BFF tests.
- Depends on: `core-specs`.
- Route: delegated direct to the Documentation Agent; five non-trivial documents require contract-to-implementation mapping.
- Risk: passive documentation; verification is structural readback and parent spot-check.
- Verification: confirm all five files exist; check canonical/evidence links and referenced REST/Core operations; confirm OpenAPI/code are unchanged.
- Commit: pending.

### FRONTEND — Derive Frontend specs

- [ ] `frontend-specs`: Create five Frontend specs mapping canonical behavior to UI states, BFF requests/types, and Frontend tests.
- Depends on: `bff-specs`.
- Route: delegated direct to the Documentation Agent; five non-trivial documents require UI/API/test evidence mapping.
- Risk: passive documentation; verification is structural readback and parent spot-check.
- Verification: confirm all five files exist; check canonical/evidence links and BFF references; confirm app code and generated types are unchanged.
- Commit: pending.

## Delivery and verification

- Estimated authored size: approximately 750 lines across 15 specs; generated files are not in scope.
- Delivery strategy: `single-pr` to keep the related documentation slice coherent if a PR is later requested. This task does not create or publish a PR.
- Applicable checks are documentation structural checks, not application test suites, because no executable behavior changes.

## Current state

- Feature branch: `CU-05` (not the local `main` branch).
- Existing worktree has unrelated untracked files, including the Frontend project; do not stage or alter them outside the explicit authorized edit scope.
- Progress: Core derivation is complete; BFF and Frontend remain pending.
- Verification evidence: five Core specs were committed on `CU-05`; structural validation resolved all relative references and confirmed every named GraphQL operation against `bgg-shop-core/specs/schema.graphql`. The contract, implementation, and Core tests remain unchanged. No application test suite or live-stack check was run for this passive documentation change.
- Next step: derive and structurally verify the five BFF project specs.
