# CU-C01 Layered Flask BFF

## Objective
Refactor the complete Flask BFF into minimal DTO, controller, and service
layers while preserving all current REST and GraphQL behavior.

## Scope
- Keep `/health`, authentication, and paginated/filtered product routes.
- Add DTOs, controllers, and services for authentication and catalog flows.
- Keep `app.py` focused on Flask setup and route registration.
- Preserve OpenAPI payloads, status codes, error redaction, CORS, and GraphQL
  variable/response mappings.
- Update focused tests and CU-C01 documentation.

## Constraints
- Do not change the Core service or Frontend.
- Do not add dependency injection, generic repositories, or mapper hierarchies.
- Preserve unrelated existing worktree changes.

## Tasks
- [x] map-bff-layering: document current route and proxy responsibilities.
- [x] define-bff-layers: add minimal DTO, service, and controller modules.
- [x] refactor-bff-routes: delegate Flask routes through controllers.
- [x] update-bff-tests-docs: align tests and CU-C01 documentation.
- [x] verify-layered-bff: run focused BFF checks and inspect the diff.

## Acceptance criteria
- Existing BFF tests remain green.
- `/health`, `/api/v1/auth/register`, `/api/v1/auth/login`, and
  `/api/v1/products` preserve their current responses and error behavior.
- Authentication and catalog logic are no longer concentrated in `app.py`.
- Controllers own HTTP concerns; services own orchestration; DTOs own typed
  request/response data.

## Verification
- `cd bgg-shop-bff && python -m pytest`
- `cd bgg-shop-bff && python -m compileall -q app.py src tests`
- Structural review of changed files and route imports.

## Progress
- Route: delegated direct writer; multiple non-trivial BFF modules are involved.
- Status: implemented and verified.
- Verification: `python -m pytest` — 19 passed; `python -m compileall -q
  app.py src tests` — passed; `git diff --check` — passed.
- Work-unit commit: `95b1a31` (`refactor(bff): layer Flask request handling`).

## Sectioning follow-up

- Split controllers into `src/controllers/` by resource.
- Split REST DTOs into `src/dtos/` with classes for authentication and product
  contract shapes.
- Verification: `python -m pytest` — 19 passed; compileall and diff checks
  passed.
