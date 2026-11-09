# BGG Shop

## Separate persistent local database

`scripts/create_parallel_database.py` provisions a **parallel database only**.
It does not switch the running Core/BFF/frontend away from `saleor_db`, copy
customers or purchases, change service contracts, or require external services.
It uses cached PostgreSQL 15 and Core images (`--pull=never`) and read-only mounts
of Core's `saleor` and `opkeys` directories, excluding `.env`.

Run from this repository with Podman and Python 3:

```sh
python3 scripts/create_parallel_database.py create
python3 scripts/create_parallel_database.py status
python3 scripts/create_parallel_database.py access
python3 scripts/create_parallel_database.py verify
```

Creation uses `127.0.0.1:55432`, container `bgg_shop_parallel_db`, persistent named
volume `bgg_shop_parallel_pgdata`, and an isolated internal Podman network with
no external egress. `create --port 55433` can select another free port in
55432–55499 **before initialization**. Existing containers, volumes, networks,
or configuration are refused; creation never resets or overwrites a database.
The detached Podman database remains available after the command exits.

To prepare the local application switch after verification, run:

```sh
python3 scripts/create_parallel_database.py switch-application
podman stop saleor_api saleor_celery saleor_bff
podman rm saleor_api saleor_celery saleor_bff
podman-compose up -d api celery bff
```

The switch helper requires the owned database to be `READY`, verifies its
schema and seed data, then creates `.local/parallel-db/database.env` and
`.local/parallel-db/auth.env` once. It refuses to overwrite either file or
rotate the key again. The database URL (and its credential) is supplied only to
Core, Celery, and the inactive audit-retention service; the new shared
`SECRET_KEY` and empty `SECRET_KEY_FALLBACKS` are supplied to Core, Celery, BFF,
and audit retention. The three running application containers must be removed
and recreated explicitly so their process environments change; the command does
not start, stop, or modify containers. Core and Celery join the existing
`bgg_shop_parallel_internal` network as well as `saleor_network`; BFF remains
on `saleor_network` and receives no database credential. Compose no longer
routes application DB traffic to the original `saleor_db`.

Verify the new container environments and IDs after recreation; a successful
`podman-compose up` alone does not prove that existing container environments
changed. Podman may refuse to remove BFF while the existing frontend container
records it as a dependency. If that happens, do not use `podman rm --depend` or
remove/recreate the frontend without separate authorization; the prepared
configuration is not active until all three requested services can be safely
recreated and verified.

Rotating the signing key invalidates old Core access/refresh JWTs and signed
sessions. The old key is not configured as a fallback. Do not roll back by
restoring an old signing key; returning to the original database requires a
separately authorized guarded database configuration while retaining the new
signing key. The original database container and volume are not altered.

The private database credential is generated locally and stored only in
`.local/parallel-db/connection.env` (directory 0700, file 0600, gitignored).
Do not print, source, commit, or share this file. Status/access never reveal its
password. Connect using the new container's local PostgreSQL socket:

```sh
podman exec -it bgg_shop_parallel_db psql -U bgg_shop_parallel -d bgg_shop_parallel
```

The synthetic superuser's username and email are `admin@example.test`. Its
password is **unusable** until you explicitly set it in your local terminal:

```sh
python3 scripts/create_parallel_database.py admin-password
```

This runs Django `changepassword admin@example.test` in a temporary, read-only
Core helper connected only to the parallel database. No admin password is
generated or embedded. The helper is removed after success or failure.

Initialization applies real auth/contenttypes and promotions `0001` migrations,
then the unmanaged commercial **legacy** baseline in
`scripts/sql/parallel_baseline.sql`, then the entire remaining migration graph.
The baseline deliberately retains the legacy review constraint/index required
by graphql `0019`; Django creates promotion/coupon/audit/stock/credit/chat tables
and applies promotions' state synchronization itself. No migrations are faked.
Only the validated 49-product INSERT is extracted from `import_catalog.sql`;
its auth seeds, credentials, gift-card seeds, cleanup, and other SQL are never
executed. Sixteen synthetic paid purchases, immutable line snapshots and
invoices belong to the new superuser, with dates across the last 7/30 days.
They are demonstration data, not real payments or fulfillment operations.

