# CU-A01 — Administrar Catálogo, Inventario y Promociones

Short name: manage-catalog-inventory

## Objetivo
Permitir al Administrador/Vendedor gestionar el ciclo de vida de los productos (alta, baja, modificación), controlar el stock y configurar promociones o cupones con fechas de vigencia, de modo que el catálogo público muestre la oferta y precios vigentes.

## Actores
- Administrador / Vendedor (requiere rol de administración)

## Alcance y Descripción
Incluye: creación y edición de productos, referencia a una imagen y gestión de descripciones, control de inventario por producto y gestión de promociones (precios en oferta y cupones con rango de validez). Cada edición o variante de un juego se registra como un producto independiente. No existe despublicación; la baja no presupone eliminación física.

No incluye: integración con pasarelas de pago, logística de envío ni la generación de facturas (cubierto por otros casos de uso).

## Precondiciones
- Usuario autenticado con rol de Administrador.
- Acceso al panel de administración.

## Poscondiciones
- Los cambios en productos, stock y promociones se reflejan en el catálogo público y en los endpoints de consulta disponibles para la tienda.

## Flujo Principal
1. El Administrador accede al panel de gestión de productos.  
2. Selecciona "Crear producto" o elige uno existente para editar.  
3. Completa/actualiza los campos obligatorios: título, descripción, categoría, precio base y stock inicial del producto.
4. (Opcional) Indica una imagen `.webp` mediante URL o nombre de archivo, y documentación (manual, reglas). No se presupone subida de binarios.
5. (Opcional) Configura promoción: precio en oferta o crea un cupón con fecha de inicio y fin, condiciones y límite de uso.  
6. Guarda la configuración.  
7. El sistema valida los datos, persiste los cambios y actualiza la visibilidad en el catálogo público.

## Flujos Alternativos y Excepciones
- Campos inválidos o faltantes: el sistema muestra validaciones por campo y no permite guardar hasta corregir.  
- `IN` aumenta el inventario y `OUT` lo reduce, incluso parcialmente. La baja a cero deja el producto visible y el frontend muestra exactamente «Sin stock». No se hacen reservas.
- Si `OUT` supera el stock disponible, se informa al usuario que el stock quedará en cero. No se establece una confirmación ni un código HTTP para este caso.
- Si una operación `IN`/`OUT` no impacta la base, se cancela o rechaza; una transacción efectivamente rechazada o revertida no deja el cambio aplicado. Un rechazo o rollback confirmado permite reintentar con el mismo UUID y datos. Un error de comunicación o HTTP no demuestra rollback: el servidor puede confirmar la operación y perderse la respuesta. Cada movimiento tiene un UUID y su identidad incluye producto, dirección y cantidad. El mismo UUID y datos devuelve el resultado original sin duplicar el cambio; datos distintos se rechazan. El UUID puede registrarse provisionalmente como `IN_PROGRESS`; el stock, la auditoría y el resultado definitivo se confirman atómicamente. Un reintento con los mismos datos reanuda un movimiento que no se haya completado, incluso después de una caída o una demora prolongada; si otro intento está ejecutándolo, se informa que sigue en curso. No se aplica ningún movimiento automáticamente sin un reintento. Los UUID exitosos no vencen. La política de retención de rechazos sigue pendiente.

## User Scenarios & Testing
- Escenario 1 — Alta de producto: Un Administrador crea una edición coleccionista como producto independiente con stock 50. Verificar que el producto aparece en el catálogo público con stock 50.
- Escenario 2 — Edición de descripción e imagen: Editar un producto y reemplazar su referencia a una imagen `.webp`; validar que la imagen se muestra en la ficha pública.
- Escenario 3 — Ingreso de stock previsto: Para un producto con stock 10, ingresar 20 unidades y verificar que el stock resultante sea 30.
- Escenario 4 — Promoción temporal: Crear una promoción que aplica un precio de oferta durante 7 días; verificar precio en catálogo y que al terminar la vigencia el precio vuelve al valor base.

