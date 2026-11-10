# Local validation and acceptance evidence

## Boundary

The feature is implemented. The planning-era sections below retain their original
historical scope and future-target wording; they are not current execution
evidence. See **Scoped correction verification** for the latest observed results.
This is not a deployment guide. All checks are local. Never read/source `.env`,
`.local` connection/auth files, SMTP credentials or runtime container environments.
Do not install dependencies, pull images, contact Gmail, send external email,
migrate an existing database or use main-stack compose for tests.

## Planning checks (safe now)

From any directory, using the existing interpreter and installed packages:

```bash
python -c 'from pathlib import Path; import yaml; from openapi_spec_validator import validate; from graphql import build_schema, validate_schema; r=Path("/home/eze/develop/boardgame-app"); d=yaml.safe_load((r/"bgg-shop-bff/specs/openapi.yaml").read_text()); validate(d); assert not validate_schema(build_schema((r/"bgg-shop-core/specs/schema.graphql").read_text())); print("PASS: canonical OpenAPI and Core SDL")'
git -C /home/eze/develop/boardgame-app --no-pager diff --check
git -C /home/eze/develop/boardgame-app --no-pager status --short
```

These imports do not import application settings or initialize Django/BFF. Validate `$ref`s locally; never resolve external references over the network.

The feature directory is untracked at authoring time; `git diff --check` alone does not inspect it. Also run `git diff --no-index --check -- /dev/null <absolute-planning-file>` for each generated file. Exit status 1 from an actual diff is not by itself a whitespace failure; inspect diagnostics. Do not stage anything merely to inspect the diff.

## Future contract-first prerequisites (NOT run)

1. Approve proposals and update the two owning canonical contracts, then validate full OpenAPI/SDL, BFF GraphQL request documents, error/status/header mappings and generated types. Existing installed `graphql-core`/OpenAPI tooling is sufficient for structural checks; no dependency install needed.
2. Run `npm --prefix /home/eze/develop/boardgame-app/bgg-shop-frontend run generate:types` from the canonical OpenAPI only. Compile/typecheck consumers; never edit generated definitions manually.
3. Add proposed tests/fixtures from [plan](plan.md). New test filenames below do not exist yet; commands are future targets, not claims of runnable/passing feature tests.

## Hermetic test prerequisites

- Core `saleor/settings.py` unconditionally calls `environ.Env.read_env(.../.env)`. Merely setting DATABASE_URL or a DSN does **not** prevent this read. Never invoke current Core tests/manage.py directly under the present no-env boundary.
- Add `tests/email_verification_settings.py` as an explicit **independent minimal test settings module**, without importing `saleor.settings` or reading files. Provide dummy test signing/service values from fixtures, locmem mail, auth/contenttypes/sessions/Graphene/OpKeys as needed, and only the validated disposable DB configuration. Audit import-time configuration in BFF too; stub dotenv entrypoints before imports if necessary.
- Existing refresh tests launch subprocesses importing default `saleor.settings`; a parent monkeypatch will not protect those subprocesses. Run those regressions only with a reviewed hermetic subprocess harness; do not blindly run the whole current refresh suite.
- Install nothing. Check already installed Python dependencies, frontend node_modules and local browser binary availability. Missing prerequisites mean BLOCKED, not permission to install or use remote infrastructure.
- Block outbound sockets in unit tests; allow only expressly selected loopback PostgreSQL and optional isolated Mailpit during integration. Fake sender must simulate accepted, rejected, timeout and unknown submission without opening SMTP sockets.

Future focused command patterns, **after** the hermetic fixtures/new tests are implemented:

```bash
cd /home/eze/develop/boardgame-app/bgg-shop-core
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/eze/develop/boardgame-app/bgg-shop-core/tests:/home/eze/develop/boardgame-app/bgg-shop-core DJANGO_SETTINGS_MODULE=email_verification_settings python -m pytest -q -p no:cacheprovider tests/test_email_verification.py tests/test_email_verification_postgres.py
cd /home/eze/develop/boardgame-app/bgg-shop-bff
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/eze/develop/boardgame-app/bgg-shop-bff python -m pytest -q -p no:cacheprovider tests/test_email_verification.py tests/test_services_email_verification_contract.py
cd /home/eze/develop/boardgame-app/bgg-shop-frontend
./node_modules/.bin/vitest run src/auth/AuthScreens.test.tsx src/auth/EmailVerificationScreen.test.tsx
```

The PostgreSQL suite additionally requires the guarded DSN provision below. Existing BFF and frontend auth/current-user/refresh/OpKey/cart regressions must also run under the same audited no-env/no-outbound rules. Vite test configuration can read dotenv files: use a reviewed isolated test mode/config with env loading disabled, not an assumption that ordinary `vitest` is secret-free. Do not execute the command patterns until those prerequisites are met.

## Disposable PostgreSQL only (future, not provisioned)