`verify` checks the actual sales GraphQL resolver, exact order/line revenue,
7/30-day metrics, credit schema, no pending migrations, and chat
create/record/history/cross-owner denial/delete using synthetic local assertions
without any model/provider call. Chat test writes roll back. It also runs
`makemigrations --check --dry-run` and reports any existing drift without
changing files. The existing canonical SDL/OpenAPI sales and chat interfaces
remain unchanged; no frontend connection change is authorized by this tool.
Purchases become visible in the sales panel only after a separately authorized
service connection switch.

A failed initialization preserves the new database and marks private state
`FAILED`. `resume-empty` is restricted to this tool's owned, running database
with **zero public tables**; nonempty partial state requires manual diagnosis
and is never automatically repaired, dropped, or reseeded.

Local execution verified 49 products, 16 paid orders/lines/invoices, 31 units,
ARS 4,540,800.00, all 42 migrations, and no model drift. The original database's
schema/migration fingerprints and aggregate counts/revenue were unchanged.
Catalog media URLs and filenames use canonical BGG IDs. The 49 existing assets
were renamed using their own IDs, without changing their content: 16/49 catalog
images are present and 33 remain missing. An HTTP 200 HTML fallback is **not**
an available image; no missing images have been assigned to unrelated games.

Focused safeguard tests:

```sh
PYTHONPATH=. bgg-shop-bff/.venv/bin/python -m pytest -q tests/test_parallel_database_plan.py
```

## Arquitectura actual

```text
Frontend React/Vite ── REST/JSON ──> BFF Flask ── GraphQL ──> Core Django/Graphene
     localhost:3000       :5000                         :8000/graphql/
                               PostgreSQL ◄── Core ──► Redis / Celery
```

El Frontend usa la API REST del BFF; no consume GraphQL directamente. El BFF
adapta y coordina las operaciones del cliente, y el Core aplica las reglas de
dominio y persiste datos en PostgreSQL. Redis presta servicios de broker/cache
al Core y también aloja el límite de solicitudes del chatbot; Celery ejecuta
trabajo asíncrono. El Compose local incluye además Mailpit para correo de
desarrollo.

Los contratos canónicos son [`bgg-shop-bff/specs/openapi.yaml`](bgg-shop-bff/specs/openapi.yaml)
(REST) y [`bgg-shop-core/specs/schema.graphql`](bgg-shop-core/specs/schema.graphql)
(GraphQL). Los tipos del Frontend se generan desde OpenAPI con
`npm run generate:types`; una operación presente en un contrato o en tipos
generados no implica que su flujo esté implementado.

### Estado funcional

El catálogo, autenticación, carrito, Wishlist, checkout/pedidos e interfaz de
administración de métricas tienen implementaciones en los servicios. El
checkout se orienta a Mercado Pago sandbox y requiere configuración propia;
no se incluyen aquí validaciones remotas ni pasos de staging/producción. El
detalle de cada API está en los README de
[BFF](bgg-shop-bff/README.md), [Core](bgg-shop-core/README.md) y
[Frontend](bgg-shop-frontend/README.md).

### Chatbot CU-C07: implementación parcial

Hay una implementación funcional en las capas principales, pero la aceptación
local de extremo a extremo todavía está incompleta:

- El BFF ofrece creación, mensajes, lectura y eliminación de conversaciones,
  aplica el límite de 2.000 caracteres, guardrails de alcance y privacidad, y
  limita solicitudes en Redis. Para usuarios registrados usa el ID verificado
  por Core; para visitantes usa únicamente la cookie `chat_session`.
