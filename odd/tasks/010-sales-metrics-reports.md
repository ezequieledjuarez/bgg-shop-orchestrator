# ODD Task Record — 010-sales-metrics-reports

## Objective

Implement CU-A02 sales metrics from contracts through local verification, beginning with the Core PostgreSQL tests.

## Problem and Why

The feature plan described only the main metrics operation, while the feature task lists also required category retrieval. The user confirmed that category retrieval belongs in this contract work and asked to record a reusable rule to evaluate endpoint coverage in both service contracts.

## Feature Scope

- `specs/010-sales-metrics-reports/plan.md`
- `specs/010-sales-metrics-reports/tasks.md`
- `bgg-shop-core/specs/schema.graphql`
- `bgg-shop-core/specs/010-sales-metrics-reports-tasks.md`
- `bgg-shop-bff/specs/openapi.yaml`
- `bgg-shop-bff/specs/010-sales-metrics-reports-tasks.md`
- `odd/tasks/010-sales-metrics-reports.md`

## Completed Work Unit: Contracts

- [x] X-1 Define the Core SDL operations and payload types.
- [x] X-2 Define the BFF metrics endpoint.
- [x] X-3 Define the BFF categories endpoint and matching Core query.
- [x] X-4 Validate both contract documents and record the service-test runner result.

## Completed Work Unit: Core Tests

- [x] C-1 Write and run the initial Core PostgreSQL tests, observing expected RED against the missing Graphene query fields.

## Completed Work Unit: Paired Date Bounds

- [x] X-5 Document that callers must provide both `from` and `to`, or omit both; a one-sided range returns `INVALID` with `extensions.field` identifying the missing bound, while omitting both defaults to the last 30 days.
- [x] C-1a Add PostgreSQL GraphQL tests for `from`-only (explicit `to: None`) and `to`-only (explicit `from: None`) inputs and observe expected RED. Keep both-omitted/default coverage unchanged.

### Allowed edit surfaces for X-5 and C-1a

- `specs/010-sales-metrics-reports/plan.md`
- `specs/010-sales-metrics-reports/tasks.md`
- `bgg-shop-core/specs/schema.graphql`
- `bgg-shop-core/specs/010-sales-metrics-reports-tasks.md`
- `bgg-shop-core/tests/test_admin_sales_metrics_postgres.py`
- `bgg-shop-bff/specs/openapi.yaml`
- `bgg-shop-bff/specs/010-sales-metrics-reports-tasks.md`
- `odd/tasks/010-sales-metrics-reports.md`

No resolver, controller, database schema, migration, or frontend implementation is included in X-5/C-1a.

### X-5 and C-1a routing and verification

- Route: delegated direct contract writer across Core and BFF; parent performed independent review and commit.
- Risk: high; these are public contracts and PostgreSQL integration tests.
- Verification: OpenAPI/SDL parsing with paired-bound assertions, test module compile, and fresh loopback-only PostgreSQL 15 run; active `saleor` database was not used.

## Completed Work Unit: Core Resolver

- [x] C-2 Implement `adminSalesMetrics` in `bgg-shop-core/saleor/graphql/api.py` and make metrics/filter cases in C-1/C-1a pass; categories remain for C-3.

### Allowed edit surfaces for C-2

- `bgg-shop-core/saleor/graphql/api.py`
- `bgg-shop-core/tests/test_admin_sales_metrics_postgres.py`
- `bgg-shop-core/specs/010-sales-metrics-reports-tasks.md`
- `specs/010-sales-metrics-reports/tasks.md`
- `odd/tasks/010-sales-metrics-reports.md`

No controller, database schema, migration, or frontend implementation is included in C-2.

## Completed Work Unit: Core Categories

- [x] C-3 Implement `adminSalesCategories` in `bgg-shop-core/saleor/graphql/api.py` and pass the category retrieval and authorization tests.

### Allowed edit surfaces for C-3

- `bgg-shop-core/saleor/graphql/api.py`
- `bgg-shop-core/tests/test_admin_sales_metrics_postgres.py`
- `bgg-shop-core/specs/010-sales-metrics-reports-tasks.md`
- `specs/010-sales-metrics-reports/tasks.md`
- `odd/tasks/010-sales-metrics-reports.md`

No controller, database schema, migration, or frontend implementation is included in C-3.

## Completed Work Unit: Query Plan Review

