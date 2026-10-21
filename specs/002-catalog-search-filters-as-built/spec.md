# Feature Specification: Catalog Search and Filters (As-Built)

**Feature Branch**: `not applicable — retrospective specification`
**Created**: 2026-10-21
**Status**: As-built / retrospective
**Input**: CU-C02, implemented catalog discovery, search, and filtering in the orchestrator repository.

> This document describes the buyer-facing behavior evidenced in the current repository. It is not a proposal for planned discovery features. “MUST” statements below describe the observed baseline.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse and search the catalog (Priority: P1)

A visitor browses the board-game catalog or searches by a title or publisher name to find matching products.

**Why this priority**: Catalog discovery is the primary entry point for visitors exploring available products.

**Independent Test**: Load the catalog, submit a search term, and verify that matching results or an explicit empty state is shown.

**Acceptance Scenarios**:

1. **Given** the catalog is available, **When** a visitor opens the catalog, **Then** products and their available catalog information are displayed.
2. **Given** a visitor enters a search term, **When** they submit it, **Then** the displayed results are filtered by a case-insensitive match against product name or publisher.
3. **Given** the submitted search and filters match no products, **When** results load, **Then** an empty-results message and a way to clear filters are shown.

### User Story 2 - Narrow the catalog by product attributes (Priority: P2)

A visitor combines available filters to narrow products by publication year, supported player count, category, and price range.

**Why this priority**: Attribute filters help visitors find games that fit their requirements without browsing unrelated products.

**Independent Test**: Apply one or more supported filters and verify that each returned product satisfies the selected criteria; try an invalid range and verify that it is rejected.

**Acceptance Scenarios**:

1. **Given** valid year, player-count, category, or price criteria, **When** the visitor applies them, **Then** the results satisfy the submitted criteria.
2. **Given** a minimum player count above the maximum or a minimum price above the maximum, **When** the criteria are submitted, **Then** the request is rejected as invalid rather than presented as a successful filtered result.
3. **Given** a category identifier outside the currently supported category map, **When** the visitor applies it, **Then** no matching products are returned.

### User Story 3 - Inspect the displayed catalog order (Priority: P3)

A visitor selects one of the available catalog display-order options to compare products by price or featured status.

**Why this priority**: Local ordering gives the visitor limited control over the currently displayed results, but does not replace relevance ranking.

**Independent Test**: Select each available order option and verify that the visible products are reordered according to the selected local rule.

**Acceptance Scenarios**:

1. **Given** catalog results are visible, **When** the visitor selects a low-to-high or high-to-low price order, **Then** the visible results are ordered by price in that direction.
2. **Given** catalog results are visible, **When** the visitor selects “Recommended”, **Then** the view uses the optional featured indicator; it does not claim server-calculated relevance.

### Edge Cases

- A blank or whitespace-only search, invalid numeric parameter, nonpositive page value, or inverted range is rejected with validation feedback at the service boundary.
- A valid filter combination can produce zero results; the catalog shows an empty state rather than treating it as a service error.
- The category filter currently uses a limited mapping; an unknown category identifier yields no results.
- Upstream service or malformed-payload failures are distinct from an empty catalog and are shown with a retry action.
- Search is submitted with Enter or the search control; results are not requested for every keystroke.
- The UI does not expose navigation beyond the first requested catalog page.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: As built, the system MUST allow visitors to browse products without authentication.
- **FR-002**: As built, the system MUST support catalog search by case-insensitive product-name or publisher match.
- **FR-003**: As built, the system MUST filter catalog results by publication year, minimum and maximum player counts, supported category, and inclusive minimum and maximum price.
- **FR-004**: As built, the system MUST reject invalid filter values and inverted player-count or price ranges.
- **FR-005**: As built, the system MUST show distinct loading, error, empty, and successful catalog states; an empty result MUST permit clearing filters.
- **FR-006**: As built, the visitor MUST be able to order the displayed results locally by ascending or descending price and by the optional featured indicator.
- **FR-007**: As built, the catalog MUST display only the first requested page and MUST NOT imply that “Recommended” is server-calculated relevance.

### Key Entities

- **Catalog product**: A listed board game with descriptive attributes, category, publisher, price, image, and availability.
- **Catalog criteria**: Optional search text and product attributes used together to narrow the visible product set.
- **Catalog result page**: A subset of matching products with result-count and page metadata; the current UI does not provide page navigation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 3 search-and-browse acceptance scenarios display the matching, empty, or initial catalog state as stated.
- **SC-002**: All 3 filter acceptance scenarios apply criteria or reject invalid/unsupported input with the stated result.
- **SC-003**: Both local-order acceptance scenarios reorder the visible results according to their stated local rules.
- **SC-004**: A zero-result search is represented as an empty state, while an upstream failure is represented as an error state.

## Assumptions

- Catalog browsing does not require authentication.
- Search and filters are submitted together against the current product catalog.
- “Supported category” means the limited category mapping present in the current Core behavior, not an unrestricted category-management feature.
- Personalized recommendations, relevance ordering, user-defined filter persistence, and visible page navigation are not implemented behavior in CU-C02.

### As-Built Status, Limitations, and Evidence

- **Verified in source/tests**: The current catalog sends search and supported filters for service-side filtering; local display-order options and loading/error/empty/success states are described in the implementation notes and UI source.
- **Reported, not rerun for this documentation change**: The CU-C02 implementation record reports BFF, Core, and Frontend test/build checks, but says browser visual validation and full service/database end-to-end validation were not performed there.
- **Known gaps**: Relevance ordering is not implemented by BFF/Core. “Recommended” uses a local featured field. The API supports pagination, but the UI requests only the first page (up to 100 entries) and exposes no pagination controls. Category identifiers map through a limited local Core map.
- **Evidence references**:
  - Use case and implementation record: [CasosDeUso.md](../../CasosDeUso.md), [CU-C02 filtering notes](../../docs/CU-C02-FILTERING-CHANGES.md).
  - Contracts: [BFF OpenAPI](../../bgg-shop-bff/specs/openapi.yaml), [Core GraphQL schema](../../bgg-shop-core/specs/schema.graphql).
  - Implementation: [Catalog UI](../../bgg-shop-frontend/src/App.tsx), [BFF product controller](../../bgg-shop-bff/src/controllers/products_controller.py), [BFF product proxy](../../bgg-shop-bff/src/proxy.py), [Core GraphQL implementation](../../bgg-shop-core/saleor/graphql/api.py).
  - Tests: [Frontend catalog tests](../../bgg-shop-frontend/src/App.test.tsx), [BFF product tests](../../bgg-shop-bff/tests/test_products.py), [Core product tests](../../bgg-shop-core/tests/test_graphql_products.py).
