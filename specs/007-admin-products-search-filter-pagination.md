# Admin Products: Búsqueda, Filtros y Paginación

## Resumen

Objetivo: añadir soporte para búsqueda por texto, filtros y paginación en el endpoint de productos del admin para permitir listados eficientes, búsquedas por nombre/slug/categoría y navegación por páginas.

Impacto: cambios en Core (GraphQL), BFF (parsing + mapping), Frontend (UI + query params) y tests (unit + integración + e2e).

## Por qué

- Mejora la usabilidad del panel de administración con búsqueda rápida.
- Evita sobrecargar la respuesta con todos los productos (escala mejor con paginación).
- Permite flujos E2E deterministas (crear → buscar → verificar).

## Alcance

- Endpoint público del admin HTTP: `GET /api/v1/admin/products` (BFF)
- Parámetros de consulta soportados: búsqueda libre (`q` / `search`), filtros (categoría, price range, availability), orden y paginación (`page`, `page_size`).
- Mapear a la consulta/resolver GraphQL correspondiente en Core.

## Requisitos funcionales (FR)

- FR-001: El cliente puede buscar por texto libre en `name`, `slug` y campo `bgg_id` usando `search`.
- FR-002: El cliente puede filtrar por `category` (ID o slug), `min_price`, `max_price`, `available` (boolean), y `publisher`.
- FR-003: Soportar paginación mediante `page` (1-based) y `page_size` (limitado por `max_page_size`).
- FR-004: Respuesta incluye `items`, `page`, `page_size`, `total`, `total_pages`.
- FR-005: El BFF valida parámetros y aplica `max_page_size` por seguridad (p.ej. 200).
- FR-006: Mantener correlación (`X-Debug-Correlation`) y propagar encabezados de autenticación al Core.

## Criterios de aceptación / Success Criteria (SC)

- SC-001: Una búsqueda por nombre que coincida con un producto recién creado debe devolverlo en la primera página.
- SC-002: Un `page_size` mayor que `max_page_size` resulta en error 400 o se recorta al valor máximo (definir comportamiento; preferible recortar con advertencia en logs).
- SC-003: Los filtros combinados (ej. categoria + rango de precio) devuelven resultados correctos y consistentes con Core.
- SC-004: No introducir regresiones en endpoints existentes; autenticación y CORS siguen funcionando.

## Contrato API (BFF)

Request:

GET /api/v1/admin/products?search=...&category=...&min_price=...&max_price=...&available=true&page=1&page_size=50&sort=price:asc

Query params:
- `search` (string, optional): texto libre para búsquedas.
- `category` (string|int, optional): id o slug de categoría.
- `min_price` (decimal, optional)
- `max_price` (decimal, optional)
- `available` (boolean, optional)
- `page` (int, optional, default=1)
- `page_size` (int, optional, default=50, max=200)
- `sort` (string, optional) e.g. `price:asc` o `name:desc`

Headers:
- `Authorization: Bearer <token>` (requerido en admin flows)
- `X-Debug-Correlation` (opcional)

Response (200):

{
  "items": [ { "id": 123, "name": "...", "bgg_id": 345, "price": 19.99, "quantity": 5, "category": [...], "image_url": "..." } ],
  "page": 1,
  "page_size": 50,
  "total": 1234,
  "total_pages": 25
}

Errores relevantes:
- 400: parámetros inválidos
- 401: autenticación requerida
- 500: error interno

## Mapping BFF → Core (GraphQL)

- BFF parsea params y construye variables para la query GraphQL: `q`, `filters: { category, priceRange, available }`, `pagination: { offset, limit }`, `orderBy`.
- Convertir `page,page_size` a `offset = (page-1)*page_size`, `limit = page_size`.

Ejemplo (pseudo-GraphQL variables):

{
  "q": "search text",
  "filters": { "category": "board-games", "minPrice": 10.0, "maxPrice": 50.0, "available": true },
  "offset": 0,
  "limit": 50,
  "orderBy": { field: "price", direction: "ASC" }
}

## Validaciones y límites

- `page` >= 1
- `page_size` entre 1 y `MAX_PAGE_SIZE` (configurable; sugerido 200)
- `min_price` y `max_price` deben ser números; `min_price` <= `max_price` si ambos presentes
- `category` sanitizado y validado contra Core si necesario

Si parámetros inválidos → 400 con body explicativo.

## Decisiones y comportamiento operativo

- Default `page_size`: 50 (coordinado entre BFF, OpenAPI y Core GraphQL)
- `MAX_PAGE_SIZE`: 200 (configurable en BFF)
- Comportamiento cuando `page_size` > `MAX_PAGE_SIZE`: recortar (clamp) el valor solicitado a `MAX_PAGE_SIZE` y continuar la petición. Registrar una advertencia en logs con la `X-Debug-Correlation` para facilitar triage.
- Cuando se produzca un recorte, el BFF incluirá un encabezado de respuesta informativo `X-Page-Size-Used: <n>` indicando el `page_size` efectivo usado por la consulta.

