#!/usr/bin/env bash
# Disposable local-only CU-A04 integration. Requires cached postgres:15-alpine,
# Python service dependencies, frontend node_modules and installed Chromium.
set -euo pipefail
cd "$(dirname "$0")/.."
runner_pid=''
trap 'if [[ -n "$runner_pid" ]]; then kill -TERM "$runner_pid" 2>/dev/null || true; wait "$runner_pid" || true; fi' EXIT INT TERM
python3 - <<'PY' &
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit

root = Path.cwd()
run_id = secrets.token_hex(16)
work = root / f".spec012-local-{run_id}"
work.mkdir(mode=0o700)
os.umask(0o077)
isolated_home = work / "home"
isolated_home.mkdir(mode=0o700)
env = {
    "PATH": os.defpath + os.pathsep + str(Path(shutil.which("node") or "/missing").parent),
    "HOME": str(isolated_home), "LANG": "C.UTF-8", "TMPDIR": str(work),
    "NETRC": str(work / "no-ambient-netrc"),
    "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1",
    "npm_config_offline": "true", "npm_config_update_notifier": "false",
    "npm_config_cache": str(work / "npm-cache"),
    "npm_config_userconfig": "/dev/null", "npm_config_globalconfig": "/dev/null",
}
runtime_env = {**env, "HOME": str(Path.home())}
runtime = []
container_id = None
creation_attempted = False
processes = []
logs = []
password = secrets.token_hex(24)
secret = secrets.token_hex(48)
database = f"user_permissions_test_{run_id}"
container_name = f"spec012-postgres-{run_id}"
private = [password, secret]


def safe(value):
    text = str(value)
    for item in private:
        text = text.replace(item, "[redacted]")
    text = re.sub(r"(?:postgres(?:ql)?|redis)://\S+", "[private endpoint]", text)
    text = re.sub(r"Bearer\s+[A-Za-z0-9._~+/-]+=*", "Bearer [redacted]", text)
    text = re.sub(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "[private token]", text)
    return re.sub(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "[synthetic email]", text)


def run(args, *, cwd=root, child_env=None, timeout=60):
    return subprocess.run(
        args, cwd=cwd, env=child_env or env, text=True, capture_output=True,
        check=True, timeout=timeout,
    ).stdout.strip()


def start(name, args, cwd, child_env):
    log = (work / f"{name}.log").open("w+")
    logs.append(log)
    process = subprocess.Popen(
        args, cwd=cwd, env=child_env, stdout=log, stderr=log,
        start_new_session=True,
    )
    processes.append((name, process, log))
    return process


def ready(name, url, expected, process):
    deadline = time.monotonic() + 60
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    while time.monotonic() < deadline:
        if process.poll() is not None:
            log = next(log for _, item, log in processes if item is process)
            log.seek(0)
            lines = log.read().splitlines()
            raise RuntimeError(f"{name} exited during startup: {safe(lines[-1] if lines else 'no output')}")
        try:
            with opener.open(url, timeout=1) as response:
                body = response.read().decode()
                if response.status == 200 and expected in body:
                    print(f"READY {name}: loopback HTTP 200", flush=True)
                    return
        except (urllib.error.URLError, TimeoutError, OSError):
            pass
        time.sleep(0.2)
    raise RuntimeError(f"{name} HTTP readiness timed out after 60s")


def interrupted(signum, frame):
    raise RuntimeError(f"Interrupted by signal {signum}")


for sig in (signal.SIGTERM, signal.SIGINT):
    signal.signal(sig, interrupted)

