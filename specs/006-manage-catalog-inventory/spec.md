# CU-A01 — Administrar Catálogo, Inventario y Promociones

Short name: manage-catalog-inventory

## Objetivo
Permitir al Administrador/Vendedor gestionar el ciclo de vida de los productos (alta, baja, modificación), controlar el stock y configurar promociones o cupones con fechas de vigencia, de modo que el catálogo público muestre la oferta y precios vigentes.

## Actores
- Administrador / Vendedor (requiere rol de administración)

## Alcance y Descripción
Incluye: creación y edición de productos, subida/gestión de imágenes y descripciones, control de inventario (stock por variantes), publicación/despublicación de productos, y gestión de promociones (precios en oferta y cupones con rango de validez).

No incluye: integración con pasarelas de pago, logística de envío ni la generación de facturas (cubierto por otros casos de uso).

## Precondiciones
- Usuario autenticado con rol de Administrador.
- Acceso al panel de administración.

## Poscondiciones
- Los cambios en productos, stock y promociones se reflejan en el catálogo público y en los endpoints de consulta disponibles para la tienda.

## Flujo Principal
1. El Administrador accede al panel de gestión de productos.  
2. Selecciona "Crear producto" o elige uno existente para editar.  
3. Completa/actualiza los campos obligatorios: título, descripción, categoría, precio base, variantes (si las hay), y stock inicial por variante.  
4. (Opcional) Sube imágenes y documentación (manual, reglas).  
5. (Opcional) Configura promoción: precio en oferta o crea un cupón con fecha de inicio y fin, condiciones y límite de uso.  
6. Guarda la configuración.  
7. El sistema valida los datos, persiste los cambios y actualiza la visibilidad en el catálogo público.

## Flujos Alternativos y Excepciones
- Campos inválidos o faltantes: el sistema muestra validaciones por campo y no permite guardar hasta corregir.  
- Stock insuficiente para una modificación solicitada: se rechaza la operación y se informa la cantidad máxima posible.  
- Colisión de edición concurrente: el sistema avisa y ofrece opciones para sobrescribir o reintentar con los datos actuales.

## User Scenarios & Testing
- Escenario 1 — Alta de producto: Un Administrador crea un nuevo juego con una variante (edición coleccionista) y stock 50. Verificar que el producto aparece en el catálogo público y que la variante muestra stock 50.
- Escenario 2 — Edición de descripción y imágenes: Editar un producto existente y reemplazar imágenes; validar que las nuevas imágenes se muestran en la ficha pública.
- Escenario 3 — Gestión de stock: Reducir el stock de una variante a 0; verificar que la disponibilidad en la ficha pública refleje "Sin stock" y que no sea posible añadir al carrito.
- Escenario 4 — Promoción temporal: Crear una promoción que aplica un precio de oferta durante 7 días; verificar precio en catálogo y que al terminar la vigencia el precio vuelve al valor base.

## Requisitos Funcionales (testables)
RF-1: El sistema permitirá crear un producto con al menos: título, descripción, categoría y precio base. (Test: crear y consultar públicamente, 201/GET).
RF-2: El sistema permitirá editar los campos de un producto existente. (Test: editar y reflejo en consulta pública).
RF-3: El sistema almacenará y servirá hasta N imágenes por producto (N definido por configuración). (Test: subir N imágenes y obtenerlas).
RF-4: El sistema mantendrá stock por variante y rechazará operaciones que excedan disponibilidad. (Test: intentar descontar más unidades que stock → error 400).
RF-5: El sistema permitirá definir promociones de precio con fecha de inicio y fin; la lógica aplicará automáticamente el precio vigente según la fecha del servidor. Promotions include an optional `stackable` boolean: by default promotions do not stack; promotions with `stackable=true` may be combined according to admin configuration. (Test: crear promoción y validar precio en rango de fechas; crear promoción `stackable=true` y verificar comportamiento combinado).
RF-6: El sistema permitirá crear y administrar cupones con: código, porcentaje o monto fijo, fecha de validez, y **límite global de uso** (contador total de usos). Per-user limits are out of scope for the first iteration. La validación se realizará al aplicar el cupón. (Test: crear cupón con `global_limit=100` y simular usos hasta agotar el contador).
RF-7: El sistema validará entradas y devolverá errores por campos inválidos con mensajes por campo. (Test: enviar payloads incompletos → errores 4xx detallados).
RF-8: El sistema registrará auditoría básica (usuario, operación, timestamp) para creación/edición/baja de productos y promociones. (Test: consultar logs/auditoría tras operaciones).

