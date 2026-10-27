# Detailed Test Cases — Manage Catalog & Inventory

Each test case below lists type (unit/E2E), priority, and brief steps.

1) Admin — Product List (E2E, High)
  - Steps: navigate to `/admin/products`, assert header, assert product rows present, search/filter, paginate, click `Editar` on a row opens edit page.

2) Admin — Create Product (E2E, High)
  - Steps: `/admin/products/new` open, submit empty → client validation errors; fill valid data (incl. at least one variant) → submit → expect redirect to list and success toast; verify new item visible.

3) Admin — Edit Product (E2E, High)
  - Steps: open existing product, change price and variant stock, save, assert persisted changes in list and audit entry.

4) Variants & Stock (E2E + Unit, High)
  - Cases: add variant, set inventory levels, validate min-allowed and reserved behavior, attempt to reduce stock below min-allowed → expect validation/error.

5) Promotions — Create & Preview (E2E, Medium)
  - Steps: open promotions panel, create promotion, verify client-side price preview matches expected calculation, save and verify listed.

6) Audit View (E2E, Medium)
  - Steps: perform product create/edit, open audit view, filter by action and assert presence of recent entries describing the change.

7) Async & Error Handling (E2E, High)
  - Steps: simulate slow network and error responses via MSW; assert loading spinners, disabled submit, retry logic, and mapped server field errors.

8) Client-side Field Error Mapping (Unit + E2E, High)
  - Steps: server returns `{ errors: [{ field, message }] }`; assert UI shows inline messages next to fields.

9) Public Catalog & Shopping Cart (E2E, High)
  - Steps: view product detail, add to cart, update quantity, verify total, remove item; replicate failing scenario from `home-tests.json` and stabilize.

10) Authentication (E2E, High)
  - Steps: unauthenticated user tries to access `/admin` → redirected to login; login flow works and lands back on admin.

11) Accessibility Checks (E2E, Medium)
  - Steps: run axe checks on admin forms and product list.

12) Cross-browser smoke (E2E, Low)
  - Steps: run a subset of tests on Firefox and WebKit to catch engine-specific regressions.

Mapping of responsibilities and mock level (MSW vs real BFF) is included in the implementation tasks.
