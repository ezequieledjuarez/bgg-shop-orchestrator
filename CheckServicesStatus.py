import json
import socket
import urllib.request

# Mapa de servicios expuestos en el host mediante Podman
SERVICES = {
    "PostgreSQL (OLTP)": ("localhost", 5432),
    "Redis (Cache & Broker)": ("localhost", 6379),
    "Mailpit (SMTP UI)": ("localhost", 8025),
    "Saleor API Core (GraphQL)": ("localhost", 8000),
    "Flask Middleware (BFF REST)": ("localhost", 5000),
    "Frontend Storefront (Vite)": ("localhost", 3000),
}

SALEOR_GRAPHQL_URL = "http://localhost:8000/graphql/"
FLASK_HEALTH_URL = "http://localhost:5000/health"


def check_socket(host: str, port: int) -> bool:
    """Valida la conectividad a nivel de capa de transporte (TCP Sockets)."""
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except (socket.timeout, ConnectionRefusedError):
        return False


def check_graphql() -> str:
    """Valida que Saleor Core responda consultas GraphQL correctamente."""
    # Consultamos el campo 'hello' definido en saleor.graphql.api.schema
    query = json.dumps({"query": "{ hello }"}).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (TestUp-Audit-Agent)",
    }

    req = urllib.request.Request(
        SALEOR_GRAPHQL_URL, data=query, headers=headers
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as res:
            if res.status == 200:
                body = json.loads(res.read().decode("utf-8"))
                message = body.get("data", {}).get("hello", "N/A")
                return f"🟢 ONLINE (Respuesta GraphQL: '{message}')"
            return f"⚠️ HTTP {res.status}"
    except urllib.error.HTTPError as e:
        # Imprime la respuesta interna devuelta para trazabilidad
        error_payload = e.read().decode("utf-8")
        return f"🔴 HTTP {e.code} ({error_payload[:100]})"
    except Exception as e:
        return f"🔴 OFFLINE ({e})"


def check_flask_bff() -> str:
    """Valida que el Gateway de Flask (BFF) esté escuchando peticiones HTTP."""
    req = urllib.request.Request(FLASK_HEALTH_URL)
    try:
        with urllib.request.urlopen(req, timeout=3) as res:
            if res.status == 200:
                return "🟢 ONLINE (Endpoint /health OK)"
            return f"⚠️ HTTP {res.status}"
    except Exception as e:
        # Si no tenés configurado la ruta /health aún, pero el socket responde:
        return f"🟡 ONLINE / SIN HEALTHCHECK ({e})"


if __name__ == "__main__":
    print("=" * 60)
    print("  AUDITORÍA DE INFRAESTRUCTURA PODMAN - BGG SHOP (BFF ARCHITECTURE)")
    print("=" * 60)

    # 1. Verificación de Sockets TCP
    print("\n[1] Verificación de Puertos y Sockets TCP:")
    for name, (host, port) in SERVICES.items():
        status = "🟢 OK" if check_socket(host, port) else "🔴 FAIL"
        print(f"  - {name.ljust(30)} [{host}:{port}]: {status}")

    # 2. Verificación de Endpoints HTTP / APIs
    print("\n[2] Verificación de Capa de Aplicaciones (HTTP/APIs):")
    print(f"  - Saleor API (GraphQL Core)   : {check_graphql()}")
    print(f"  - Flask Gateway (BFF REST)    : {check_flask_bff()}")
    print("=" * 60)