- [x] C-4 Review local EXPLAIN plans on synthetic seeded data and record whether a query index is justified.

### Allowed edit surfaces for C-4

- `bgg-shop-core/specs/010-sales-metrics-reports-tasks.md`
- `specs/010-sales-metrics-reports/tasks.md`
- `odd/tasks/010-sales-metrics-reports.md`

No application code, database schema, index, or migration is included in C-4. Any justified index change is a separately reviewed task.

### C-4 routing and verification

- Route: direct local query-plan review using the cached PostgreSQL image and synthetic data in a disposable loopback-only database.
- Risk: medium; seeded data and EXPLAIN run only inside the temporary database, never the active `saleor` database.
- Verification: `EXPLAIN (ANALYZE, BUFFERS)` covered unfiltered paid-at range, combined category/product filtering, and created-at status counts over 100,000 synthetic orders/lines and 500 products. All completed in 28–46 ms; the selective filter matched 12 rows but scanned purchase-order lines sequentially. No index was added because the synthetic data does not establish a representative workload or latency target. Temporary DB/container removed.

No application code, database schema, index, or migration was added in C-4. Any future index change is a separately reviewed task.

## Completed Work Unit: BFF Metrics Tests

- [x] B-1 Write BFF tests for authentication, paired/range validation, repeated-filter forwarding, `no-store`, and public error redaction. Collection succeeded and expected route-not-registered RED was observed.

### Allowed edit surfaces for B-1

- `bgg-shop-bff/tests/test_admin_sales_metrics.py`
- `bgg-shop-bff/specs/010-sales-metrics-reports-tasks.md`
- `specs/010-sales-metrics-reports/tasks.md`
- `odd/tasks/010-sales-metrics-reports.md`

No BFF implementation, OpenAPI, frontend, or Core changes are included in B-1.

### B-1 routing and verification

- Route: delegated test generation via `Test Generator (BFF)`; parent independently reran the focused tests and reviewed the auth/error fixtures.
- Risk: high; the tests cover public authorization and error-redaction behavior, without changing runtime behavior.
- Verification: exact `pytest -q tests/test_admin_sales_metrics.py` failed collection because the console entrypoint omitted the BFF root from `sys.path`; the venv runner with `PYTHONPATH=.` could not import missing `redis`. `PYTHONPATH=. pytest -q tests/test_admin_sales_metrics.py` collected successfully and produced 20 expected failures, all 405 from the generic OPTIONS-only catch-all on unregistered GET routes. All GraphQL requests were mocked; no database or network access occurred. No commit was made, per user instruction.

## Current Work Unit: BFF Metrics Routes

- [ ] B-2 Add proxy/service calls for metrics and categories.
- [ ] B-3 Add controller validation/error mapping and register both GET routes in `app.py`.

### Allowed edit surfaces for B-2/B-3

- `bgg-shop-bff/app.py`
- `bgg-shop-bff/src/proxy.py`
- `bgg-shop-bff/src/services.py`
- `bgg-shop-bff/src/controllers/admin_sales_controller.py`
- `bgg-shop-bff/src/controllers/__init__.py`
- `bgg-shop-bff/tests/test_admin_sales_metrics.py`
- `bgg-shop-bff/specs/010-sales-metrics-reports-tasks.md`
- `specs/010-sales-metrics-reports/tasks.md`
- `odd/tasks/010-sales-metrics-reports.md`

No Core or frontend edits are included in B-2/B-3.

### B-2/B-3 routing and verification

- Route: delegated direct implementation; proxy/service/controller/route-registration changes form one API behavior slice.
- Risk: high; public authorization, validation, and error-redaction behavior.
- Test-first evidence: B-1 collected successfully and all 20 tests received 405 from the unregistered-route catch-all.
- Verification: run `PYTHONPATH=. pytest -q tests/test_admin_sales_metrics.py` from BFF and any directly affected focused controller tests; all B-1 cases must pass. Calls to Core remain mocked; no database required.

### C-3 routing and verification

- Route: delegated direct implementation via `Python Entity Implementer`; parent independently reviewed category retrieval/authentication and reran the full suite.
- Risk: high; category data access and authorization are part of the public admin query.
- Verification: run the full Core sales-metrics PostgreSQL test module, syntax compilation, whitespace validation, and GraphQL schema parity; database checks use a fresh loopback-only disposable PostgreSQL container, never the active `saleor` database.

### C-2 routing and verification

