# MCP del workspace

Este workspace configura servidores MCP para ampliar las herramientas del
asistente durante el desarrollo. **No son dependencias ni servicios de la
tienda en ejecución**. La configuración está en [`mcp.json`](mcp.json).

## Servidores configurados

| MCP | Funcionalidad | Ejemplos de uso |
| --- | --- | --- |
| **Context7** | Busca documentación actual de librerías, frameworks y herramientas. | Consultar documentación de Django, React o una biblioteca antes de implementar una integración. |
| **GitHub** | Conecta con GitHub para consultar repositorios y código, buscar issues y pull requests y, según los permisos concedidos, gestionar elementos del repositorio. Usa el endpoint remoto oficial y autenticación OAuth de VS Code. | Buscar una implementación en un repositorio, revisar un PR o consultar un issue. |
| **Engram** | Guarda y recupera decisiones y contexto técnico entre sesiones. | Recuperar por qué se eligió una tecnología o qué quedó pendiente de una tarea. |
| **Terminal (Git)** | Expone operaciones Git para consultar el estado, diferencias, ramas, commits, historial y remotos; también incluye operaciones que modifican el repositorio. Cada operación recibe la ruta del repositorio objetivo. | Revisar cambios antes de una tarea o consultar el historial de una rama. Confirmar el alcance antes de operaciones destructivas. |
| **Playwright** | Automatiza un navegador en modo headless para navegar y validar interfaces, interacciones y respuestas. | Abrir la tienda local, completar un flujo de interfaz o revisar errores de consola. |
| **Mercado Pago** | Consulta documentación y ofrece herramientas para usuarios de prueba, notificaciones/webhooks y evaluación de integraciones. | Buscar documentación de Checkout Pro o diagnosticar una notificación de prueba. Algunas herramientas pueden acceder a datos o credenciales sensibles. |

## Uso en VS Code

1. Abrí el workspace y habilitá el modo **Agent** en Copilot Chat.
2. Si un servidor MCP todavía no aparece, recargá los servidores desde la
   interfaz de VS Code y completá la autenticación que solicite.
3. Pedile al asistente la tarea indicando el servidor o el contexto que querés
   usar. El asistente elegirá las herramientas pertinentes si están disponibles.

El servidor GitHub se conecta a `https://api.githubcopilot.com/mcp/`. VS Code
gestiona OAuth; no agregues un Personal Access Token ni credenciales al archivo
`mcp.json`. Las acciones disponibles dependen de la cuenta autorizada y de sus
permisos.

## Alcance y seguridad

- Los servidores remotos requieren conexión de red y pueden solicitar
  autenticación.
- Revisá el destino y el efecto antes de autorizar cambios remotos en GitHub,
  creación o modificación de recursos, pagos o acciones irreversibles.
- No compartas secretos, tokens ni datos de clientes en prompts o archivos.
- Playwright está configurado con `HEADLESS=true`; para probar la aplicación,
  primero iniciá los servicios locales según la [guía del proyecto](../README.MD).
- La configuración de Engram usa una ruta local específica de Windows para el
  ejecutable. En otra máquina o sistema operativo puede ser necesario adaptar
  esa entrada.
- Azure no está configurado en este archivo. Su disponibilidad en VS Code no
  forma parte de los MCP declarados por este workspace.
