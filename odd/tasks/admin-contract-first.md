# Administrative API Contract

## Approved implementation scope (2026-11-02)

The user approved implementation of only Spec 007 tasks X-1, X-2 and C-1.
This supersedes the earlier read-only constraint below for these exact tasks.
Work remains local: do not contact remote services, deploy, or apply migrations
to an active database. Preserve all existing edits and do not stage or commit
pre-existing user changes. The current branch is `fix/spec-follow-ups`; its
naming warning does not authorize switching or renaming it.

Approved contract and data decisions:

- Admin access requires an active `is_staff` or `is_superuser` user in BFF and
  Core.
- `Product` maps the existing `product_boardgame` table as unmanaged. Product
  base price is greater than zero, name is unique, and quantity is
  nonnegative. Create requires name, price and quantity; update is partial and
  cannot change BGG ID or quantity. Exactly one `.webp` image reference (URL or
  path/filename) is allowed; binary upload is not part of this contract.
- Coupon codes are unique by exact, case-sensitive equality, without
  normalization. Remaining uses are nonnegative. When both UTC validity
  boundaries exist, `starts_at < ends_at`; the valid interval is
  `[starts_at, ends_at)`.
- Promotion discounts are 0–50%, with at most one active promotion per
  product; every promotion links to a product. Creation requires an explicit
  `active` boolean; update is partial. Existing promotions become inactive
  during migration.
- Calculate discounts with decimal precision. Sum all product-promotion
  savings and compare against coupon saving on the undiscounted cart subtotal.
  Round each total alternative once upward to whole pesos, choose the higher
  saving, and favor the store promotion on a tie. Reject a coupon discount
  above 50% of undiscounted subtotal. There are no configurable exclusions;
  gift cards and credit are payment methods, not discounts.
- Stock is nonnegative. An overstock `OUT` is partial-to-zero and reports
  requested and applied quantities. A movement UUID is permanent and bound to
  product, direction and quantity; mismatched payload rejects. The same
  payload may retry indefinitely after confirmed no-change. Never infer
  rollback from timeout or HTTP error.
- `POST /api/v1/cart/coupons/preview` is authenticated and read-only against
  the current user's cart, and neither reserves nor consumes a use. Checkout
  receives the chosen coupon and atomically reserves its use. Confirmed
  failure/cancellation releases the reservation; uncertainty retains it for
  provider reconciliation and unresolved cases go to manual review. Timeout
  alone never releases it.
- Audit read filters, pagination and redaction, and event/cache decisions are
  approved. Their implementation remains work in their respective tasks; this
  record does not mark those tasks complete. ZIP archive generation is outside
  Spec 007 scope.

### Task status

- [x] X-1 — define and validate the approved OpenAPI/Core GraphQL contracts.
- [x] X-2 — migration graph, full PostgreSQL application, and persisted
  constraints verified on fresh and legacy schemas.
- [x] C-1 — model/state alignment and persisted PostgreSQL constraints verified;
  the stock-reservation FK/check are enforced on fresh and legacy schemas.
- X-1 closes on the focused contract tests and OpenAPI 3.2 validation. X-2 and
  C-1 close on the temporary PostgreSQL migration and data-preservation checks
  recorded below.
- Contract instructions were found at
  `bgg-shop-bff/.github/agents/api-contract-validator.agent.md`; the requested
  `.agents/database-migration.agent.md` is absent from this repository and no
  equivalent database-migration agent instruction was found.
- Engram task mirror: pending; memory tools are unavailable in this session.
- Feature document: this existing file; no separate task record is created.

## Objective

Define the 007 administrative API contract before implementation, preserving
existing local changes and the project's local-only scope. The approved
implementation exception is limited to X-1, X-2 and C-1 above; document
proposed behavior separately from verified runtime implementation.

## Tasks

- [x] T001 Draft the administrative product-list contract and check its structure.
- [x] T002 Draft contracts for the other existing product, stock, promotion, and
  coupon routes; mark them as planned rather than verified implementation.
- [x] T003 Check YAML, local references, operation IDs, route parameters and
  security declarations; record unresolved discrepancies.
- [x] T004 Update 007 task evidence and contract-first instructions without
  marking implementation work as completed.
- [x] T005 Record the approved product, stock, promotion and coupon decisions;
  approved audit read and event/cache decisions remain implementation work in
  their respective tasks.
- [ ] T006 Verify the approved contracts against Core, BFF and Frontend behavior.
  Formal OpenAPI 3.2 validation has passed; runtime conformance remains open.

## Constraints

Do not modify implementation, the active database, or remote services. Do not
claim that a proposed contract has been implemented. Historical note: the
Engram mirror was pending when these tasks were originally recorded.

## Evidence (2026-10-31)

- Historically, `bgg-shop-bff/specs/openapi.yaml` contained nine planned operations on six
  existing administrative paths. New lifecycle, image, coupon-management,
  promotion-preview and audit routes remain undecided.
