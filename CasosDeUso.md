Tema: E-commerce Juegos de mesa.

- Stack de tecnología a utilizar:

- Frontend: React

- Backend: Python con Flask •

- Core E-commerce / Headless Engine: Saleor (plataforma open-source basada en Django/GraphQL)

- Base de Datos: PostgreSQL

- API: GraphQL (para consultar Saleor) + REST (para los endpoints en Flask)

## Integrantes:

- Nombre: Ezequiel Eduardo Juarez

- Mail: ezequieledjuarez@gmail.com

- Usuario de github: ezequieledjuarez

- Nombre: Nahuel Martín Sosa

- Mail: nahuelmartin.sosa@gmail.com

- Usuario de github: NahueSosa


## 1. Actores del Sistema

- Comprador: Usuario cliente (visitante o registrado) que busca, explora, selecciona y adquiere juegos de mesa.

- Administrador / Vendedor: Usuario con credenciales de gestión encargado de la administración del catálogo, ventas, moderación y configuración del sistema.

## 2. Casos de Uso: Módulo Comprador

## CU-C01: Gestionar Identidad y Autenticación de Usuario

- Actor Principal: Comprador (Visitante o Registrado).

- Objetivo: Registrar una nueva cuenta o iniciar sesión en la plataforma (mediante credenciales locales o Google).

- Precondiciones: Ninguna para registro; para inicio de sesión, contar con registro previo.

- Poscondiciones: El sistema establece una sesión autenticada para el usuario.

- Flujo Principal (Registro / Login Local):

- 1. El comprador accede al módulo de Autenticación ("Registrarse" / "Iniciar Sesión").

- 2. Ingresa los datos solicitados (nombre, correo y contraseña para registro; correo y contraseña para login).

- 3. El comprador presiona el botón de confirmación.

- 4. El sistema valida la información e inicia la sesión del usuario.

- Flujo Alternativo A (Autenticación con Google):

- 1. En el paso 1, el comprador selecciona "Continuar con Google".

- 2. El sistema redirige al proveedor de identidad de Google para la validación de credenciales.

- 3. Al recibir la confirmación de Google, el sistema busca la cuenta vinculada (o la crea si es un registro nuevo) y activa la sesión.

- 2a. Credenciales incorrectas o correo duplicado: El sistema notifica el error especifico sin comprometer la seguridad.

- 2b. Cancelación en Google: El sistema muestra una alerta de fallo en la autenticación externa y regresa a la vista de login.

## Flujos de Excepción:

## CU-C02: Descubrir y Buscar Juegos de Mesa

- Actor Principal: Comprador.

- Objetivo: Encontrar títulos específicos o explorar productos sugeridos en base a criterios y recomendaciones.

- Precondiciones: Ninguna.

- Poscondiciones: El sistema despliega el catálogo de productos filtrado o sugerido.

- Flujo Principal:

- 1. El comprador ingresa un texto de búsqueda o aplica filtros avanzados (año de publicación, número de jugadores, categoría, rango de precio).

- 2. El sistema procesa los criterios y muestra la lista de resultados ordenados por relevancia.


- 3. (Opcional) El comprador visualiza el bloque de "Recomendaciones Personalizadas" generado dinámicamente según sus preferencias e historial.

- Flujos de Excepción:

- 2a. Sin coincidencias: El sistema notifica la ausencia de resultados y sugiere términos populares o limpiar los filtros.

## CU-C03: Consultar Ficha del Producto y Reseñas

- Actor Principal: Comprador.

- Objetivo: Obtener información detallada de un juego de mesa, incluyendo

especificaciones, disponibilidad y opiniones de otros usuarios.

- Precondiciones: El juego debe existir en el catálogo activo.

- Poscondiciones: Se presenta la vista detallada del producto.

- Flujo Principal:

- 1. El comprador selecciona un juego del catálogo o listado de búsqueda.

- 2. El sistema carga la ficha con imágenes, descripción, reglas/manuales, número de jugadores, rango de edad, precio y stock actual.

- 3. El sistema muestra la calificación promedio y el listado de reseñas enviadas por la comunidad.

## CU-C04: Gestionar Carrito de Compras

- Actor Principal: Comprador.

- Objetivo: Seleccionar, modificar cantidades o remover productos en el carrito previo al pago.

- Precondiciones: El producto debe contar con stock disponible.

- Poscondiciones: El carrito se actualiza y recalcula los subtotales y montos parciales.

- Flujo Principal:

- 1. El comprador especifica la cantidad deseada y presiona "Añadir al carrito" desde la ficha del juego.

- 2. El sistema confirma la adición y actualiza el estado del carrito.

- 3. El comprador accede al Carrito para revisar los ítems guardados, ajustar cantidades o eliminar productos.

- 4. El sistema recalcula inmediatamente los subtotales de la orden.

- Flujos de Excepción:

- 1a. Stock insuficiente: El sistema advierte el límite de unidades disponibles y ajusta la cantidad permitida.

