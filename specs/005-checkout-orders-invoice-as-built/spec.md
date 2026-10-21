# Feature Specification: Checkout, Orders, and Invoice (As-Built)

**Feature Branch**: `not applicable — retrospective specification`
**Created**: 2026-10-21
**Status**: As-built / retrospective
**Input**: CU-C05, implemented sandbox checkout, buyer orders, payment confirmation, and invoice behavior in the orchestrator repository.

> This document records current buyer-facing behavior and verification limits. Payment behavior is sandbox-only; it does not represent production payment acceptance. “MUST” statements below describe the observed baseline.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Start checkout from a populated cart (Priority: P1)

A signed-in buyer chooses a delivery mode, supplies the required delivery information where applicable, and starts payment for the server-calculated cart contents.

**Why this priority**: Checkout turns a buyer's cart into an order and begins the implemented payment flow.

**Independent Test**: With a nonempty cart and authenticated buyer, create a checkout and verify a pending-payment order with a server-calculated total and a sandbox payment destination.

**Acceptance Scenarios**:

1. **Given** an authenticated buyer with a nonempty cart and valid delivery selection, **When** they start checkout, **Then** an order is created from a server-side snapshot and the buyer receives a payment destination for the enabled sandbox flow.
2. **Given** a guest or an empty cart, **When** checkout is requested, **Then** checkout is not started and the buyer receives an appropriate authentication or cart validation outcome.
3. **Given** standard delivery is selected, **When** required address details are missing, **Then** the buyer is asked to provide the required information before checkout proceeds.

### User Story 2 - Confirm payment and view purchase outcome (Priority: P1)

A buyer returns from the payment provider and receives an outcome based on a payment verification performed by the system.

**Why this priority**: An order is not treated as paid merely because the browser reports a successful redirect.

**Independent Test**: Exercise approved, rejected, pending, and stock-conflict payment outcomes using the provider verification test scenarios; verify order status and inventory behavior.

**Acceptance Scenarios**:

1. **Given** the provider confirms an eligible sandbox payment as approved, **When** the buyer confirms checkout, **Then** the order becomes paid, stock is decremented once, an invoice is created, and purchased quantities are removed from the cart.
2. **Given** the provider reports a rejected payment, **When** confirmation completes, **Then** the buyer sees the rejection outcome and can start a retry for an eligible order.
3. **Given** the provider reports a pending payment or the buyer has not returned to the result page, **When** no approved confirmation has completed, **Then** the order is not presented as paid.
4. **Given** payment is approved after the required stock is no longer available, **When** confirmation completes, **Then** the order is represented as a paid stock conflict rather than silently decrementing below zero.

### User Story 3 - Review orders and download an invoice (Priority: P2)

A signed-in buyer reviews their purchase history and downloads an invoice for an eligible paid order.

**Why this priority**: Order history and invoice access let the buyer review and retain purchase records after checkout.

**Independent Test**: As the order owner, view order history and download a PDF invoice; as another buyer, verify that the order/invoice is not accessible.

**Acceptance Scenarios**:

1. **Given** a signed-in buyer with orders, **When** they open purchase history or an order detail, **Then** only their orders and their order lines are shown.
2. **Given** an eligible paid order with an invoice, **When** its owner requests the invoice, **Then** a PDF is downloaded.
3. **Given** an order belonging to another buyer, **When** a buyer requests its detail or invoice, **Then** access is denied.

### Edge Cases

- The order total and line prices come from the server-side cart snapshot, not values supplied by the browser.
- Payment confirmation verifies provider data and order ownership; a browser redirect alone does not mark an order paid.
- A live-mode payment is rejected by the current sandbox-only flow.
- Confirmation is idempotent for stock changes, but without provider webhooks a payment made by a buyer who never returns can remain pending.
- If stock is unavailable at approval time, the order can enter `paid_stock_conflict`; this is not a normal successful fulfillment.
- A duplicate approved payment may charge a buyer twice even though stock is not decremented again; refunds are outside the implemented scope.
- Delivery costs, shipping fulfillment, refunds, and production payment operations are not part of this as-built feature.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: As built, checkout MUST require an authenticated buyer and a nonempty cart.
- **FR-002**: As built, the buyer MUST be able to select standard delivery or pickup; required standard-delivery details MUST be collected before checkout.
- **FR-003**: As built, the order and its line prices MUST be based on a server-side cart snapshot.
- **FR-004**: As built, payment initiation MUST be limited to the configured sandbox payment flow and MUST NOT accept a live-mode payment as verified.
- **FR-005**: As built, the system MUST verify payment with the provider before marking an order paid.
- **FR-006**: As built, successful payment confirmation MUST update the order, decrement stock once, create an invoice, and remove only the purchased quantities from the cart.
- **FR-007**: As built, the system MUST represent rejected, pending, cancelled, and paid-stock-conflict outcomes distinctly and permit retry for an eligible rejected order.
- **FR-008**: As built, a signed-in buyer MUST be able to list and inspect only their own orders and download an available PDF invoice for an owned paid order.

