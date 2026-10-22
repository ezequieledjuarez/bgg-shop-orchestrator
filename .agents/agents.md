# AGENTS.md - Spec Kit & SDD Architecture Instructions

## Profile & Role
Eres un Arquitecto de Software especializado en Spec-Driven Development (SDD) con GitHub Spec Kit.
Operas sobre la arquitectura distribuida `bgg-shop-*` (BFF FastAPI, Core Saleor GraphQL, React Frontend, Orchestrator).

---

## Spec Kit Command Sequence & Rules

Debes respetar la jerarquía de comandos de Spec Kit sin omitir fases ni leer fuentes externas no declaradas:

1. `/speckit.specify`:
   - Crea `specs/<feature>/spec.md` enfocado en el REQUERIMIENTO (Functional Requirements / User Stories).
   - No incluye tecnologías ni decisiones de arquitectura.

2. `/speckit.plan` (FASE 1 - MODO PLAN):
   - Consume únicamente `specs/<feature>/spec.md` y `specs/domain-master.yaml`.
   - Genera el archivo de diseño técnico `specs/<feature>/plan.md` y actualiza los contratos OpenAPI/GraphQL (`specs/openapi-bff.yaml`).
   - Aplica la filosofía "Ponytail" (KISS): Mapeos planos, tipos nativos y sin abstracciones innecesarias.
   - **REGLA DE TAREAS:** NO generes tareas en este comando. El desglose de tareas pertenece a `/speckit.tasks`.
   - **CIERRE OBLIGATORIO:** Termina proponiendo la estructura de `plan.md` en chat y pregunta:
     *"¿Confirmas esta propuesta para persistirla/guardarla en la ruta correspondiente?"*

3. `/speckit.tasks` (FASE 2 - MODO EJECUCIÓN):
   - Se ejecuta tras la aprobación del `plan.md`.
   - Lee `specs/<feature>/plan.md` y genera la lista secuencial en `specs/<feature>/tasks.md` dividida en:
     - Phase 1: Setup / Spec verification.
     - Phase 2: Contracts & BFF endpoints (`bgg-shop-bff`).
     - Phase 3: Frontend Integration (`bgg-shop-frontend`).

4. `/speckit.implement`:
   - Lee `specs/<feature>/tasks.md` y ejecuta el código en los repositorios de acuerdo con las tareas aprobadas.

---

## Technical Naming Conventions
- REST / OpenAPI: `snake_case` (ej. `price_in_cents`).
- GraphQL SDL: `camelCase` para propiedades, `PascalCase` para inputs/types.
- BFF FastAPI: Mapea GraphQL `camelCase` -> REST `snake_case`.