## Success Criteria (verificables)
- SC-1: El 100% de los productos creados por Administradores aparecen en el catálogo público dentro de los 30 segundos posteriores a guardar los cambios.
- SC-2: Promociones con fecha de inicio/finalización aplican correctamente en el 100% de las comprobaciones automatizadas (crear + consultar dentro/fuera de rango).
- SC-2b: Cuando múltiples promociones son aplicables, la política elegida se cumple: por defecto no se apilan; si una promoción tiene `stackable=true` se permite apilado según la configuración.
- SC-3: Las operaciones inválidas devuelven mensajes claros y códigos HTTP apropiados (4xx) en al menos el 95% de los escenarios de prueba automatizados.
- SC-4: Auditoría: para el 100% de las operaciones de administración, exista un registro con usuario, acción y timestamp.
- SC-5: El sistema evita que un Administrador reduzca el stock por debajo de las unidades reservadas para pedidos en curso (bloqueo validado en UI/API).

## Key Entities
- Producto: id, título, slug, descripción, categoría, atributos, imágenes, precio_base, variantes.  
- Variante: id, atributos (ej. edición), sku, stock, precio (opcional).  
- Promoción: id, tipo (precio_oferta | cupón), valor, fecha_inicio, fecha_fin, condiciones, límite_uso, stackable.  
- Auditoría: id, usuario_id, acción, entidad, entidad_id, cambios, timestamp.

## Assumptions
- El catálogo público consume los datos mediante los endpoints de la plataforma (APIs) y refresca visibilidad en menos de 30s.  
- Los límites (p. ej. número máximo de imágenes) se definen en la configuración global y serán documentados por el equipo de operaciones.

## Dependencies
- Autenticación y autorización del módulo de usuarios.  
- Servicio de almacenamiento de archivos para imágenes.  
- Servicio de búsqueda/caché que pueda invalidar/actualizar índices tras cambios importantes de catálogo.

## Clarifications and Decisions
Las siguientes decisiones aclaran comportamientos del producto y guían la implementación:

- Q1 (combinar promociones): Se eligió la opción C — por defecto las promociones no se apilan; existe un atributo `stackable: boolean` para permitir apilado cuando el administrador lo marque.
- Q2 (límite de cupones): Se eligió la opción B — soportar límite **global** de usos por cupón (ej.: 100 usos totales). No se requiere límite por usuario en la primera iteración.
- Q3 (ajuste de stock vs. pedidos en curso): Se eligió la opción A — no se permitirá reducir el stock por debajo de las unidades ya reservadas para pedidos en curso; la UI/API debe bloquear esa reducción y mostrar el mínimo permitido.

Estas decisiones actualizan y concretan los requisitos funcionales y criterios de aceptación.

## Acceptance Criteria
- Un Administrador autenticado puede crear, editar y despublicar productos con todos los campos obligatorios.  
- Las variaciones de stock se reflejan en la ficha pública y bloquean la adición al carrito cuando no hay stock.  
- Promociones y cupones se aplican según sus reglas de validez y límites de uso, y la política de apilado definida por `stackable`.
- Registro de auditoría presente para cada cambio administrativo.

## Next Steps
- Crear `tasks.md` para dividir la implementación en subtareas (API, panel UI, integración de almacenamiento, pruebas automatizadas).  
- Ejecutar hooks de git si deseado (crear rama de feature).  


