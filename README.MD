# BGG Shop

## Arquitectura y servicios expuestos

El flujo previsto separa la interfaz de la API de dominio:

```text
Frontend React/Vite ── REST/JSON (previsto) ──> BFF Flask ── GraphQL ──> Core Django
       (client-only hoy)                         :5000                  :8000
```

El Frontend consume el catálogo y la autenticación a través del BFF REST. El
BFF traduce esas operaciones a consultas y mutaciones GraphQL del Core. El
Core consulta `product_boardgame` y persiste usuarios mediante Django Auth; su
endpoint GraphQL está habilitado con GraphiQL.

### Servicios y operaciones actuales

| Servicio | Método | Ruta u operación | Request | Response / error |
| --- | --- | --- | --- | --- |
| Frontend | — | — | No recibe requests de API. | Renderiza la vista client-only y datos mock; no tiene errores de API propios. |
| BFF | `GET` | `/health` | Sin parámetros. | `200` y `{"status":"healthy"}`. |
| BFF | `GET` | `/api/v1/products` | `page` y `page_size` opcionales; positivos, `page_size <= 100`. | `200` con `ProductPage` REST; `400` por paginación inválida; `502` por fallo o payload inválido del Core. |
| Core | `POST` | `/graphql/` (`hello`, `products`) | Body JSON GraphQL; `page` y `pageSize` opcionales para `products`. | Datos GraphQL; errores en `errors`. GraphiQL está habilitado en la ruta. |

Los contratos completos y ejemplos están en los README de cada servicio:
[`bgg-shop-bff/README.md`](bgg-shop-bff/README.md),
[`bgg-shop-core/README.md`](bgg-shop-core/README.md) y
[`bgg-shop-frontend/README.md`](bgg-shop-frontend/README.md).

### URLs locales verificadas

Con `podman-compose.yaml` se publican estos puertos:

- Frontend: `http://localhost:3000`
- BFF: `http://localhost:5000`
- Core GraphQL/GraphiQL: `http://localhost:8000/graphql/`

La URL `SALEOR_GRAPHQL_URL` usada por el BFF dentro de Compose es
`http://api:8000/graphql/`. Los servicios de persistencia (`db` y `redis`)
no forman parte de la API pública documentada aquí.

### Autenticación implementada

El caso de uso CU-C01 está integrado para credenciales locales:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- Pantallas frontend `/register` y `/login`
- Sesión de login en `sessionStorage` y cierre de sesión desde el catálogo

La trazabilidad completa de contratos, decisiones, flujo y pruebas está en
[`docs/CU-C01-AUTHENTICATION-CHANGES.md`](docs/CU-C01-AUTHENTICATION-CHANGES.md).

El caso de uso CU-C04 (carrito) está implementado: el stock (`quantity`) se
muestra en el catálogo y el carrito admite agregar, modificar y quitar
artículos con total calculado, sin reservar stock.

El caso de uso CU-C05 (compra) está implementado solo para el entorno de
pruebas de Mercado Pago: checkout con dirección de entrega, orden y factura
persistidas, descuento de stock al aprobarse el pago, factura PDF y vista
"Mis Compras". Requiere `MP_ACCESS_TOKEN` (credencial de prueba) y
`MP_SANDBOX=true` en el servicio `api`; ver `.env.example`. La validación en
vivo del flujo completo está pendiente.

## Configuración inicial del proyecto

Python version 3.12.8
Node version 20

- Verificar si node y python están instalados
1. 
- Si están instalados:
1. npm -v && pip --version
- Verificar si la versión de node requerida está instalada:
1. nvm list 
# La versión que se va a usar es la 20. La 20 LTS es la 20.20.2.
   
- Si no están instalados 
- Para NODE:
1. curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
2. source ~/.bashrc57  
3. nvm install 20.20.2
4. nvm --version
- Para PYTHON (En LINUX generalmente ya viene instalado)
1. which python
2. which python3
# Si which python no devuelve nada
1. sudo apt install python3 python3-pip python3-venv -y
2. sudo apt update && sudo apt install -y nodejs npm
3. sudo apt install python3 python3-pip python3-venv -y
4.   echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
     echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
     echo 'eval "$(pyenv init -)"' >> ~/.bashrc
# Recargar la configuración
1. source ~/.bashrc
2. which python
3. pyenv local 3.12.8
- Volver a ejecutar
1. node -v && python --version
2. npm -v && pip --version
- Opcional ejecutar:
1. sudo apt update
2. apt list --upgradable
3. sudo apt upgrade

- Para el proyecto en Python:
- Crear un entorno virtual en la raíz del proyecto con la versión de PYTHON a utilizar (3.12.8):
1. pyenv local 3.12.8
2. python -m venv .venv
3. pip install requests pandas sqlalchemy psycopg2-binary pydantic

- Para el proyecto en React:
1. npm create vite@latest bgg-shop-frontend -- --template react-ts
2. cd bgg-shop-frontend
3. npm install
4. npm install @apollo/client graphql
5. npx skills add vercel-labs/agent-skills
  # https://vercel.com/blog/introducing-react-best-practices


- Para los contenedores (PODMAN):
1. sudo apt-get -y install podman
2. sudo apt update && sudo apt install podman-compose
3. podman compose up -d --build
# En %USERPROFILE%
4. cd .config
5. mkdir containers && cd containers
6. touch registries.conf
  # Local
  # unqualified-search-registries = ["docker.io", "quay.io"]
7. podman compose up -d