# Establish Spec Kit constitutions across four repositories

## Objective

Replace the four placeholder Spec Kit constitutions with a shared governance baseline and repository-specific rules for the orchestrator, Core, BFF, and Frontend.

## Problem and rationale

All four repositories contain Spec Kit assets, but their constitutions are still templates. The workspace already has five canonical end-to-end as-built specifications and fifteen service-level as-built specifications. The adoption should govern future changes without duplicating those documents or changing existing behavior.

## Scope and constraints

- Update the four `.specify/memory/constitution.md` files and this ODD tracking record.
- Preserve root canonical specifications, service-level specifications, OpenAPI, GraphQL SDL, application code, tests, and generated Frontend types.
- Keep shared product and cross-service governance in the orchestrator constitution.
- Keep Core, BFF, and Frontend rules local to each repository's verified responsibilities and authoritative contract.
- Treat existing behavior as the compatibility baseline; constitution principles do not retroactively authorize behavior or contract changes.
- Preserve unrelated untracked files and do not publish changes.

## Authorized edit scope

- `.specify/memory/constitution.md`
- `bgg-shop-core/.specify/memory/constitution.md`
- `bgg-shop-bff/.specify/memory/constitution.md`
- `bgg-shop-frontend/.specify/memory/constitution.md`
- `odd/tasks/spec-kit-constitutions-four-repos.md`

## Tasks

### CONSTITUTION-1 — Establish shared and repository-specific governance

- [x] Replace all four placeholder constitutions with concise, evidence-based principles tailored to the repository roles.
- [x] Define the precedence and compatibility rule: root governs shared product/cross-service behavior; each service governs its local implementation; contract changes require explicit approval and downstream traceability.
- [x] Retain the existing root canonical and service-level specifications and authoritative contract/generation boundaries.

**Route:** Delegated direct. The four constitutions require cross-repository context and coordinated wording.

**Risk tier:** High/unclear because the constitutions establish governance for future work. Require writer verification and an independent read-only review.

**Acceptance criteria:**

- None of the four constitutions contains template placeholders.
- Each constitution identifies its repository scope and names only verified or explicitly agreed guardrails.
- Shared principles are consistent, while service-specific rules remain within that service's responsibility.
- Existing specifications, contracts, implementation, tests, and generated types are unchanged.
- The update clearly states that existing behavior remains the compatibility baseline unless a task explicitly approves a change.

**Verification:**

- Structural readback of all four constitutions.
- Search confirms no constitution template placeholders remain.
- `git diff --check` passes in each repository.
- Verify referenced specification and contract paths exist.
- Confirm only the four constitution files and this task record are changed.
- No application tests are applicable because the change is documentation-only.

## Progress and evidence

- Initial inspection: all four constitutions are unmodified Spec Kit templates.
- Initial Git state: all four repositories are on branch `CU-05`; multiple unrelated untracked files and directories exist and must remain untouched.
- Existing SDD baseline: five canonical root specifications and fifteen derived service specifications are already present.
- Estimated authored change: approximately 220 lines across four constitutions and this task record.
- Delivery strategy: `ask-on-risk` (default); no chain strategy is currently required by the estimate.

## Progress and verification

- Writer update and verification completed. The four constitution files are:
  - `.specify/memory/constitution.md`
  - `bgg-shop-core/.specify/memory/constitution.md`
  - `bgg-shop-bff/.specify/memory/constitution.md`
  - `bgg-shop-frontend/.specify/memory/constitution.md`
- Traceability reviewed against canonical specs `specs/001-authentication-as-built/spec.md` through `specs/005-checkout-orders-invoice-as-built/spec.md`; service specs `bgg-shop-{core,bff,frontend}/specs/001-*` through `005-*`; contracts `bgg-shop-core/specs/schema.graphql` and `bgg-shop-bff/specs/openapi.yaml`; implementation areas `bgg-shop-core/saleor/graphql/`, `bgg-shop-bff/src/controllers/`, and `bgg-shop-frontend/src/`; and tests under `bgg-shop-core/tests/`, `bgg-shop-bff/tests/`, and `bgg-shop-frontend/src/`.
- Verification observed: the requested Python placeholder/trailing-whitespace check passed; referenced paths exist; Frontend `generate:types` points to the BFF OpenAPI file; and `git diff --check` passed in all four worktrees as a supplemental tracked-worktree check. Constitution files are untracked, so `git diff --check` does not inspect them.
- Application tests were not run; this is a documentation-only change and no contract or application source was changed.
- Independent read-only review found one task-record scope inconsistency: the scope said only the constitutions could change, while the authorized edit list included this record. Corrected the scope statement to include the tracking record.
- The independent reviewer found no substantive constitution or contract-ownership defects; compatibility rules and referenced paths were verified.
- Final parent verification after the scoped task-record correction passed: no constitution placeholders or trailing whitespace; all 20 root/service specs and contract/type paths exist; task scope and authorized edit surfaces agree. `git diff --check` passed in all four repositories.
- Independent review found no substantive constitution or contract-ownership defects. The task-record scope inconsistency was corrected and rechecked.
- No application tests were run because this documentation-only change does not alter executable behavior.

## Completion

- CONSTITUTION-1 is complete. The four constitutions define shared authority and service-specific governance without changing existing behavior, contracts, application code, tests, or generated types.
- Work-unit commits on the existing `CU-05` branches:
  - Orchestrator: `d637ffa` — `docs(spec-kit): establish shared constitution`
  - Core: `e8083f6` — `docs(spec-kit): define Core constitution`
  - BFF: `c7f6794` — `docs(spec-kit): define BFF constitution`
  - Frontend: `2078da8` — `docs(spec-kit): define Frontend constitution`
- All commits are local. No remote operations are authorized or planned.