### Key Entities

- **Purchase order**: A buyer-owned record of checkout status, total, delivery choice, payment outcome, and purchase lines.
- **Order line**: A snapshot of product name, unit price, quantity, and subtotal at checkout.
- **Payment attempt**: A payment-provider transaction associated with an order and subject to server-side verification.
- **Invoice**: A buyer-owned PDF purchase record issued for an eligible paid order.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 3 checkout-start acceptance scenarios produce an order/payment start or validation outcome as stated.
- **SC-002**: All 4 payment-outcome acceptance scenarios resolve to the corresponding paid, rejected/retry, pending, or paid-stock-conflict state.
- **SC-003**: For an approved payment, stock is decremented once, an invoice is associated with the order, and only purchased quantities are removed from the cart.
- **SC-004**: All 3 order and invoice acceptance scenarios enforce buyer ownership and return an invoice only for an eligible owned order.

## Assumptions

- Checkout is available only to signed-in buyers with at least one cart item.
- The current payment integration is for development/sandbox only; production payment support is not implied.
- “Paid” means the Core has verified the payment with the payment provider, not merely received a browser return.
- Invoice availability follows the paid-order behavior described by the current contract and implementation.

### As-Built Status, Limitations, and Evidence

- **Verified in source/tests**: The source, contract, and existing tests cover order creation, payment retry/confirmation, order ownership, invoice retrieval, and the buyer-facing checkout/history flow.
- **Reported, not rerun for this documentation change**: The CU-C05 implementation note reports Core, BFF, and Frontend automated tests and a successful checkout creation against a sandbox flow. Provider behavior is mocked in automated tests.
- **Pending end-to-end verification**: The full browser return-to-provider-to-confirm path, stock decrement, invoice row/PDF download, cart cleanup, and guest-cart merge followed by checkout remain pending in the implementation record. Sandbox test-user `live_mode` behavior and clean-database loading also remain unverified there.
- **Known limitations**: No webhooks, refunds, production payments, shipping costs, or shipping fulfillment are implemented. A buyer who pays but does not return may leave an order pending. The implementation notes also disclose possible duplicate charging on a second approved payment; refund handling is out of scope.
- **Evidence references**:
  - Use case and implementation record: [CasosDeUso.md](../../CasosDeUso.md), [CU-C05 purchase notes](../../docs/CU-C05-PURCHASE.md).
  - Contracts: [BFF OpenAPI](../../bgg-shop-bff/specs/openapi.yaml), [Core GraphQL schema](../../bgg-shop-core/specs/schema.graphql).
  - Implementation: [Frontend checkout screen](../../bgg-shop-frontend/src/checkout/CheckoutScreen.tsx), [Frontend order history](../../bgg-shop-frontend/src/checkout/OrdersScreen.tsx), [Frontend checkout navigation](../../bgg-shop-frontend/src/checkout/navigation.ts), [BFF order controller](../../bgg-shop-bff/src/controllers/orders_controller.py), [Core order implementation](../../bgg-shop-core/saleor/graphql/orders.py), [Core payment implementation](../../bgg-shop-core/saleor/graphql/payments.py), [database schema and seed](../../import_catalog.sql).
  - Tests: [Frontend checkout tests](../../bgg-shop-frontend/src/App.checkout.test.tsx), [Frontend payment-navigation tests](../../bgg-shop-frontend/src/checkout/navigation.test.ts), [BFF order tests](../../bgg-shop-bff/tests/test_orders.py), [Core order tests](../../bgg-shop-core/tests/test_graphql_orders.py).
