# Normalizing service specification directories

## Objective

Group the remaining flat service-owned feature plans, notes, and task ledgers
under their corresponding feature directories, repair stale references, and
commit the scoped documentation changes in the existing local feature branches.

## Scope and constraints

- Move CU-A01 legacy task ledgers under each service's
  `specs/006-manage-catalog-inventory/` directory.
- Group the Core/BFF/Frontend CU-A01 responsibilities and implementation
  artifacts under `specs/007-manage-catalog-inventory/`, preserving separate
  legacy and current task ledgers.
- Group Core/BFF/Frontend CU-A02 ledgers under
  `specs/010-sales-metrics-reports/`.
- Move Core's original OpKeys notes into its existing
  `specs/008-operations-keys-auth/` directory and update references.
- Keep Core `specs/schema.graphql`, BFF `specs/openapi.yaml` and its repair
  backups, root feature artifacts, and unrelated worktree changes untouched.
- Update only references affected by the relocations and the root layout guide.
- Work locally on the existing `docs/unify-feature-specs` branches; no push.

## Acceptance criteria

- Every service-owned feature note/plan/task file listed above resides under a
  service feature directory.
- Stale CU-A01 links target the canonical root spec or the correct feature
  plan; all links altered by moves resolve.
- No feature evidence is merged or discarded; task ledgers with different
  purpose remain distinguishable.
- Authoritative contracts, unrelated files, and existing worktree changes are
  preserved.
- Local link validation and `git diff --check` pass in all four repositories.
- Each repository's scoped changes are committed with a Conventional Commit.

## Verification

- Validate moved relative Markdown links and changed inbound references.
- Review each repository's staged file list before committing.
- Run `git diff --check` in the root, Core, BFF, and Frontend repositories.
- Confirm each work-unit commit contains only authorized paths.

## Progress

- Authorized by the user to apply the pertinent layout corrections and commit.
- Implementation route: direct documentation changes across the root, Core,
  BFF, and Frontend repositories.
- Existing `docs/unify-feature-specs` branches are active in all four repos.
- Risk tier: passive documentation; structural readback and link verification
  are proportionate.
- Moved the named ledgers, CU-A01 documents, and Core 008 notes into their
  feature directories with `git mv`; kept Core `specs/schema.graphql`,
  BFF `specs/openapi.yaml`, backups, root canonical feature artifacts, and
  unrelated worktree changes untouched.
- Repaired local links in the moved docs and changed the authorized inbound
  references in `odd/tasks/010-sales-metrics-reports.md` and
  `odd/tasks/admin-contract-first.md`. Updated `specs/README.md` to document
  feature grouping, legacy ledgers, service-only notes, and flat contracts.
- Link check: a Python local-Markdown-link resolver checked 26 local links in
  16 moved documents; all targets existed. Scoped search found no stale
  responsibility headers or old moved filenames in the edited references.
- Structural readback confirmed the new Core, BFF, and Frontend feature
  directory contents. `git diff --check` passed in root, Core, BFF, and
  Frontend.
- Inbound-reference limit: repository-wide search also found
  `odd/tasks/manage-catalog-inventory-frontend.md:4` still naming
  `specs/007-manage-catalog-inventory-frontend.md`. That file is outside the
  authorized edit surfaces, so it remains unchanged and needs separate
  authorization to repair.
- No functional tests were run; this change only reorganizes and corrects
  documentation paths. The unchanged product spec and authoritative contracts
  remain `specs/006-manage-catalog-inventory/spec.md`,
  `bgg-shop-core/specs/schema.graphql`, and `bgg-shop-bff/specs/openapi.yaml`.
- Service commits (scoped staged-path reviews passed before commit):
  - Core: `93a28c3df3d70f533182125a3216e12b95a42086`
  - BFF: `00b6caf005c88c2bcd926c9c17faa96cc90779cd`
  - Frontend: `a540f1f15ae2033d08253a69573b1acf7f1fcc48`
- Root changes and this evidence update are staged for the separate root
  documentation commit; record its observed hash in the final report.
