# Tasks for Checkout Mercado Pago Sandbox Validation

## Task 1: Validar creación de preferencia Mercado Pago sandbox
- Revisar los logs backend para confirmar creación de preferencia con credenciales sandbox.
- Confirmar que el objeto `preference` contiene las URLs de retorno correctas.
- Verificar que el `init_point` generado es válido y apunta a sandbox.
- Escribir pruebas unitarias/integración para este flujo.

## Task 2: Verificar y crear ruta de resultado en frontend
- Buscar o implementar la ruta React que maneje `/compra/resultado`.
- Asegurar que reciba y procese correctamente el resultado del pago (query params o API).
- Implementar UI que muestre estado exitoso, fallo o pendiente.

## Task 3: Diagnosticar y corregir errores de interfaz
- Analizar error de hidratación React y componentes tokenización.
- Revisar estados y props en componentes `SmartTokenizationProvider`, `InputCVVProvider`, etc.
- Implementar correcciones para evitar las excepciones y permitir habilitar el botón pagar.

## Task 4: Ejecutar pruebas end-to-end en modo sandbox
- Testear flujo completo de pago desde checkout a redirección y resultado.
- Usar tarjetas y datos oficiales de prueba Mercado Pago sandbox.
- Validar que la experiencia usuario sea fluida y sin errores.

## Task 5: Documentar y reportar
- Crear reporte con resultados de validación y pruebas.
- Documentar pasos y configuración necesarias en `.env` y app.
- Notificar posibles mejoras o incidencias.

---

Estos tasks cubren el plan completo para validar y corregir la integración Mercado Pago sandbox en checkout.

## Avance de validación - 2026-10-27

- Core: `tests/test_graphql_orders.py`, 20 pruebas aprobadas con Mercado Pago simulado; verifica moneda y URLs de retorno. La creación real de una preferencia fue registrada anteriormente en `odd/tasks/cu-c05-purchase.md`, no se repitió en esta sesión.
- Frontend: botón de pago deshabilitado hasta completar los campos obligatorios de envío; retiro en tienda no requiere dirección. La prueba de descarga de factura espera la liberación de su URL. `npm test -- --run --reporter=dot`: 65 pruebas aprobadas.
- BFF: `tests/test_orders.py` y `tests/test_services_wishlist_orders_contract.py`: 30 aprobadas y 2 fallidas para rutas inválidas; Flask propaga `MethodNotAllowed` desde el manejador global de excepciones. Pendiente diagnosticar y corregir sin asumir que los pagos funcionan.
- `npm run build` falla porque TypeScript 5.4.5 no reconoce opciones existentes de los tsconfig; `npm run lint` falla por imports duplicados preexistentes en `src/admin/products/ProductForm.test.tsx`.
- El E2E existente de Mercado Pago usa credenciales de respaldo y presupone formularios e iframes del proveedor; no se ejecutó y no constituye evidencia de pago.
- Pendiente: comprobar hidratación y consola, corregir el E2E y ejecutar con cuentas de prueba autorizadas el pago completo; verificar regreso, estado pagado, decremento de stock, carrito y factura PDF. No se han marcado como completadas las tareas de validación integral.

## Ejecución sandbox autorizada - 2026-10-27

- Se creó una cuenta local sintética y un carrito con una unidad de Watergate. Al elegir retiro se habilitó el botón de pago y la aplicación redirigió al checkout de Mercado Pago, que mostró el producto y 90.000 ARS.
- Orden `9160d16c-f871-4894-a8e8-e8e38c4b8137`: `pending_payment`, preferencia registrada, cantidad 1, stock 10 y sin factura. Ningún pago fue enviado.
- La bandera local `MP_SANDBOX=true` y el prefijo `APP_USR-` no demuestran por sí solos que el pago sea de prueba. La documentación oficial indica iniciar sesión con una cuenta compradora de prueba y usar una tarjeta de prueba. Se abrió el inicio de sesión del proveedor; la autenticación debe realizarla el usuario sin compartir credenciales.
- Pendiente: comprobar el entorno de prueba y completar un único pago de prueba; verificar la confirmación y sus efectos sobre stock, carrito y factura.

