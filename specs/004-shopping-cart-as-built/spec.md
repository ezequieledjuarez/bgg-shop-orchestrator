# Feature Specification: Shopping Cart (As-Built)

**Feature Branch**: `not applicable — retrospective specification`
**Created**: 2026-10-21
**Status**: As-built / retrospective
**Input**: CU-C04, implemented guest and authenticated shopping-cart behavior in the orchestrator repository.

> This document describes observed cart behavior and known boundaries. It is not a proposal to reserve stock or to guarantee inventory until purchase. “MUST” statements below describe the observed baseline.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add and review cart items (Priority: P1)

A visitor or signed-in buyer adds in-stock games to a cart and reviews the resulting quantities and total.

**Why this priority**: The cart is the implemented buyer workspace for collecting products before checkout.

**Independent Test**: Add products to an empty cart and verify the resulting lines, quantities, available stock, subtotals, and total.

**Acceptance Scenarios**:

1. **Given** a product with available stock, **When** the buyer adds a quantity to the cart, **Then** the cart contains that product with the accepted quantity and a recalculated subtotal and total.
2. **Given** a guest buyer, **When** they use the cart, **Then** the cart persists server-side and is associated with the guest browser without exposing its opaque identifier to the UI.
3. **Given** a signed-in buyer, **When** they view the cart, **Then** the cart is associated with the authenticated account rather than a client-supplied account identity.

### User Story 2 - Change or remove cart items (Priority: P2)

A buyer adjusts a product quantity or removes a product and sees the cart totals recalculated.

**Why this priority**: Cart editing lets buyers correct their intended purchase before checkout.

**Independent Test**: Change a line quantity, remove a line, and verify the updated lines and total after each action.

**Acceptance Scenarios**:

1. **Given** a product already in the cart, **When** the buyer changes its quantity, **Then** the line and total reflect the accepted quantity.
2. **Given** a product in the cart, **When** the buyer removes it, **Then** the line is absent and the total is recalculated.
3. **Given** a requested quantity exceeds current stock, **When** the buyer adds or updates the line, **Then** the accepted quantity is capped to available stock and an insufficient-stock warning is returned.
4. **Given** a guest cart and an account cart both contain items, **When** the buyer signs in, **Then** the carts are merged, same-product quantities are summed subject to current stock, and zero-stock lines are removed.

### Edge Cases

- A zero-stock product cannot be added from the catalog; a request above stock is capped with a warning instead of silently reserving inventory.
- A cart quantity must be positive; invalid quantity and integer-bound inputs are rejected as validation errors.
- Prices and subtotals are recalculated from the current product price when the cart is read; the cart does not freeze product prices.
- Cart edits do not reserve or decrement inventory. Inventory changes only after a purchase is approved.
- Guest-to-account merge behavior is implemented, but the end-to-end live-stack merge remains pending verification in the implementation record.
- Empty, loading, error, and stock-warning states are distinct cart states.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: As built, both guest visitors and authenticated buyers MUST be able to read and edit a server-persisted cart.
- **FR-002**: As built, the cart MUST support adding a product, changing its quantity, and removing it.
- **FR-003**: As built, each cart line MUST display the product, accepted quantity, current unit price, subtotal, and available stock, and the cart MUST display its recalculated total.
- **FR-004**: As built, cart identity MUST be derived from the guest browser cart or the authenticated buyer session, not from a client-provided user identifier.
- **FR-005**: As built, the system MUST cap a requested quantity at current stock and return an insufficient-stock warning when the requested amount is too high.
- **FR-006**: As built, login MUST merge the guest cart into the account cart, summing same-product quantities subject to current stock and removing lines with no stock.
- **FR-007**: As built, cart changes MUST NOT reserve or decrease stock.

### Key Entities

- **Cart**: A buyer's current collection of product lines, associated with either a guest browser or an authenticated buyer.
- **Cart line**: A product and positive accepted quantity, with the current unit price, calculated subtotal, and available-stock information.
- **Stock warning**: Feedback that a requested quantity exceeded current availability and was adjusted.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each of the 3 add/read-cart acceptance scenarios resolves to the correct cart identity and visible cart contents.
- **SC-002**: All 4 cart-editing acceptance scenarios show the accepted line quantity, recalculated totals, warning, or merge result as stated.
- **SC-003**: Cart-only add, update, and remove actions do not reduce the reported product stock.
- **SC-004**: After a requested quantity exceeds stock, the stored/displayed accepted quantity does not exceed that available stock.

## Assumptions

- A guest cart may be used without creating an account.
- Account identity for an authenticated cart comes from the validated login context.
- Current product prices, not a cart-time price snapshot, determine the displayed cart subtotal.
- Stock is not held for a buyer during cart editing and can change before purchase.

### As-Built Status, Limitations, and Evidence

- **Verified in source/tests**: Cart operations, stock-bound behavior, server-side cart association, and cart presentation are represented in Core, BFF, and Frontend source/tests.
- **Reported, not rerun for this documentation change**: The CU-C04 notes report automated Core/BFF/Frontend checks and a live development check of stock capping, totals, removal, and guest persistence.
- **Pending verification**: Real-browser behavior, guest-to-account merge against the live stack, purchase after login/cart merge, and a clean-database run remain pending as recorded in the implementation notes.
- **Known limitation**: Cart edits do not reserve stock. Availability is subject to change before purchase approval.
- **Evidence references**:
  - Use case and implementation record: [CasosDeUso.md](../../CasosDeUso.md), [CU-C04 cart notes](../../docs/CU-C04-SHOPPING-CART.md).
  - Contracts: [BFF OpenAPI](../../bgg-shop-bff/specs/openapi.yaml), [Core GraphQL schema](../../bgg-shop-core/specs/schema.graphql).
  - Implementation: [Frontend cart and catalog flow](../../bgg-shop-frontend/src/App.tsx), [BFF cart controller](../../bgg-shop-bff/src/controllers/cart_controller.py), [Core GraphQL implementation](../../bgg-shop-core/saleor/graphql/api.py), [database seed and cart schema](../../import_catalog.sql).
  - Tests: [Frontend cart tests](../../bgg-shop-frontend/src/App.cart.test.tsx), [BFF cart tests](../../bgg-shop-bff/tests/test_cart.py), [Core cart tests](../../bgg-shop-core/tests/test_graphql_cart.py).