- From `bgg-shop-frontend`, `node_modules/.bin/openapi-typescript ../bgg-shop-bff/specs/openapi.yaml --output /dev/null` passed. A `js-yaml` structural check passed for operation IDs, required path parameters, security alternatives and local references; it is not formal OpenAPI 3.2 validation.
- BFF `.venv/bin/python -m openapi_spec_validator --version` failed because the
  module is not installed. Subsequently, the system Python's
  `openapi-spec-validator 0.9.0` validated the document successfully using
  `OpenAPIV32SpecValidator` for version `3.2.0`.
- The user confirmed that administrative operations require an active user
  with `is_staff` or `is_superuser`; a seller without those permissions is not
  authorized. BFF `tests/test_opkey_middleware.py` passed 16 tests and Core
  `tests/test_opkeys_internal.py::test_admin_operation_requires_active_administrator`
  passed three cases. These focused tests do not prove authorization or
  propagation for every 007 operation; see the BFF task record for commands.
- See `bgg-shop-bff/specs/007-manage-catalog-inventory-tasks.md` for observed
  BFF/Core/Frontend discrepancies. T001-T003 there remain open because the full
  inventory, decisions, and approved contract are not complete.

## Historical stock note (2026-10-31; superseded by the approved decisions above)

At that point, each edition was recorded as a separate product with its own
stock. The planned
`POST /api/v1/admin/products/{product_id}/stock` adds non-negative `new_stock`
units (10 + 20 = 30) via the planned Core `addProductStock` mutation. Neither
was implemented; the then-current public route and Core signature still
required a variant identifier and were incompatible. Reduction, reservations,
retries and idempotency were undecided in that historical note. The current
stock contract is recorded in the approved decisions above. T005 is recorded
complete; T006 remains open for runtime conformance.

## Contracts/data implementation evidence (2026-11-02)

- `bgg-shop-bff/specs/openapi.yaml` now defines the approved product, promotion,
  stock, coupon preview and checkout contracts; the system
  `openapi-spec-validator 0.9.0` accepted OpenAPI 3.2.0.
- Core SDL syntax and the new query/mutation/type fields are checked by the
  focused Core test. No resolver, controller, frontend or checkout behavior
  was changed.
- `saleor.promotions.models` now maps the existing unmanaged product table and
  links promotions by BGG ID; product price, promotion range and one-active-
  promotion-per-product constraints are reflected in model metadata.
- Discovered GraphQL migration `0017_007_contract_data_dependencies` extends
  `0016_coupon_constraints`, validates existing rows, adds the product link and
  records no duplicate coupon or audit tables. At the time of this earlier
  check, the promotions migration directory had no discovered migrations.
- Focused test: five passed. `manage.py check`: passed.
  `makemigrations --check --dry-run`: no changes detected, with a warning that
  migration history could not be checked because the configured local host
  `db` did not resolve. Migration was not applied to any database.
- No disposable local PostgreSQL DSN was configured. The active database was
  not contacted or modified; X-2 remains partial until the migration is
  exercised against an isolated local database.
- Engram mirror remains pending because memory tools are unavailable.

## Migration-discovery and contract follow-up (2026-11-02; historical snapshot)

- Added the promotions migration package marker and preserved the existing
  GraphQL dependency while adding `promotions.0001_initial` to
  `graphql.0014_promotion_manual_activation`.
- A focused no-database `MigrationLoader(None)` test passes discovery,
  dependency and graph-order checks. The contracts test now verifies that
  create/update product request schemas inherit the shared strictly-positive
  price constraint; Core SDL documents update-price positivity and the
  staff/superuser requirement on `adjustProductStock`.
- Focused Core tests: 6 passed. `python manage.py check` passed. The installed
  OpenAPI 3.2 validator passed.
- `makemigrations --check --dry-run` with an in-memory SQLite override fails
  while rendering `promotions.0001_initial`: its relation target
  `saleor.promotions.Promotion` has three components where Django expects two.
  Correcting that historical file requires approval for
  `bgg-shop-core/saleor/promotions/migrations/0001_initial.py`.
- `Product.name` is unique in `import_catalog.sql` but not in the model;
  Promotion/Coupon models use default `BigAutoField` IDs while existing DDL and
  the initial migration use `SERIAL`/`AutoField`. Model alignment requires
  approval for `bgg-shop-core/saleor/promotions/models.py`; C-1 is partial.
- At that earlier snapshot, the separate
  `bgg-shop-frontend/specs/006-manage-catalog-inventory-tasks.md` contained
  image-upload and unresolved-reduction wording. It was not edited because it
  is outside the authorized surfaces; current approved decisions are recorded
  in this recovery record and Spec 007 docs.
- The default-host `makemigrations` invocation attempted `db` at
  `192.168.1.202` and received connection refused; no connection was
  established and no migration was applied. No active database was migrated.

## State-sync slice (2026-11-02, implementation recorded)

- User authorized exact new file `promotions/migrations/0002_007_state_sync.py`
  and edits to `promotions/models.py` and `graphql/0017`. Plan: RED static
  MigrationLoader state test, then models/0017/0002 state-only sync. No
  database is used; SQLite in-memory and static checks only. Engram mirror is
  unavailable (pending).