## Resultado de la operación - 2026-10-27

- Mercado Pago mostró la operación `186369757300` como acreditada. La API del proveedor devolvió `approved`, 90.000 ARS, referencia de la orden coincidente y `live_mode: true`.
- El comprador y el vendedor coinciden con los identificadores configurados para prueba. La API `/users/me` identifica al vendedor con la etiqueta `test_user`; el usuario confirmó que el ID del comprador aparece en la sección de cuentas de prueba del panel de Mercado Pago, y ese ID coincide con el pagador de la operación.
- La pantalla permaneció en Mercado Pago; al abrir manualmente la URL de resultado con los identificadores, la tienda respondió HTTP 422 y mostró un error genérico. Core rechaza pagos con `live_mode: true`; no se modificó esa protección.
- Tras el intento, la orden sigue en `pending_payment`, el stock permanece en 10, el carrito conserva una unidad y no hay factura. Pendiente resolver con evidencia del proveedor el significado de `live_mode` para esta operación antes de cambiar la validación o repetir el pago.

## Validación con MCP - 2026-10-27

- La preferencia guardada en Mercado Pago conserva la referencia correcta de la orden, pero devuelve vacías las tres `back_urls`. Core configura `http://localhost:3000/compra/resultado`; la guía oficial recomienda un dominio controlado y ejemplifica URLs HTTPS, sin establecer que localhost sea la causa de este resultado.
- La preferencia pertenece a la aplicación del vendedor de prueba, diferente de la aplicación principal visible por OAuth en el MCP. La evaluación de calidad con el ID de la aplicación de prueba falló por validación de propiedad OAuth; no se obtuvo un resultado de evaluación.
- La búsqueda oficial consultada no explica por qué este pago de prueba devuelve `live_mode: true`. Mantener la protección y consultar al proveedor; no repetir el pago.

## Restricción de entorno

- El proyecto es solo de prueba y no es viable utilizar un dominio HTTPS. Mantener la validación local sin depender de uno.
- Los estados de pago y sus efectos pueden probarse localmente con Mercado Pago simulado; esto no demuestra el retorno real desde el proveedor. El retorno manual a la ruta local tampoco resuelve por sí mismo el rechazo independiente de `live_mode: true`.
- Investigar el comportamiento de `back_urls` de localhost y la discrepancia de `live_mode` antes de modificar la protección o reconciliar la orden existente. No repetir el pago.

## Segundo recorrido E2E - 2026-10-27

- La sesión local anterior tenía el token vencido: agregar al carrito devolvía HTTP 200, pero el carrito consultado permanecía vacío. Con una nueva cuenta local de prueba y sesión vigente, el carrito conservó una unidad.
- Algunos controles no superaron la espera de estabilidad de Playwright y se activaron mediante el DOM; esto no valida una interacción normal de puntero.
- Se creó la orden nueva `1a3c23c6-43d6-48cd-8afc-22e9ab007638`: `pending_payment`, 90.000 ARS, una unidad, stock 10 y sin factura. Checkout respondió HTTP 200 y redirigió a Mercado Pago, donde se muestra una sesión de prueba.
- El usuario completó el pago de prueba `185335878895`; Mercado Pago mostró que fue acreditado. Su API devolvió `approved`, `accredited`, 90.000 ARS, `live_mode: true`, referencia de orden coincidente y el comprador de prueba configurado.
- La pantalla permaneció en Mercado Pago y la nueva preferencia también devolvió las tres `back_urls` vacías. No se observó una confirmación en la tienda: la orden sigue pendiente, el stock en 10, el carrito conserva una unidad y no hay factura. No se intentó una segunda confirmación manual ni se repitió el pago.