Reuse the safety policy of `bgg-shop-core/tests/test_user_permissions_postgres.py`: DSN must parse as PostgreSQL, host exactly `127.0.0.1`, explicit port, nonempty newly generated test password, no query/fragment, and matching `user_permissions_test_<32-hex>` database/role. Reject a bad present DSN before connecting; never fall back to settings/default DB. Use `USER_PERMISSIONS_TEST_POSTGRES_DSN` for that existing suite, and the same guard for the new verification integration suite.

Choose a dedicated disposable container/loopback port, or the pre-existing isolated reviews configuration **only after** checking it is unused and dedicated. Never touch `saleor_db`, main PostgreSQL volumes/network/ports, or the persistent parallel DB created by `scripts/create_parallel_database.py`. Do not run that script: it reads private config/runtime secrets and switches persistent application infrastructure.

Prerequisites for later provisioning: local Podman tooling, already cached PostgreSQL image, isolated owned container/network/volume, fresh generated role/database credentials held only in the test process and guarded DSN. No image pull, host data mount or import of `import_catalog.sql` (it contains unrelated catalog/admin seeds). Do not run existing broad E2E scripts blindly; they are references for isolation, not feature runners.

Construct auth tables with real Django schema/migrations, not `auth_user(id)` skeletal review fixtures. Verify current database/user/schema before any DDL. Each test schema is random, with explicit search_path excluding public; cleanup only the schema/container/role/database this run demonstrably created. Apply relevant migration dependencies in this owned fixture; migrating the entire existing graph requires its baseline domain schema and must not be assumed runnable on an empty database.

Migration test coverage: legacy backfill customers/staff/superusers/disabled, unchanged role/password/activation/session records, null historic verified_at, registration cutover, rollback safety, real PK/FK/length/index metadata, and failure rollback. Concurrency must use independent PostgreSQL connections and barriers with bounded timeouts. SQLite or mocked transactions cannot prove single-use/replacement/window correctness.

## Future local acceptance walkthrough

1. Use fake/locmem captured messages for ten fresh registrations; record counts, not raw proofs. Each gets pending instructions; zero credentials/session/cookies and zero cart merges before verification.
2. Open link GET/HEAD/preview; assert no POST, account mutation or proof consumption. Capture fragment and replace browser history before telemetry; no token in persistent storage/referrers/logs. Explicit button POST verifies once, does not login; then password login works.
3. Execute C01–C18 in [contract matrix](contracts/README.md). Inject clock just before/exact/after expiry, cooldown and rolling-window cutoffs; test casing, reload, parallel workers and persisted counter restart. Verify Retry-After matches ceiling caller wait.
4. Race two confirms, resend against confirm and two resends. Inspect committed DB state/side effects, not only responses.
5. Simulate rejection, timeout, post-commit process failure and lost responses; same neutral resend acknowledgment, pending recovery, no hidden retries or restored old proof.
6. Test legacy policy and every pending credential bypass path, including synthetic access JWT, opaque refresh subject and privileged/user-bound OpKeys.
7. Walk through pending/success/unusable outcomes with five participants; at least four identify the next action without help. Report anonymous counts, not invented usability success.

Optional later Mailpit validation needs separately approved isolated local listener/ports and disabled relay, with dummy sender credentials only. Do not connect now. Gmail's future roughly ten-message demo needs new authorization for configuration/connectivity/sends; passing local capture does not prove Gmail delivery.

## Observed authoring checks

- Setup script returned feature 016 paths with explicit directory override; selector unchanged.
- Installed tooling discovery found PyYAML, graphql-core, pytest, Django and openapi-spec-validator; no installs.
- Standalone OpenAPI 3.2.0 validation accepted the draft; YAML duplicate-key check passed, 50 local references resolved and 16 examples passed JSON Schema validation. One deliberately invalid `<VERIFICATION_TOKEN>` example was excluded from value validation.
- GraphQL build/validate returned no schema errors; the example document containing both mutations validated, and six unchanged auth type signatures matched the canonical SDL. This is structural validation, not current runtime Core conformance.
- All seven generated files were read back; 29 relative Markdown links resolved, and 16 functional requirements / seven success criteria / 18 contract cases were traced. Every documented response resolved to a no-store header.
- `git diff --check` and per-file no-index whitespace checks passed after correcting Markdown trailing spaces. Example validation also caught and corrected a YAML flow-mapping comma in the neutral resend example.
- Final status retained the same pre-existing dirty/untracked root surfaces, plus planning files inside feature 016. Core remained clean and BFF retained its pre-existing untracked `.pytest-tmp/`. No selector, canonical contract, service code or agent-context file was edited.
- No feature runtime, migration, browser, SMTP, Mailpit or real-delivery outcome is claimed. Checklist runtime acceptance remains pending.

## Scoped correction verification

The following supersedes the historical planning-only execution status above.
One scoped correction addressed two independently reported regressions:

