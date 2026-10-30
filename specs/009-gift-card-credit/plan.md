# Implementation Plan: Gift Card Credit

**Branch**: `009-gift-card-credit` | **Date**: 2026-10-27 | **Spec**: [spec.md](spec.md)
**Status**: Closed for the agreed non-production scope; deferred work and unresolved risks are tracked in [follow-up.md](follow-up.md).

## Summary

Add single-use gift card redemption into a buyer-owned credit balance and a credit-funded checkout. Preserve the existing Mercado Pago flow. A redeemed card adds its entire value once; the resulting balance may fund multiple purchases. Validate entirely in local test environments.

Late-payment handling, including discovery, reviews, scheduling and notifications, is excluded from the remaining work by user request. Existing implementation and historical evidence are preserved; the exclusion does not resolve or eliminate the associated payment risk.

## Technical Context

- **Core**: Python, Django/Graphene, PostgreSQL; existing purchase logic in `bgg-shop-core/saleor/graphql/orders.py` and SDL in `bgg-shop-core/specs/schema.graphql`.
- **BFF**: Flask/Python; API contract in `bgg-shop-bff/specs/openapi.yaml`.
- **Frontend**: React/TypeScript; types generated from the BFF OpenAPI contract.
- **Persistence**: Existing checkout tables are defined in `import_catalog.sql`. Its gift card block defines a single-use record and seeds one 20,000 ARS test card; determine the supported migration and upgrade path before changing deployed data.
- **Tests**: Core and BFF pytest, frontend Vitest and local browser E2E. A complete provider-backed payment flow remains unverified and requires separate explicit authorization before any payment or account mutation.
- **Constraint**: No public HTTPS domain; no production payment, provider configuration, or modification of the paused Mercado Pago work.

## Constitution Check

- Draft only. Review the applicable project constitutions and security/contract rules before implementation; no implementation gate is claimed as passed.
- Monetary values, credentials, concurrency, and persistence make this a high-risk change requiring transaction, authorization, negative, and concurrent tests.

## Work Plan

1. **Product rules and initial scope**: gift cards do not expire and credit uses ARS only. Credit is personal and non-transferable, with no commercial balance limit; show the balance without transaction history. Insufficient credit or stock rejects checkout without a debit or split payment; remaining credit stays available. Any pending Mercado Pago order belonging to the buyer blocks a new credit checkout. Card distribution, deactivation, and cancellation functionality are deferred. When cancellation is implemented, cancelled credit-funded orders restore the full credit payment once; cancellation eligibility remains to be defined.
2. **Design contracts and data**: define a safe card lifecycle, balance and credit transaction model, order payment association, idempotency strategy, lock order, migration/rollback, and Core GraphQL/BFF REST contracts. Do not place card codes in URLs, logs, or plaintext storage.
3. **Implement Core**: create redemption and balance operations and credit checkout under database transactions; enforce single-use cards, owner authorization, server-derived amounts, balance and stock consistency, and idempotent retries. Reuse existing order/invoice mechanisms where their transaction boundaries permit.
4. **Implement BFF**: expose validated operations, map domain errors without leaking sensitive details, update OpenAPI, and add contract and authorization tests.
5. **Implement frontend**: add authenticated credit balance/redemption and credit selection in checkout; generate types from the updated OpenAPI and provide loading, error, insufficient-balance, and success states.
6. **Verify locally**: run layer tests, OpenAPI/GraphQL contract checks, frontend build/lint, and browser E2E with locally issued test cards and no external payment. Check database invariants after successful, failed, retried, and concurrent operations.
7. **Document**: describe local setup, authorized test-card issuance, migration and rollback, limitations, and verification evidence. Do not add real credentials or reusable card codes to the repository.

The migration preconditions, isolated backup verification, and recovery limitations are documented in [migration-recovery.md](migration-recovery.md). They do not authorize migration or restoration of an existing database.

## Contracts and Endpoints Gate

The following contracts are integrated in the general Core and BFF schemas. Their presence does not mean the operations are all implemented or verified:

| Operation | Candidate REST surface | Request / response | Authentication |
| --- | --- | --- | --- |
| Issue card | `POST /api/v1/admin/gift-cards` | Positive decimal amount as string; one-time code, ID, amount and currency | Administrator bearer |
| Read balance | `GET /api/v1/credit` | No body; balance and currency | Buyer |
| Redeem card | `POST /api/v1/gift-cards/redeem` | Code and idempotency mechanism; resulting balance and redemption outcome | Buyer |
| Pay at checkout | `POST /api/v1/checkout/credit` | Existing shipping request and an idempotency key; returns a paid order and credit balance | Buyer |

The authoritative contracts are `bgg-shop-bff/specs/openapi.yaml` and `bgg-shop-core/specs/schema.graphql`. Earlier files under `contracts/` are drafts and can differ from those contracts. The existing Mercado Pago checkout remains separate.

**Evidence plan**: Validate the OpenAPI fragment and Core SDL, run BFF contract tests against the chosen schema, and cover authenticated and unauthorized scenarios with Core, BFF, frontend, and local E2E tests. Capture commands and observed outcomes in the implementation record; do not mark simulated provider calls as live validation.

**Pre-delivery gates**: Decisions and contracts approved; migrations and rollback reviewed; single-use/concurrency/idempotency and ownership tests pass; existing checkout regression passes; frontend build/lint and relevant E2E pass; no credentials or gift card codes appear in logs or artifacts.

## Risks and Open Decisions

- A partial implementation can consume a card without crediting the balance or debit credit without delivering an order. Use one database transaction per local operation and test rollback at each boundary.
- Split payments introduce reservation, provider failure, retries, and compensation. Do not implement mixed payment without an explicit approved policy.
- A one-time card is a bearer secret. The local test seed uses a random 64-character hexadecimal code and a SHA-256 verifier; it returns the code only on initial insertion. Do not capture the result in logs or artifacts. Decide the verifier and secret-management strategy for subsequent issuance, and add rate limiting and sanitized errors.
- Concurrency can overspend balances or oversell stock. Establish consistent lock ordering and database constraints, and test using independent transactions.
- The current checkout has existing pending test orders and incomplete provider validation. Preserve their state and do not reconcile or repeat provider payments as part of this feature.
- Each service is a separate repository. This plan and spec are on the orchestrator branch; create appropriately named branches in service repositories only when implementation is authorized, preserving their existing changes.

## Relevant Existing Surfaces

- `bgg-shop-core/saleor/graphql/orders.py` and `bgg-shop-core/specs/schema.graphql` for order behavior and the Core contract.
- `bgg-shop-bff/src/controllers/orders_controller.py` and `bgg-shop-bff/specs/openapi.yaml` for order API adaptation and contract.
- `bgg-shop-frontend/src/checkout/` and `bgg-shop-frontend/src/App.checkout.test.tsx` for checkout UI and tests.
- `import_catalog.sql` for existing purchase tables; `specs/005-checkout-orders-invoice-as-built/spec.md` for current behavior and limitations.