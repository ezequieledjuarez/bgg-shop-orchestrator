# BGG Shop

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
