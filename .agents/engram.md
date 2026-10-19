# Skill: Engram Multi-Project Router

## Contexto
El workspace contiene múltiples proyectos registrados en Engram (`bgg-shop-orchestrator`, `bgg-shop-core`, `bgg-shop-bff`, `bgg-shop-frontend`). Para evitar el error de ambigüedad al persistir sesiones/memorias, siempre se debe especificar el parámetro `--project`.

## Regla de Persistencia
Antes de realizar el guardado o síntesis de sesión en Engram, identifica el repositorio sobre el cual se realizaron las modificaciones y ejecuta el comando con el flag explícito:

- Cambios en `bgg-shop-frontend/` -> `engram save --project bgg-shop-frontend`
- Cambios en `bgg-shop-bff/`      -> `engram save --project bgg-shop-bff`
- Cambios en `bgg-shop-core/`     -> `engram save --project bgg-shop-core`
- Cambios en `specs/` u orquestador -> `engram save --project bgg-shop-orchestrator`