# CU-C01 / CU-C03 E2E Validation (register, login, review)

Run id: `20261020113031`. Target: the live dev stack (BFF `:5000` → Core `:8000` → PostgreSQL `saleor_db`).
Synthetic account: `e2e+20261020113031@example.test` (password not recorded; tokens redacted).

## Environment

- Containers up: `saleor_db` (healthy), `saleor_redis`, `saleor_mailpit`, `saleor_api`, `saleor_bff`, `saleor_frontend`, `saleor_celery`.
- `GET /health` → `{"status":"healthy"}`; frontend `:3000` → 200.
- Target product: slug `watergate` (`bgg_id=274364`), detail returns 200.

## Data counts

| Table | Before | After |
|---|---|---|
| `auth_user` | 5 | 6 |
| `product_review` | 1 | 2 |

Rows created by this run: `auth_user.id=6`, `product_review.id=2` (`bgg_id=274364`, `user_id=6`, `rating=4`, `status=PENDING`).
No password in plaintext was found in `auth_user` (checked for the run password).

## Results (API level, through the BFF)

| # | Case | Expected | Observed | Result |
|---|---|---|---|---|
| 1 | Register new user | 201 | 201, user id 6 | PASS |
| 2 | Register duplicate email | 409 `errors[]` | 409 `EMAIL_EXISTS` | PASS |
| 3 | Login wrong password | 401 `INVALID_CREDENTIALS` | 401 `INVALID_CREDENTIALS` | PASS |
| 4 | Login valid | 200 + session | 200, `session.access_token` present | PASS |
| 5 | Review without token | 401 | 401 `UNAUTHENTICATED` | PASS |
| 6 | Rating 0 / 6 | 400 | 400 `INVALID` | PASS |
| 7 | Empty body / body > 2000 | 400 | 400 `INVALID` | PASS |
| 8 | Unknown slug | 404 | 404 `PRODUCT_NOT_FOUND` | PASS |
| 9 | Valid review | 201 `PENDING` | 201 `PENDING` | PASS |
| 10 | Second review, same user and game | 409 | 409 `REVIEW_ALREADY_EXISTS` | PASS |
| 11 | Pending review hidden from public detail | not listed | not listed | PASS |
| 12 | DB row matches (rating, status, user) | match | match | PASS |

Frontend suites: `npm run test -- --run` 17/17 passed; `npm run build` OK; `npm run lint` 0 errors, 1 warning (`src/App.tsx:203`, set-state-in-effect).

## Follow-up run (browser + suites)

- Browser flow (headless Chromium via Playwright, live stack): register → redirected to `/login` → login (session stored in `sessionStorage`) → review on `/juegos/watergate` → toast "pending moderation". Result: PASS. Screenshots in `docs/evidence/e2e-ui/`.
- DB: review row created with `rating=4`, `status=PENDING`; both runs' synthetic rows (users 6 and 7, reviews 2 and 4) were deleted by id. Final counts: `auth_user` 5, `product_review` 1 (same as before the runs).
- BFF pytest: 20 passed (new `tests/test_reviews.py`). Core pytest: 23 passed (new `tests/test_graphql_reviews.py`, DB mocked).
- Finding B fixed: review-create `502` now returns `errors[]` (`UPSTREAM_ERROR`) and is documented in OpenAPI. Finding A: runtime code `EMAIL_EXISTS` is the canonical one; the OpenAPI spec does not enumerate it, so no change.

## Remaining

- Core uniqueness per user and product is only tested as an `IntegrityError` mapping; it needs a real PostgreSQL test DB.
- `auth_controller.py` 502 fallback still uses the legacy `{"error": ...}` shape.
- Frontend types are not regenerated for the new review `502`.
- SDL-vs-Graphene drift test is still missing.
