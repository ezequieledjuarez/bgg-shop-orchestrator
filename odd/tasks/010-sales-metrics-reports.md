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

No resolver, controller, database schema, migration, or frontend implementation is included in this work unit.

### X-5 and C-1a routing and verification

- Route: delegated direct contract writer across Core and BFF; parent performs independent review and handles commit after review.
- Risk: high; these are public contracts and PostgreSQL integration tests.
- Verification: parse OpenAPI and SDL with paired-bound assertions, compile the Core test module, and run the focused tests against a fresh loopback-only PostgreSQL 15 container using the cached image; never use the active `saleor` database.

## Current Work Unit: Core Resolver

- [ ] C-2 Implement `adminSalesMetrics` in `bgg-shop-core/saleor/graphql/api.py` and make metrics/filter cases in C-1/C-1a pass; `adminSalesCategories` cases remain for C-3.

### Allowed edit surfaces for C-2

- `bgg-shop-core/saleor/graphql/api.py`
- `bgg-shop-core/tests/test_admin_sales_metrics_postgres.py`
- `bgg-shop-core/specs/010-sales-metrics-reports-tasks.md`
- `specs/010-sales-metrics-reports/tasks.md`
- `odd/tasks/010-sales-metrics-reports.md`

No controller, database schema, migration, or frontend implementation is included in C-2.

### C-2 routing and verification

- Route: delegated direct implementation; GraphQL resolver, SQL aggregation, authentication, and PostgreSQL test behavior span multiple concerns.
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
- [ ] C-2 Implement the Core metrics resolver and make its C-1 metrics/filter cases pass.
- [ ] C-3 Implement and test the Core categories resolver.
- [ ] C-4 Review the local query plan and record whether an index is justified.
- [ ] B-1..B-6 Implement and validate the BFF endpoints.
- [ ] F-1..F-6 Implement and validate the admin dashboard.
- [ ] V-1..V-3 Verify local results, security, and documentation.

## C-2 Routing and Verification

- Route: delegated direct implementation for the Core resolver and its integration tests.
- Risk: high; the resolver includes authorization, input validation, SQL aggregation, and PostgreSQL behavior.
- Verification: run the focused metrics tests against a fresh loopback-only disposable PostgreSQL container; keep category cases for C-3 and do not use the active `saleor` database.

## Progress and Evidence

- Current state: X-5 and C-1a are complete; C-2 is the sole current work unit. No resolver, controller, database, or frontend implementation is included in the completed work.
- Checks: PyYAML/OpenAPI and graphql-core/SDL parsing and shape assertions passed. `bash bgg-shop-bff/scripts/run_contracts.sh` exited 1 with 9 failed and 7 passed service tests, including unrelated `allow_redirects` mock mismatches and undefined `op_key` failures; full details are in the global evidence ledger.
- C-1 progress: added Core PostgreSQL GraphQL tests for metrics, dispatch/payment statuses, validation/authentication, and distinct categories. Category and product filtering are asserted independently and together. `python -m py_compile` passed. The focused run against an isolated local PostgreSQL 15 container produced 18 expected failures because Graphene lacks `adminSalesMetrics` and `adminSalesCategories`. The container was removed and the active `saleor` database was not used.
- X-5/C-1a evidence: both contract parsers and paired-bound assertions passed; Core test compilation passed. The focused run against fresh loopback-only PostgreSQL 15 produced 20 failed, 1 warning in 5.35s. A parent rerun reproduced 20 expected failures in 5.23s, with no collection or database setup errors; container cleanup was verified. A delegated execution verifier reported 20 errors without a traceback and is not accepted as behavior evidence. No behavior pass is claimed.
- C-1 partial work-unit commits: orchestrator `4a7af5f542030b6be388289b6b5396d3f252a10c`; Core `c7f0b3c132264b2cf1279526abce5ffc46eda414`.
- C-1 discovery: runtime Graphene currently exposes neither `adminSalesMetrics` nor `adminSalesCategories`; the plan does not decide whether `revenueByDay` should zero-fill days without revenue, so the test documents that gap without asserting either behavior.
- Work-unit commits: orchestrator `4ebff3883e85bc222ccba260889e2138729f14df`; Core `b98a131da4ead699952e601f3af4f15e0a8416d6`; BFF `9c3924a7e290f4d92011685baf16970bfa078d04`.
- C-1 completion commits: orchestrator `a9a68426529d99d04b35fac5c118b7dad64bb1df`; Core `071c072c9571a94c04079bc65604a20cfab7419f`.
- Next step: implement C-2 and rerun its metrics/filter cases on a disposable local PostgreSQL container.