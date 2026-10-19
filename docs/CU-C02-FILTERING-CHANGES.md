# CU-C02: alcance implementado y cambios de filtrado

## Propósito y diferencia de alcance

El CU-C02 original describía una búsqueda de catálogo por texto, año,
cantidad de jugadores, categoría y rango de precio, con orden orientado a
relevancia, resultados vacíos y paginación. También proponía mantener la
compatibilidad de la consulta `products` existente y no crear una migración.

La implementación efectivamente entregada extendió el flujo
`Frontend → BFF REST → Core GraphQL`:

- el Frontend consulta el BFF y ya no depende de un catálogo estático;
- el BFF valida parámetros REST en `snake_case`, los traduce a GraphQL
  `camelCase` y adapta la respuesta de vuelta a `snake_case`;
- el Core filtra `product_boardgame` mediante SQL parametrizado antes de
  contar y paginar;
- se conservaron las rutas y formas de respuesta existentes y se agregaron
  estados de carga, error, vacío y éxito a la Home;
- se añadieron tipos TypeScript generados desde OpenAPI y pruebas de las tres
  capas.

Hay decisiones del alcance original que no llegaron a ser funcionalidad
completa: el orden por relevancia no está implementado, la paginación del
resultado no se expone como control de UI y el mapa de categorías sigue siendo
local al resolver.

## Evolución del trabajo aplicado al CU-C02

El comportamiento actual reúne tres trabajos previos que forman parte del
mismo caso de uso:

### 1. Construcción inicial de la Home

`build-home-catalog-view.md` reemplazó la pantalla inicial de Vite por una
Home de catálogo de juegos de mesa. Ese trabajo incorporó:

- estructura visual de storefront con tarjetas de producto;
- datos con forma `Product`, imágenes de portada, precios, categorías,
  editoriales y metadatos;
- controles visuales de inicio de sesión y registro;
- estructura semántica, navegación por teclado, estilos de foco y soporte de
  movimiento reducido;
- diseño responsive y validación mediante `npm run build`.

La restricción original de esa etapa era mantener la vista client-only, con
datos mock y sin llamadas de red, autenticación ni estado de carrito. Esa
decisión fue supersedida por la integración posterior del catálogo con el BFF;
los controles visuales de autenticación y compra continúan siendo solo
presentación.

### 2. Exposición paginada del catálogo

`list-products-paginated.md` incorporó la primera comunicación entre servicios:

```text
Frontend → GET /api/v1/products → BFF Flask → products(...) → Core GraphQL
```

Ese trabajo agregó:

- el tipo GraphQL `Product`;
- la consulta paginada `products` del Core sobre `product_boardgame`;
- el tipo `ProductPage` con `items`, `page`, `pageSize`, `total` y
  `totalPages`;
- el endpoint REST `GET /api/v1/products` en el BFF;
- transformación de nombres GraphQL `camelCase` a REST `snake_case`;
- separación de la categoría persistida por comas en una lista;
- validación de `page` y `page_size`;
- propagación explícita de fallos del Core como HTTP `502`;
- pruebas de contrato, mapeo, paginación y errores.

La forma paginada se conservó cuando se agregaron los filtros. Por eso el
Frontend solicita actualmente `page=1&page_size=100`, dentro del límite
permitido por el BFF, aunque todavía no ofrece navegación visual entre
páginas.

### 3. Búsqueda y filtros de la Home

`search-home-catalog-filters.md` definió inicialmente filtros client-side
sobre el catálogo mock: texto por nombre/editorial, año, jugadores, categoría,
precio, orden y estado sin resultados. Sus criterios de accesibilidad,
limpieza de filtros, contador y estado vacío se conservaron.

La decisión de mantener el catálogo estático y no modificar BFF/Core quedó
supersedida al implementar CU-C02 de extremo a extremo. Actualmente los
criterios de búsqueda se envían al BFF y se resuelven en Core; el Frontend
solo conserva el ordenamiento visual local. Esta separación evita duplicar
la lógica de filtrado y hace que el resultado dependa del catálogo real.

## Frontend

`bgg-shop-frontend/src/App.tsx` consume:

```text
GET ${VITE_API_BASE_URL}/products
```

El valor por defecto es `http://localhost:5000/api/v1`; la URL de Compose usa
el mismo prefijo. La Home envía los filtros del formulario con los nombres
REST `search`, `year_published`, `min_players`, `max_players`, `category_id`,
`price_min` y `price_max`. La búsqueda por nombre o editorial se confirma con
Enter o el botón `Buscar`; no se solicita al BFF durante la escritura.
Solicita `page=1&page_size=100`, que coincide con el límite permitido por el
BFF, pero no presenta controles de páginas ni botones de categoría al usuario.

Los modelos usados por la aplicación provienen de
`src/types/generated/bff-api.d.ts`, generado con
`npm run generate:types` a partir de
`bgg-shop-bff/specs/openapi.yaml`. Los mocks de MSW también usan esos tipos.
La Home distingue:

