# Feature Specification: Gift Card Credit

**Feature Branch**: `009-gift-card-credit`
**Created**: 2026-10-27
**Status**: Closed for the agreed non-production scope; deferred work and unresolved risks are tracked in [follow-up.md](follow-up.md).
**Input**: Buyers can load credit using single-use gift cards and use that credit as another payment method.

## User Scenarios & Testing

### User Story 0 - Issue a gift card as an administrator (Priority: P1)

An authenticated administrator specifies a positive amount and receives a single-use gift card code once. The store persists only the code verifier.

**Independent Test**: Issue a card as an administrator and verify the amount, code and stored hash; reject anonymous and non-administrator requests without creating a card.

**Acceptance Scenarios**:

1. **Given** an administrator and a valid ARS amount, **When** they create a card, **Then** the code is returned once and only its hash is stored.
2. **Given** an anonymous or non-administrator user, **When** they request issuance, **Then** no card is created.
3. **Given** an invalid amount or an unavailable service, **When** issuance is requested, **Then** a sanitized error is shown and no automatic retry is performed.

### User Story 1 - Redeem a gift card (Priority: P1)

An authenticated buyer enters a gift card code to load its value into their account credit.

**Independent Test**: Redeem an issued card and verify the buyer's balance and redemption record; retry the same card as the same and a different buyer.

**Acceptance Scenarios**:

1. **Given** an authenticated buyer and an eligible unused card, **When** the buyer redeems its code, **Then** the card's full value is added to their credit and the card cannot be redeemed again.
2. **Given** an already redeemed or invalid code, **When** any buyer attempts to redeem it, **Then** no credit is added and the buyer receives a safe error.
3. **Given** simultaneous redemption requests for one card, **When** they complete, **Then** at most one succeeds and at most one credit is recorded.
4. **Given** a failed redemption transaction, **When** the operation is retried, **Then** the card and balance remain consistent and no credit is duplicated.
5. **Given** an unused gift card, **When** it is redeemed after any amount of time, **Then** it is not rejected due to expiration.

### User Story 2 - Pay with account credit (Priority: P1)

An authenticated buyer chooses account credit at checkout and receives the existing order and invoice experience for a successful purchase.

**Independent Test**: Pay for an eligible cart with sufficient credit and verify the order, credit, stock, purchased cart quantities, and invoice; retry the same operation and check that none is applied twice.

**Acceptance Scenarios**:

1. **Given** a buyer with sufficient credit, an eligible cart, and valid delivery data, **When** the buyer pays with credit, **Then** the server-priced order is paid, the balance is debited once, stock is decremented once, an invoice is created, and only purchased quantities leave the cart.
2. **Given** multiple concurrent checkout requests against the same balance or stock, **When** they complete, **Then** the balance and inventory cannot become negative and each successful order is charged once.
3. **Given** a failed credit checkout, **When** the buyer reviews their balance and cart, **Then** there is no partial debit, invoice, or stock decrement for that failed operation.
4. **Given** insufficient credit, **When** checkout is attempted, **Then** the payment is rejected without a debit or partial payment.
5. **Given** a buyer whose only credit is a redeemed gift card of 20,000 ARS, **When** they pay an order totaling at most 20,000 ARS, **Then** the purchase can succeed if the other checkout requirements are satisfied; an order above that amount is rejected without a debit.
6. **Given** a purchase costing less than the buyer's available credit, **When** payment succeeds, **Then** the remaining balance stays available for future purchases.
7. **Given** a cancelled order paid with credit, **When** its payment is refunded, **Then** the full amount paid with credit is restored to the buyer's balance once.
8. **Given** a buyer with any pending Mercado Pago order, **When** they attempt a new credit checkout, **Then** payment is rejected without changing their balance, cart, stock, or orders.
9. **Given** a successful credit checkout, **When** the buyer retries a previously rejected Mercado Pago order, **Then** the retry is rejected. Because historical orders cannot be reliably associated with the current cart, this includes unrelated rejected orders belonging to the same buyer.

### User Story 3 - View account credit (Priority: P2)

An authenticated buyer can view their available balance and distinguish successful redemption and purchase outcomes.

**Independent Test**: View a balance before and after a redemption and a credit-funded purchase, and verify another user cannot access it.

### Edge Cases

- Empty, malformed, non-existent, or already redeemed codes. Gift cards do not expire, and deactivation is outside the initial scope.
- Repeated requests, network retries, process interruption, and simultaneous redemption or checkout.
- Credit exactly equal to the total, insufficient credit, and balance remaining after a purchase.
- Price or stock changes between cart display and server-side checkout.
- Ownership violations, negative or overflow amounts, currency mismatches, and unauthorized attempts.
- A gift card is redeemed once; the resulting account balance can be spent across purchases until exhausted.
- Existing Mercado Pago sandbox checkout remains separate and paused; this feature must not weaken its validation.