status = 1
try:
    if shutil.which("podman"):
        runtime = [shutil.which("podman"), "--remote=false"]
    elif shutil.which("docker"):
        runtime = [shutil.which("docker"), "--host", "unix:///var/run/docker.sock"]
    else:
        raise RuntimeError("No local Podman or Docker executable is installed")
    image = "docker.io/library/postgres:15-alpine"
    run(runtime + ["image", "inspect", image], child_env=runtime_env)
    python = sys.executable
    run([python, "-c", "import django, environ, psycopg2, graphene, celery, flask, flask_cors, redis"])
    frontend = root / "bgg-shop-frontend"
    if any((directory / ".npmrc").exists() for directory in (root, frontend)):
        raise RuntimeError("Refusing project .npmrc; the harness cannot consume ambient npm credentials")
    if not (frontend / "node_modules/.bin/playwright").is_file():
        raise RuntimeError("Local frontend Playwright dependency is missing; no installation attempted")
    browser_cache = Path.home() / ".cache/ms-playwright"
    if not any(browser_cache.glob("chromium-*/chrome-linux64/chrome")):
        raise RuntimeError("Cached Chromium is missing; no browser download attempted")

    # Keep reservations until each server is launched; strict binds reject a race.
    reservations = []
    for _ in range(3):
        reservation = socket.socket()
        reservation.bind(("127.0.0.1", 0))
        reservation.listen()
        reservations.append(reservation)
    core_port, bff_port, front_port = [item.getsockname()[1] for item in reservations]
    core_url, bff_url, front_url = [
        f"http://127.0.0.1:{port}" for port in (core_port, bff_port, front_port)
    ]
    db_env = {**runtime_env, "POSTGRES_DB": database, "POSTGRES_USER": database, "POSTGRES_PASSWORD": password}
    creation_attempted = True
    container_id = run(runtime + [
        "run", "--detach", "--pull=never", "--name", container_name,
        "--label", f"spec012.run={run_id}", "--publish", "127.0.0.1::5432",
        "--tmpfs", "/var/lib/postgresql/data:rw",
        "--env", "POSTGRES_DB", "--env", "POSTGRES_USER", "--env", "POSTGRES_PASSWORD",
        image,
    ], child_env=db_env)
    details = json.loads(run(runtime + ["inspect", container_id], child_env=runtime_env))[0]
    if any(mount.get("Type") == "volume" for mount in details.get("Mounts", [])):
        raise RuntimeError("Refusing PostgreSQL container with a persistent volume")
    binding = details["NetworkSettings"]["Ports"]["5432/tcp"]
    if len(binding) != 1 or binding[0]["HostIp"] != "127.0.0.1":
        raise RuntimeError("Refusing PostgreSQL publication outside loopback")
    db_port = int(binding[0]["HostPort"])
    dsn = f"postgresql://{database}:{password}@127.0.0.1:{db_port}/{database}"
    private.append(dsn)
    parsed = urlsplit(dsn)
    if (parsed.hostname != "127.0.0.1" or not parsed.port
            or not re.fullmatch(r"user_permissions_test_[0-9a-f]{32}", parsed.username or "")
            or parsed.username != database or parsed.path != f"/{database}"
            or parsed.query or parsed.fragment):
        raise RuntimeError("Refusing non-loopback or mismatched dedicated database/user")
    deadline = time.monotonic() + 60
    while True:
        try:
            run(runtime + ["exec", container_id, "pg_isready", "-U", database, "-d", database], child_env=runtime_env, timeout=5)
            break
        except subprocess.CalledProcessError:
            if time.monotonic() >= deadline:
                raise RuntimeError("Dedicated PostgreSQL readiness timed out after 60s")
            time.sleep(0.2)
    print("READY PostgreSQL: unique loopback container, tmpfs data, matching synthetic database/user", flush=True)

    service_env = {
        **env, "DATABASE_URL": dsn, "DJANGO_SETTINGS_MODULE": "saleor.settings",
        "SECRET_KEY": secret, "SECRET_KEY_FALLBACKS": "[]", "DEBUG": "false",
        "ALLOWED_HOSTS": "127.0.0.1", "FRONTEND_URL": front_url,
        "CORS_ALLOWED_ORIGINS": front_url, "CSRF_TRUSTED_ORIGINS": front_url,
        "OPKEYS_ISSUE_ON_LOGIN": "false", "OPKEY_INTERNAL_SECRET": secret,
        "SALEOR_GRAPHQL_URL": f"{core_url}/graphql/", "SALEOR_BASE_URL": core_url,
        "CELERY_BROKER_URL": "memory://", "REDIS_URL": "redis://127.0.0.1:0/0",
        "CATALOG_REDIS_URL": "redis://127.0.0.1:0/0",
        "E2E_SPEC012_RUN_ID": run_id, "E2E_SPEC012_PASSWORD": password,
    }
    bootstrap = """
import environ
# Core unconditionally loads .env; disable that loader before importing settings.
environ.Env.read_env = staticmethod(lambda *args, **kwargs: None)
import django
django.setup()
"""
    seed = bootstrap + """
import json
import os
import time
import jwt
from django.conf import settings
from django.core.management import call_command
from django.contrib.auth import get_user_model
from saleor.graphql.api import schema
assert schema is not None
db = settings.DATABASES['default']
name = 'user_permissions_test_' + os.environ['E2E_SPEC012_RUN_ID']
assert db['HOST'] == '127.0.0.1' and db['NAME'] == db['USER'] == name
call_command('migrate', 'auth', verbosity=0, interactive=False, skip_checks=True)
call_command('migrate', 'opkeys', verbosity=0, interactive=False, skip_checks=True)
for role, active, staff, superuser in [
    ('superadmin', True, False, True), ('staff', True, True, False),
    ('target', True, False, False), ('selfdemoter', True, False, True),
    ('inactive', False, False, True), ('solo', True, False, True),
    ('race-a', True, False, True), ('race-b', True, False, True),
]:
    email = role + '-' + os.environ['E2E_SPEC012_RUN_ID'] + '@example.test'
    user = get_user_model().objects.create_user(
        username=email, email=email, password=os.environ['E2E_SPEC012_PASSWORD'],
        first_name='Synthetic', last_name=role, is_active=active,
        is_staff=staff, is_superuser=superuser,
    )
    if role == 'inactive':
        inactive_token = jwt.encode(
            {'sub': str(user.pk), 'token_type': 'access', 'exp': int(time.time()) + 600},
            settings.SECRET_KEY, algorithm='HS256',
        )
print(json.dumps({'inactive_token': inactive_token}))
"""
    seeded = json.loads(run([python, "-c", seed], cwd=root / "bgg-shop-core", child_env=service_env, timeout=90))
    inactive_token = seeded["inactive_token"]
    private.append(inactive_token)
    print("READY seed: eight synthetic accounts; inactive Superadmin and solo/race actors; is_staff=false", flush=True)

    reservations[0].close()
    core = start("Core", [python, "-c", bootstrap + f"""
from django.core.management import call_command
call_command('runserver', '127.0.0.1:{core_port}', use_reloader=False, skip_checks=True)
"""], root / "bgg-shop-core", service_env)
    ready("Core", core_url + "/graphql/?query=%7B__typename%7D", '"Query"', core)
    reservations[1].close()
    bff = start("BFF", [python, "-c", f"""
import app
# The existing diagnostic hook writes /tmp; disable it only in this process.
app._append_incoming_log = lambda entry: None
app.app.run(host='127.0.0.1', port={bff_port}, debug=False, use_reloader=False)
"""], root / "bgg-shop-bff", service_env)
    ready("BFF", bff_url + "/health", '"healthy"', bff)
    reservations[2].close()
    # Same-origin browser API requests avoid changing the BFF's fixed CORS policy.
    vite = start("Frontend", ["node", "--input-type=module", "-e", f"""
import {{ createServer }} from 'vite';
import react from '@vitejs/plugin-react';
const server = await createServer({{
  configFile: false, envFile: false, plugins: [react()],
  cacheDir: {json.dumps(str(work / "vite-cache"))},
  define: {{
    'import.meta.env.VITE_API_BASE_URL': {json.dumps(json.dumps(front_url + "/api/v1"))},
    'import.meta.env.VITE_USE_OPKEY': '"false"'
  }},
  server: {{host: '127.0.0.1', port: {front_port}, strictPort: true,
    proxy: {{'/api': {{target: {json.dumps(bff_url)}, changeOrigin: true}}}}}}
}});
await server.listen();
"""], frontend, env)
    ready("Frontend", front_url + "/login", "<html", vite)
    test_env = {
        **env, "E2E_OPKEY_ISOLATED": "true", "E2E_SPEC012_ISOLATED": "true",
        "E2E_SPEC012_RUN_ID": run_id, "E2E_SPEC012_PASSWORD": password,
        "E2E_SPEC012_INACTIVE_TOKEN": inactive_token,
        "VITE_API_BASE_URL": front_url, "PW_BFF_URL": bff_url,
        "PLAYWRIGHT_BROWSERS_PATH": str(browser_cache),
        "PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD": "1",
    }
    print("RUN local Playwright admin-users.spec.ts --project=chromium --workers=1 "
          "(list reporter and unique output directory; credentials/artifacts not printed)", flush=True)
    playwright = start("Playwright", [
        str(frontend / "node_modules/.bin/playwright"), "test", "tests/e2e/admin-users.spec.ts",
        "--project=chromium", "--workers=1", "--reporter=list",
        "--output", str(work / "playwright"),
    ], frontend, test_env)
    playwright.wait(timeout=240)
    playwright_log = processes[-1][2]
    playwright_log.seek(0)
    result = playwright_log.read()
    if playwright.returncode:
        raise subprocess.CalledProcessError(playwright.returncode, "local Playwright", output=result)
    print(safe(result), flush=True)
    status = 0
