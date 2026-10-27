# QA Plan — Manage Catalog & Inventory (Frontend)

## Goal

Validate the admin and public catalog/inventory flows end-to-end, ensuring correctness of product CRUD, stock-by-variant behavior, promotions, audit view, client-side validation mapping, async states, previews, and critical public flows (catalog and shopping cart).

## Scope

- Frontend (React + Vite) admin flows under `/admin`
- Public catalog and shopping cart flows
- Integration/contract checks against expected BFF shape (field errors: `{ errors: [{ field, message }] }`)
- Accessibility and basic performance smoke

## Test Types

- Unit tests (Vitest) — existing and new component-level tests
- Integration / Contract tests — OpenAPI or contract-driven tests where applicable
- E2E tests (Playwright) — core user journeys across admin and public UX
- Accessibility checks (axe via Playwright)
- Flakiness monitoring and artifacted failure reporting (screenshots/videos)

## Test Data & Fixtures

- Canonical fixtures stored in `tests/fixtures/`:
  - `products.json` — sample products with variants
  - `promotions.json` — sample promotion objects
- Use MSW (mock service worker) to stub backend responses for deterministic E2E where running full BFF is impractical.

## Environment Matrix

- Local developer: Chrome/Chromium headless, `http://localhost:3000` (dev) or built `dist` served on `:3000`.
- CI: Ubuntu latest runner, Chromium (primary). Optional runs for Firefox and WebKit on demand.
- Viewports: Desktop (1280x720) primary; Mobile (375x812) spot checks for catalog flows.

## Acceptance Criteria

- Admin product create/edit/delete happy paths covered by E2E and passing in CI.
- Variant stock behaviors (min-allowed, reserved) validated via tests and fixtures.
- Promotions preview calculation validated client-side for representative scenarios.
- Public shopping cart core flow (add/update/remove) passes deterministically.
- Accessibility: key forms and lists pass automated axe checks.

## Reporting

- Playwright JSON output saved to `results/playwright-report.json`.
- Vitest JSON output saved to `results/home-tests.json`.
- Upload artifacts (screenshots, videos, traces) on CI failures.

## CI Job (high level)

- Checkout → `npm ci` → `npm run build` → `npx playwright install --with-deps` → `npx playwright test`
- Option: start BFF as service via Docker Compose if end-to-end with real backend is required.

## Roadmap / Deliverables

1. Save this QA plan (done).
2. Add canonical fixtures and MSW handlers for admin happy & error paths.
3. Expand E2E tests to cover all core admin cases and public cart flow.
4. Add CI job to run Playwright and publish artifacts.
5. Triage and fix preexisting failing suites (shopping-cart) and stabilize suite.

---

Generated: 2026-10-22