## Requirements

### Functional Requirements

- **FR-001**: Authenticated buyers MUST be able to redeem an eligible single-use gift card for account credit.
- **FR-002**: Redemption MUST atomically associate the card with the buyer and credit its full value at most once, including under retries and concurrency.
- **FR-003**: Buyers MUST be able to view their own available account credit; other users MUST NOT access it.
- **FR-004**: Buyers MUST be able to select credit as a checkout payment method; order totals MUST be calculated on the server.
- **FR-005**: A successful credit-funded purchase MUST atomically debit credit, update the order, decrement stock, create the invoice record, and update purchased cart quantities.
- **FR-006**: Failed, repeated, or concurrent operations MUST NOT cause duplicate credit/debit, duplicate invoices, negative balances, or negative stock.
- **FR-007**: Gift card secrets MUST NOT appear in logs, public errors, URLs, or persisted plaintext; their verification MUST resist guessing and unauthorized redemption.
- **FR-008**: Credit and payment records MUST remain traceable to a buyer, redemption or order, amount, and currency without exposing the card code.
- **FR-009**: Gift card credit and its transactions MUST use ARS only, without currency conversion. Insufficient credit or stock MUST reject payment without a debit or split payment. Remaining credit MUST remain available for future purchases. Credit is personal and non-transferable; no commercial balance limit applies in the initial scope. When cancellation is implemented, cancelled credit-funded orders MUST restore the full amount paid with credit to the buyer's balance once.
- **FR-010**: The existing Mercado Pago path and its security checks MUST remain unchanged unless separately authorized.
- **FR-011**: The store's authorized administrators MUST be able to issue cards from an administrative screen; the code MUST be shown once and responses containing it MUST NOT be cached.

### Key Entities

- **Gift card**: A code-backed value that can be redeemed by at most one buyer once, with issuance and lifecycle attributes to be decided.
- **Account credit**: The available monetary value owned by one buyer in a defined currency.
- **Credit transaction**: A traceable credit or debit associated with a redemption or purchase.
- **Credit payment**: An association between an order and its debit; it must not rely on a Mercado Pago payment ID.

## Success Criteria

- **SC-001**: All redemption scenarios pass, including concurrent attempts against one code and failures before transaction commit.
- **SC-002**: All credit checkout scenarios pass, including concurrent purchases, duplicate requests, insufficient funds, and stock conflicts.
- **SC-003**: A successful purchase has exactly one debit and invoice, stock is decremented once, and the resulting balance and order match the server-calculated total.
- **SC-004**: Unauthorized access and code guessing tests do not reveal codes, balances, or other buyers' information.
- **SC-005**: Existing payment behavior passes applicable regression tests; no live provider transaction is needed for local credit E2E tests.

## Assumptions and Decisions

- Reuse existing buyer authentication, orders, stock, invoices, and cart behavior; credit checkout does not require a Mercado Pago redirect.
- The application is currently for local testing; no public HTTPS domain or real-money transaction is required for validation.
- The store issues cards. The local SQL seed creates one 20,000 ARS test card and returns its generated code only when first inserted; it stores only the SHA-256 hash. Treat the returned code as a secret and avoid recording it in logs or artifacts.
- **Initial scope**: Administrative issuance already exists. Card distribution is outside this feature.
- **Decision**: Insufficient credit blocks credit checkout; partial charges and split payments are not supported.
- **Decision**: Gift cards do not expire.
- **Decision**: Gift cards and account credit use ARS, the store's currency.
- **Decision**: Credit is personal and non-transferable, with no commercial balance limit. The buyer can view their balance; transaction history and card deactivation are outside the initial scope.
- **Decision**: A cancelled credit-funded order restores the full amount paid with credit to the buyer's balance once. Remaining credit is available for future purchases.
- **Decision**: Insufficient stock rejects credit checkout without a debit. Cancellation functionality is deferred; eligibility remains to be defined when it is implemented.
- **Decision**: Any pending Mercado Pago order belonging to the buyer blocks a new credit checkout, including orders created earlier.
- **Decision**: A successful credit checkout blocks retries of all previously rejected Mercado Pago orders belonging to the same buyer. Existing provider preferences require separate reconciliation and are not revoked by this local block.
- **Decision**: An approved payment from an older provider preference after credit checkout requires manual review; do not issue an automatic refund.
- **Decision**: An administrator can close a detected review by recording what was done and why. Closing it does not automatically refund money or unblock provider payment attempts.
- **Decision**: Recorded idempotency rejections are retained for 30 days; after expiration the same key may be processed as a new request. Successful idempotency records do not expire under this policy.
- **Decision**: A buyer with sufficient credit can choose either credit or Mercado Pago, subject to the existing payment safety rules and without split payment.