## Requisitos Funcionales (testables)
RF-1: El sistema permitirá crear un producto con al menos: título, descripción, categoría y precio base. (Test: crear y consultar públicamente, 201/GET).
RF-2: El sistema permitirá editar los campos de un producto existente. (Test: editar y reflejo en consulta pública).
RF-3: Por ahora cada producto tendrá como máximo una imagen `.webp`, indicada mediante URL o nombre de archivo, sin asumir subida de binarios. (Test previsto: guardar la referencia y mostrar la imagen).
RF-4: El sistema mantendrá stock por producto: `IN` aumenta el inventario y `OUT` lo reduce, incluso parcialmente. La baja a cero mantiene visible el producto con el texto «Sin stock»; no se hacen reservas. Si `OUT` supera el stock disponible, se informa que el stock quedará en cero. Cada movimiento tendrá un identificador único para evitar duplicaciones al reintentar; los identificadores de movimientos exitosos se conservarán sin vencimiento. Reutilizar un identificador con datos diferentes rechazará la operación sin aplicar un nuevo cambio de stock. Un movimiento confirmado como rechazado o revertido sin cambios en la base puede volver a procesarse con el mismo identificador y datos. (Tests previstos: 10 + 20 = 30, reducción parcial, exceso de `OUT`, baja con producto visible, reintento con el mismo identificador y datos tras perder la respuesta o después de un intervalo prolongado, nuevo procesamiento tras rechazo o rollback confirmado sin cambios, rechazo con datos diferentes sin nuevo cambio de stock, y confirmación atómica del identificador y el stock).
RF-5: El sistema permitirá definir promociones de precio con fecha de inicio y fin; la lógica aplicará automáticamente el precio vigente según la fecha del servidor. En un carrito con varios productos, cada producto puede tener su propia promoción, sin combinar descuentos sobre un mismo producto. Al comparar descuentos aplicables al mismo producto, prevalece el que descuente más pesos, también al comparar un porcentaje con un monto fijo. Ante dos promociones iguales para un producto aplica la ofrecida por la tienda. La identidad de promociones iguales y la precedencia si ambas proceden de la tienda quedan pendientes. La suma de ahorros de las promociones aplicables a todo el carrito se compara con el ahorro del cupón calculado sobre la compra sin descuentos; se aplica exclusivamente la alternativa que ahorre más pesos. Si ambas alternativas ahorran lo mismo, se aplican las promociones y no se consume un uso del cupón; cuando el usuario usa un cupón que empata con una promoción, se le avisa que se aplicará la promoción de tienda y no el cupón. No se define la interfaz de ese aviso. (Tests previstos: vigencia, selección del descuento mayor y empate, una vez resueltos los detalles necesarios).

RF-5a: `active` es un interruptor manual independiente de las fechas de vigencia. Una promoción desactivada no se aplica aunque la fecha esté dentro del rango; una promoción activada sigue sujeta a las fechas. Las promociones existentes quedarán inactivas al incorporar este campo. Esta regla no acredita implementación ni migración de datos.

El redondeo se aplica al total de los ahorros de las promociones, después de sumarlos, no a cada promoción por separado. Por ejemplo, dos ahorros de $1,51 suman $3,02 y ese total se conserva. Los ahorros totales de promociones y del cupón se comparan después de redondear ambos. Si empatan, se aplican las promociones y no se consume el cupón; por ejemplo, ahorros de $3,60 y $3,80 se redondean a $4 y empatan, siempre sujeto al límite del 50 %.

