# SDD Agent Capabilities

## Objective

Update existing Copilot agents and related workspace instructions so they have accurate repository context, supported minimum tool access, and reproducible procedures to close the identified SDD evidence gaps. CI/CD remains excluded.

## Problem and rationale

Existing agent guidance contains stale framework/spec references, nonstandard execution tool names, and responsibilities that require checks the agents cannot run. In particular, contract validation, review-flow tests, PostgreSQL E2E evidence, safe error handling, and documentation traceability need clear ownership.

## Scope and constraints

- Update existing root, Core, BFF, and Frontend agents and the related workspace instructions identified in the approved session plan. Core agent scope is `.github/agents/python-entity-implementer.agent.md`, `.github/agents/graphql-contract-planner.agent.md`, and `.github/agents/test-generator-agent.md` inside `bgg-shop-core`.
- Do not implement the underlying contract/test changes, create new agents by default, or modify CI/CD configuration/agent.
- Use documented Copilot tool aliases and least-privilege tool lists.
- Preserve unrelated untracked files and changes; only stage/commit exact authorized paths.
- Worktree starts on branch `CU-3`; do not change branches or publish.
- Engram full-task mirror is pending/unverified; this file remains the detailed local recovery record.

## Tasks

### SDDAG-1 — Correct existing agent ownership and repository guidance

- [x] Assign existing agents to the contract, Core/BFF/Frontend testing, QA, security evidence, and traceability responsibilities.
- [x] Correct BFF Flask/Python and Core Graphene guidance, actual spec paths, frontend agent references, and stale tool names.

### SDDAG-2 — Add actionable verification capability

- [x] Give only execution-dependent validator, test, and QA agents supported `execute` access; planning and static-review roles retain read-only access.
- [x] Specify repository-grounded REST/OpenAPI and GraphQL SDL/Graphene contract checks and generated frontend type verification.
- [x] Specify focused Core/BFF/Frontend tests and PostgreSQL E2E prerequisites, commands, and required evidence.

### SDDAG-3 — Strengthen safe-error and traceability guidance

- [x] Require controlled public error envelopes and tests that reject upstream/internal detail leakage.
- [x] Require documentation updates to cross-reference specs, implementation, tests, task status, and observed verification evidence.

### SDDAG-4 — Validate customization changes

- [x] Validate frontmatter/tool aliases and referenced paths/commands.
- [x] Confirm only authorized customization files changed and CI/CD remains untouched.

## Acceptance criteria

- Every applicable SDD gap has an existing agent owner and explicit evidence procedure.
- Agents that run checks can execute them; planning-only roles retain least-privilege access.
- Framework, contract path, script, and agent references match the repository.
- Agent guidance covers OpenAPI/BFF, GraphQL SDL/Graphene, generated types, focused tests, PostgreSQL E2E, safe error responses, and traceability.
- No CI/CD or pipeline files are modified.

## Verification evidence

- Structural readback of each modified Markdown customization and its YAML frontmatter.
- Search/read verification that referenced paths and commands exist.
- Diff/status check scoped to the authorized customization files; verify CI/CD files are unchanged.
- Functional service tests are not applicable to instruction-only changes.

## Progress and next step

- Approved plan: update existing agents and related workspace instructions; CI/CD excluded.
- Renamed the existing documentation agent to `.github/agents/documentation-agent.agent.md` so its filename matches the documented custom-agent discovery pattern; repository search found no references to the former filename.
- Initial worktree check: all four repositories are on branch `CU-3`; the root has pre-existing untracked `CasosDeUso.md`, `README.MD`, and the nested frontend repository, which must be preserved.
- Implementation route: delegated direct, because the task modifies multiple non-trivial customization files.
- Risk tier: high/unclear because adding command-execution capability changes agent authority; independent verification is required.
- Completed SDDAG-1 through SDDAG-3 by updating the existing agents and related workspace instructions; no new agent or CI/CD file was added.
- Repository evidence: BFF is Flask/Python with `specs/openapi.yaml`; Core is Django/Graphene with `specs/schema.graphql`; frontend has `generate:types`, `test`, `test:report`, `build`, and `lint` scripts. The root `podman-compose.yaml` defines PostgreSQL with a persistent named volume, but that does not establish an isolated disposable E2E database. No existing frontend browser E2E runner was found.
- PostgreSQL E2E remains conditional on a disposable isolated database and an implemented full-stack test; QA guidance requires reporting it as `NO EJECUTADA` when either prerequisite is absent.
- Engram full-task mirror: pending/unverified because the memory write capability was unavailable in this runtime; this file retains the detailed task and verification state.
- Verification: all four requested repository `git diff --check` commands exited 0 after the scoped corrections; `python3` with PyYAML parsed the 11 agent frontmatters and two instruction frontmatters and validated documented tool aliases; stale BFF entrypoint and former documentation-agent path searches returned no matches; corrected files were read back. The initial parser attempt used unavailable `python`, and the first `python3` attempt had one incorrect Frontend test-agent path; the corrected `python3` command passed.
- Scope check: only authorized customization paths changed; CI/CD agent and pipeline files remain untouched. Existing root untracked files were preserved. No functional service tests were run because the edits affect guidance only.
- Runner discovery: both service virtual environments lack pytest, and neither requirements file lists it; QA and test guidance reports these tests as not executed until a project-provided test environment supplies the runner.
- Independent review found and corrected three material issues: the BFF validator pointed at a FastAPI stub instead of the Flask `app.py`; the task record missed the root Compose file and its persistent database volume; and the documentation agent filename did not match the documented `*.agent.md` discovery pattern.
- Post-correction parent verification: all four `git diff --check` commands exited 0; the corrected route, Compose evidence, and documentation-agent filename were read back; no `src/app.py` or former documentation-agent path references remain in workspace customizations.
- No functional service tests were run because these edits change agent guidance only; service pytest runners were also unavailable in the local service environments.
- Engram full-task mirror remains pending/unverified because the memory write capability was unavailable in this runtime.
- Next: complete the authorized work-unit commits using only the changed agent/instruction/task paths, then record commit IDs here.