- RED: new state test and 0017 quantity-check test failed first. GREEN: focused
  tests 7 passed; `manage.py check` clean; `makemigrations --check --dry-run`
  "No changes detected" (SQLite in-memory only). 0002 uses
  `SeparateDatabaseAndState` with empty database_operations, so no SQL is
  duplicated; 0017 now adds and validates `product_quantity_nonnegative`.
  OpenAPI validator not re-run (contracts untouched). Not staged or committed.

## Review correction slice (2026-11-02)

- Decision: promotion creation requires explicit boolean `active`
  (OpenAPI `AdminCreatePromotionRequest` now matches Core SDL); updates remain
  partial. X-1 complete.
- Models and state-only `0002` now include `StockReservation.bgg_id` FK to
  `Product.bgg_id` and `reserved_qty >= 0` check (existing DDL; no reservation
  behavior). `0017` drops the duplicate `product_quantity_nonnegative`; the
  quantity check is the DDL inline `product_boardgame_quantity_check`
  (`import_catalog.sql` line 21). Price > 0 stays in `0017`.
- RED: 2 focused tests failed first; GREEN: 7 passed, `manage.py check` clean,
  `makemigrations --check --dry-run` no changes, OpenAPI 3.2 valid (SQLite
  in-memory only). X-2 and C-1 stay partial: no SQL applied on disposable
  PostgreSQL. Not staged or committed.

## Current verification and trace (2026-11-02)

Requirements/decisions: `specs/007-manage-catalog-inventory/plan.md` and
`specs/007-manage-catalog-inventory/tasks.md`. Contracts:
`bgg-shop-bff/specs/openapi.yaml` and `bgg-shop-core/specs/schema.graphql`.
Implementation: `bgg-shop-core/saleor/promotions/models.py`,
`bgg-shop-core/saleor/graphql/migrations/0017_007_contract_data_dependencies.py`,
and `bgg-shop-core/saleor/promotions/migrations/0002_007_state_sync.py`.
Tests: `bgg-shop-core/tests/test_007_catalog_data_contracts.py`.

Observed checks from `bgg-shop-core`: `python -m pytest -q
tests/test_007_catalog_data_contracts.py` passed 7 tests; `python manage.py
check` passed; `python manage.py makemigrations --check --dry-run` reported no
changes using SQLite in-memory; and `openapi-spec-validator` 0.9.0 accepted
OpenAPI 3.2. One Django `USE_TZ` deprecation warning was observed. Promotions
migration discovery/order and state synchronization are verified statically.
No migration was executed in this current verification slice, so PostgreSQL
SQL application and persisted constraints remain unverified. X-1 is complete;
X-2 and C-1 remain partial. Runtime service behavior is not claimed. No commit
was made, and no unrelated task status was changed.

Earlier dated entries in this recovery record describe their then-current
state. The malformed migration-state blocker and model/DDL mismatches noted
earlier are superseded by the later state-sync work and current model state;
they are not current remaining blockers.

## PostgreSQL validation correction (2026-11-02)

- The full Django migration plan through `graphql.0017_007_contract_data_dependencies`
  and `promotions.0002_007_state_sync` applied in a newly-created local
  PostgreSQL database. Existing product, order, promotion and coupon data were
  preserved in a synthetic legacy-adoption schema; legacy promotions/coupons
  were inactive after migration.
- On the fresh-schema path, `stock_reservation` had only its primary-key
  constraint. PostgreSQL accepted both a negative `reserved_qty` and a
  reservation for an unknown product. The legacy schema already had the FK
  and check, so adoption alone did not expose this gap.
- The temporary database and login role were removed and verified absent. No
  existing database, persistent application database, or repository source
  file was modified during this validation.
- Authorized follow-up: add an idempotent migration for the stock-reservation
  FK/check and a PostgreSQL test covering fresh installation and legacy
  adoption. At that snapshot, X-2/C-1 remained partial pending those checks.

## PostgreSQL correction verification (2026-11-02)

- Added `bgg-shop-core/saleor/promotions/migrations/0003_stock_reservation_constraints.py`.
  The migration adds missing constraints as `NOT VALID`, validates existing
  rows, and leaves canonical legacy constraints intact when already present.
- Added PostgreSQL coverage for fresh installation and legacy adoption in
  `bgg-shop-core/tests/test_graphql_credit_postgres.py`. The fresh schema
  rejects negative reservation quantities and unknown product IDs; the legacy
  schema preserves product, order, promotion, coupon and reservation data.
- The two PostgreSQL migration tests plus the seven catalog/data contract
  tests passed (9 total). The independent verifier also passed these tests,
  `manage.py check`, and `makemigrations --check --dry-run`; one existing
  Django `USE_TZ` deprecation warning remains.
- Temporary PostgreSQL database and role cleanup was verified. No active DB
  was migrated and no commit was made. X-2 and C-1 are complete; X-1 remains
  complete; T006 and all unrelated Spec 007 implementation tasks remain open.
