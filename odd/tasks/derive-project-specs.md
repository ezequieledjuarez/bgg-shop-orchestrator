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

- [x] `bff-specs`: Create five BFF specs mapping canonical behavior to REST/OpenAPI, Core operations, controllers/services, and BFF tests.
- Depends on: `core-specs`.
- Route: completed directly by the Documentation Agent after reading all five canonical specs, the BFF OpenAPI contract, Core SDL, BFF controllers/services/DTOs, and BFF tests.
- Risk: passive documentation; verification is structural readback and parent spot-check.
- Verification: PASS — structural readback confirmed all five BFF specs, canonical and test evidence links, all local Markdown links, named REST operation IDs against `bgg-shop-bff/specs/openapi.yaml`, Core operations against `bgg-shop-core/specs/schema.graphql`, and required document sections. PASS — `git -C bgg-shop-bff diff --cached --check` completed before commit. PASS — commit `666888907d474390c084850a57d821a30b13810e` contains only the five BFF spec paths (`git -C bgg-shop-bff show --format= --name-only 666888907d474390c084850a57d821a30b13810e`). PASS — BFF OpenAPI/source/tests and Core SDL/source/tests have no changes from this work (`git -C bgg-shop-bff diff HEAD^ HEAD --exit-code -- specs/openapi.yaml src tests`; `git -C bgg-shop-core diff --exit-code -- specs/schema.graphql saleor tests`). No application tests were run because this was documentation-only work.
- Commit: `666888907d474390c084850a57d821a30b13810e` — `docs(bff): derive five as-built functional specs` (nested `bgg-shop-bff` repository, branch `CU-05`).

### FRONTEND — Derive Frontend specs

- [x] `frontend-specs`: Create five Frontend specs mapping canonical behavior to UI states, BFF requests/types, and Frontend tests.
- Depends on: `bff-specs`.
- Route: completed directly by the Documentation Agent after reading all five canonical specs, BFF OpenAPI, generated Frontend API types, relevant React screens/API helpers, and Frontend tests.
- Risk: passive documentation; verification is structural readback and parent spot-check.
- Verification: PASS — structural readback confirmed all five Frontend specs, required sections, canonical/evidence links, generated BFF schema types, OpenAPI paths, and operation IDs. PASS — `git -C /home/eze/develop/boardgame-app/bgg-shop-frontend diff --cached --check` completed before commit. PASS — commit `6a615fdd8e72af7b3c838daca8b83b4d76d844a4` contains only the five Frontend spec paths (`git -C bgg-shop-frontend show --format= --name-only 6a615fdd8e72af7b3c838daca8b83b4d76d844a4`). PASS — tracked Frontend source and package configuration were unchanged (`git -C bgg-shop-frontend diff --exit-code HEAD -- src package.json` before commit); generated API types, OpenAPI, tests, and Core SDL were not edited. No Frontend application tests were run because this was passive documentation work.
- Commit: `6a615fdd8e72af7b3c838daca8b83b4d76d844a4` — `docs(frontend): derive five as-built functional specs` (nested `bgg-shop-frontend` repository, branch `CU-05`).

## Delivery and verification

- Estimated authored size: approximately 750 lines across 15 specs; generated files are not in scope.
- Delivery strategy: `single-pr` to keep the related documentation slice coherent if a PR is later requested. This task does not create or publish a PR.
- Applicable checks are documentation structural checks, not application test suites, because no executable behavior changes.

## Current state

- Feature branch: `CU-05` (not the local `main` branch).
- Existing worktree has unrelated untracked files, including the Frontend project; do not stage or alter them outside the explicit authorized edit scope.
- Progress: Core, BFF, and Frontend derivation are complete.
- Verification evidence: Core commit `88300a398a58db71c67615b4b78a9043a4534c54`, BFF commit `666888907d474390c084850a57d821a30b13810e`, and Frontend commit `6a615fdd8e72af7b3c838daca8b83b4d76d844a4` contain only their five respective project specs. Structural validation confirmed project spec references, evidence links, OpenAPI operation/path mappings, and generated Frontend API schema references. OpenAPI, Core SDL, application implementation, generated types, and tests were not changed by this documentation work. No application test suite or live-stack check was run for this passive documentation work.
- Next step: no project-spec derivation task remains; retain the existing delivery strategy without creating or publishing a PR.
