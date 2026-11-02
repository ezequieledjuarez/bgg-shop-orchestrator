# Spec 007 Stock UI

## Objective

Complete the next approved Spec 007 stock slice (Core C-2 and Frontend F-3)
without changing the existing stock API contract or touching unrelated work.

## Problem and rationale

Core already implements UUID-bound stock movements, partial reductions to zero,
atomic audit/result persistence, retries and status lookup. The administrative
frontend has no usable stock-adjustment control; product editing currently
exposes stock as a normal product field even though the approved update contract
does not permit quantity updates.

## Scope and constraints

- Add an accessible admin stock-adjustment flow for IN and OUT using the
  approved BFF endpoints and one UUID bound to the exact movement payload.
- Preserve unresolved movement identity across page reloads. A request/HTTP
  failure is uncertain: do not claim rollback, generate a replacement UUID, or
  retry automatically. Let the administrator explicitly check status or retry
  the exact same payload.
- Show requested and applied quantities; overstock OUT must report its partial
  application to zero. Keep a zero-stock product visible with the exact label
  `Sin stock`.
- Keep initial quantity entry on product creation, but do not submit quantity
  as a field update when editing.
- Do not change BFF/Core contracts, reservation behavior, promotions, or other
  Spec 007 tasks. Do not modify the active database or contact remote services.
- Preserve all existing dirty worktree changes; do not stage or commit.
- The user authorized adding only
  `bgg-shop-frontend/src/types/generated/bff-api.d.ts` to the implementation
  surfaces if needed to synchronize existing OpenAPI stock types. Inspect its
  pre-existing diff first; regenerate through the package script and stop if
  local edits cannot be safely preserved.

## Tasks and checks

- [x] SUI-1 — Add the admin stock adjustment interface and component tests for
  IN, partial OUT to zero, retry/status recovery with the same UUID, uncertain
  responses, and zero-stock visibility. Independent review corrections enforce
  the BFF integer maximum, refresh ProductForm inventory after confirmed
  movements, and prevent overwriting an unresolved per-product movement.
  - Route: delegated writer. Trigger: UI, integration and test changes touch
    multiple non-trivial files.
  - Risk: medium; writer runs focused Frontend tests/build and parent performs
    a focused spot check.
- [x] SUI-2 — Verify Core stock guarantees with the focused PostgreSQL suite
  and update the Spec 007 task evidence for C-2/F-3.
  - Route: direct verification and documentation.
  - Checks: focused stock PostgreSQL tests, focused Frontend tests, typecheck/
    build, `git diff --check`.

## Acceptance criteria

- Stock movement request is exactly the approved product ID, direction,
  positive integer quantity and UUID.
- On uncertainty, the UI retains the UUID and full payload, clearly communicates
  that the result is unknown, and offers explicit status lookup/retry without
  changing the UUID or automatically replaying.
- Successful movement feedback reports requested/applied quantity and final
  stock; OUT beyond available stock is described as partial-to-zero.
- Editing product details cannot change stock through the product update call.
- At zero stock, the product remains visible and displays `Sin stock`.
- Applicable local checks pass; any unavailable check or failure is recorded.

## Progress and evidence

- 2026-11-02: Existing Core code and PostgreSQL tests show movement UUID
  identity, replay after later stock changes/new DB connection, partial OUT to
  zero, changed-identity rejection, concurrency, audit atomicity, and recovery
  across BFF/Core. The current edit form exposes quantity, but the admin stock
  UI is not implemented. `ProductsList.tsx`, `ProductsList.test.tsx`,
  `App.tsx`, API client, BFF and OpenAPI files already contain unrelated
  user-owned edits and are outside the writer's allowed surfaces.
- 2026-11-02: Writer added the stock adjustment panel and updated the edit form,
  regenerated OpenAPI types after explicit user authorization, and reported
  10 focused Frontend tests, build, lint, and diff checks passing. Parent
  reran the focused Frontend tests (10 passed). Core PostgreSQL stock movement
  tests passed (21 passed, 113 deselected); temporary DB and role were removed
  and verified absent. Independent review reran focused Frontend tests (10)
  and build successfully and found three in-scope issues recorded under SUI-1.
- 2026-11-02: Regression tests for the three review findings were observed
  failing first (RED); after correction, the focused suite passed (13 tests)
  and the production build passed. The review findings were: quantity above
  the API maximum could leave an unrecoverable pending ID; confirmed results
  did not refresh the parent stock display; and an already-open tab could
  overwrite another tab's pending movement. The fix validates `2147483647`
  before ID allocation, updates displayed stock only from the server result,
  checks for stored pending work before allocation and before persistence, and
  refuses to overwrite an existing unresolved movement.
- 2026-11-02: Core's focused PostgreSQL stock-movement suite passed 21 tests
  (113 deselected); its temporary database and role were removed and verified
  absent. Root Spec 007 evidence was updated. `git diff --check` passed.
- The same review found `AdminUpdateProductRequest` generated types still allow
  `quantity`, because OpenAPI expresses its exclusion using `not` over a shared
  product-fields schema. Correcting this generated contract typing requires
  changing the BFF OpenAPI source, which is not an authorized SUI-1 edit
  surface. Keep this discrepancy open; do not hand-edit generated output or
  change the contract in this task.
- Engram recovery mirror: unavailable in this session; pending.

## Next step

SUI-1/SUI-2 implementation and focused checks are complete. F-3 remains partial
pending a browser E2E run through BFF/Core; C-2 remains partial pending
late-replay and indefinite-retention evidence. Correct the generated update
type only after separately authorizing an OpenAPI contract change.