| Estado | Comportamiento comprobado |
| --- | --- |
| Carga | muestra `Cargando catálogo...` mientras la solicitud está pendiente |
| Error | muestra el mensaje, un estado accesible y `Reintentar` |
| Vacío | muestra `No encontramos juegos` y permite limpiar filtros |
| Éxito | muestra los productos recibidos y los controles de orden local |

El orden visible `Precio menor` y `Precio mayor` se realiza localmente. La
opción `Recomendados` usa el campo opcional `featured` del modelo de vista; no
es un orden de relevancia calculado por el Core.

## BFF REST

El contrato fuente es `bgg-shop-bff/specs/openapi.yaml`. La operación es
`GET /api/v1/products`; también existe `GET /health`. Los parámetros del
catálogo son:

| Parámetro | Tipo | Regla verificada |
| --- | --- | --- |
| `page`, `page_size` | entero | positivos; `page_size` máximo 100 |
| `search` | texto | no vacío y máximo 200 caracteres |
| `year_published` | entero | entre 0 y 9999 |
| `min_players`, `max_players` | entero | entre 1 y 999; el mínimo no supera al máximo |
| `category_id` | entero | mayor o igual que 1 |
| `price_min`, `price_max` | número | no negativos; el mínimo no supera al máximo |

Los nombres REST se transforman explícitamente a los argumentos GraphQL
`yearPublished`, `minPlayers`, `maxPlayers`, `categoryId`, `priceMin` y
`priceMax`. Los campos de la respuesta se transforman de `bggId`,
`releaseYear`, `pageSize`, `totalPages` e `imageUrl` a `snake_case`.
Una entrada inválida responde `400` con `{"error": "..."}`.

Los errores de red, HTTP, GraphQL o payload inválido del Core se convierten en
`502` con `error` y `detail`; no se exponen como un éxito REST. El BFF permite
CORS para `http://localhost:3000` y `http://127.0.0.1:3000` en las rutas de
API.

## Core GraphQL y persistencia

La consulta `POST /graphql/` mantiene `products` y acepta estos argumentos
opcionales:

| GraphQL | Semántica |
| --- | --- |
| `search` | coincidencia insensible a mayúsculas en nombre o editor |
| `yearPublished` | igualdad con `release_year` |
| `minPlayers`, `maxPlayers` | solapamiento con el rango soportado |
| `categoryId` | token de la categoría persistida |
| `priceMin`, `priceMax` | límites inclusivos sobre `price_amount` |
| `page`, `pageSize` | paginación positiva |

El resolver construye condiciones y parámetros separados y ejecuta SQL
parametrizado contra `product_boardgame`. Usa las mismas condiciones para
`COUNT(*)` y para la selección; por ello el filtrado ocurre antes del conteo,
`LIMIT` y `OFFSET`. Los resultados conservan `ORDER BY id` y los metadatos
`total` y `totalPages`.

`categoryId` no consulta una tabla de categorías: usa un mapa local limitado a
`1 = Juegos de Estrategia`, `2 = Juegos Temáticos` y `3 = Juegos Familiares`.
Un identificador fuera de ese mapa produce cero resultados. Este cambio usa
columnas existentes de `product_boardgame` y no requiere migración de base de
datos.

## Verificación

Verificaciones ejecutadas en este entorno:

```text
cd bgg-shop-bff && python -m pytest       10 passed
cd bgg-shop-core && python -m pytest      4 passed, 1 warning
cd bgg-shop-core && python -m compileall -q saleor/graphql tests  passed
cd bgg-shop-frontend && npm run test:report  2 suites, 7 tests passed
cd bgg-shop-frontend && npm run build     passed
cd bgg-shop-frontend && npm run lint      passed with 1 warning
```

El warning de Core es `RemovedInDjango50Warning` sobre el valor futuro de
`USE_TZ`. Oxlint reporta `react(set-state-in-effect)` en `src/App.tsx`; no
bloquea el lint actual. La generación de tipos se verificó mediante el script
`npm run generate:types` y el archivo generado presente en el árbol.
No se realizó validación visual en un navegador ni una prueba end-to-end con
servicios y base de datos levantados; las pruebas de Frontend usan mocks.

## Limitaciones pendientes

1. La Home conserva controles visuales de autenticación y compra, pero esos
   flujos pertenecen a otros casos de uso y no tienen lógica implementada.
2. El mapa de categorías es local al Core y debe coordinarse con el catálogo
   real si cambian los nombres o aparecen nuevas categorías.
3. No se implementó ordenamiento por relevancia en el BFF/Core; el Frontend
   solo ordena localmente por precio o por `featured`.
4. La API admite paginación, pero la UI siempre solicita la primera página de
   hasta 100 elementos y no expone navegación.
5. Las pruebas Python dependen de los entornos virtuales y dependencias
   instaladas de cada servicio. En un entorno sin `pytest`, Django,
   Graphene o las dependencias del BFF, deben instalarse los respectivos
   `requirements.txt` antes de reproducirlas.
6. No se añadió migración: la funcionalidad depende de las columnas y valores
   ya presentes en `product_boardgame`.
