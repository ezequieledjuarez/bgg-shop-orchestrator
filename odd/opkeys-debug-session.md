# Sesión: Depuración OpKeys — create_product admin

Fecha: 2026-10-26
Autor: Copilot (resumen de la sesión)

## Contexto
Trabajo multi-repo: `bgg-shop-frontend` (Playwright), `bgg-shop-bff` (Flask) y `bgg-shop-core` (Django/Graphene). Objetivo inmediato: hacer funcionar de forma determinista el "create product" admin cuando el frontend usa `X-Op-Key` en lugar de Authorization bearer.

## Cambios intentados
- BFF
  - `src/proxy.py`: añadir `op_key` como parámetro en `_graphql_request` y forward de headers.
  - `src/services.py`: pasar `op_key`/`token` desde servicios hacia `proxy` y fallback a `BFF_ADMIN_TOKEN` o `/tmp/bff_admin_token`.
  - `src/controllers/admin_products_controller.py`: adjuntar `validated["_op_key"]` y `_auth_token`.
  - `src/opkey_middleware.py`: validar `X-Op-Key` contra Core `/internal/op-validate` y cachear el resultado en `g`.
  - Logging persistente en `/tmp` para traza y correlación (`bff-calltrace.log`, `bff-graphql-outgoing.log`, `bff-opkey.log`).

- Core
  - `opkeys` app: `op-create`, `op-validate`, `op-revoke` en `opkeys/views.py` y `opkeys/urls.py`.
  - Registrar `opkeys.middleware.OpKeyAuthMiddleware` en `saleor/settings.py` para aceptar `X-Op-Key` y mapear a `request.user`.
  - `LoginMutation` (`saleor/graphql/api.py`): lógica para emitir `tokens.op_key` cuando `OPKEYS_ISSUE_ON_LOGIN=true` y `user.is_staff`.

## Qué falló / entendimientos por qué
- Intermitencia: BFF a veces envía la petición upstream con `"headers": {}` (sin `X-Op-Key` ni `Authorization`) según `/tmp/bff-graphql-outgoing.log` → ocurre de forma intermitente.
- Login no devuelve `op_key` para `ezze.juarezz@gmail.com` porque `OPKEYS_ISSUE_ON_LOGIN` está `false` por defecto y no definido en `.env`.
- `op_validate` a veces devuelve `user_id: null` — indica que la `OpSession` fue creada sin `user_id` (o creado con user_id nulo) en algunos casos de prueba/manual.
- Core sigue devolviendo `UNAUTHENTICATED` para `createProduct` en runs donde BFF no envió `Authorization` ni `X-Op-Key` correctamente.
- Posible causa adicional: orden/alcance del middleware en Core (que valide `X-Op-Key` antes del guard de GraphQL) o rutas donde BFF no está propagando headers debido a un code-path que limpia headers antes del `requests.post`.

## Estado actual
- Endpoints BFF listos y OpenAPI disponible (`bgg-shop-bff/specs/openapi.yaml`); colección Insomnia combinada creada en `insomnia/bgg-shop-both-insomnia.json`.
- Core expone `/internal/op-create`, `/internal/op-validate`, `/internal/op-revoke` y `POST /graphql/`.
- BFF valida `X-Op-Key` contra Core y puede usar fallback `BFF_ADMIN_TOKEN` cuando está presente.
- `create_product` admin funciona solo cuando BFF consigue enviar `Authorization` (fallback) o cuando upstream recibe headers correctos; de otro modo devuelve `UNAUTHENTICATED`.

## Estado deseado
1. Crear productos admin determinísticamente cuando el cliente envía `X-Op-Key` (sin bearer).
2. `Login` para staff devuelve `op_key` en el `session.tokens` o BFF crea/retorna `op_key` automáticamente.
3. BFF siempre forwardea credenciales en petición saliente (sin `headers: {}` vacíos).
4. `op_validate` siempre devuelve `user_id` para sesiones creadas con `user_id`.
5. Logs correlacionados con `request_id` entre controller entrante y petición GraphQL saliente.

## Próximos pasos recomendados (priorizados)
1. Habilitar `OPKEYS_ISSUE_ON_LOGIN=true` en `.env` (rápido) para que logins de staff entreguen `op_key` y poder probar flujo completo desde frontend.
2. Añadir logging justo antes del `requests.post` en `bgg-shop-bff/src/proxy.py` para capturar exactamente qué headers y payload se intentan enviar cuando aparecen `headers: {}` (diagnóstico crítico).
3. Verificar que `OpSession` se crea con `user_id` en todos los lugares relevantes (login y llamadas a `op-create` automáticas). Corregir creación manual si corresponde.
4. Si Core no aplica `OpKeyAuthMiddleware` antes de la autorización GraphQL, mover middleware más arriba o asegurar que la vista GraphQL vea el `request.user` mapeado por `OpKeyAuthMiddleware`.
5. Alternativa robusta: implementar en BFF intercambio op_key→token (interno) y siempre enviar `Authorization` upstream. Esto resuelve dependencia del orden del middleware y es más explícito.

## Acciones concretas que puedo ejecutar ahora (confirmame)
- A) Editar `./.env` y poner `OPKEYS_ISSUE_ON_LOGIN=true` y darte el comando para reiniciar (o ejecutarlo si autorizás).
- B) Añadir logs temporales en `bgg-shop-bff/src/proxy.py` para capturar headers justo antes de la llamada upstream y reiniciar BFF para reproducir y recopilar diagnóstico.
- C) Generar un `op_key` de prueba con `POST /internal/op-create` (ya tengo la colección Insomnia creada) y pasarlo al frontend para una prueba manual.
- D) Implementar intercambio op_key→token en BFF (cambio más grande), prueba y validar.

## Dudas / confirmaciones
- ¿Querés que habilite `OPKEYS_ISSUE_ON_LOGIN` en el entorno ahora para acelerar pruebas, o preferís que generemos claves manualmente con `/internal/op-create`? 
- Para la solución final, ¿preferís que Core acepte `X-Op-Key` directamente (middleware) o que BFF intercambie `op_key` por `Authorization` al llamar a GraphQL?

---

Si confirmás, ejecuto la opción que elijas y dejo los cambios/enlaces de logs. Gracias.