RF-6: El sistema permitirá crear y administrar cupones de descuento aplicables a toda la compra con: código, porcentaje o monto fijo, fecha de validez, y **límite global de uso** (contador total de usos). Los cupones por producto no se implementan en este MVP. Per-user limits are out of scope for the first iteration. Los cupones aplican al momento del pago; la validación se realizará al aplicar el cupón. Un cupón no se consume antes de que se realice el pago; esto no implica que todos sean de un solo uso. Si queda un solo uso y dos clientes intentan pagar simultáneamente, el segundo espera hasta que termine el primero; si el cupón se agota, se le informa. Un pago confirmado como fallido no consume el uso. Si el resultado del primer pago es incierto, el último uso permanece bloqueado hasta confirmar el resultado. Un administrador consulta el pago y, si no obtiene respuesta, no se desbloquea el cupón; la falta de respuesta no confirma un fallo. La propuesta de liberarlo tras más de tres reintentos queda descartada. Los mecanismos de espera, consulta y confirmación permanecen pendientes. No se acredita implementación. (Tests previstos: pago confirmado, fallo confirmado, consulta sin respuesta y dos intentos concurrentes por el último uso).

Si el descuento de un cupón excede el 50 % de la compra sin descuentos, se rechaza su aplicación y se informa el motivo. Por ejemplo, un cupón de $600 sobre una compra de $1.000 se rechaza; no se reduce a $500. Esta decisión reemplaza la regla anterior de limitar el cupón. Queda pendiente precisar en qué etapa se compara el descuento con el límite cuando interviene el redondeo. Los cálculos intermedios se truncan a dos decimales antes de aplicar la regla de redondeo: $10,505 se convierte en $10,50. Este requisito no acredita implementación.

RF-6a: Cada cupón tiene activación y vigencia propias, independientes de las promociones. Los cupones existentes quedarán inactivos y sin fechas hasta que un administrador los configure. Clientes, administradores e invitados pueden consultar los cupones activos sin carrito. El servicio GraphQL debe devolver los cupones habilitados y disponibles. Para aplicar un cupón se requiere un carrito y un usuario autenticado; un invitado puede consultarlos, pero no usarlos. La consulta previa solo muestra cupones y no consume ni reserva usos. La estimación se identifica como tal en la vista que ofrece la opción de pago. Al intentar aplicar un cupón inactivo se informa el motivo del rechazo; entre las causas indicadas se incluyen superar el 50 % de descuento, vencimiento y agotamiento de usos. Se indicó `404` para cupón no encontrado y `401` para uso no autorizado. La aplicación al carrito y el tratamiento de un uso bloqueado por pago incierto quedan pendientes; estos requisitos no acreditan su implementación.

RF-7: El sistema validará entradas y devolverá errores por campos inválidos con mensajes por campo. (Test: enviar payloads incompletos → errores 4xx detallados).
RF-8: El sistema registrará auditoría básica para cambios de productos, movimientos de stock, promociones y cupones, incluyendo usuario, fecha, acción y valores anteriores y nuevos. Esta auditoría básica permanece en el alcance actual. Como requisitos futuros, pendientes y fuera del alcance actual de la 007, se prevén siete días en base y un ZIP local semanal; no se eliminarán filas sin verificar previamente que el archivo se creó correctamente. No se acuerda purga automática. Queda pendiente compatibilizar la frecuencia semanal con la retirada exactamente a los siete días, pues ambas podrían retrasarse. Los ZIP no vencen ni se eliminan automáticamente y se conservan indefinidamente hasta su eliminación manual, a cargo del usuario y acordada exclusivamente para `is_superuser=true`; `is_staff=true` por sí solo no autoriza esa eliminación, aunque un superuser puede tener ambos atributos. Tanto la generación semanal como el mecanismo que hace cumplir el permiso de borrado quedan pendientes y fuera del alcance actual. No se afirma que la solución futura esté implementada o validada ni que el permiso se aplique en el filesystem. La decisión anterior de conservar los ZIP un mes queda reemplazada. Se conserva el requisito previo para creación/edición/baja de productos y promociones; la baja no presupone eliminación física. (Tests actuales previstos: verificar registros y datos de las cuatro áreas; archivo, conservación y permisos corresponden a la solución futura).

