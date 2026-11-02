# Spec: Validación de Flujo Sandbox Mercado Pago en Checkout

## Objetivo
Validar que la integración de Mercado Pago en modo sandbox funcione correctamente, incluyendo la creación de la preferencia, redirección y manejo del resultado del pago.

## Alcance
- Backend: generación de la preferencia Mercado Pago con credenciales sandbox y URLs de retorno.
- Frontend: manejo de la ruta de resultado del pago y visualización de estado.
- UI: habilitación del botón pagar y corrección de errores de interfaz relacionados.

## Criterios de Aceptación

### Backend
- [ ] Se crea correctamente una preferencia Mercado Pago en sandbox.
- [ ] El `init_point` generado es válido y apunta a sandbox.
- [ ] Las URLs de retorno (`back_urls`) apuntan a la ruta `/compra/resultado` en frontend.
- [ ] Se registran logs para validar el contenido de la preferencia y URL de pago.

### Frontend
- [ ] Existe una ruta en React que maneja `/compra/resultado`.
- [ ] La ruta recibe y procesa correctamente los parámetros o estado de resultado de pago.
- [ ] Se muestra un mensaje claro de éxito, falla o estado pendiente.
- [ ] El botón "Continuar a Mercado Pago" se habilita sólo con datos válidos y usuario autenticado.
- [ ] No existen errores de hidratación React ni errores en consola relacionados.

### Pruebas Integrales
- [ ] Se pueden hacer pagos en modo sandbox con tarjetas y datos oficiales de prueba.
- [ ] La redirección post-pago lleva a la página de resultado con los estados correctos.
- [ ] Validación funcional y visual confirmada por QA.

## Datos de prueba
- Tarjetas y códigos CVV recomendados oficiales Mercado Pago sandbox.
- Cuentas de prueba configuradas y tokens en `.env`.

## Flujo de trabajo
1. Ejecutar pruebas unitarias y de integración backend para validar preferencia.
2. Verificar en frontend la ruta de resultado y manejo de estados.
3. Realizar pruebas end-to-end en sandbox.
4. Reportar y corregir errores encontrados.

## Notas
- Revisar configuración en `.env` para activar sandbox (`MP_SANDBOX=true`).
- Validar consistencia entre SSR y render cliente para evitar errores React.

---

Esta especificación servirá como base para el desarrollo y pruebas del flujo completo de pago en sandbox Mercado Pago en la aplicación.
