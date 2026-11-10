# Bitácora de AI Engineering

## Alcance y procedencia

Esta bitácora reconstruye el proceso de ingeniería asistida por IA de este TP a
partir de artefactos versionados y registros selectivos de Engram. No se
conservaron aquí las conversaciones completas: Engram retiene decisiones,
prompts seleccionados, resúmenes y evidencia de trabajo, pero no necesariamente
cada mensaje original. Por eso no se presentan paráfrasis como citas textuales;
cuando el prompt literal no está preservado, se indica como no disponible.

La bitácora documenta el método y algunos hitos verificables, no certifica que
los once casos de uso estén completos ni aceptados. La lista funcional está en
[CasosDeUso.md](../CasosDeUso.md); el README describe la arquitectura y el
estado parcial del chatbot. Se priorizan los contratos vigentes
([OpenAPI del BFF](../bgg-shop-bff/specs/openapi.yaml) y
[SDL GraphQL del Core](../bgg-shop-core/specs/schema.graphql)) frente a borradores
de contratos guardados dentro de planes.

## Arquitectura y responsabilidades de IA

El recorrido de la aplicación es Frontend React/Vite → BFF Flask mediante
REST/JSON → Core Django/Graphene mediante GraphQL → PostgreSQL. Redis presta
servicios de caché y límite de solicitudes; Celery ejecuta trabajo asíncrono
(detalle en [README, arquitectura](../README.MD#arquitectura-actual)).

Para CU-C07, el BFF es dueño de la orquestación LangChain, el guard de alcance,
la recuperación RAG con ChromaDB y el límite REST. El índice contiene solo
material público, estable y aprobado —por ejemplo, preguntas frecuentes y
políticas—; no se incorporan conversaciones, datos personales o de pedidos ni
resultados dinámicos del catálogo. Las recomendaciones consultan el catálogo
por la ruta existente, no por el índice vectorial. OpenRouter se aprobó como
proveedor principal y Ollama local (`deepseek-r1:8b`) como respaldo; los
embeddings permanecen locales. Core conserva y autoriza las conversaciones en
PostgreSQL; el navegador no llama directamente a Core. Entre las decisiones
registradas están el límite de 2.000 caracteres, hasta 10 turnos de contexto,
10 solicitudes por minuto por usuario o sesión, y retención tras 30 días de
inactividad. Son decisiones del plan, no prueba de aceptación integral:
[plan de CU-C07](../specs/013-add-chatbot/plan.md).

## Ciclo de trabajo observado

1. **Partir de casos y evidencia existente.** Los casos de uso orientan el
   alcance; las especificaciones as-built deben describir el comportamiento
   implementado, no convertir requisitos pendientes en hechos.
2. **Definir contratos antes de cambiar interfaces.** OpenAPI y SDL son las
   fuentes canónicas por servicio; los tipos del Frontend se generan desde el
   OpenAPI del BFF. Los borradores de planificación no sustituyen esos
   contratos.
3. **Trazar tareas pequeñas y acotadas.** Los planes y ledgers relacionan
   decisiones, tareas, capas, pruebas y límites conocidos; una tarea cerrada
   administrativamente no equivale a aceptación técnica.
4. **Implementar y comprobar en local.** Cuando corresponde, se registra RED
   antes del cambio, y luego resultados de suites enfocadas y revisión
   independiente. En documentación pasiva se comprueban estructura, enlaces y
   whitespace: no se inventa una prueba ejecutable.
5. **Mantener especificaciones as-built y límites visibles.** La documentación
   resultante conserva las diferencias entre implementado, parcial y pendiente.

## Hitos con evidencia

### 2026-10-20 — especificaciones retrospectivas CU-C01–CU-C05

Se generaron cinco especificaciones funcionales a partir de casos de uso,
implementación, contratos y pruebas: autenticación, catálogo/búsqueda/filtros,
detalle/reseñas, carrito y checkout/pedidos/factura. El ledger informa cinco
documentos y 490 líneas; excluye Wishlist y administración por no estar
implementadas y marca limitaciones y validaciones pendientes. La comprobación
fue documental —secciones, rutas/enlaces y `git diff --check`—; no aplicaban
pruebas ejecutables. Ver
[ledger de regeneración](../odd/tasks/regenerate-as-built-specs.md) y las
[cinco especificaciones](../specs/001-authentication-as-built/spec.md),
[catálogo](../specs/002-catalog-search-filters-as-built/spec.md),
[detalle/reseñas](../specs/003-product-detail-reviews-as-built/spec.md),
[carrito](../specs/004-shopping-cart-as-built/spec.md) y
[checkout](../specs/005-checkout-orders-invoice-as-built/spec.md).

Los registros también conservaron límites concretos: el catálogo no tenía
paginación de servidor ni orden por relevancia; la moderación de reseñas estaba
fuera del alcance; los cambios del carrito no reservaban inventario; y el
checkout era sandbox, con E2E pendiente en aquella evaluación (Engram #43/#44).
Esas notas son límites de la evidencia de entonces, no afirmaciones sobre el
estado actual de cada flujo.

### 2026-10-27 — evaluación MCP de Mercado Pago

El intento de evaluación de calidad mediante Mercado Pago MCP no produjo una
evaluación: la aplicación de prueba vendedora no coincidía con el propietario
OAuth conectado, y la herramienta exponía además sus propios requisitos de
pago. No se cambió ninguna configuración ni se inició otro pago como resultado
de ese intento. La tarea local documenta el fallo de propiedad y sus límites;
Engram #86 conserva la evaluación. Véase
[validación sandbox de Mercado Pago](../odd/tasks/checkout-mercadopago-sandbox-validation.md),
sección «Validación con MCP».

### 2026-11-05 — moderación como planificación, no implementación

El plan de CU-A03 explicita el flujo esperado, la propiedad de cada servicio y
la prioridad de contratos canónicos. Los contratos que aparecen en la carpeta
de la feature son borradores, no fuentes autoritativas; el plan declara que no
se modificaron contratos, implementación ni pruebas y que la verificación se
limitó a estructura local. No atribuye comportamiento ejecutable al diseño:
[plan de moderación](../specs/011-moderate-content-reviews/plan.md).

### 2026-11-06/07 — iteración local de CU-C07

El plan registra una observación RED para el arranque local y después una
selección enfocada de **165 pruebas aprobadas, 215 advertencias**. En T031, la
selección enfocada pasó **117 pruebas, 181 advertencias**; el agente revisor
independiente repitió la misma selección con el mismo resultado. El ledger
también registra **7 pruebas de UI con Playwright y API simulada**: no prueban
por sí solas la integración HTTP real entre Frontend, BFF y Core.

El 2026-11-07 se comprobó el camino directo del servicio local: tras exactamente
un fallo de conexión a OpenRouter simulado, Chroma recuperó una FAQ aprobada y
Ollama local produjo una respuesta en español con atribución a la fuente
aprobada. No se leyó `.env`, no se usó ni transmitió una credencial real y no
hubo una llamada real a OpenRouter. Esto verifica el fallback del servicio con
Chroma/Ollama, **no** la aceptación HTTP completa de Frontend/Core ni la validez
de credenciales reales. Evidencia y comandos históricos:
[plan](../specs/013-add-chatbot/plan.md),
[tareas](../specs/013-add-chatbot/tasks.md) y
[quickstart local](../specs/013-add-chatbot/quickstart.md).

Persisten límites explícitos: SC-001 (20 casos FAQ, al menos 19 resultados
esperados y cero afirmaciones sin respaldo) y SC-007 (10 compradores
representativos, al menos 9 éxitos) no se ejecutaron; tampoco se estableció
E2E HTTP completo ni autenticación real de OpenRouter. T030 y T032 se cerraron
administrativamente a pedido del usuario, con brechas de validación exentas
solo para cerrar el registro de tareas. La suite de contratos BFF reportó
7 aprobadas y 9 fallidas, con línea base desconocida. Nada de ello debe
presentarse como aceptación completa o certificación de seguridad. Las
distinciones y el estado vigente están en
[estado del plan](../specs/013-add-chatbot/plan.md) y
[tareas de CU-C07](../specs/013-add-chatbot/tasks.md).

## MCP: configuración y uso que puede demostrarse

La configuración local declara seis servidores en
[.vscode/mcp.json](../.vscode/mcp.json). Declarar un servidor no demuestra que
se haya usado en una tarea; tampoco se atribuye al MCP una prueba ejecutada con
otra herramienta.

| Servidor | Configurado | Uso respaldado por la evidencia consultada |
|---|---|---|
| Context7 | Sí | No se demuestra una consulta en los artefactos citados. |
| GitHub | Sí | No se demuestra uso en los artefactos citados. |
| Engram | Sí | Sí: decisiones, resúmenes y evidencia de tareas retenidos; por ejemplo #43/#44, #86 y los registros de CU-C07 (#547/#618/#623). |
| Terminal | Sí | No se demuestra uso de este MCP específico. |
| Playwright | Sí | No se demuestra uso de este MCP específico. El ledger sí registra pruebas de navegador, pero eso no identifica al servidor MCP como ejecutor. |
| Mercado Pago | Sí | Sí: se usó `search_documentation` para consultar documentación de Mercado Pago; también se intentó la evaluación de calidad el 2026-10-27, que falló la validación de propiedad OAuth y no produjo evaluación. |

## Aprendizajes y registro futuro

- Separar **requisito**, **decisión**, **implementación** y **aceptación**:
  cada uno necesita evidencia propia.
- Nombrar pruebas con su alcance y resultado exactos; mocks, pruebas unitarias
  o un camino directo del servicio no equivalen a E2E entre servicios.
- Registrar explícitamente fallos, advertencias, pruebas omitidas y cierres
  administrativos. Un check marcado no reemplaza el resultado observado.
- Mantener los contratos de servicio como fuentes canónicas y enlazar los
  borradores de diseño como tales.
- Evitar registrar secretos, datos personales o transcripciones no preservadas.
  Cuando falta el prompt literal, decirlo en vez de reconstruir una cita.

### Plantilla para una nueva entrada

- **Fecha real:**
- **Objetivo:**
- **Agente/modelo:** indicar el dato solo si quedó registrado.
- **Prompt exacto:** transcribirlo únicamente si se preservó; si no, «no disponible».
- **Artefactos cambiados:**
- **Prueba:** comando exacto y resultado observado, o motivo por el que no aplica.
- **Decisión humana:** aprobación, rechazo, alcance o waiver; distinguirlo de una decisión del agente.
- **Evidencia:** enlaces relativos a contratos, tareas, pruebas y documentación.