## CU-C05: Procesar Compra y Consultar Factura

- Actor Principal: Comprador.

- Objetivo: Finalizar la transacción, efectuar el pago, generar la orden de pedido y acceder al comprobante digital.

- Precondiciones: El comprador debe haber iniciado sesión (CU-C01) y tener al menos un producto en el carrito.

- Poscondiciones: Se registra la orden de compra, se disminuye el stock, se liquida el pago


- y se emite la factura en PDF.

- Flujo Principal:

- 1. El comprador selecciona "Proceder al Pago" dentro del carrito.

- 2. Selecciona/ingresa la dirección de entrega y la modalidad de envío.

- 3. Selecciona la pasarela/método de pago y confirma la operación.

- 4. El sistema procesa la transacción, emite la confirmación y descuenta el stock de los productos.

- 5. El sistema redirige a la vista de confirmación y permite descargar o consultar la factura en PDF desde el historial de compras ("Mis Compras").

- Flujos de Excepción:

- 3a. Transacción rechazada: El sistema informa el motivo del rechazo del pago y habilita el reintento con otro medio de pago.

## CU-C06: Gestionar Lista de Deseos (Wishlist)

- Actor Principal: Comprador.

- Objetivo: Guardar y administrar títulos de interés para su posterior revisión o compra.

- Precondiciones: El comprador debe estar autenticado en la plataforma.

- Poscondiciones: Se guarda de forma persistente la lista de favoritos en la cuenta del usuario.

- Flujo Principal:

- 1. El comprador presiona "Guardar en Lista de Deseos" desde la ficha técnica de un juego.

- 2. El sistema vincula el juego al perfil del cliente.

- 3. El comprador accede a "Mi Lista de Deseos" para consultar los artículos guardados, transferirlos directamente al carrito o eliminarlos.

## 3. Casos de Uso: Módulo Administrador / Vendedor

## CU-A01: Administrar Catálogo, Inventario y Promociones

- Actor Principal: Administrador / Vendedor.

- Objetivo: Gestionar el ciclo de vida de los productos (alta, baja, modificación, control de stock) y aplicar reglas de precios o cupones promocionales.

- Precondiciones: Autenticación activa con rol de administración.

- Poscondiciones: El catálogo público de la tienda se actualiza con la oferta de productos y precios vigentes.

- Flujo Principal:

- 1. El administrador accede al panel de gestión de productos.

- 2. Selecciona crear un nuevo juego o editar uno existente (ajustando descripción, imágenes o stock).

- 3. (Opcional) Configura reglas de descuento, precios en oferta o cupones con fecha de inicio y fin.

- 4. El administrador guarda la configuración.

- 5. El sistema valida los datos y actualiza la base de datos de la tienda.


## CU-A02: Consultar Métricas y Reportes de Ventas

- Actor Principal: Administrador / Vendedor.

- Objetivo: Analizar el rendimiento comercial, facturación y comportamiento de ventas mediante reportes.

- Precondiciones: Sesión de administración activa.

- Poscondiciones: El sistema genera resúmenes gráficos e informes consolidados.

- Flujo Principal:

- 1. El administrador ingresa al Dashboard de Ventas.

- 2. Selecciona un rango de fechas y filtros aplicables (por categoría o producto).

- 3. El sistema calcula y presenta métricas clave: volumen de facturación, títulos más vendidos y estado de las órdenes de despacho.

## CU-A03: Moderar Contenido y Reseñas

- Actor Principal: Administrador / Vendedor.

- Objetivo: Evaluar, aprobar, ocultar o eliminar comentarios y calificaciones enviadas por la comunidad.

- Precondiciones: Existen valoraciones cargadas por los compradores.

- Poscondiciones: Se actualiza la visibilidad de los comentarios en las fichas públicas de los juegos.

- Flujo Principal:

- 1. El administrador accede al panel de moderación.

- 2. Revisa las opiniones y calificaciones publicadas o marcadas como sospechosas.

- 3. Aplica la acción requerida ("Aprobar", "Ocultar" o "Eliminar").

- 4. El sistema ajusta inmediatamente el estado del comentario y actualiza el promedio de valoración del producto.

## CU-A04: Administrar Usuarios y Permisos

- Actor Principal: Administrador Principal (Superadmin).

- Objetivo: Gestionar cuentas de usuario del personal, asignando roles y niveles de acceso a los módulos administrativos.

- Precondiciones: Autenticación activa con permisos de Superadministrador.

- Poscondiciones: Se actualiza el esquema de permisos de los operadores de la plataforma.

- Flujo Principal:

- 1. El super administrador accede al módulo de "Gestión de Personal".

- 2. Registra un nuevo empleado o selecciona un operador existente.

- 3. Asigna o modifica el rol correspondiente (ej. Vendedor, Moderador, Encargado de Depósito).

- 4. El sistema guarda la configuración y aplica las restricciones de acceso necesarias.