1. Malformed confirmation requests no longer bypass the Core caller quota.
   The BFF sends a fixed empty GraphQL String for every invalid token, including
   missing, non-string, oversized and extra-field request bodies. No raw malformed
   value is sent upstream, logged or echoed. The Core performs its usual atomic
   counting and returns the same generic invalid response or caller throttling.
2. The isolated user-permissions fixture now applies migration 0021 and gives
   its synthetic pre-feature users `LEGACY_EXEMPT` sidecars with null
   `verified_at`. The actual registration test asserts `PENDING`, null
   `verified_at` and authentication ineligibility; it never uses that fixture
   exemption.

Observed RED, before the corresponding fixes:

- BFF `tests/test_email_verification.py -k malformed_confirm`: **13 failed**.
- Core `tests/test_email_verification_postgres.py -k bff_malformed`:
  **1 failed**, observing zero invalid-attempt rows instead of ten.
- Core `tests/test_user_permissions_postgres.py`: **23 failed, 1 passed**.

Observed final GREEN commands (from the respective service directories):

```bash
# Both DSNs were supplied inline to this process, never read from secret files.
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests:. DJANGO_SETTINGS_MODULE=email_verification_settings SALEOR_SKIP_DOTENV=1 \
  EMAIL_VERIFICATION_TEST_POSTGRES_DSN="$EMAIL_VERIFICATION_TEST_POSTGRES_DSN" \
  USER_PERMISSIONS_TEST_POSTGRES_DSN="$USER_PERMISSIONS_TEST_POSTGRES_DSN" \
  python -m pytest -q -p no:cacheprovider \
  tests/test_email_verification.py tests/test_email_verification_postgres.py \
  tests/test_opkeys_internal.py tests/test_graphql_auth.py \
  tests/test_auth_refresh.py tests/test_auth_refresh_integration.py \
  tests/test_user_permissions_postgres.py
# 278 passed, zero skipped; includes all 24 user-permissions and 39 feature PG cases.

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m pytest -q -p no:cacheprovider \
  tests/test_email_verification.py tests/test_services_email_verification_contract.py \
  tests/test_auth.py tests/test_auth_current_user.py tests/test_refresh_proxy.py \
  tests/test_refresh_integration.py tests/test_services_openapi_contract.py \
  tests/test_services_graphql_contract.py tests/test_cart.py
# 128 passed, zero skipped.

./node_modules/.bin/vitest run --config vitest.email-verification.config.ts
# 349 passed across 35 files.
./node_modules/.bin/tsc -b
# Exit 0.
```

DSN evidence: both used `postgresql`, `127.0.0.1:55998`, a synthetic test-only
password, no query/fragment, and matching role/database names
`email_verification_test_cb9e84a905e14722a15436c45b49b740` and
`user_permissions_test_cb9e84a905e14722a15436c45b49b740`. A new owned container
`ev016_correction_cb9e84a905e14722a15436c45b49b740` used cached
`docker.io/library/postgres:15` with `--pull=never`; no main-stack database was
used. Each test owned an isolated schema. Zero leftover test schemas were
observed in both databases. The container was removed and removal verified;
credentials were never persisted in a file.

The new BFF adapter → actual Core GraphQL → PostgreSQL test proves exactly ten
invalid attempts, the eleventh returning a 900-second wait, no further event
while throttled, no valid-token consumption by the exhausted caller, caller
isolation, and acceptance at the exact 900-second boundary.

MigrationExecutor now loads the dependency graph with the existing
`saleor.promotions` app enabled only for that test. Ancestors through 0020 are
explicitly faked because the pre-feature commerce baseline is not provisioned;
0021 alone is really applied, recorded, checked as idempotently planned, and
reversed. Legacy/disabled backfill and new pending registration are asserted.
This is not evidence that every historical commerce migration executes from an
empty database. An initial graph test exposed the missing promotions app in
the hermetic test configuration; the test-local app override resolved it
without changing baseline migrations or application settings.

Two added tests exercise Django's actual SMTP backend against an owned
stdlib TCP capture on an ephemeral `127.0.0.1` port: acceptance yields
`SUBMITTED`, rejection yields `UNCONFIRMED`, and logs contain neither recipient
nor token. All listener sockets and threads are closed. No Mailpit/Gmail,
external SMTP connection, external mail delivery or provider acceptance is
claimed. SMTP credentials/sender configuration still require explicit user
configuration and external-send authorization.

Canonical OpenAPI validation and full Core SDL build/validation passed again.
BFF GraphQL request validation is included above; contracts were not changed in
this correction. `git diff --check` passed in root and all three services, and
new feature files passed no-index whitespace checks. Existing Python
`utcnow` deprecation warnings and frontend MSW/React `act` warnings remain;
there were no failing or skipped final tests.

The independent verifier's earlier full local browser/Core/BFF flow passed
using locmem delivery; it was not rerun in this correction. SC-005 participant
study remains unavailable without participants. No commits, dependency
installations, image pulls, persistent database operations or secret-file reads
were performed. The unrelated pre-existing JWT/opaque-refresh mismatch was not
changed.
