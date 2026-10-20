---
description: "Usa estas reglas para la coordinación SDD, los contratos y la trazabilidad entre servicios de boardgame-app."
---

# Instrucciones del Proyecto (bgg-shop-orchestrator)

- **Filosofía de Código:** Todos los agentes deben cumplir estrictamente con las reglas definidas en `#file:.agents/ponytail.md`.
- **E-Commerce de Juegos de Mesa:** Mantén la lógica de catálogo, carrito y pedidos alineada con los contratos OpenAPI sin crear abstracciones extra.
- **Trazabilidad SDD:** Mantén cada cambio solicitado rastreable entre la tarea, el contrato correspondiente, la implementación, sus pruebas y la documentación. Registra solo checks realmente ejecutados y su resultado; no confundas el estado de una tarea con evidencia de verificación.
- **Contratos por servicio:** El BFF usa Flask/Python y `bgg-shop-bff/specs/openapi.yaml`; Core usa Django/Graphene y `bgg-shop-core/specs/schema.graphql`. El frontend genera tipos desde el OpenAPI del BFF. No sustituyas estas fuentes por rutas o stacks no presentes en el repositorio.
- **Errores públicos:** Las respuestas públicas no deben filtrar detalles upstream, excepciones, trazas, URLs internas ni credenciales. Exige pruebas negativas para comprobar que esos detalles no aparecen.