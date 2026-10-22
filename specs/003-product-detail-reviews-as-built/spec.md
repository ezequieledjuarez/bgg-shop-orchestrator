# Feature Specification: Product Detail and Reviews (As-Built)

**Feature Branch**: `not applicable — retrospective specification`
**Created**: 2026-10-21
**Status**: As-built / retrospective
**Input**: CU-C03, implemented product detail and customer review behavior in the orchestrator repository.

> This document records implemented buyer behavior. It does not adopt every behavior described in the original use-case narrative as a current requirement. “MUST” statements below describe the observed baseline.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View a product detail (Priority: P1)

A buyer opens a board game's detail page to inspect the product information, current availability, and public review summary.

**Why this priority**: A detail page gives the buyer product-specific information needed before deciding whether to add a game to the cart.

**Independent Test**: Open an existing product by its public slug and verify that the detail and approved-review information load; open an unknown slug and verify the not-found state.

**Acceptance Scenarios**:

1. **Given** a product exists, **When** a buyer opens its detail page, **Then** the product's available descriptive fields, price, current stock, approved reviews, and approved-review summary are displayed.
2. **Given** a product slug does not identify a catalog product, **When** the buyer opens the detail page, **Then** a not-found state is shown.
3. **Given** a product has no approved reviews, **When** the detail page loads, **Then** it shows an empty approved-review list and a summary with no average rating.

### User Story 2 - Submit a product review (Priority: P2)

A signed-in buyer submits one rating and written review for a product and receives confirmation that it is awaiting moderation.

**Why this priority**: Buyers can contribute feedback while the pending state keeps unreviewed content out of public product information.

**Independent Test**: Submit a valid review as an authenticated buyer and verify the pending confirmation; test unauthenticated, invalid, and duplicate submissions separately.

**Acceptance Scenarios**:

1. **Given** an authenticated buyer, an existing product, and valid review content, **When** the buyer submits a rating from 1 through 5 and a nonempty body within the supported length, **Then** the review is accepted with a pending status.
2. **Given** a buyer is not authenticated, **When** they submit a review, **Then** the review is rejected and the buyer is asked to sign in.
3. **Given** the buyer has already submitted a review for that product, **When** they try to submit another, **Then** the duplicate is rejected.
4. **Given** review input is outside the supported rating or text bounds, **When** the buyer submits it, **Then** validation feedback is shown and no valid review is reported as created.

### Edge Cases

- An unknown slug produces a not-found result and does not create a review.
- Only approved reviews contribute to the public list and average; newly submitted pending reviews do not appear as public reviews.
- Review submission failures, validation failures, and duplicate submissions produce feedback without exposing internal service details.
- Moderation actions and administrative review workflows are outside this buyer feature.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: As built, the system MUST allow a buyer to open a product detail using its public slug.
- **FR-002**: As built, the detail MUST show the available product attributes, price, stock, approved public reviews, and the approved-review count and average when defined.
- **FR-003**: As built, the system MUST identify a missing product with a not-found outcome.
- **FR-004**: As built, only an authenticated buyer MUST be able to submit a review.
- **FR-005**: As built, a review MUST contain one rating from 1 through 5 and a body from 1 through 2000 characters.
- **FR-006**: As built, a buyer MUST be limited to one review per product; an accepted review MUST start pending moderation.
- **FR-007**: As built, only approved reviews MUST contribute to the public review list and product review summary.

### Key Entities

- **Product detail**: A catalog product identified for buyers by its public slug, with descriptive information, price, and current quantity available.
- **Customer review**: A buyer's product-specific rating and text, with a moderation state and creation time.
- **Review summary**: The count and average rating derived from public approved reviews.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 3 detail acceptance scenarios resolve to a product, not-found, or empty-review presentation as stated.
- **SC-002**: All 4 review acceptance scenarios produce the stated accepted-pending, authentication, duplicate, or validation result.
- **SC-003**: Only reviews with approved status appear in the public list and contribute to the public review summary.

## Assumptions

- Product details are only available for products in the active catalog.
- Buyers can read approved reviews without signing in; authentication is required to submit.
- The public product route uses a slug derived from the unique game name.
- Moderation is intentionally outside CU-C03. Administrative approval, hiding, deletion, and moderation screens are not implemented as part of this buyer flow.
- Any additional original-use-case details not present in the current product contract, such as manuals or rules, are not asserted here as implemented.

### As-Built Status, Limitations, and Evidence

- **Verified in source/tests**: The contract and linked implementation/tests cover slug-based detail, approved public reviews, review summary, authenticated review creation, and domain validation.
- **Reported, not rerun for this documentation change**: The CU-C03 implementation notes report Core, BFF, and Frontend automated test results, type generation, lint, and build checks. The notes state that independent live end-to-end database validation was environment-dependent and not completed in that workspace.
- **Known scope boundary**: New reviews remain pending; moderation is outside scope. Wishlist and administrator workflows remain excluded from these canonical buyer specifications.
- **Evidence references**:
  - Use case and implementation record: [CasosDeUso.md](../../CasosDeUso.md), [CU-C03 review notes](../../docs/CU-C03-REVIEWS.md).
  - Contracts: [BFF OpenAPI](../../bgg-shop-bff/specs/openapi.yaml), [Core GraphQL schema](../../bgg-shop-core/specs/schema.graphql).
  - Implementation: [Frontend product and review flow](../../bgg-shop-frontend/src/App.tsx), [BFF product detail controller](../../bgg-shop-bff/src/controllers/product_detail_controller.py), [BFF review controller](../../bgg-shop-bff/src/controllers/reviews_controller.py), [Core GraphQL implementation](../../bgg-shop-core/saleor/graphql/api.py).
  - Tests: [BFF product tests](../../bgg-shop-bff/tests/test_products.py), [BFF review tests](../../bgg-shop-bff/tests/test_reviews.py), [Core product tests](../../bgg-shop-core/tests/test_graphql_products.py), [Core review tests](../../bgg-shop-core/tests/test_graphql_reviews.py), [Frontend application tests](../../bgg-shop-frontend/src/App.test.tsx).