- Las preguntas frecuentes aprobadas se recuperan desde ChromaDB. La generación
  prioriza OpenRouter cuando está configurado y usa Ollama local
  (`deepseek-r1:8b`) como respaldo; los embeddings siguen siendo locales. Las
  respuestas en inglés y español tienen pruebas enfocadas. Las recomendaciones
  consultan el catálogo actual de Core y no agregan resultados dinámicos al
  índice. La validación local del proveedor externo usa HTTP simulado; no se
  ejecutó una llamada con credenciales reales.
- Core persiste conversaciones y mensajes en PostgreSQL con aislamiento por
  usuario o sesión anónima, e incluye eliminación y tareas de retención. El
  Frontend tiene un widget accesible para preguntas, fuentes y continuidad de
  conversación.
- T030 sigue abierto: falta verificar por HTTP la expiración y el proceso de
  retención, además de cerrar la integración BFF/Core del catálogo y la
  aceptación completa. La prueba de navegador existente simula la API y no
  demuestra por sí sola el flujo entre servicios.

Estado y alcance: [`specs/013-add-chatbot/spec.md`](specs/013-add-chatbot/spec.md),
[`specs/013-add-chatbot/plan.md`](specs/013-add-chatbot/plan.md) y
[`odd/tasks/013-add-chatbot.md`](odd/tasks/013-add-chatbot.md). Implementación:
[`bgg-shop-bff/src/controllers/chatbot_controller.py`](bgg-shop-bff/src/controllers/chatbot_controller.py),
[`bgg-shop-bff/src/chatbot/`](bgg-shop-bff/src/chatbot/),
[`bgg-shop-core/saleor/graphql/api.py`](bgg-shop-core/saleor/graphql/api.py) y
[`bgg-shop-frontend/src/chatbot/`](bgg-shop-frontend/src/chatbot/).
Las pruebas enfocadas y sus límites están registrados en
[`specs/013-add-chatbot/tasks.md`](specs/013-add-chatbot/tasks.md).

## Inicio local con Podman Compose

Prerequisitos: Podman con proveedor Compose instalado. Los valores por defecto
de `podman-compose.yaml` son para desarrollo local (incluyen `DEBUG=True` y
credenciales locales); no los reutilices en un entorno compartido. El checkout
requiere configurar en el entorno del servicio `api` un token de prueba de
Mercado Pago y `MP_SANDBOX=true`; no hace falta para iniciar el resto del
stack. No compartas ni guardes credenciales reales en el repositorio.

## Higiene de secretos y contextos de contenedor

Los `.gitignore` de la raíz y los servicios excluyen `.env` y `.env.*`; solo
`.env.example` y `.env.template` quedan permitidos para plantillas sin
credenciales reales. Cada contexto de build de Core, BFF y Frontend tiene un
`.dockerignore` que excluye archivos privados, repositorios Git, datos locales,
cachés y respaldos. No agregues credenciales a las imágenes ni amplíes estas
excepciones para incluir archivos de entorno reales.

Desde la raíz del repositorio:

```bash
podman compose -f podman-compose.yaml up -d --build
podman compose -f podman-compose.yaml exec api python manage.py migrate
```

Cuando los servicios estén iniciados, las direcciones publicadas por el
Compose son:

| Componente | Dirección local |
| --- | --- |
| Frontend | `http://localhost:3000` |
| BFF | `http://localhost:5000` |
| Core GraphQL/GraphiQL | `http://localhost:8000/graphql/` |
| PostgreSQL | `localhost:5432` |
| Redis | `localhost:6379` |
| Mailpit | `http://localhost:8025` |

El BFF se conecta al Core dentro de la red Compose mediante
`http://api:8000/graphql/`; el navegador usa el BFF en
`http://localhost:5000/api/v1`. La base de datos del Compose no importa
automáticamente un catálogo: los resultados de catálogo dependen de que haya
datos disponibles en PostgreSQL.

Para detener los contenedores sin borrar los volúmenes de datos:

```bash
podman compose -f podman-compose.yaml down
```
