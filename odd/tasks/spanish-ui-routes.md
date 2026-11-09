# Spanish UI routes

## Objective and authorized scope

Normalize storefront and administration navigation URLs to Spanish, keeping
`/admin` and already-Spanish URLs. User authorized implementation on 2026-11-09.
Do not translate REST/GraphQL endpoints, external payment URLs, identifiers,
or product slugs. Preserve all existing unrelated and feature-015 work.

## Navigation contract

| Legacy UI path | Canonical UI path |
|---|---|
| `/login` | `/iniciar-sesion` |
| `/register` | `/registro` |
| `/wishlist` | `/lista-de-deseos` |
| `/checkout` | `/finalizar-compra` |
| `/admin/products` | `/admin/productos` |
| `/admin/products/new` | `/admin/productos/nuevo` |
| `/admin/promotions` | `/admin/promociones` |
| `/admin/promotions/new` | `/admin/promociones/nueva` |
| `/admin/coupons` | `/admin/cupones` |
| `/admin/coupons/new` | `/admin/cupones/nuevo` |
| `/admin/gift-cards` | `/admin/tarjetas-de-regalo` |
| `/admin/audit` | `/admin/auditoria` |
| `/admin/sales` | `/admin/ventas` |
| `/admin/reviews` | `/admin/resenas` |
| `/admin/users` | `/admin/usuarios` |

Preserve path suffixes identifying records, query strings, and fragments.
Legacy aliases canonicalize with history replacement rather than adding a
navigation step. New links and post-login destinations use canonical routes.
Keep `/compra/resultado` and payment return parameters unchanged.
Authentication and superuser/staff gates apply equally to aliases and canonical
paths. API paths remain English and must not be passed through UI rewriting.

### Catalog query contract

User authorized visible catalog query normalization on 2026-11-09.

| Legacy query | Canonical browser query |
|---|---|
| `search` | `busqueda` |
| `category_name` | `categoria` |
| `publisher` | `editorial` |
| `year_published` | `anio` |
| `min_players` / `max_players` | `jugadores_min` / `jugadores_max` |
| `price_min` / `price_max` | `precio_min` / `precio_max` |
| `page` | `pagina` |
| `sort=price-high` | `orden=precio-descendente` |
| `sort=price-low` | `orden=precio-ascendente` |

Accept legacy query names and order values for old links; serialize new browser
URLs using the Spanish contract. Translate only catalog browser state, not API
requests, record identifiers, or payment parameters. Preserve existing
validation, hash, page reset, filter combination, and history behavior.
When both names are present, the Spanish key wins by presence, even if its value
is invalid. The chosen key must occur exactly once; an invalid or repeated
Spanish key is rejected without falling back to the English alias. When Spanish
is absent, the legacy key likewise must have exactly one value.

## Checklist

- [X] R001 Inspect existing storefront/admin routing, login returns, and payment
  callback boundaries. No new service API contract is required.
- [X] R002 Add shared canonical route normalization and deterministic tests;
  update all UI dispatch, links, form ID parsing, auth guards, pending returns,
  and frontend tests/docs while preserving API request paths.
- [X] R003 Verify unit tests, build, changed-file lint, alias/canonical browser
  navigation where feasible, and independently review permission/return-route
  consistency. Automated checks and independent browser/permission review
  passed; see the scope and limits below.
- [X] R004 Localize catalog query serialization and compatible reading, validate
  canonical and legacy links, unchanged English API requests, sorting,
  category/publisher validity, and reload/back/forward behavior.

## Route, risk, and checks

Delegated direct: one writer because this crosses nontrivial frontend routing,
admin forms, and auth navigation files. High-risk verification for route guards
and return destinations. Test-first RED → GREEN applies to deterministic routing
tests. Use existing Vitest, TypeScript/Vite build, and oxlint; no new dependencies.
Run normalization and generation before final functional checks. The frontend
uses the existing Vite/React custom router and Vitest; no dependencies were
added.

Estimated implementation exceeds 400 changed lines mostly in existing route
expectations. No automatic commits, publishing, or PR creation is authorized.
Keep this as one local coherent route-normalization change with existing aliases;
ask about delivery slicing only if the user later requests commits or a PR.