Rationale: prefijamos el comportamiento de recorte para evitar errores 400 que rompan flujos UI y para mantener resiliencia frente a clientes malformados o bots que soliciten tamaños excesivos. Los logs permiten detectar abuso o malas configuraciones.

## Encabezados y Autenticación

- `Authorization: Bearer <token>`: método preferido para flujos admin autenticados.
- `X-Op-Key: <op_key>`: cabecera alternativa para operaciones privilegiadas (op-key) en entornos donde el frontend presenta claves de operación en lugar del bearer. El BFF validará la `op_key` localmente o la propagará a Core según la política de ops definida.
- `X-Debug-Correlation: <uuid>`: cabezal opcional para correlación y trazabilidad; si no está presente, el BFF generará un UUID por petición y lo devolverá en `X-Debug-Correlation` en la respuesta.

El BFF debe propagar los encabezados de autenticación válidos (`Authorization` o `X-Op-Key`) al upstream GraphQL cuando corresponda.

## Mapping BFF → Core (GraphQL) — detalle final

- Query params aceptados en BFF y mapeo a variables GraphQL:
  - `search` → GraphQL `q` (string)
  - `category` → GraphQL `filters.category` (id o slug)
  - `min_price` → `filters.minPrice` (decimal)
  - `max_price` → `filters.maxPrice` (decimal)
  - `available` → `filters.available` (boolean)
  - `page`, `page_size` → `offset = (page - 1) * page_size`, `limit = page_size` (enteros)
  - `sort` → `orderBy` (objeto con `field` y `direction`)

Ejemplo de variables enviadas al resolver GraphQL:

```
{
  "q": "watergate",
  "filters": { "category": "strategy", "minPrice": 1000.0, "maxPrice": 50000.0, "available": true },
  "offset": 0,
  "limit": 50,
  "orderBy": { "field": "price", "direction": "ASC" }
}
```

El resolver GraphQL retornará el slice (items) y la metadata (`total`) que BFF usará para calcular `total_pages = ceil(total / page_size)`.

## Ejemplos prácticos (cURL)

Caso: petición admin con op-key y paginación recortada

```
curl -s -D - \
  -H "X-Op-Key: my-op-key-raw" \
  'https://bff.example.com/api/v1/admin/products?search=watergate&page=1&page_size=500'
```

Respuesta esperada (resumen):

- Status: 200
- Headers: `X-Page-Size-Used: 200`, `X-Debug-Correlation: <uuid>`
- Body: JSON con `items`, `page`, `page_size: 200`, `total`, `total_pages`

## Tests adicionales (detallado)

- E2E: crear N productos (>200), solicitar `page_size=500` y verificar que la respuesta contiene `page_size` efectiva `200` y que `X-Page-Size-Used` coincide con el `MAX_PAGE_SIZE`.
- Unit BFF: pruebas para `parse_params()` que confirmen clamp, validación de `min_price/max_price` y mapeo `search`→`q`.
- Integration: BFF ↔ Core con `X-Op-Key` y con `Authorization` para asegurar que ambos encabezados se propagan correctamente.

---

Fecha: 2026-10-26
Autor: Spec actualizado por agente; confirmar y/o editar según convención del repo

## Frontend UI (Admin)

- Componente de búsqueda en la cabecera de la lista (`search`), debounce 300ms.
- Panel de filtros desplegable con: categoría (select), rango de precio (dos inputs), checkbox `Disponible`.
- Controles de paginación en pie de página: prev/next, selector de página, selector `page_size` entre opciones (25, 50, 100, 200).
- Mostrar total de resultados y página actual.

## Tests

- Unit tests Core: resolver filtra y pagina correctamente.
- Unit tests BFF: parsing de params, validación y mapping a GraphQL variables; tests de límites (`page_size`), casos inválidos.
- Integration tests: BFF ↔ Core con dataset pequeño para validar combinaciones de filtros.
- E2E tests: crear producto → buscar por nombre → verificar aparece; filtros combinados; paginación (crear > page_size items y navegar).

## Rollout

1. Implementar y probar Core changes en entorno local.
2. Implementar BFF mapping y validación; desplegar a staging.
3. Actualizar frontend para consumir params; desplegar a staging.
4. Ejecutar E2E en staging; si ok, promover a producción.

## Monitorización y métricas

- Registrar métricas: latencia del endpoint, tasa de 4xx (especialmente 400/401), uso de `page_size` cercano al máximo.
- Logs de correlación para depuración (propagar `X-Debug-Correlation`).

## Edge cases y notas

- Si la búsqueda es vacía y no hay filtros, devolver primer page con default `page_size`.
- Para estabilidad, preferir recortar `page_size` a `MAX_PAGE_SIZE` en lugar de error (configurable).
- Considerar habilitar filtros por índices en DB (name, slug, category, price) para performance.

---

Fecha: 2026-10-26
Autor: Spec generado por agente (puedes editar/corregir según convención del repo)