- Route: delegated direct implementation via `Python Entity Implementer`, bounded to the Core resolver and metrics/filter tests; parent independently reviewed SQL/schema behavior and reran the focused tests.
- Risk: high; all integration checks must use a disposable loopback database, never the active `saleor` database.
- Test-first evidence: with a temporary local PostgreSQL 15 container and the safe DSN fixture, C-1 produced 18 expected failures because the Graphene query fields are not implemented.
- Verification: rerun `PYTHONPATH=. python -m pytest -q -p no:cacheprovider --tb=short tests/test_admin_sales_metrics_postgres.py -k 'not categories'` against an isolated temporary PostgreSQL container; don't mark C-2 complete unless the metrics/filter behavior tests pass.

## Constraints and Acceptance Criteria

- Core SDL defines `adminSalesMetrics` and `adminSalesCategories` with documented staff/superuser access, validation, time semantics, money basis, status rules, and error codes.
- BFF OpenAPI defines metrics and categories endpoints with documented inputs, response codes, non-cacheable behavior, and planned implementation status.
- Plan and service/global ledgers agree on both operations and contract validation precedes behavior implementation.
- Run only local checks; preserve pre-existing unrelated worktree changes.

## Work Units

- [x] X-1 Update both contracts and align the plan/task ledgers.
- [x] X-2 Parse and assert both contracts; record the BFF service-test script result separately.
- [x] X-3 Inspect the contract diff and run direct parent verification after the independent runner used a mismatched OpenAPI context.
- [x] C-1 Write failing Core PostgreSQL tests and observe expected RED.
- [x] X-5 Align paired date-range semantics in the contracts and plan.
- [x] C-1a Add tests for one-sided date ranges and observe expected RED.
- [x] C-2 Implement the Core metrics resolver and make its C-1 metrics/filter cases pass.
- [x] C-3 Implement the Core categories resolver and make its retrieval/authorization cases pass.
- [x] C-4 Review local EXPLAIN plans; no index justified by synthetic workload.
- [x] B-1 Write BFF sales-metrics tests and observe expected RED after successful collection.
- [ ] B-2..B-6 Implement and validate the BFF endpoints.
- [ ] F-1..F-6 Implement and validate the admin dashboard.
- [ ] V-1..V-3 Verify local results, security, and documentation.

## C-2 Routing and Verification

- Route: delegated direct implementation via `Python Entity Implementer`, bounded to the Core resolver and metrics/filter tests; parent independently reviewed SQL/schema behavior and reran the focused tests.
- Risk: high; the resolver includes authorization, input validation, SQL aggregation, and PostgreSQL behavior.
- Verification: run the focused metrics tests against a fresh loopback-only disposable PostgreSQL container; keep category cases for C-3 and do not use the active `saleor` database.

## Progress and Evidence

