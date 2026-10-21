# BGG Shop Orchestrator Constitution

## Purpose and authority

This constitution governs shared product behavior and cross-service coordination in the orchestrator repository. The five specifications under `specs/` are the canonical buyer-facing, as-built product baseline; they are not proposals to add excluded behavior.

The root constitution governs shared product and system behavior. A service constitution governs implementation within its own repository and cannot override the shared baseline. Service specifications and authoritative contracts describe their corresponding service scope. When requirements conflict, stop and resolve the conflict through an explicitly approved task before implementation.

## Principles

### 1. Preserve established behavior

Treat existing behavior, contracts, and documented compatibility as the baseline. No constitution automatically authorizes a retroactive behavior or contract change; a retrospective specification or completed task status does not authorize one either. Make a change only when an explicit task approves its scope and records the affected behavior.

### 2. Keep contracts and ownership explicit

Use `bgg-shop-bff/specs/openapi.yaml` as the BFF REST contract and `bgg-shop-core/specs/schema.graphql` as the Core GraphQL contract. Frontend API types are generated from the BFF OpenAPI file by `bgg-shop-frontend`'s `npm run generate:types`; do not create a competing contract or manually maintained generated-type copy. Keep shared product decisions here and implementation decisions in the responsible service.

### 3. Trace every change

For each approved change, maintain a trace from task and canonical requirement through affected service specifications, contract, implementation, tests, and documentation. Identify downstream consumers when a contract changes. Record verification commands and outcomes only after they have actually been run; a task marked complete is not test evidence.

### 4. Protect customers and service boundaries

Preserve established authentication, privacy, and data-integrity expectations. Public responses must not disclose upstream implementation details, exceptions, traces, internal URLs, or credentials. Keep service responsibilities and data transformations explicit rather than duplicating domain behavior across services.

### 5. Prefer the smallest safe change

Follow `.agents/ponytail.md`: use existing platform and project patterns, avoid unnecessary abstractions, and never trade away input validation, error handling, or security for brevity. Document verified behavior without duplicating the canonical or service-level specifications.

## Governance

An implementation change requires an explicitly scoped task and applicable requirement or specification. Contract changes require explicit approval, compatibility consideration, and downstream traceability before implementation. This constitution sets future governance; it does not itself approve or require retroactive changes. If an approved task conflicts with this constitution, resolve the conflict by an explicit constitution or task decision before proceeding.
