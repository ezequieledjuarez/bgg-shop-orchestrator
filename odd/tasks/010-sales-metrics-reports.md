# ODD Task Record — 010-sales-metrics-reports

## Objective

Define the sales metrics and category-filter contracts in both Core and BFF before implementing service behavior.

## Problem and Why

The feature plan described only the main metrics operation, while the feature task lists also required category retrieval. The user confirmed that category retrieval belongs in this contract work and asked to record a reusable rule to evaluate endpoint coverage in both service contracts.

## Authorized Scope

- `specs/010-sales-metrics-reports/plan.md`
- `specs/010-sales-metrics-reports/tasks.md`
- `bgg-shop-core/specs/schema.graphql`
- `bgg-shop-core/specs/010-sales-metrics-reports-tasks.md`
- `bgg-shop-bff/specs/openapi.yaml`
- `bgg-shop-bff/specs/010-sales-metrics-reports-tasks.md`
- `odd/tasks/010-sales-metrics-reports.md`

No resolver, controller, database, or frontend implementation is authorized in this work unit.

## Constraints and Acceptance Criteria

- Core SDL defines `adminSalesMetrics` and `adminSalesCategories` with documented staff/superuser access, validation, time semantics, money basis, status rules, and error codes.
- BFF OpenAPI defines metrics and categories endpoints with documented inputs, response codes, non-cacheable behavior, and planned implementation status.
- Plan and service/global ledgers agree on both operations and contract validation precedes behavior implementation.
- Run only local checks; preserve pre-existing unrelated worktree changes.

## Work Units

- [x] X-1 Update both contracts and align the plan/task ledgers.
- [x] X-2 Parse and assert both contracts; record the BFF service-test script result separately.
- [x] X-3 Inspect the contract diff and run direct parent verification after the independent runner used a mismatched OpenAPI context.

## Routing and Verification

- Route: delegated direct writer for the two contract files plus their related plan/task ledgers; this crosses Core and BFF and needs contract-file preparation.
- Risk: high, because these are public service contracts.
- Verification: writer runs `bgg-shop-bff/scripts/run_contracts.sh`; a separate read-only verifier inspects the final diff and reruns the same command; parent spot-checks one reported result.
- Forecast: below 400 authored lines; delivery strategy `ask-on-risk`.

## Progress and Evidence

- Current state: contract work is complete; no resolver, controller, database, or frontend implementation is included here.
- Checks: PyYAML/OpenAPI and graphql-core/SDL parsing and shape assertions passed. `bash bgg-shop-bff/scripts/run_contracts.sh` exited 1 with 9 failed and 7 passed service tests, including unrelated `allow_redirects` mock mismatches and undefined `op_key` failures; full details are in the global evidence ledger.
- Next step: begin Core implementation task C-1 in a separate work unit.