- Current state: X-5, C-1a, C-2, C-3, C-4, and B-1 are complete; B-2/B-3 are the next BFF work units. C-3 changed the Core Graphene resolver, its PostgreSQL test, and the authorized task ledgers. No controller, migration, or frontend implementation is included in Core.
- B-1 evidence: added 20 collected cases in `bgg-shop-bff/tests/test_admin_sales_metrics.py` covering both endpoints' auth and no-store behavior, staff/superuser access, date bounds/defaults, product-id parsing, repeated filters, and error redaction. The exact requested command failed collection due to import-path configuration; the successful `PYTHONPATH=.` run returned 20 expected 405 failures from the preflight-only fallback. The focused outcomes and environment limitations are in the BFF and global ledgers.
- Checks: PyYAML/OpenAPI and graphql-core/SDL parsing and shape assertions passed. `bash bgg-shop-bff/scripts/run_contracts.sh` exited 1 with 9 failed and 7 passed service tests, including unrelated `allow_redirects` mock mismatches and undefined `op_key` failures; full details are in the global evidence ledger.
- C-1 progress: added Core PostgreSQL GraphQL tests for metrics, dispatch/payment statuses, validation/authentication, and distinct categories. Category and product filtering are asserted independently and together. `python -m py_compile` passed. The focused run against an isolated local PostgreSQL 15 container produced 18 expected failures because Graphene lacks `adminSalesMetrics` and `adminSalesCategories`. The container was removed and the active `saleor` database was not used.
- X-5/C-1a evidence: both contract parsers and paired-bound assertions passed; Core test compilation passed. The focused run against fresh loopback-only PostgreSQL 15 produced 20 failed, 1 warning in 5.35s. A parent rerun reproduced 20 expected failures in 5.23s, with no collection or database setup errors; container cleanup was verified. A delegated execution verifier reported 20 errors without a traceback and is not accepted as behavior evidence. No behavior pass is claimed.
- C-2 evidence: the exact focused command `PYTHONPATH=. python -m pytest -q -p no:cacheprovider --tb=short tests/test_admin_sales_metrics_postgres.py -k 'not categories'` passed with 17 passed, 4 deselected, and 1 Django `USE_TZ` deprecation warning in 4.25s against a fresh loopback-only Podman PostgreSQL 15 container. A parent rerun passed 17 in 4.20s. `python -m py_compile saleor/graphql/api.py` and `git diff --check` passed. The parent's container remained after the command despite its exit trap; it was explicitly removed and absence verified. A delegated runner reported 20 setup errors without a traceback; the parent rerun reproduced the passing result.
- C-2 SDL check: the existing whole-schema parity test fails only because runtime lacks `adminSalesCategories`, reserved for C-3. A targeted comparison confirmed `adminSalesMetrics` return type, argument types/names, payload type fields, and description match the SDL. Category tests remain excluded and unimplemented.
- C-2 implementation: uses parameterized SQL with exact category/product array filters; paid revenue is matching line `subtotal`, order counts are distinct, top products use the required tie-break, daily revenue groups in UTC, and dispatch/payment counts filter on `created_at`.
- C-3 evidence: category-only RED was 4 failed, 17 deselected, 1 warning before implementation. The focused category run passed 5 tests (17 deselected, 1 warning). The delegated full command passed 22 tests in 4.73s; the parent rerun passed 22 in 5.04s with explicit `TEST_CONTAINER_CLEANUP=PASS`. A separate delegated verifier reported 22 skipped because its process lacked the DSN; that result is not accepted. Parent rerun passed with the DSN explicitly passed. `python -m py_compile saleor/graphql/api.py`, `git diff --check`, and schema parity passed; parity was confirmed to be schema-only and did not connect to PostgreSQL.
- C-3 implementation: `adminSalesCategories` uses the active staff/superuser guard and a static `SELECT DISTINCT category ... ORDER BY category`; stored strings remain unmodified. Tests cover ordering, duplicates, case/whitespace, inactive and unauthorized users, and superuser access.
- C-1 partial work-unit commits: orchestrator `4a7af5f542030b6be388289b6b5396d3f252a10c`; Core `c7f0b3c132264b2cf1279526abce5ffc46eda414`.
- C-1 discovery: runtime Graphene currently exposes neither `adminSalesMetrics` nor `adminSalesCategories`; the plan does not decide whether `revenueByDay` should zero-fill days without revenue, so the test documents that gap without asserting either behavior.
- Work-unit commits: orchestrator `4ebff3883e85bc222ccba260889e2138729f14df`; Core `b98a131da4ead699952e601f3af4f15e0a8416d6`; BFF `9c3924a7e290f4d92011685baf16970bfa078d04`.
- C-1 completion commits: orchestrator `a9a68426529d99d04b35fac5c118b7dad64bb1df`; Core `071c072c9571a94c04079bc65604a20cfab7419f`.
- X-5/C-1a work-unit commits: orchestrator `76531206b92a58215d17e0f36c8782cc81ce758c`; Core `590c9fac40f8a57224c07395f82588774c93a326`; BFF `0d86f13807134e3a8436409c08299f6fa4705da9`.
- C-2 work-unit commits: Core `b447261a93d6f127963646ea24874ea9a9eb487d`; orchestrator `717be40568313763f6c09f94f64aa8455871fe6c`.
- C-3 preparation commit: orchestrator `413a8df28a7520a550920df613b08b0ba17808a6`.
- C-3 implementation and verification commits: Core `5c7724ec875ba8076d486fe87cd88966d263413d`; orchestrator `ae0e724956aaf9a9c5d9a441cbf4eb30d7e10bf0`.
- C-4 query-plan review commits: Core `16fb5a92ee3dd642fec876638f096165a4c1e241`; orchestrator `8b777bf147bd6d0d0c6772c8cf96de561cd47be1`.
- Next step: B-2/B-3 implement the BFF proxy/service/controller routes that make the B-1 tests pass; keep the frontend and Core data layers within their existing scoped tasks.