## Success Criteria (verificables)
- SC-1: El 100% de los productos creados por Administradores aparecen en el catálogo público dentro de los 30 segundos posteriores a guardar los cambios.
- SC-2: Promociones con fecha de inicio/finalización aplican correctamente en el 100% de las comprobaciones automatizadas (crear + consultar dentro/fuera de rango).
- SC-2b: Cuando múltiples promociones son aplicables a un mismo producto, no se combinan y se aplica la que descuente más pesos, también al comparar porcentaje y monto fijo; distintos productos pueden tener sus propias promociones. Ante dos promociones iguales para un producto aplica la ofrecida por la tienda; quedan pendientes la identidad de promociones iguales y la precedencia si ambas proceden de la tienda.
- SC-3: Las operaciones inválidas devuelven mensajes claros y códigos HTTP apropiados (4xx) en al menos el 95% de los escenarios de prueba automatizados.
- SC-4: Auditoría: para el 100% de las operaciones de administración, exista un registro con usuario, acción y timestamp; los cambios de productos, movimientos de stock, promociones y cupones incluirán valores anteriores y nuevos.
- SC-5: `IN` aumenta el inventario y `OUT` lo reduce, incluso parcialmente; la baja a cero mantiene visible el producto y muestra «Sin stock». No se hacen reservas; si `OUT` supera el stock disponible, se informa que quedará en cero.

## Key Entities
- Producto: id, título, slug, descripción, categoría, atributos, referencia a imagen `.webp`, precio_base y stock. Cada edición o variante se registra como otro producto.
- Promoción: id, tipo, valor, fecha_inicio, fecha_fin y condiciones. No se combinan descuentos sobre un mismo producto; prevalece el que descuente más pesos.
- Auditoría: id, usuario_id, acción, entidad, entidad_id, cambios con valores anteriores y nuevos, timestamp.

## Assumptions
- El catálogo público consume los datos mediante los endpoints de la plataforma (APIs) y refresca visibilidad en menos de 30s.  

## Dependencies
- Autenticación y autorización del módulo de usuarios.  
- Servicio de búsqueda/caché que pueda invalidar/actualizar índices tras cambios importantes de catálogo.

## Clarifications and Decisions
Las siguientes decisiones aclaran comportamientos del producto y guían la implementación:

