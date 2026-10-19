# CU-C01: Registro, login y cierre de sesión

## 1. Propósito

Este documento consolida el diseño, las decisiones, los contratos, la
implementación y la evidencia de verificación del caso de uso **CU-C01:
Gestionar identidad y autenticación de usuario**.

El alcance implementado es:

```text
Frontend React/Vite → REST/JSON → BFF Flask → GraphQL → Core Django → PostgreSQL
```

El navegador solo conoce la API REST del BFF. El Core es la fuente de verdad
para usuarios, contraseñas y emisión de tokens.

## 2. Alcance funcional

### Incluido

- Registro con email, contraseña, nombre y apellido.
- Login con email y contraseña.
- Validación local de formularios y validación de payload en el BFF.
- Persistencia mediante `django.contrib.auth.models.User`.
- Hash de contraseña mediante `create_user`.
- Emisión de JWT access/refresh en el login.
- Sesión local del frontend en `sessionStorage`.
- Header adaptado al estado de sesión.
- Cierre de sesión eliminando la sesión local y navegando al catálogo.
- Tratamiento de errores de validación, credenciales, duplicados y upstream.

### Fuera de alcance

- Google OAuth u otros proveedores externos.
- Confirmación de email.
- Recuperación o cambio de contraseña.
- Rotación o revocación server-side de refresh tokens.
- Cookies `HttpOnly`.
- Roles, permisos administrativos y metadata de usuario.
- Sesión automática después del registro.

## 3. Decisiones de diseño

| Decisión | Motivo y consecuencia |
| --- | --- |
| Solo credenciales locales | Mantiene el primer corte pequeño y evita introducir OAuth antes de contar con el flujo base. |
| Email + contraseña como credenciales | Es suficiente para el comprador y coincide con el modelo de identidad seleccionado. |
| Registro sin auto-login | El usuario recibe confirmación y es redirigido a `/login`; no se emiten tokens durante el alta. |
| `django.contrib.auth.User` | Reutiliza la identidad estándar de Django y evita duplicar tablas o modelos de usuario. |
| Frontend consume únicamente BFF | Aísla GraphQL y las reglas internas del navegador. |
| REST en `snake_case`, GraphQL en `camelCase` | Conserva las convenciones de cada contrato y concentra la adaptación en el BFF. |
| `sessionStorage` | Limita la duración de la sesión al contexto de la pestaña y no persiste tokens en `localStorage`. |
| Logout local | Elimina access/refresh token del navegador; la revocación server-side queda pendiente para una iteración futura. |
| Evento `bgg-shop:session-change` | `storage` no notifica al mismo documento que escribió la sesión; el evento permite actualizar el header inmediatamente tras login/logout. |
| Sin React Router | El proyecto ya utiliza History API y `popstate`; no se agrega una dependencia para dos rutas. |

## 4. Contrato GraphQL del Core

Fuente: [`bgg-shop-core/specs/schema.graphql`](../bgg-shop-core/specs/schema.graphql).

### Inputs

```graphql
input RegisterInput {
  email: String!
  password: String!
  firstName: String!
  lastName: String!
}

input LoginInput {
  email: String!
  password: String!
}
```

### Tipos de salida

```graphql
type User {
  id: ID!
  email: String!
  firstName: String!
  lastName: String!
  isActive: Boolean!
}

type AuthToken {
  token: String
  refreshToken: String
  csrfToken: String
}

type UserError {
  field: [String!]
  code: String!
  message: String!
}
```

### Mutaciones

```graphql
type Mutation {
  register(input: RegisterInput!): RegisterPayload!
  login(input: LoginInput!): LoginPayload!
}
```

`register` devuelve `user` y `errors`; `tokens` permanece vacío. `login`
devuelve `user`, `tokens` y `errors`.

### Reglas del Core

- El email se recorta y normaliza con `casefold()`.
- El duplicado se informa con código `DUPLICATE_EMAIL`.
- El login utiliza `authenticate`.
- Credenciales inválidas devuelven `INVALID_CREDENTIALS` sin enumerar si el
  email existe.
- No se exponen contraseña ni hash en `User`.
- Los JWT se firman con `settings.SECRET_KEY`, algoritmo `HS256`, expiración
  de 15 minutos para access token y 30 días para refresh token.
- Los claims emitidos incluyen `sub`, `iat`, `exp` y `token_type`.

## 5. Contrato REST del BFF

Fuente: [`bgg-shop-bff/specs/openapi.yaml`](../bgg-shop-bff/specs/openapi.yaml).

