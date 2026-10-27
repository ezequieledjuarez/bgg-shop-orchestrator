# T001 — Matriz de cobertura: OpenAPI ↔ Handlers BFF ↔ DTOs ↔ Tests

Fecha: 2026-10-22

Resumen: esta matriz compara las rutas/operaciones administrativas implementadas en el BFF con la especificación OpenAPI, los controladores (`src/controllers`), los DTOs (`src/dtos`) y las pruebas existentes (`tests/`). Marca gaps y recomendaciones.

## Observaciones generales
- OpenAPI principal (`bgg-shop-bff/specs/openapi.yaml`) expone la API pública bajo `/api/v1/...` (productos, carrito, checkout, wishlist, orders, etc.).
- Las rutas administrativas del BFF (`/admin/...`) están implementadas en `src/controllers/*` pero no aparecen en la `specs/openapi.yaml` (gap de contrato). Decidir si las rutas admin deben incluirse en OpenAPI o quedar fuera del contrato público.

## Matriz (resumen por ruta administrativa)

- `/admin/products` (GET)
  - Handler: `src/controllers/admin_products_controller.admin_list_products`
  - DTOs: none (query args handled ad-hoc)
  - Tests: `tests/test_admin.py::test_admin_allows_admin_and_returns_list`
  - OpenAPI: *NO* (gap)

- `/admin/products` (POST)
  - Handler: `src/controllers/admin_products_controller.admin_create_product`
  - DTOs: `src/dtos/products.AdminCreateProductDto`
  - Tests: `tests/test_admin_validation.py::test_create_product_requires_name_and_valid_fields`, `tests/test_admin_error_mapping.py::test_create_product_maps_user_error_to_400_with_field`
  - OpenAPI: *NO* (gap)

- `/admin/products/<product_id>` (update)
  - Handler: `src/controllers/admin_products_controller.admin_update_product`
  - DTOs: `src/dtos/products.AdminUpdateProductDto`
  - Tests: *No direct tests found* (gap: add unit/contract test)
  - OpenAPI: *NO* (gap)

- `/admin/products/<product_id>/variants/<variant_id>/adjust-stock` (POST)
  - Handler: `src/controllers/admin_products_controller.admin_adjust_variant_stock`
  - DTOs: `src/dtos/products.AdjustStockDto`
  - Tests: `tests/test_admin_validation.py::test_adjust_stock_requires_integer_and_non_negative`, `tests/test_admin_error_mapping.py::test_adjust_stock_maps_user_error_to_400_with_field`
  - OpenAPI: *NO* (gap)

- `/admin/promotions` (GET)
  - Handler: `src/controllers/admin_promotions_controller.admin_list_promotions`
  - DTOs: none for listing
  - Tests: `tests/test_admin_promotions.py::test_promotions_list_requires_auth`
  - OpenAPI: *NO* (gap)

- `/admin/promotions` (POST)
  - Handler: `src/controllers/admin_promotions_controller.admin_create_promotion`
  - DTOs: `src/dtos/promotions.PromotionCreateDto`
  - Tests: `tests/test_admin_promotions.py::test_promotions_create_validation_and_success`
  - OpenAPI: *NO* (gap)

- `/admin/promotions/<promotion_id>` (update)
  - Handler: `src/controllers/admin_promotions_controller.admin_update_promotion`
  - DTOs: `src/dtos/promotions.PromotionUpdateDto`
  - Tests: *No direct tests found* (gap)
  - OpenAPI: *NO* (gap)

- `/admin/coupons/{code}/apply` (POST)
  - Handler: `src/controllers/admin_coupons_controller.admin_apply_coupon_preview`
  - DTOs: `src/dtos/coupons.CouponApplyDto`
  - Tests: `tests/test_admin_coupons.py::test_coupons_apply_preview_success`, `tests/test_admin_coupons.py::test_coupons_apply_user_error_maps_400`
  - OpenAPI: *NO* (gap)

## DTO inventory (used by admin handlers)
- `src/dtos/products.AdminCreateProductDto`
- `src/dtos/products.AdminUpdateProductDto`
- `src/dtos/products.AdjustStockDto`
- `src/dtos/promotions.PromotionCreateDto`
- `src/dtos/promotions.PromotionUpdateDto`
- `src/dtos/coupons.CouponApplyDto`

## Tests que sirven como cobertura/contrato (contratos simulados)
- `tests/test_admin*.py` — verification of admin auth, error mapping and basic flows
- `tests/test_admin_validation.py` — DTO validation checks
- `tests/test_admin_error_mapping.py` — mapping of `UpstreamError(user_error)` → HTTP 400 with `errors[]`

## Gaps y riesgos identificados
- Las rutas administrativas no están presentes en `specs/openapi.yaml` — riesgo de que el frontend u otros consumidores no tengan contrato oficial para admin. Decidir publicar (y si es así, con qué seguridad/oauth scopes) o mantener admin fuera del contrato público.
- Falta de tests para `admin_update_product` y `admin_update_promotion` (handlers implementados pero no cubiertos). Añadir tests unitarios/contractuales.
- OpenAPI documenta `api/v1` público mientras el BFF implementa endpoints `/admin/*` — hay que decidir si OpenAPI debe ampliarse con un tag `Admin` y operaciones protegidas o crear un OpenAPI privado separado.
- Algunos handlers usan ad-hoc query args (e.g., admin_list_products reads `page`/`page_size`); estandarizar DTOs para query params ayudaría a la matriz y validación.