- Q1 (histórica, reemplazada): se había elegido permitir apilado mediante `stackable`; la decisión vigente es no combinar descuentos sobre un mismo producto y aplicar el que descuente más pesos.
- Q2 (límite de cupones): Se eligió la opción B — soportar límite **global** de usos por cupón (ej.: 100 usos totales). No se requiere límite por usuario en la primera iteración.
- Q3 (histórica, reemplazada): se había elegido bloquear reducciones por debajo de reservas. La decisión vigente es no hacer reservas.
- Decisión vigente (2026-10-31): los cupones de descuento aplican a toda la compra al momento del pago; los cupones por producto no se implementan en este MVP. Cada producto de un carrito puede tener su propia promoción, sin combinar descuentos sobre un mismo producto; al comparar descuentos aplicables al mismo producto, prevalece el que descuente más pesos, también al comparar un porcentaje con un monto fijo. Ante dos promociones iguales para un producto aplica la ofrecida por la tienda. Se compara la suma de ahorros de las promociones aplicables a todo el carrito con el ahorro del cupón calculado sobre la compra sin descuentos; se aplica exclusivamente la alternativa que ahorre más pesos. Si ambas alternativas ahorran lo mismo, se aplican las promociones y no se consume un uso del cupón; cuando el usuario usa un cupón que empata con una promoción, se le avisa que se aplicará la promoción de tienda y no el cupón. Si se eligen las promociones, cada producto puede recibir su propia promoción; si se elige el cupón, no se aplican promociones. Las gift cards y el crédito son medios de pago, no cupones de descuento. No hay impuestos y el envío es gratis. Las fracciones hasta 0,50 inclusive se mantienen; desde 0,51 se redondean hacia arriba y el límite de descuento es 50%. Quedan pendientes la elegibilidad o exclusiones; la identidad de promociones iguales y la precedencia si ambas proceden de la tienda; otras igualdades; la unidad y etapa del redondeo; si el 50% aplica por producto, cupón o compra y si las configuraciones se rechazan o limitan; y el consumo del contador ante un intento de pago fallido. La implementación requiere resolver estos puntos y definir y validar los contratos primero. El checkout actual usa precios base y la integración de descuentos no está validada; estas decisiones no modifican otras specs cerradas de checkout.
- Decisión vigente: cada edición o variante es un producto independiente y el inventario pertenece al producto. Los movimientos requieren UUID, dirección `IN`/`OUT` y cantidad positiva. La ruta BFF y la mutación Core implementan el registro provisional, la confirmación atómica y los reintentos idempotentes. La mutación anterior sin UUID rechaza escrituras. Las migraciones 0012 y 0013 se probaron en PostgreSQL descartable, pero no se aplicaron a la base activa; el despliegue y la recuperación de registros que queden en curso siguen pendientes.
- Decisiones vigentes (2026-10-31): baja a stock cero con producto visible y texto «Sin stock»; una imagen `.webp` por producto, por URL o nombre de archivo, sin asumir carga de binarios; sin reservas; descuentos no combinables sobre un mismo producto, aplicando el que descuente más pesos.
- `IN` aumenta y `OUT` reduce el stock, también parcialmente; no existe despublicación y no se infiere eliminación física. Si `OUT` supera el stock disponible, el BFF informa que queda en cero. La integración de la interfaz no está verificada.
- Decisión vigente (2026-10-31): auditoría básica de cambios de productos, movimientos de stock, promociones y cupones, con usuario, fecha, acción y valores anteriores y nuevos. Esto es un requisito, no evidencia de que todos los flujos usen el modelo de auditoría existente.
- Abierto: los detalles de aplicación de descuentos indicados arriba; el alcance y significado de los filtros; los detalles contractuales del identificador y la recuperación del estado incierto de inventario; y, para la solución futura de auditoría, el inicio de los siete días, la compatibilidad entre ejecución semanal y retirada exactamente a los siete días, el horario del proceso, el mecanismo de archivo atómico ante fallas, el acceso y consulta de archivos y el cifrado. También siguen pendientes el acceso a la auditoría, filtros, paginación y captura de secretos. Los ejemplos de filtros por producto, usuario, fecha o acción no son decisiones confirmadas. Se conservan los requisitos de auditoría existentes.
- Discrepancias observadas en código, no conformidad: Core conserva `stackable` y un modelo y consulta de reservas; el formulario frontend acepta URL y nombre de imagen, y una tarjeta muestra «Sin stock» para cantidad cero. Eso no demuestra el flujo completo de baja, el límite o formato de imagen ni la selección de promociones.

Estas decisiones actualizan y concretan los requisitos funcionales y criterios de aceptación.

## Acceptance Criteria
- Un Administrador autenticado puede crear y editar productos con todos los campos obligatorios; no existe despublicación.
- Las variaciones de stock se reflejan en la ficha pública y bloquean la adición al carrito cuando no hay stock.  
- Cada producto puede tener su propia promoción; los descuentos no se combinan sobre un mismo producto y prevalece el que descuente más pesos. Ante dos promociones iguales para un producto aplica la ofrecida por la tienda. Se aplica exclusivamente el conjunto de promociones o el cupón de compra completa, según cuál ahorre más pesos. En caso de empate entre ambas alternativas se aplican las promociones sin consumir un uso del cupón; cuando el usuario usa un cupón que empata con una promoción, se le avisa que se aplicará la promoción de tienda y no el cupón. Los detalles pendientes deben resolverse antes de aceptar la integración.
- Registro de auditoría presente para cada cambio administrativo; para productos, movimientos de stock, promociones y cupones incluye usuario, fecha, acción y valores anteriores y nuevos.

## Next Steps
- Mantener las tareas alineadas con las decisiones vigentes y resolver los puntos abiertos antes de definir contratos y pruebas.
- Ejecutar hooks de git si deseado (crear rama de feature).  


