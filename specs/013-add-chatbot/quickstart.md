# Feature 013: safe local verification record

> **Administrative status (2026-11-07):** T030/T032 are closed at the user's request; validation gaps were waived for task closure only. This is not a verified acceptance report. SC-001 and SC-007 were not executed, live OpenRouter authentication was not tested, and the unrelated BFF contract result remains unresolved (**7 passed, 9 failed**). Any further evidence collection is optional and does not block the administrative closure; see [tasks.md](tasks.md#administrative-task-closure-2026-11-07).

This is a record of locally observed commands and their limits, not a clean acceptance report. Run commands only from the repository root and only against local fixtures. Do not use CI, staging, production, remote services, real personal/order data, or a non-disposable database. Do not print or copy environment secrets. Do not install dependencies or contact package registries.

The optional `OPENROUTER_API_URL` defaults, when unset, to
`https://openrouter.ai/api/v1/chat/completions`. Only that exact URL is accepted:
an empty value or any other URL disables the OpenRouter attempt and uses the
existing local Ollama fallback. If both providers fail, the public error remains
sanitized. No change to FAQ retrieval, guardrails, or the API contract is required.

## Container chat configuration

The root [Podman startup instructions](../../README.MD#inicio-local-con-podman-compose)
start the local stack. Before creating containers, the user must provision
`CHAT_ASSERTION_SECRET`: a shared, high-entropy secret dedicated to chat identity
assertions. Compose passes the same setting to BFF and Core. Do not reuse
`OPKEY_INTERNAL_SECRET`, an OpenRouter API key, or a Django secret; do not commit
or print credentials. The empty Compose default deliberately keeps the existing
fail-closed behavior, so conversation creation remains unavailable without it.

The BFF receives `CHAT_REDIS_URL` pointing to the Compose Redis service on
database 2, separate from the Core cache and Celery broker. Redis must be
available for chat rate limiting. Optional `OPENROUTER_API_KEY` and
`OPENROUTER_MODEL` are passed through; `OPENROUTER_API_URL` defaults to the
official endpoint described above. Missing credentials retain local fallback,
not an authenticated OpenRouter connection.

`CHAT_EMBEDDING_MODEL` defaults to `embeddinggemma`, the model used in the
earlier local checks recorded below; it must already be pulled into the
reachable Ollama instance. `CHAT_CHROMA_DIR` uses `/app/.local/approved-faq-chroma`,
persisted through the existing BFF `/app` bind mount. The BFF Dockerfile installs
Redis, LangChain Chroma, and LangChain Ollama from `requirements.txt`; an older
image may still need rebuilding if those dependencies are absent.

The approved local Compose topology runs the official Ollama image on a
dedicated `chat-models` bridge shared only with the BFF. The BFF also stays on
the default Compose network for Core and Redis. Ollama listens on
`0.0.0.0:11434` inside its container only; the Compose service publishes no host
port and persists model files in the named `ollama_models` volume. The provider
accepts this exact internal endpoint (`http://ollama:11434`, optionally with a
trailing slash) in addition to its existing loopback HTTP(S) URLs. Other
non-loopback hosts, including `host.containers.internal`, remain rejected. This
is local deployment configuration, not a public BFF/API contract change.

After starting the stack, pull `embeddinggemma` manually with the command in
the root startup instructions; Compose does not pull models on startup.
`deepseek-r1:8b` remains the configured local answer fallback and must also be
pulled manually if it is not already present. To verify service reachability
and real embedding generation locally, run the root README's BFF-container
checks for `/api/tags` and `/api/embed`.

Changing root environment settings or Compose entries does not inject them into
existing containers with a plain restart. Applying this Ollama endpoint and
network change requires recreating the BFF, not Core, without resetting volumes
or migrating the existing database.

**Local connectivity verification (2026-11-10):** After owner approval, Ollama
was created and `embeddinggemma` was pulled into its persistent volume
(621 MB). BFF and its dependent frontend container were recreated; no database
or existing volume was reset. From the BFF, `/api/tags` returned the embedding
model and `/api/embed` returned one 768-dimensional vector. Approved FAQ
indexing and retrieval using real Ollama embeddings and temporary Chroma
storage returned one document; the temporary storage was cleaned up. Ollama
had no published host port, and BFF catalog and frontend checks returned HTTP
200. Provider/startup/service regressions passed with **64 tests**; a parent
provider/startup repeat passed with **41 tests**. No live OpenRouter generation
or HTTP conversation exchange was exercised. The new Ollama volume does not
yet contain `deepseek-r1:8b`, so local answer fallback remains unavailable until
that separate model is pulled.

## Focused passing checks

| Purpose | Command | Observed outcome and limit |
|---|---|---|
| OpenRouter endpoint configuration | `cd bgg-shop-bff && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. .venv/bin/python -m pytest -q -p no:cacheprovider --tb=short tests/test_chatbot_provider.py tests/test_chatbot_openrouter_integration.py tests/test_chatbot_local_startup.py` | **47 passed, 22 warnings.** Synthetic credentials and mocked requests cover the default and exact configured URL, rejection without a remote call, local fallback, and sanitized failure. Live OpenRouter validation was not performed; no `.env` file or external service was accessed. It is an optional evidence follow-up, not a task blocker. |
| Local Chroma retrieval/index regression | `cd bgg-shop-bff && PYTHONPATH=. .venv/bin/python -m pytest -q --tb=short tests/test_chatbot_service_local.py` | **1 passed** after fixing the Chroma `where` filter. Test uses actual installed Chroma with temporary persistence and deterministic in-process embeddings; it verifies approved FAQ retrieval, update, and withdrawal. `CHAT_EMBEDDING_MODEL` remains unset, so production Ollama embeddings are not covered. |
| BFF chatbot regression selection | `cd bgg-shop-bff && PYTHONPATH=. .venv/bin/python -m pytest -q --tb=short tests/test_chatbot_service_integration.py tests/test_chatbot_rag.py tests/test_chatbot_guardrails.py tests/test_chatbot_privacy.py tests/test_chatbot_catalog.py tests/test_chatbot_conversations.py tests/test_chatbot_service_local.py` | **82 passed, 111 warnings.** Includes the real local Chroma test; other deterministic fake-backed RAG cases remain complementary. |
| Historical provider smoke (before `embeddinggemma` was downloaded) | Direct local `OllamaChatProvider` invocation and grounded `ApprovedFaqRag` invocation with a synthetic approved document using Ollama `deepseek-r1:8b` | **Passed at that earlier point.** This historical run predated the embedding model pull and did not test Ollama embedding generation. |
| Full direct BFF path with real Ollama embeddings (not HTTP E2E) | Explicit process environment: `CHAT_EMBEDDING_MODEL=embeddinggemma CHAT_OLLAMA_BASE_URL=http://127.0.0.1:11434`. Root `.env` has `CHAT_EMBEDDING_MODEL=embeddinggemma`, but `bgg-shop-bff/app.py` does not load dotenv, so direct BFF launchers must pass these settings into the process environment. | **Passed:** real Ollama embedding generation, approved FAQ indexing into temporary Chroma, Spanish approved-payment-FAQ retrieval, grounded `deepseek-r1:8b` answer, and expected source attribution. This exercised the direct BFF service path, not BFF/Core HTTP E2E. |
| BFF integration, RAG, guardrails, privacy | `cd bgg-shop-bff && PYTHONPATH=. pytest -q tests/test_chatbot_service_integration.py tests/test_chatbot_rag.py tests/test_chatbot_guardrails.py tests/test_chatbot_privacy.py` | **64 passed, 0 failed, 87 warnings.** Tests around lines 205–265 of `bgg-shop-bff/tests/test_chatbot_service_integration.py` assert invalid/refused inputs make zero answer/provider/Core calls and that provider failures expose sanitized responses; the catalog guard test is around lines 281–293. |
| BFF guardrails, privacy, RAG, catalog, conversations | `cd bgg-shop-bff && PYTHONPATH=. pytest -q tests/test_chatbot_guardrails.py tests/test_chatbot_privacy.py tests/test_chatbot_rag.py tests/test_chatbot_catalog.py tests/test_chatbot_conversations.py` | **69 passed, 0 failed, 99 warnings.** RAG tests include updated/withdrawn sources and deleted files; the catalog focused tests pass within this selection. The RAG tests use deterministic fakes, not local Chroma. |
| T031 English/Spanish parity focused verification | `cd bgg-shop-bff && PYTHONPATH=. .venv/bin/python -m pytest -q --tb=short tests/test_chatbot_service_integration.py tests/test_chatbot_guardrails.py tests/test_chatbot_privacy.py tests/test_chatbot_rag.py tests/test_chatbot_catalog.py` | **117 passed, 181 warnings in 3.01s** on parent spot-check. An independent review found no high-confidence regressions and independently ran the same command: **117 passed, 181 warnings in 2.99s**. These deterministic focused tests cover the ten fixed English/Spanish cases required by FR-012/SC-008: grounded FAQ, refusal, clarification, insufficient-evidence/unavailable fallback, and catalog recommendation (one each per language), with privacy/safety assertions in the focused set. The warnings are the existing `datetime.datetime.utcnow()` deprecation at `bgg-shop-bff/app.py:196`. |
| Pure greeting routing follow-up (2026-11-09) | `cd bgg-shop-bff && PYTHONPATH=. .venv/bin/python -m pytest -q --tb=short tests/test_chatbot_guardrails.py tests/test_chatbot_service_integration.py tests/test_chatbot_privacy.py tests/test_chatbot_rag.py tests/test_chatbot_catalog.py tests/test_chatbot_openrouter_integration.py` | **154 passed, 206 existing deprecation warnings in 7.17s.** The added tests cover exact-match English/Spanish introductions, punctuation and accents, safe checks preceding greetings, no provider/Core persistence for a pure greeting, and grounded retrieval for a greeting plus a shop question. Initial targeted RED was **10 failed, 71 passed** before implementation. The API response shape and canonical contracts are unchanged. |
| T031 actual FAQ model smoke (separate from focused tests) | Parent ran the actual FAQ service with local Ollama, temporary Chroma persistence, `CHAT_EMBEDDING_MODEL=embeddinggemma`, and `CHAT_OLLAMA_BASE_URL=http://127.0.0.1:11434`, using `deepseek-r1:8b`. | **Passed for FAQ only:** `¿Qué medios de pago acepta la tienda?` received a Spanish answer and `What payment methods does the store accept?` received an English answer; both returned approved source `Preguntas Frecuentes` (`http://localhost:3030`). The temporary directory was automatically cleaned. This does not verify guardrail or catalog behavior with a real model. |
| T032 OpenRouter-primary/local fallback tests | `cd bgg-shop-bff && PYTHONPATH=. .venv/bin/python -m pytest -q --tb=short tests/test_chatbot_provider.py tests/test_chatbot_service_local.py tests/test_chatbot_service_integration.py tests/test_chatbot_rag.py` | Writer observed RED before implementation (new fallback class missing), then GREEN: **51 passed, 12 warnings**. Independent review and parent spot-check each reran the command with **51 passed, 12 warnings**. OpenRouter requests are mocked with synthetic credentials; no `.env` file or external service was accessed. A review alert about the Authorization value was a false positive caused by output redaction; AST inspection confirmed it is built from `OPENROUTER_API_KEY`. Live credential validation was not performed; it is an optional follow-up after T032's administrative closure. |
| T032 local fallback E2E (2026-11-07) | One-off direct `create_local_chatbot_service` invocation from `bgg-shop-bff`; explicit process environment only, with no dotenv load | **Passed:** loopback Ollama tags showed `embeddinggemma:latest` and `deepseek-r1:8b`. The process used `CHAT_EMBEDDING_MODEL=embeddinggemma`, `CHAT_OLLAMA_BASE_URL=http://127.0.0.1:11434`, and synthetic `OPENROUTER_API_KEY` / `OPENROUTER_MODEL` values. Monkeypatched `src.chatbot.provider.requests.post` raised one synthetic `requests.ConnectionError`; no OpenRouter connection was attempted. With approved sources `knowledge/approved`, temporary Chroma, and question `¿Qué medios de pago acepta la tienda?`, the service returned a real local `deepseek-r1:8b` answer attributed to `Preguntas Frecuentes`. Process exited 0 and temporary Chroma was cleaned up. This verifies the direct service flow through local Ollama and Chroma only, not frontend/Core HTTP E2E; live OpenRouter credential/auth validation was not performed. No `.env` was accessed, no secret was displayed/transmitted, and no external request was made. Trace: `specs/013-add-chatbot/tasks.md` T032, `specs/013-add-chatbot/plan.md` approved provider decision, `bgg-shop-bff/src/chatbot/provider.py`, `bgg-shop-bff/src/chatbot/service.py`, and tests `bgg-shop-bff/tests/test_chatbot_provider.py`, `bgg-shop-bff/tests/test_chatbot_service_local.py`, `bgg-shop-bff/tests/test_chatbot_service_integration.py`, `bgg-shop-bff/tests/test_chatbot_rag.py`. |
| Frontend chatbot tests | `cd bgg-shop-frontend && npm test -- --run src/chatbot` | **12 passed**, with **3 React `act(...)` warnings**. |
| Frontend source attribution | `cd bgg-shop-frontend && npm test -- --run src/chatbot/Chatbot.test.tsx` | **6 passed**, with React `act(...)` warnings. An independent verifier reran this command and the browser command below with the same passing results; a parent spot-check also passed 6/6. |
| Deterministic Chromium browser flow | `cd bgg-shop-frontend && E2E_OPKEY_ISOLATED=true npx playwright test tests/e2e/chatbot.spec.ts --project=chromium` | **7 passed.** `bgg-shop-frontend/tests/e2e/chatbot.spec.ts` intercepts `/api/v1/**` with deterministic route mocks and blocks external hosts. This proves frontend states only; it does not verify Core owner enforcement, persisted ownership, or database expiry/retention. |
| Core chat tests with disposable PostgreSQL | `cd bgg-shop-core && python -m pytest -q --tb=short tests/test_graphql_chat.py` | **25 passed, 0 skipped, 1 Django warning in 11.23s.** Run with a unique loopback-only `CHAT_CONVERSATION_TEST_POSTGRES_DSN` matching `chat_conversation_test_<32hex>`, supplied externally in the command environment. The fixture verifies DB/user identity, applies the auth and full migration graph in a per-test unique schema, asserts the chat migration/tables, and drops the schema in teardown. This verifies Core-to-PostgreSQL ownership/retention behavior, not an HTTP BFF/Core E2E. |
| Historical BFF/Core HTTP conversation flow (superseded by corrected proof below) | Disposable Core/BFF servers, PostgreSQL 15, Redis, temporary Chroma, and local Ollama; no checked-in harness or standalone reproduction command | **Passed:** create 201; real grounded FAQ reply 200 with source; owner history contained user and assistant messages; another cookie received 404; delete returned 204; owner read after deletion returned 404. This earlier flow did not verify HTTP-mediated expiry/retention or catalog integration. All temporary containers, servers, Chroma data, and the isolated BFF log were removed; dedicated ports were free; active Saleor containers remained running. |

## Failed, skipped, and unavailable checks

- BFF contract tests: `cd bgg-shop-bff && bash scripts/run_contracts.sh` reported **7 passed, 9 failed**. Observed failures are existing non-chatbot product/cart/coupon/checkout/wishlist/order tests. Error classes included test mocks rejecting unexpected `allow_redirects` and `NameError: op_key is not defined`. Baseline and cause are not established; these failures were not fixed or treated as pre-existing.
- Invalid Core migration check: `cd bgg-shop-core && python manage.py makemigrations --check --dry-run` exited 0 and printed `No changes detected`, but Django attempted a migration-history connection to a configured non-loopback database and the connection was refused. Treat this check as invalid; do not retry against that database. It does not invalidate the successful isolated Core database suite above.
- Historical non-venv LangChain/Chroma/Ollama import probe: `cd bgg-shop-bff && python -c 'import langchain, langchain_chroma, langchain_ollama; print("LangChain, Chroma, and Ollama integrations import locally")'` failed because `langchain` was missing from that interpreter. The requirements already declare these integrations. No installation or package-registry access was attempted. This limitation is superseded for the BFF `.venv`: the local Chroma regression and separate `deepseek-r1:8b` provider smoke above passed.
- Historical BFF/Core HTTP flow: verified anonymous create/record/history, grounded answer/source attribution, cross-owner denial, and deletion. It did not cover expiry/retention or catalog integration; the corrected proof below supersedes those gaps. **Historical, superseded T031 observation:** the initial Spanish HTTP question (`¿Qué medios de pago acepta la tienda?`) was refused before retrieval, while the successful HTTP question used English and retrieved the Spanish approved FAQ. T031 later added bilingual guardrail coverage in focused deterministic tests; no HTTP/model guardrail claim is made. Playwright API calls remain intercepted, and the running Saleor application stack and its database were not used or touched.

## Traceability and task outcome

- Spec: [`spec.md`](spec.md), especially the approved guardrail, retrieval, provider, catalog, ownership, retention, and browser requirements.
- BFF implementation/tests: `bgg-shop-bff/src/chatbot/guardrails.py`, `rag.py`, `provider.py`, `service.py`, `catalog.py`, `bgg-shop-bff/src/controllers/chatbot_controller.py`; tests under `bgg-shop-bff/tests/test_chatbot_*.py`.
- Core implementation/tests: `bgg-shop-core/tests/test_graphql_chat.py`.
- Frontend implementation/tests: `bgg-shop-frontend/src/chatbot/` and `bgg-shop-frontend/tests/e2e/chatbot.spec.ts`.
- Task ledger: [`tasks.md`](tasks.md). T013 is complete for focused guardrail/privacy behavior; T014 is complete for deterministic local Chroma regression; T015 is complete for scoped local provider/RAG behavior. Root `.env` is not loaded by `app.py`; direct launchers must pass `CHAT_EMBEDDING_MODEL` and other required settings in the process environment. T019's focused BFF tests pass; the corrected local HTTP proof provides bounded BFF/Core catalog integration evidence. T029 remains limited to mocked browser routes. Core DB-backed retention tests and the corrected HTTP/runner proof provide scoped retention evidence. T030/T032 are administratively closed; SC-001/SC-007 and live authentication are unverified, and full-stack acceptance is not claimed. T031 bilingual parity is complete for focused tests; no HTTP/model guardrail claim is made.

## Latest local Chroma/provider reconciliation (2026-11-07)

- Test-first RED: Chroma 1.5.9 rejected the flat filter with `Expected where to have exactly one operator`.
- Fix: `bgg-shop-bff/src/chatbot/service.py` now expresses approved and active metadata as a `$and` conjunction.
- GREEN: the focused Chroma regression passed **1/1**, exercising approved FAQ retrieval, update, and withdrawal against the real installed Chroma vector store with temporary persistence and deterministic embeddings.
- Chatbot regression command above passed **82 tests, 111 warnings**. The earlier local Ollama `deepseek-r1:8b` direct and grounded-answer smoke passed before `embeddinggemma` was downloaded; that historical smoke did not test embeddings.
- T014/T015 are complete for their scoped acceptance: the deterministic embedding Chroma test verifies retrieval/index synchronization, and the later full direct BFF path exercised real Ollama embeddings and the approved Spanish payment FAQ flow. Root `.env` contains `CHAT_EMBEDDING_MODEL=embeddinggemma`, but `app.py` does not load dotenv; a direct BFF launcher must pass it in the process environment. The corrected BFF/Core HTTP proof now verifies bounded ownership/expiry, retention-runner, and catalog behavior. T030 is administratively closed; SC-001/SC-007 remain unexecuted. The BFF contract suite still reports **7 passed, 9 failed**, with causes and baseline unknown.

The earlier outcomes above preserve previously observed evidence. For the earlier update, the local Chroma test-first RED, focused GREEN, chatbot regression, and provider-smoke results were observed before `embeddinggemma` was downloaded; the no-model-pull note applies only to that historical point. The later full direct BFF path successfully used real Ollama embeddings and temporary Chroma as recorded above. This documentation correction made no BFF/Core database operation, runtime, app-container, `.env`, package, remote, deployment, or commit change.

## Latest Core disposable PostgreSQL reconciliation (2026-11-07)

The full `bgg-shop-core/tests/test_graphql_chat.py` suite was rerun against a fresh disposable PostgreSQL 15 container bound only to `127.0.0.1:15432`. The test database and role each used a unique random name matching `chat_conversation_test_<32hex>` and a unique generated synthetic password. The DSN was passed only in the command environment; no credential, database/role instance name, or static DSN is recorded. Reproduce with a unique loopback-only `CHAT_CONVERSATION_TEST_POSTGRES_DSN` matching that naming pattern and the exact command in the table.

The fixture verified DB/user identity, applied the auth and complete migration graph in a unique schema per test, asserted the chat migration and tables, and dropped the schema in teardown. The command passed **25 tests, 0 skipped, 1 Django warning in 11.23s**. Covered behavior includes Core assertion identity/ownership, cross-owner denial, deletion, 30-day inactivity access behavior, and physical purge. No container remained with label `feature=013-chat-conversation-test`; all pre-existing app containers remained running and untouched.

This Core suite verifies Core-to-PostgreSQL behavior. The corrected BFF/Core HTTP proof below separately verifies bounded ownership/expiry and retention-runner behavior. The running Saleor stack uses the normal application database/services and was not touched. The earlier Core result of 18 passed and 7 skipped is superseded as the current result; it may be read only as historical. The migration-check attempt above remains invalid.

## Historical isolated BFF/Core HTTP validation (superseded)

A one-off local harness started Core and BFF against disposable PostgreSQL 15 and Redis containers bound only to loopback, with PostgreSQL data on tmpfs, a unique schema, synthetic secrets, temporary Chroma persistence, and local Ollama at `127.0.0.1:11434`. Core dotenv loading was disabled for the isolated process and the BFF launcher used `FLASK_SKIP_DOTENV=1`; no root `.env`, existing Saleor container, application database, or remote service was used.

Observed HTTP outcomes: anonymous conversation creation returned 201; a real grounded answer from the approved FAQ returned 200 with source attribution; owner history returned both persisted messages; a second anonymous cookie received 404; owner deletion returned 204; and a subsequent owner read returned 404. The message path used real Ollama `embeddinggemma` embeddings, temporary Chroma, and `deepseek-r1:8b`. **Historical, superseded T031 observation:** the first Spanish query was blocked before retrieval; the successful HTTP request used an English prompt and retrieved the approved Spanish FAQ. T031 later verified bilingual guardrail behavior with focused deterministic tests. This earlier HTTP run was not repeated for guardrail behavior, and the later actual-model FAQ smoke does not verify guardrails.

Cleanup removed the isolated BFF/Core processes, PostgreSQL and Redis containers, temporary Chroma data, and unique BFF log. The dedicated ports were free and all active Saleor containers remained running. This historical run established HTTP ownership/persistence/deletion only; the corrected proof below adds bounded expiry/retention-runner and catalog integration evidence. SC-001/SC-007 remain unverified; T030 was later administratively closed without claiming full acceptance.

## T031 local verification reconciliation (completed)

T031 is complete for the ten fixed bilingual test cases in `specs/013-add-chatbot/spec.md` FR-012/SC-008: grounded FAQ, guardrail refusal, guardrail clarification, insufficient-evidence/unavailable fallback, and catalog recommendation, with one English and one Spanish case per scenario. The description-only OpenAPI change adds no routes, request/response fields, status codes, security changes, or limits. Test coverage is in `bgg-shop-bff/tests/test_chatbot_rag.py`, `bgg-shop-bff/tests/test_chatbot_guardrails.py`, and `bgg-shop-bff/tests/test_chatbot_catalog.py`; safety/privacy coverage also runs in `bgg-shop-bff/tests/test_chatbot_privacy.py` and `bgg-shop-bff/tests/test_chatbot_service_integration.py`. Relevant implementation paths are `bgg-shop-bff/src/chatbot/guardrails.py`, `bgg-shop-bff/src/chatbot/rag.py`, `bgg-shop-bff/src/chatbot/catalog.py`, and `bgg-shop-bff/src/controllers/chatbot_controller.py`.

The exact focused command was run and passed on parent spot-check:

```bash
cd bgg-shop-bff && PYTHONPATH=. .venv/bin/python -m pytest -q --tb=short tests/test_chatbot_service_integration.py tests/test_chatbot_guardrails.py tests/test_chatbot_privacy.py tests/test_chatbot_rag.py tests/test_chatbot_catalog.py
```

Observed result: **117 passed, 181 warnings in 3.01s**. An independent code review found no high-confidence regressions and independently ran the same command: **117 passed, 181 warnings in 2.99s**. The reviewer verified that the Spanish charge-dispute example is refused before answer-service/persistence and that Spanish and English child-audience recommendation requests receive localized clarification without catalog queries. Authenticated requests do a Core identity lookup before classification; no general claim that all authenticated guardrails make zero Core calls is made. The warnings are the existing `datetime.datetime.utcnow()` deprecation at `bgg-shop-bff/app.py:196`.

Separate actual FAQ service smoke evidence: local Ollama with temporary Chroma persistence, `CHAT_EMBEDDING_MODEL=embeddinggemma`, `CHAT_OLLAMA_BASE_URL=http://127.0.0.1:11434`, and `deepseek-r1:8b` returned a Spanish answer for `¿Qué medios de pago acepta la tienda?` and an English answer for `What payment methods does the store accept?`; both returned approved source `Preguntas Frecuentes` (`http://localhost:3030`). The temporary directory was automatically cleaned. This does not claim real-model verification for guardrails/catalog scenarios.

SC-001 and SC-007 remain unverified; T030/T032 are administratively closed with validation waivers, not acceptance. The unrelated BFF non-chatbot contract suite remains **7 passed, 9 failed**, with unknown baseline/cause. The earlier non-loopback migration check is invalid and must not be retried. See [`tasks.md`](tasks.md) for the task ledger and evidence limits.

## Explicit local BFF startup and offline OpenRouter integration (013-I)

Delivery verification independently reran the focused ten-module selection: **165 passed, 215 warnings in 7.49s**. Launcher syntax and root/BFF whitespace checks passed. Parent startup/OpenRouter integration spot-check: **24 passed, 22 warnings in 4.17s**. These are offline checks, not live OpenRouter credential validation or full-stack acceptance.

For authorized local use, run the launcher from any working directory:

```bash
/path/to/boardgame-app/bgg-shop-bff/scripts/run_local.sh
```

The launcher resolves the BFF and orchestrator directories relative to itself, uses the existing BFF `.venv/bin/python`, and invokes Flask with `--env-file /path/to/boardgame-app/.env --app app:app run --host 127.0.0.1 --port 5000`. It never shell-sources the file. Exported environment settings take precedence. `FLASK_SKIP_DOTENV=1` disables implicit `.env`/`.flaskenv` discovery while preserving the explicit `--env-file` load. This uses Flask 3.0-compatible options; isolated startup tests passed on both Flask **3.0.0** and the installed **3.1.3**. `python-dotenv>=1.0.0` is declared explicitly; installed `python-dotenv` was **1.2.4**, so no dependency installation was needed.

`python app.py` remains unchanged and still requires exported process settings; importing the app does not automatically load dotenv. Earlier direct-launch environment instructions in this document describe that path, not the new explicit launcher. Configure `CHAT_EMBEDDING_MODEL` to a pulled local Ollama embedding model and `CHAT_OLLAMA_BASE_URL` to its loopback endpoint. Ollama must remain available for embeddings even when OpenRouter successfully generates the answer. `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` select the primary answer provider; `deepseek-r1:8b` remains the local answer fallback.

Offline verification command:

```bash
cd bgg-shop-bff && PYTHONPATH=. .venv/bin/python -m pytest -q --tb=short tests/test_chatbot_local_startup.py tests/test_chatbot_service_integration.py tests/test_chatbot_openrouter_integration.py tests/test_chatbot_provider.py tests/test_chatbot_service_local.py tests/test_chatbot_rag.py tests/test_chatbot_guardrails.py tests/test_chatbot_privacy.py tests/test_chatbot_catalog.py tests/test_chatbot_conversations.py
bash -n scripts/run_local.sh
git diff --check
cd .. && git diff --check
```

Writer observed **165 passed, 215 warnings in 7.53s**; warnings are the existing `datetime.utcnow()` deprecation in `app.py`. `bash -n scripts/run_local.sh` and `git diff --check` in both BFF and root exited **0**. Launcher test-first evidence: **1 failed, 1 passed** before the script existed, then **2 passed** after implementation. The new REST/OpenRouter selection and existing REST service integration passed **34 tests, 34 warnings in 5.08s** on their first run; the pre-existing provider path already satisfied these tests, so no provider RED is claimed. Minimum-version compatibility used only a downloaded Flask 3.0.0 wheel, extracted inside the existing `.venv` and temporarily placed on `PYTHONPATH`; its two startup tests passed, and compatibility files were removed without changing installed packages.

The tests retain actual `GroundedAnswerService`, `ApprovedFaqRag`, approved FAQ ingestion, and provider selection. Synthetic credentials and URL-dispatched HTTP isolate OpenRouter and Core; embedding, vector/retrieval, Ollama client, and Redis clients are local mocks. Coverage verifies English/Spanish grounded prompts, configured model/auth headers, source attribution, no Ollama chat on OpenRouter success, connection-error fallback, rejected protected/off-topic injection examples, insufficient approved evidence, and sanitized dual-provider failure without persistence. This is not a general in-scope prompt-injection detector or real model/credential validation.

Startup tests use only synthetic files in isolated project-local directories and a mocked executable or synthetic Flask CLI command; they never launch a server or read the repository `.env`. No real OpenRouter request, credential transmission, or real service traffic occurred. Public REST/Core contracts and feature metadata are unchanged. Live-key validation and full local acceptance remain unverified; T030/T032 are administratively closed, and those evidence gaps are not task blockers.

## Fresh validation reconciliation (2026-11-07)

These are fresh checks, recorded separately from the historical results above. No source was changed as part of this reconciliation.

| Scope | Command or observed procedure | Result and limit |
|---|---|---|
| BFF focused selection | `cd bgg-shop-bff && PYTHONPATH=. .venv/bin/python -m pytest -q --tb=short tests/test_chatbot_local_startup.py tests/test_chatbot_service_integration.py tests/test_chatbot_openrouter_integration.py tests/test_chatbot_provider.py tests/test_chatbot_service_local.py tests/test_chatbot_rag.py tests/test_chatbot_guardrails.py tests/test_chatbot_privacy.py tests/test_chatbot_catalog.py tests/test_chatbot_conversations.py` | **165 passed, 215 warnings**. Focused test evidence only; not full acceptance. |
| Frontend chatbot tests | `cd bgg-shop-frontend && npm test -- --run src/chatbot13` | Passed; React `act(...)` warnings were observed. |
| Frontend production build | `cd bgg-shop-frontend && npm run build` | Passed. |
| Browser flow | `E2E_OPKEY_ISOLATED=true npx playwright test tests/e2e/chatbot.spec.ts --reporter=list --output=/tmp/feature013-playwright` | **7 passed** with mocked API routes; no backend ownership, persistence, or retention proof. |
| Non-chatbot BFF contract suite | `cd bgg-shop-bff && bash scripts/run_contracts.sh` | **7 passed, 9 failed**. Fresh triage found four `NameError: op_key` failures at `proxy.py:820/1128` and five mock signatures without `allow_redirects`. These are unrelated to chatbot, baseline is not established, and no repair was authorized. |
| Core disposable-PostgreSQL suite | Initial local Core `.venv` invocation was blocked by missing modules; an isolated Core worker used the cached Core image and fresh PostgreSQL 15, with network disabled and no application credentials/database | **25 passed, 0 skipped, 1 warning**. The cached image enabled the isolated suite without installing packages. This verifies Core-to-disposable-PostgreSQL behavior only. The worker procedure did not expose an exact host command, so none is reconstructed here. |
| Isolated Core HTTP/retention/catalog observations | Worker used source-read-only, environment-excluded mounts and a disposable database; retention invoked with `--once` | Worker observed expiry `404` without conversation text/ID, active access `200`, retention of 2 conversations/4 messages down to 1/2 while preserving 2 catalog products, and exact seeded catalog facts without answer-provider invocation or Chroma. Writer-observed only; not independently replicated. |
| Historical BFF/Core HTTP attempts (superseded) | Two complete attempts with fresh isolated containers and synthetic configuration; no source or authentication changes | Both received HTTP **401** on message/catalog send. The corrected run below established the harness cause; these failures are not evidence of a production authentication defect. |

The previously failing proof was safely rerun after correcting the isolated BFF environment; see [Corrected isolated BFF/Core HTTP proof](#corrected-isolated-bffcore-http-proof-2026-11-07). The temporary harness remains uncommitted. No authentication bypass, architecture change, or live-provider request was used.

### Acceptance and traceability limits

- Contract: [`spec.md`](spec.md) FR-001–FR-012; the still-unmet acceptance claims include [SC-001](spec.md#success-criteria) (20 fixed FAQ cases, at least 19 expected outcomes, zero unsupported claims) and [SC-007](spec.md#success-criteria) (10 representative buyers, at least 9 successes). Neither was executed by these checks; deterministic tests and mocked browser runs do not substitute for them.
- Code and tests: BFF chatbot implementation under `bgg-shop-bff/src/chatbot/` and `bgg-shop-bff/src/controllers/`; focused tests under `bgg-shop-bff/tests/test_chatbot_*.py`; Core implementation/tests under `bgg-shop-core/` and `bgg-shop-core/tests/test_graphql_chat.py`; frontend implementation/tests under `bgg-shop-frontend/src/chatbot/` and `bgg-shop-frontend/tests/e2e/chatbot.spec.ts`.
- [`tasks.md`](tasks.md): T030/T032 are administratively closed with validation waived for bookkeeping only. SC-001/SC-007 and live OpenRouter authentication remain unverified; this is not full acceptance.

## Corrected isolated BFF/Core HTTP proof (2026-11-07)

**Observed command:** `python3 /home/eze/.copilot/session-state/1bf53275-98d7-409a-985e-b169ddf974a4/files/run_feature013_http_proof.py` — exit **0**. The parent-added harness fix was setting `APP_ENV=development` for the isolated HTTP BFF. In `bgg-shop-bff/app.py`, development is determined from `app.debug`, `FLASK_DEBUG`, `FLASK_ENV`, or `APP_ENV`; `CHAT_SESSION_COOKIE_SECURE` is set to `not development`. Without the development setting the harness minted a Secure cookie and its HTTP client did not send it. This supersedes the earlier harness 401; it is not a production authentication bug. Shared OPKEY values were unrelated, and requests sent no `X-Op-Key`.

The synthetic log showed create **201**, cookie present with `Secure=False`, and recommendation with the cookie sent and OPKEY absent. Real local BFF/Core catalog and record operations passed. Expired-owner access returned **404** without ID/content; active-owner access returned **200**. The management runner `--once` removed one inactive conversation and two messages, retaining one conversation and two messages; the seeded product count stayed at two. The forbidden-answer check used no answer provider or Chroma. Rate limiting was fake; no browser, real model, or remote request was used.

The environment was disposable: fresh PostgreSQL 15, three isolated containers, network disabled in a shared namespace, and all containers removed. No source, default, authentication guard, or production configuration changed. Trace: [`spec.md`](spec.md) FR-005/FR-007/FR-008/FR-010/FR-012; implementation `bgg-shop-bff/src/chatbot/catalog.py`, `bgg-shop-bff/src/controllers/chatbot_controller.py`, `bgg-shop-core/saleor/graphql/api.py`, and `bgg-shop-core/saleor/graphql/management/commands/run_chat_conversation_retention.py`; tests `bgg-shop-bff/tests/test_chatbot_catalog.py` and `bgg-shop-core/tests/test_graphql_chat.py`.

This closes bounded BFF/Core catalog, ownership/expiry, and one-shot retention-runner evidence. SC-001 (20 fixed FAQ cases, at least 19 expected outcomes and zero unsupported claims) and SC-007 (10 representative buyers, at least 9 successes) were not run. The separate optional-`OPENROUTER_API_URL` integration check was mocked (47 passed, 22 warnings on parent); it is not live-provider evidence.

## Administrative task closure (2026-11-07)

At the user's request, T030 and T032 were marked complete in the canonical task ledger. The waiver applies to task closure only: SC-001 and SC-007 remain unexecuted, live OpenRouter authentication remains untested, and the unrelated BFF general contract suite remains **7 passed, 9 failed** with unknown baseline. Do not represent these task checkboxes as passing acceptance, security certification, or live-provider evidence. Optional future evidence collection is not a blocker to the requested administrative closure. See [`spec.md`](spec.md) for the unchanged criteria and [`tasks.md`](tasks.md#administrative-task-closure-2026-11-07) for implementation/test traceability. No runtime tests were run for this documentation-only status update.
