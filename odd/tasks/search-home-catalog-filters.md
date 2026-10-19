# Search Home Catalog Filters

## Objective
Implement the buyer use case for searching and filtering the Home catalog.

## Scope
- Add client-side text, year, player-count, category, and price-range filters.
- Preserve the current static catalog data source.
- Keep sorting available and expose a no-results state with a clear action.
- Add behavior and accessibility tests for the filtering flow.

## Constraints
- Do not change the BFF or Core contract.
- Do not add authentication, product detail, cart, or checkout behavior.
- Keep the implementation minimal and aligned with the existing Home.

## Tasks
- [x] Add accessible filter controls and derive visible products from user criteria.
- [x] Add no-results recovery and preserve existing Home rendering.
- [x] Extend tests and generate the frontend test report.

## Acceptance criteria
- A visitor can search by product name or publisher.
- A visitor can filter by publication year, players, category, and price range.
- Results update without a page reload and show the number of matching products.
- Empty results explain the state and offer a way to clear filters.
- Existing rendering and accessibility validations remain green.

## Verification
- `cd bgg-shop-frontend && npm run test:report`
- `cd bgg-shop-frontend && npm run build`
- `cd bgg-shop-frontend && npm run lint`
## Progress and verification

- Implementada la búsqueda client-side por nombre y editorial.
- Implementados filtros por año, jugadores, categoría y rango de precio.
- Activados los controles de categoría y orden recomendado/precio.
- Añadidos contador de resultados, estado vacío accesible y acciones para limpiar.
- Tests de renderizado, accesibilidad y filtros: 5/5 pasaron; reporte generado en `bgg-shop-frontend/results/home-tests.json`.
- `npm run build`: pasó.
- `npm run lint`: pasó.
- No se modificó el contrato del BFF/Core; la búsqueda permanece client-side sobre el catálogo estático.