### Registro

`POST /api/v1/auth/register`

```json
{
  "email": "player@example.test",
  "password": "Boardgame-Test-123!",
  "first_name": "Test",
  "last_name": "Player"
}
```

Respuesta `201`:

```json
{
  "user": {
    "id": "1",
    "email": "player@example.test",
    "first_name": "Test",
    "last_name": "Player",
    "is_active": true
  }
}
```

El registro no devuelve `session`.

### Login

`POST /api/v1/auth/login`

```json
{
  "email": "player@example.test",
  "password": "Boardgame-Test-123!"
}
```

Respuesta `200`:

```json
{
  "user": {
    "id": "1",
    "email": "player@example.test",
    "first_name": "Test",
    "last_name": "Player",
    "is_active": true
  },
  "session": {
    "access_token": "<JWT>",
    "refresh_token": "<JWT>",
    "csrf_token": null
  }
}
```

### Mapeo de errores

| Situación | HTTP | Código público |
| --- | ---: | --- |
| Body no JSON/objeto o campo inválido | 400 | `INVALID` |
| Email o contraseña incorrectos | 401 | `INVALID_CREDENTIALS` |
| Email ya registrado | 409 | `EMAIL_EXISTS` |
| Core inaccesible, GraphQL inválido o payload inesperado | 502 | error genérico de upstream |

El BFF acepta tanto `DUPLICATE_EMAIL` como `EMAIL_EXISTS`/`UNIQUE` desde el
Core y los normaliza a `409`/`EMAIL_EXISTS`. Las respuestas `502` no exponen
detalles internos del Core, credenciales ni mensajes de infraestructura.

## 6. Responsabilidades por capa

### Frontend

Archivos principales:

- [`src/App.tsx`](../bgg-shop-frontend/src/App.tsx): rutas, header, estado
  autenticado y logout.
- [`src/auth/AuthScreens.tsx`](../bgg-shop-frontend/src/auth/AuthScreens.tsx):
  formularios, validación, requests REST y persistencia de sesión.
- [`src/auth/session.ts`](../bgg-shop-frontend/src/auth/session.ts): clave y
  evento de sincronización de sesión.
- [`src/App.css`](../bgg-shop-frontend/src/App.css): estilos de pantallas y
  navegación.

Comportamiento:

1. `/register` valida nombre, apellido, email, contraseña y confirmación.
2. `/login` valida email y contraseña.
3. El formulario muestra loading, errores por campo, error general y éxito.
4. El login guarda únicamente la sesión recibida en
   `sessionStorage['bgg-shop.session']` y vuelve a `/`.
5. El registro muestra confirmación y navega a `/login`, sin guardar tokens.
6. Un visitante ve “Iniciar sesión” y “Crear cuenta”.
7. Un usuario con sesión ve “Cerrar sesión”.
8. Logout elimina `bgg-shop.session`, emite el evento local y actualiza el
   header.
9. “Crear cuenta” usa el mismo tratamiento visual de enlace que “Catálogo”.

### BFF

Archivos principales:

- [`app.py`](../bgg-shop-bff/app.py): configuración Flask, CORS y registro de
  rutas.
- [`src/dtos/auth.py`](../bgg-shop-bff/src/dtos/auth.py) y
  [`src/dtos/products.py`](../bgg-shop-bff/src/dtos/products.py): DTOs de
  contrato para payloads de autenticación y catálogo.
- [`src/controllers/auth_controller.py`](../bgg-shop-bff/src/controllers/auth_controller.py),
  [`src/controllers/products_controller.py`](../bgg-shop-bff/src/controllers/products_controller.py)
  y [`src/controllers/health_controller.py`](../bgg-shop-bff/src/controllers/health_controller.py):
  adaptación HTTP, serialización de respuestas y códigos de error por recurso.
- [`src/services.py`](../bgg-shop-bff/src/services.py): servicios de
  autenticación y catálogo que orquestan las operaciones del BFF.
- [`src/proxy.py`](../bgg-shop-bff/src/proxy.py): cliente GraphQL, validación
  específica de dominio y adaptación de nombres.

El BFF no persiste usuarios, no hashea contraseñas y no implementa las reglas
de identidad. Los controllers manejan HTTP, los services coordinan los casos
de uso y el proxy mantiene la comunicación GraphQL con el Core. Esta
separación mantiene la validación del contrato público y evita filtrar detalles
internos sin introducir un framework de inyección de dependencias.

### Core

Archivos principales:

- [`saleor/graphql/api.py`](../bgg-shop-core/saleor/graphql/api.py):
  mutaciones Graphene y emisión de JWT.
- [`specs/schema.graphql`](../bgg-shop-core/specs/schema.graphql): contrato
  fuente.
- Django `User`: persistencia y hash de contraseña.

No se creó una tabla de usuario paralela ni una migración específica para este
caso de uso.

## 7. Flujos

### Registro exitoso

```text
Usuario → /register
        → valida formulario
        → POST BFF /api/v1/auth/register
        → GraphQL register(input)
        → Django User.create_user()
        → BFF 201 sin session
        → frontend muestra éxito
        → navegación a /login
```

### Login exitoso

```text
Usuario → /login
        → valida formulario
        → POST BFF /api/v1/auth/login
        → GraphQL login(input)
        → Django authenticate()
        → Core firma JWT
        → BFF 200 con user/session
        → sessionStorage
        → evento de sesión
        → navegación a /
        → header muestra Cerrar sesión
```

### Logout

```text
Usuario → Cerrar sesión
        → removeItem('bgg-shop.session')
        → emite bgg-shop:session-change
        → header vuelve a estado visitante
        → catálogo permanece en /
```

## 8. Seguridad y límites conocidos

- Los passwords se envían por `POST` y no se incluyen en URLs, logs ni
  respuestas.
- El Core almacena hashes mediante la API estándar de Django.
- El BFF no devuelve mensajes internos para fallos inesperados.
- `sessionStorage` reduce persistencia frente a `localStorage`, pero sigue
  siendo accesible a JavaScript de la misma origin; una política de
  producción debe considerar cookies `HttpOnly`, `Secure` y `SameSite`.
- Logout elimina los tokens del navegador, pero no revoca tokens ya emitidos
  en el Core. La API que consuma JWT debe validar expiración y firma.
- El `SECRET_KEY` por defecto del entorno de desarrollo no es aceptable para
  producción; debe ser obligatorio y secreto fuera de desarrollo.
- No hay todavía recuperación de contraseña, refresh endpoint, rotación ni
  blacklist de refresh tokens.

## 9. Verificación ejecutada

### Pruebas automatizadas

```text
bgg-shop-core:    python3 -m pytest -q  → 6 passed
bgg-shop-bff:     python3 -m pytest -q  → 19 passed
frontend:         npm run test:report  → 15 passed
frontend:         npm run build        → passed
frontend:         npm run lint         → passed
```

El lint conserva un warning preexistente sobre `setState` dentro de un efecto
en [`src/App.tsx:74`](../bgg-shop-frontend/src/App.tsx:74).

### Flujo HTTP real

Con los servicios locales levantados se verificó:

| Escenario | Resultado |
| --- | --- |
| Registro válido | `201` |
| Registro duplicado | `409` |
| Login válido | `200`, access/refresh presentes |
| Contraseña inválida | `401` |
| Payload inválido | `400` |

Los valores reales de tokens no se conservaron en la documentación.

### Prueba de navegador

No se ejecutó automatización Playwright porque el entorno no tenía Chromium
instalado. Las pruebas de componente y el flujo HTTP sí fueron ejecutados.

## 10. Archivos de referencia

- Contrato GraphQL:
  [`bgg-shop-core/specs/schema.graphql`](../bgg-shop-core/specs/schema.graphql)
- Contrato OpenAPI:
  [`bgg-shop-bff/specs/openapi.yaml`](../bgg-shop-bff/specs/openapi.yaml)
- Resolver Core:
  [`bgg-shop-core/saleor/graphql/api.py`](../bgg-shop-core/saleor/graphql/api.py)
- Proxy y rutas BFF:
  [`bgg-shop-bff/src/proxy.py`](../bgg-shop-bff/src/proxy.py) y
  [`bgg-shop-bff/app.py`](../bgg-shop-bff/app.py)
- Pantallas y sesión:
  [`bgg-shop-frontend/src/auth/AuthScreens.tsx`](../bgg-shop-frontend/src/auth/AuthScreens.tsx),
  [`bgg-shop-frontend/src/auth/session.ts`](../bgg-shop-frontend/src/auth/session.ts)
- Pruebas BFF:
  [`bgg-shop-bff/tests/test_auth.py`](../bgg-shop-bff/tests/test_auth.py)
- Pruebas frontend:
  [`bgg-shop-frontend/src/auth/AuthScreens.test.tsx`](../bgg-shop-frontend/src/auth/AuthScreens.test.tsx)
