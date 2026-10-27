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

---

## PR / MR Gating Policy (Project-wide)

- No crear ni preparar un `PR` o `MR` que incluya cambios en las rutas admin, contratos OpenAPI, o flujos end-to-end relacionados con `manage-catalog-inventory` hasta que se cumplan las siguientes condiciones obligatorias:
   1. Validación integral del flujo front <-> bff <-> core completada y con resultados reproducibles.
   2. Suite de QA (automatizada y/o pruebas manuales críticas) ejecutada y aprobada para los flujos afectados.
   3. Evidencias adjuntas (logs, reportes de tests, capturas o enlaces a pipelines) asociadas a la tarea/feature en `odd/tasks/`.

- Mientras no se cumplan estas condiciones, las ramas con estos cambios no deben ser empujadas a `main` ni abrir PR/MR hacia ramas de integración. Cualquier excepción requiere aprobación explícita del dueño del repositorio o del responsable de QA.

Esta política aplica a todos los agentes y flujos automatizados que ejecuten tareas en esta plataforma (orquestadores, writers, CI). Registra la evidencia en `odd/tasks/<feature>.md` antes de intentar preparar un PR/MR.

Loader: the orchestrator will automatically load the agent→task mapping from `0. Orchestrator/agent_task_mapping.json` using the helper script `0. Orchestrator/load_agent_mapping.py`. This file is the machine-readable source of truth for delegation rules; update it when responsibilities change.

Quick check (local):

```bash
python "0. Orchestrator/load_agent_mapping.py" --print
```

Manual reload / restart policy

- The orchestrator loads `0. Orchestrator/agent_task_mapping.json` once at process start. To apply updates to the JSON you must restart the orchestrator process (manual restart).
- Recommended minimal steps to reload mapping:
   1. Verify the new mapping locally:

```bash
python "0. Orchestrator/load_agent_mapping.py" --print
```

   2. Restart the orchestrator process. Examples (pick the one that matches your deployment):

```bash
# systemd-managed service
sudo systemctl restart orchestrator.service

# background process started with nohup / screen / tmux
pkill -f "orchestrator" && nohup python path/to/orchestrator_main.py &

# Kubernetes: rollout restart the deployment
kubectl rollout restart deployment/orchestrator -n your-namespace
```

- After restart, confirm the mapping is loaded by running the quick check above on the orchestrator host or in its environment.
- Note: If you need hot-reload without restart, consider using the file `mtime` check or a watcher; we can implement that later if desired.
 - Hot-reload: the orchestrator now supports hot-reload by checking the `mtime` of `0. Orchestrator/agent_task_mapping.json` at load time. The helper `0. Orchestrator/load_agent_mapping.py` performs cached loads and automatically reloads the mapping when the file timestamp changes. Use the `--no-cache` flag to force a disk read.
