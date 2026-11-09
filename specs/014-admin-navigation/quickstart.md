# Verification ledger: Admin Navigation and Discoverability

This ledger records observed local checks for the implemented feature. T001–T015 are complete for the scoped slice; this is not evidence of full live CRUD across all admin modules or a full Core migration bootstrap. No staging, production, CI, or remote service was used. The disposable local database and all temporary services/directories were removed after verification.

## Contract and implementation trace

| Scope | Specification / contract | Implementation | Tests / observed checks |
| --- | --- | --- | --- |
| Current-user role projection and safe access | [spec.md FR-001–002, FR-008, FR-011–012](spec.md); canonical [`GET /api/v1/auth/me`](../../bgg-shop-bff/specs/openapi.yaml) | `bgg-shop-bff/app.py`; `bgg-shop-bff/src/controllers/auth_controller.py`; `bgg-shop-bff/src/proxy.py`; Core's existing `Query.me` in `bgg-shop-core` (no Core source or contract change) | `bgg-shop-bff/tests/test_auth_current_user.py`, `test_auth.py`, `test_opkey_middleware.py`, `test_opkey_admin.py`; isolated live-path verification below |
| Role-aware storefront and admin routes | [spec.md FR-001–013](spec.md) | `bgg-shop-frontend/src/App.tsx`; `src/auth/adminCapabilities.ts`; `src/admin/AdminRouter.tsx`; generated `src/types/generated/bff-api.d.ts` | `src/App.admin-navigation.test.tsx`; `src/admin/AdminRouter.test.tsx`; `src/auth/adminCapabilities.test.tsx`; `src/lib/apiClient.test.ts` |
| Shared admin presentation | [spec.md FR-014–017](spec.md) | `bgg-shop-frontend/src/admin/admin.css` and existing panel components under `src/admin/` | `tests/e2e/admin-styling.spec.ts`; `tests/e2e/admin-navigation.spec.ts`; four-viewport Chromium checks |

The approved fragment at `contracts/admin-session.openapi.yaml` is retained as a **non-canonical design copy**. The canonical REST contract is `bgg-shop-bff/specs/openapi.yaml`. Core `Query.me` and its existing identity fields were reused; Core source and SDL were not changed.

## BFF checks

The independent endpoint/auth/operation-key rerun passed **89 tests** and reported **59 existing `datetime.utcnow` deprecation warnings**. Its wrapper suppressed the existing incoming-request file logger to avoid external temporary logs; the unit tests made no network or database calls. Exact command, run from `bgg-shop-bff`:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -c 'import app, pytest; app._append_incoming_log = lambda entry: None; raise SystemExit(pytest.main(["tests/test_auth_current_user.py", "tests/test_auth.py", "tests/test_opkey_middleware.py", "tests/test_opkey_admin.py", "-q", "--tb=short", "--basetemp=.pytest-local-spec014-verify"]))'
```

The endpoint tests first showed **27 new failures** while **17 existing auth tests passed** before implementation. The implemented suite then passed. Unit coverage includes the exact two-field response, bearer-only access, inactive/missing/invalid and operation-key-only `401`, no-store error responses, and sanitized upstream failures. A real upstream outage was not injected; the `502` behavior was verified by unit tests.

## Frontend checks

- Test-first: the initial focused run showed **13 failing tests and 1 passing** before behavior implementation.
- Before the final test-fixture-only correction, `npm run test -- --run` passed **28 files / 273 tests**; `npm run build` passed; `npm run lint` exited **0** with **27 warnings and 0 errors**.
- After adding only the buyer `/api/v1/auth/me` handler in `src/App.wishlist.test.tsx` (no production change), the following focused rerun passed **5 files / 48 tests**. Two existing unhandled `product-categories` warnings remained in the wishlist test; its `/auth/me` warning was gone:

  ```bash
  npm --prefix bgg-shop-frontend run test -- --run src/App.wishlist.test.tsx src/App.admin-navigation.test.tsx src/admin/AdminRouter.test.tsx src/auth/adminCapabilities.test.tsx src/lib/apiClient.test.ts
  ```

- Parent and independent reruns also passed **37 focused tests** and an independent build. The full 273-test suite was not rerun after the fixture-only correction.
- Mocked Chromium tests passed **10 tests** for the navigation and styling specs. Evidence covered all eight modules and product/promotion/coupon forms at **1280×720, 768×1024, 375×812, and 320×720**, keyboard focus, active navigation, error feedback, and no page-wide horizontal overflow. Measured ratios included focus **6.646**, primary **8.120**, active navigation **8.235**, heading **15.508**; boundaries and alert exceeded **3**. These measurements are not an exhaustive WCAG audit.

The browser runner used an owned local Vite origin and intercepted API calls. The reproducible command shape below uses a dynamically assigned port; the placeholder was **not** passed verbatim as a command:

```bash
E2E_OPKEY_ISOLATED=true VITE_API_BASE_URL=http://127.0.0.1:<vite-port>/api/v1 node_modules/.bin/playwright test tests/e2e/admin-navigation.spec.ts tests/e2e/admin-styling.spec.ts --project=chromium --workers=1 --reporter=list
```

## Independent isolated live service-path verification (T012)

An independent local QA run passed through **Frontend → BFF → Core → disposable PostgreSQL 15.19** using synthetic users. There were no API mocks on the `/api/v1/auth/me` path. It observed active staff, buyer, and superuser identities (including a superuser with `is_staff=false`); exact role fields and no-store; missing, invalid, inactive, and operation-key-only `401`; staff denial without a personnel-list request; operational navigation; same-bearer self-demotion on reentry; logout `204`; and a read-only database check confirming saved flags `active=true, staff=false, superuser=false`.

The run used a session-scratch adaptation of the existing `scripts/run-spec012-local-e2e.sh`. Scratch files were removed. No exact persisted invocation or permanent QA report was created, so this is an observed result, not a claim that a committed harness can reproduce it verbatim. The disposable database was destroyed; no services or listeners remain. This verifies the current-user/auth integration slice, **not** full live CRUD for all eight admin modules.

## Limitations and historical evidence

- An independent attempt to run all Core migrations on a separate disposable database failed with `ProgrammingError: relation gift_card does not exist`. This pre-existing bootstrap limitation is recorded in [`bgg-shop-core/specs/003-product-detail-reviews/tasks.md:40`](../../bgg-shop-core/specs/003-product-detail-reviews/tasks.md#L40) and [`0001_credit_accounts.py:30`](../../bgg-shop-core/saleor/graphql/migrations/0001_credit_accounts.py#L30). The successful feature-path run used only the required auth/operation-key migrations. Do not mark the full migration set as verified.
- Core pytest was not run because the Core virtual environment did not contain `pytest`; no environment changes were made to install it. Core was unchanged by this feature.
- Earlier planning-only checks are historical and do not replace the implementation evidence above. T005 approval was followed by canonical promotion in T006; the design fragment remains non-canonical.
- No full Core migration test, exhaustive accessibility audit, production/staging check, real upstream outage injection, or full eight-module live CRUD exercise is claimed.
