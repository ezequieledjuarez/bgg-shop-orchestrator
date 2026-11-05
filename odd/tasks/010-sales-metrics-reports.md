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

## Current Work Unit: Core Tests

- [ ] C-1 Write failing PostgreSQL tests for sales metrics and categories in `bgg-shop-core/tests/test_admin_sales_metrics_postgres.py`.

### Allowed edit surfaces for C-1

- `bgg-shop-core/tests/test_admin_sales_metrics_postgres.py`
- `bgg-shop-core/specs/010-sales-metrics-reports-tasks.md`
- `specs/010-sales-metrics-reports/tasks.md`
- `odd/tasks/010-sales-metrics-reports.md`

No resolver, controller, database schema, migration, or frontend implementation is included in C-1.

### C-1 routing and verification

- Route: delegated direct writer; test preparation requires mapping existing GraphQL/PostgreSQL test fixtures and a new test file.
- Risk: high; tests must use only a disposable local PostgreSQL database and must not apply migrations to an active database.
- Test-first check: `pytest -q tests/test_admin_sales_metrics_postgres.py` fails collection because the repo root is not on the entrypoint import path; `PYTHONPATH=. pytest -q tests/test_admin_sales_metrics_postgres.py` safely skips all 18 cases because `SALES_METRICS_TEST_POSTGRES_DSN` is absent. No behavior-test RED was observed.

## Constraints and Acceptance Criteria

- Core SDL defines `adminSalesMetrics` and `adminSalesCategories` with documented staff/superuser access, validation, time semantics, money basis, status rules, and error codes.
- BFF OpenAPI defines metrics and categories endpoints with documented inputs, response codes, non-cacheable behavior, and planned implementation status.
- Plan and service/global ledgers agree on both operations and contract validation precedes behavior implementation.
- Run only local checks; preserve pre-existing unrelated worktree changes.

## Work Units

- [x] X-1 Update both contracts and align the plan/task ledgers.
- [x] X-2 Parse and assert both contracts; record the BFF service-test script result separately.
- [x] X-3 Inspect the contract diff and run direct parent verification after the independent runner used a mismatched OpenAPI context.
- [ ] C-1 Write failing Core PostgreSQL tests.
- [ ] C-2 Implement the Core metrics resolver and make C-1 pass.
- [ ] C-3 Implement and test the Core categories resolver.
- [ ] C-4 Review the local query plan and record whether an index is justified.
- [ ] B-1..B-6 Implement and validate the BFF endpoints.
- [ ] F-1..F-6 Implement and validate the admin dashboard.
- [ ] V-1..V-3 Verify local results, security, and documentation.

## Routing and Verification

- Route: delegated direct writer for the two contract files plus their related plan/task ledgers; this crosses Core and BFF and needs contract-file preparation.
- Risk: high, because these are public service contracts.
- Verification: writer runs `bgg-shop-bff/scripts/run_contracts.sh`; a separate read-only verifier inspects the final diff and reruns the same command; parent spot-checks one reported result.
- Forecast: below 400 authored lines; delivery strategy `ask-on-risk`.

## Progress and Evidence

- Current state: contract work is complete; no resolver, controller, database, or frontend implementation is included here.
- Checks: PyYAML/OpenAPI and graphql-core/SDL parsing and shape assertions passed. `bash bgg-shop-bff/scripts/run_contracts.sh` exited 1 with 9 failed and 7 passed service tests, including unrelated `allow_redirects` mock mismatches and undefined `op_key` failures; full details are in the global evidence ledger.
- C-1 progress: added Core PostgreSQL GraphQL tests for metrics, dispatch/payment statuses, validation/authentication, and distinct categories. Category and product filtering are asserted independently and together. `python -m py_compile tests/test_admin_sales_metrics_postgres.py` passed. Plain `pytest -q ...` fails collection because `saleor` is not on the entrypoint import path; `PYTHONPATH=. pytest -q ...` safely reports 18 skipped because `SALES_METRICS_TEST_POSTGRES_DSN` is absent. No behavior-test RED was observed; C-1 remains unchecked until the isolated loopback database is configured and the expected missing-field failures are observed.
- C-1 discovery: runtime Graphene currently exposes neither `adminSalesMetrics` nor `adminSalesCategories`; the plan does not decide whether `revenueByDay` should zero-fill days without revenue, so the test documents that gap without asserting either behavior.
- Work-unit commits: orchestrator `4ebff3883e85bc222ccba260889e2138729f14df`; Core `b98a131da4ead699952e601f3af4f15e0a8416d6`; BFF `9c3924a7e290f4d92011685baf16970bfa078d04`.
- Next step: configure `SALES_METRICS_TEST_POSTGRES_DSN` for a loopback disposable database/role matching `sales_metrics_test_<uuid>`, rerun the Core tests to observe expected RED, then implement C-2.