except subprocess.CalledProcessError as exc:
    output = (exc.stdout or "") + (exc.stderr or "")
    lines = output.strip().splitlines()[-30:] or ["command failed"]
    print(f"BLOCKED: local command failed (exit {exc.returncode})", file=sys.stderr, flush=True)
    for line in lines:
        print(safe(line), file=sys.stderr, flush=True)
except Exception as exc:
    print(f"BLOCKED: {safe(exc)}", file=sys.stderr, flush=True)
finally:
    cleanup_ok = True
    for reservation in locals().get("reservations", []):
        reservation.close()
    for name, process, _ in reversed(processes):
        try:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=5)
            print(f"CLEANUP {name}: owned PID {process.pid} exited", flush=True)
        except Exception:
            cleanup_ok = False
            print(f"CLEANUP FAILED {name}: owned PID {process.pid}", file=sys.stderr)
    if creation_attempted and not container_id:
        try:
            owned = json.loads(run(runtime + ["inspect", container_name], child_env=runtime_env))[0]
            if owned.get("Config", {}).get("Labels", {}).get("spec012.run") == run_id:
                container_id = owned["Id"]
            else:
                raise RuntimeError("Ownership label mismatch")
        except subprocess.CalledProcessError:
            pass
        except Exception:
            cleanup_ok = False
            print("CLEANUP FAILED: cannot establish unique container ownership", file=sys.stderr)
    if container_id:
        try:
            run(runtime + ["rm", "--force", container_id], child_env=runtime_env)
            remaining = run(runtime + ["ps", "--all", "--quiet", "--filter", f"id={container_id}"], child_env=runtime_env)
            if remaining:
                raise RuntimeError("Owned container remains")
            print("CLEANUP PostgreSQL: owned container absent; tmpfs database destroyed; no volumes created", flush=True)
        except Exception:
            cleanup_ok = False
            print("CLEANUP FAILED: owned PostgreSQL container may remain", file=sys.stderr)
    else:
        print("CLEANUP PostgreSQL: no container was created", flush=True)
    for log in logs:
        log.close()
    inspected = sensitive = 0
    for artifact in work.rglob("*"):
        if artifact.is_file() and not artifact.is_symlink():
            contents = artifact.read_bytes().decode("utf-8", errors="replace")
            inspected += 1
            sensitive += int(
                any(item in contents for item in private)
                or bool(re.search(r"Bearer\s+\S+|eyJ[\w-]+\.[\w-]+\.[\w-]+|"
                                  r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b|"
                                  r"(?:postgres(?:ql)?|redis)://\S+", contents))
            )
    print(f"SECURITY disposable output: {inspected} files checked; {sensitive} contain synthetic "
          "sensitive patterns; contents withheld and all scheduled for removal", flush=True)
    shutil.rmtree(work)
    if work.exists():
        cleanup_ok = False
        print("CLEANUP FAILED: unique run directory remains", file=sys.stderr)
    else:
        print("CLEANUP artifacts: unique run directory confirmed absent; repository storage state untouched", flush=True)
    if not cleanup_ok:
        status = 1
sys.exit(status)
PY
runner_pid=$!
wait "$runner_pid"
runner_pid=''
