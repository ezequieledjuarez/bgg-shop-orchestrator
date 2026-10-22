# Regenerating Canonical As-Built Specifications

## Objective

Create five canonical, retrospective feature specifications for the implemented buyer flows in the BGG Shop orchestrator. These specifications document the verified as-built product behavior; they are not implementation plans or proposals for unimplemented use cases.

## Problem and Why

The repository contains use-case descriptions, implementation notes, service contracts, and tests, but no functional Spec Kit specifications for the implemented end-to-end flows. Canonical specifications provide a coherent functional baseline before deriving project-specific specifications in a later phase.

## Scope and Constraints

- Include CU-C01 authentication, CU-C02 catalog/search/filtering, CU-C03 product detail/reviews, CU-C04 shopping cart, and CU-C05 checkout/orders/invoice.
- Exclude wishlist and administrative use cases because they are not implemented.
- Mark partial behavior, known limitations, and pending verification explicitly; do not imply planned functionality is implemented.
- Treat source code, tests, OpenAPI/GraphQL contracts, and implementation documentation as evidence, while retaining links to the existing contracts rather than duplicating them.
- Generate canonical specifications only. Deriving specs for Core, BFF, and Frontend is a separate future task.
- Do not modify service code, contracts, or existing documentation.

## Authorized Scope

- `specs/`

## Tasks

### SPEC-001 — Generate canonical as-built specifications

- [x] Create one Spec Kit `spec.md` for each of CU-C01 through CU-C05 in sequentially numbered feature directories under `specs/`.
- [x] Ensure each spec uses the repository's Spec Kit template sections and identifies itself as retrospective/as-built.
- [x] Ground scenarios and requirements in implementation evidence and call out known limitations and pending verification.

**Route:** Delegated direct. A single bounded writer is required because this task creates five non-trivial documents and needs to read the source documents, contracts, and tests.

**Risk tier:** Passive documentation. Verify by structural readback and link/path checks; no executable behavior changes.

**Acceptance criteria:**

- Exactly five canonical functional specs exist, one for each implemented CU-C01–CU-C05 flow.
- No wishlist, administrative, or project-specific derived specifications are created.
- Each spec is complete against the Spec Kit template and distinguishes implemented behavior from limitations or pending checks.
- Existing service contracts remain unchanged.

**Verification:** Read back the generated specs; verify expected file count, required sections, source links, and `git diff --check`.

**Delivery:** `feature-branch-chain` (selected by the user). The user requested one local commit and explicitly prohibited pushing.

**Observed evidence:** Five files created (490 authored lines total). Required template headings are present in all five files, local Markdown links resolve, no trailing whitespace was found, and `git diff --check` passed. Spot checks confirmed the authentication and sandbox checkout specifications identify the implemented flow and limitations. No executable tests or builds were applicable to this passive documentation change.

**Primary work-unit commit:** `2f5a8a647ec9f47cf2018c3c0605cd3ccab74d16` — `docs: add canonical as-built specifications`. Local commit only; no push.

## Progress and Evidence

- Initial inventory confirmed existing canonical inputs in `CasosDeUso.md`, `docs/CU-C01-AUTHENTICATION-CHANGES.md`, `docs/CU-C02-FILTERING-CHANGES.md`, `docs/CU-C03-REVIEWS.md`, `docs/CU-C04-SHOPPING-CART.md`, and `docs/CU-C05-PURCHASE.md`.
- Existing technical contracts are `bgg-shop-bff/specs/openapi.yaml` and `bgg-shop-core/specs/schema.graphql`; these remain service contracts, not canonical functional specs.
- Root Spec Kit uses sequential numbering and `.specify/templates/spec-template.md`.
- The five specifications are in `specs/001-authentication-as-built/`, `specs/002-catalog-search-filters-as-built/`, `specs/003-product-detail-reviews-as-built/`, `specs/004-shopping-cart-as-built/`, and `specs/005-checkout-orders-invoice-as-built/`.

## Next Step

The five canonical specifications are generated, verified, and committed locally. Deriving project-specific specs remains a separate follow-up; do not push this commit.