## Recomendaciones y siguientes pasos
1. Confirmar intención: ¿incluir rutas admin en `specs/openapi.yaml` (privado o público)? Si sí, ejecutar T003 para agregar operaciones y esquemas.
2. Añadir tests faltantes para `admin_update_product` y `admin_update_promotion` (unit + service-mock).
3. Normalizar query param DTOs (ej. `ProductQuery`) y usar consistentemente en `admin_list_products` (reduce discrepancias T001→T005).
4. Automatizar la matriz: crear un script pequeño que extraiga `operationId`s de OpenAPI y haga grep en `src/controllers` para encontrar handlers, produciendo CSV/Markdown (útil para mantener la matriz actualizada).
5. Documentar decision: si admin se publica en OpenAPI, añadir seguridad `BearerAuth` + role annotation y actualizar `tests/CONTRACTS_README.md` con los comandos de verificación.

## Task → Agent mapping (recomendado para este repo)

Este mapeo sugiere el agente o sub-agente más apropiado según el tipo de tarea durante `/speckit.implement`.

- Spec verification / Plan review: `Documentation Agent`, `speckit.plan`
- Contracts & OpenAPI edits: `API Contract Validator` (verifica divergencias) + `Documentation Agent` (docs/examples)
- BFF endpoint implementation (Python): `Python Entity Implementer` or `Test Generator (BFF)` for tests
- Frontend integration / React components: `React Developer` (implementación y tests unitarios)
- Tests (unit/integration/contract): `Test Generator` (select Core or BFF variant) and `QA Integration Validator` for end-to-end checks
- CI / pipeline updates: `CI/CD and DevOps Agent`
- Verification / independent review for high-risk changes: `Security Reviewer` or `QA Integration Validator`

Notas:
- El orquestador decide delegar basándose en los triggers de ODD (mapping, writer, preparación). Cada delegación incluirá `## Skills to load before work` y `Allowed edit surfaces`.
- Respeta la política de PR/MR en `/.agents/agents.md`: no preparar PR/MR hasta que la evidencia E2E y QA esté en `odd/tasks/<feature>.md`.

## Resultado
- Archivo: `odd/tasks/T001-manage-catalog-inventory-matrix.md` (este documento).
- Estado: T001 implementado (matriz generada). Próximo: T002/T003 o añadir tests faltantes según confirmes la decisión sobre OpenAPI.

--
Generado por el asistente automatizado — dime si quieres que:
- (A) añada los tests faltantes ahora, o
- (B) actualice `specs/openapi.yaml` con las operaciones admin propuestas, o
- (C) cree el script automatizador para mantener esta matriz actualizada.

## Checklist obligatorio de evidencia (ANTES de preparar PR/MR o implementar)

Para cualquier trabajo que afecte endpoints BFF o el contrato OpenAPI, la siguiente evidencia debe adjuntarse en `odd/tasks/<feature>.md` y aprobarse antes de crear un PR/MR:

- **OpenAPI contract file**: ruta del archivo o fragmento en `specs/<feature>/contracts/` y diff con la rama base.
- **OpenAPI validation output**: el resultado del validador (`openapi-spec-validator`) con el comando exacto usado y el output (ejemplo):
  - `python -m openapi_spec_validator bgg-shop-bff/specs/openapi.yaml` → attach stdout/stderr.
- **Unit/Contract tests**: lista de comandos ejecutados y logs (pytest commands + path to junit/coverage reports). Ejemplo:
  - `PYTHONPATH=. pytest bgg-shop-bff/tests/test_admin_update.py -q --maxfail=1` → attach output file `results/<feature>/unit-tests.log`.
- **E2E / QA runs**: commands and artifacts (script used, environment, exit codes, logs). Example:
  - `./scripts/run-e2e.sh --env=local --spec=manage-catalog-inventory` → attach `results/<feature>/e2e.log` and any generated HTML report.
- **Authentication & Security evidence**: confirmation that admin endpoints are protected (e.g., curl command showing 401 for anonymous, and successful auth sample), or policy if OpenAPI private.
- **Integration smoke**: simple run showing front <-> bff <-> core happy path (curl or test script + logs).
- **Acceptance checklist**: short bullets with pass/fail and signer (owner/reviewer) verifying the evidence.

Sin estas piezas de evidencia el PR/MR queda bloqueado por la política del orquestador. Añade paths a los artefactos dentro del mismo `odd/tasks/<feature>.md` para permitir revisión y auditoría.

## Política de PR / MR

- No preparar un `PR` o `MR` para estos cambios hasta que se cumplan **todas** las siguientes condiciones:
  - Validación integral de la integración front <-> bff <-> core completada y verificada.
  - Suite de pruebas de QA (automatizadas y/o manuales) ejecutadas y aprobadas para los flujos afectados.
  - Evidencias adjuntas: resultados de tests (logs, reportes), capturas o enlaces a pipelines que demuestren la validación.

- Mientras no se cumplan estos requisitos, la tarea `Preparar cambios para PR` debe permanecer bloqueada y no realizarse ningún push/PR/MR.

Incluye en la evidencia los comandos exactos ejecutados y la salida relevante para reproducibilidad.

Ver también: `/.agents/agents.md` — contiene la política de PR/MR del orquestador y las reglas de bloqueo.