## Evidence and recovery

Initial mapping: custom router in `src/App.tsx`; admin router and some nested
forms parse paths separately. Payment callback already uses `/compra/resultado`.

Implementation evidence (2026-11-09):

- `src/routing/routes.ts` is the shared source for canonical paths and
  segment-bound alias normalization. Tests cover all legacy prefixes, ID
  suffixes, create routes, query/hash preservation, unrelated/absolute/API
  paths, and lookalike boundaries.
- App tests cover initial alias replacement (including history state),
  `popstate`, storefront auth links, pending-return canonicalization and
  rejection of external/API destinations. Admin tests cover direct alias
  compatibility, edit ID parsing, superuser-only user routes, and unknown
  English admin paths.
- `../bgg-shop-bff/specs/openapi.yaml` contains pre-existing feature-015
  publisher changes; REST routes remain English and unchanged by this work.
  `npm run generate:types` completed; the generated file SHA-256 was unchanged
  (`cbbcfd3569e305844bbe79445c78a69a9cd1e7cdb4dc7d3949e419ac871939b9`).
- RED was observed before adding `routes.ts` (Vitest could not resolve the
  missing module). Focused routing/admin/auth tests passed (42 tests), focused
  route/form/navigation regression tests passed (226 tests), and the complete
  suite passed: 33 files, 320 tests. `npm run build` passed TypeScript and Vite.
- `npm run lint` and changed-file `oxlint` exited successfully with warnings
  only (25 and 10 respectively); warnings are existing unused catches/params,
  including unchanged lines in E2E files. `git diff --check` passed.
- Parent spot-check: routing helper, App Spanish routes, and AdminRouter tests
  passed (30 tests).
- Independent verification reran routing, auth, and nested-form tests:
  7 files, 66 tests passed. Chromium on an isolated Vite server verified legacy
  aliases, canonical URLs, query/hash/history-state preservation, back/forward,
  reload, safe pending returns, login redirects, denied staff access to users,
  superuser access, and edit forms for record 42.
- Browser API responses were explicitly synthetic, with English request URLs.
  This validates frontend behavior and route guards, not live BFF/Core
  authentication, PostgreSQL, or payment-provider integration. No shared service
  was restarted; the verifier stopped its own Vite server and freed the port.
- No source changes were made by the verifier. Unrelated media-file changes
  observed during verification were left untouched.

R004 catalog query normalization evidence (2026-11-09):

- `src/catalog/urlState.ts` is the shared parser/serializer for Spanish visible
  query names and legacy English aliases. Spanish-key presence wins even when
  invalid; repeated chosen keys are rejected without alias fallback. Legacy
  `sort=price-high|price-low` remains accepted, while `orden` accepts only
  `precio-descendente|precio-ascendente`. Defaults remain omitted.
- RED observed first: catalog URL unit tests reported 6 failures for the
  unsupported Spanish mappings/serialization. After implementation, focused
  catalog tests passed: 2 files, 17 tests.
- Full frontend suite: `npm run test -- --run` passed, 33 files and 329 tests.
  `npm run build` passed TypeScript and Vite. `npm run lint` passed with 25
  existing warnings and 0 errors; changed-file oxlint passed with 0 warnings
  and 0 errors. `git diff --check` passed at workspace and frontend levels.
- `npm run generate:types` ran against the already-modified feature-015
  `../bgg-shop-bff/specs/openapi.yaml`; generated type SHA-256 stayed
  `cbbcfd3569e305844bbe79445c78a69a9cd1e7cdb4dc7d3949e419ac871939b9`.
  This task changed no BFF/Core/OpenAPI/generated types.
- Catalog integration coverage checks canonical/legacy direct entry, query
  and hash normalization with history state preserved, popstate restoration,
  page reset, canonical category/editorial validation, price ordering, and
  English BFF request parameters. The canonical direct-entry case performs one
  products request. No browser smoke was run; verification used Vitest/jsdom
  with synthetic API responses. Existing suite output includes MSW unhandled
  facet warnings in unrelated cart/wishlist tests and Chatbot `act` warnings.
