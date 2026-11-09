#!/usr/bin/env python3
"""Create a separate persistent local database; never reconfigure the live stack."""
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import socket
import stat
import subprocess
import sys
import time
import uuid


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".local/parallel-db/connection.env"
DATABASE_ENV = ROOT / ".local/parallel-db/database.env"
AUTH_ENV = ROOT / ".local/parallel-db/auth.env"
CONTAINER = "bgg_shop_parallel_db"
VOLUME = "bgg_shop_parallel_pgdata"
NETWORK = "bgg_shop_parallel_internal"
OWNER = "bgg-shop-parallel-v1"
PG_IMAGE = "docker.io/library/postgres:15-alpine"
CORE_IMAGE = "localhost/boardgame-app_api:latest"
DATABASE = "bgg_shop_parallel"
ADMIN = "admin@example.test"
FIELDS = (
    "bgg_id, name, release_year, min_players, max_players,\n"
    "    playing_time_minutes, min_age, weight, category,\n"
    "    price_amount, publisher, image_url, image_filename"
)


def catalog_insert(source):
    """Accept only the reviewed INSERT grammar, never the surrounding seed SQL."""
    start = "INSERT INTO product_boardgame (\n    " + FIELDS + "\n) VALUES\n"
    end = "\n\n-- Development catalog seed inventory;"
    if source.count(start) != 1 or source.count(end) != 1:
        raise ValueError("Catalog INSERT boundaries changed")
    statement = source.split(start, 1)[1].split(end, 1)[0]
    text = r"'(?:[^']|'')*'"
    integer = r"\d+"
    money = r"\d+\.\d{2}"
    row = r"\(" + r", ".join(
        [integer, text] + [integer] * 5 + [money, text, money, text, text, text]
    ) + r"\)"
    if not re.fullmatch(r"    " + row + r"(?:,\n    " + row + r")*;", statement):
        raise ValueError("Catalog contains unexpected SQL")
    if len(re.findall(r"^    \(", statement, re.MULTILINE)) != 49:
        raise ValueError("Reviewed catalog must contain exactly 49 products")
    return start + statement


def guard_new_state(container, volume, config):
    if container or volume or config:
        raise RuntimeError("Refusing existing state; use status, never reset or rerun create")


def read_private_config(path=CONFIG):
    if path.is_symlink():
        raise RuntimeError("Private config cannot be a symlink")
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600:
        raise RuntimeError("Private config must be a regular mode-0600 file")
    if info.st_uid != os.getuid():
        raise RuntimeError("Private config belongs to another user")
    values = dict(line.split("=", 1) for line in path.read_text().splitlines())
    expected = {"POSTGRES_USER", "POSTGRES_DB", "POSTGRES_PASSWORD", "LOCAL_PORT", "INIT_STATUS"}
    if set(values) != expected or values["POSTGRES_USER"] != DATABASE or values["POSTGRES_DB"] != DATABASE:
        raise RuntimeError("Unexpected private configuration")
    if not re.fullmatch(r"[A-Za-z0-9_-]{40,}", values["POSTGRES_PASSWORD"]):
        raise RuntimeError("Invalid private database credential format")
    if not 55432 <= int(values["LOCAL_PORT"]) <= 55499:
        raise RuntimeError("Unexpected local database port")
    if values["INIT_STATUS"] not in {"CREATING", "READY", "FAILED"}:
        raise RuntimeError("Unexpected initialization state")
    return values


def write_config(values, *, new=False):
    flags = os.O_WRONLY | os.O_NOFOLLOW
    flags |= os.O_CREAT | os.O_EXCL if new else os.O_TRUNC
    fd = os.open(CONFIG, flags, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write("".join(f"{key}={value}\n" for key, value in values.items()))
        stream.flush()
        os.fsync(stream.fileno())


def render_application_envs(values, secret_key):
    if values["POSTGRES_USER"] != DATABASE or values["POSTGRES_DB"] != DATABASE:
        raise RuntimeError("Parallel database configuration does not match the owned database")
    if not re.fullmatch(r"[A-Za-z0-9_-]{40,}", values["POSTGRES_PASSWORD"]):
        raise RuntimeError("Invalid private database credential format")
    if not isinstance(secret_key, str) or len(secret_key) < 50 or "\n" in secret_key or "=" in secret_key:
        raise RuntimeError("Invalid rotated authentication key")
    return {
        "database.env": (
            f"DATABASE_URL=postgresql://{DATABASE}:{values['POSTGRES_PASSWORD']}"
            f"@{CONTAINER}:5432/{DATABASE}\n"
        ),
        "auth.env": f"SECRET_KEY={secret_key}\nSECRET_KEY_FALLBACKS=[]\n",
    }


def write_private_env(path, content):
    path = Path(path)
    if path not in {DATABASE_ENV, AUTH_ENV}:
        raise RuntimeError("Refusing an unapproved private environment path")
    if path.parent.is_symlink():
        raise RuntimeError("Private directory cannot be a symlink")
    directory = path.parent.stat()
    if not stat.S_ISDIR(directory.st_mode) or stat.S_IMODE(directory.st_mode) != 0o700:
        raise RuntimeError("Private directory must be a mode-0700 directory")
    if path.is_symlink() or path.exists():
        raise RuntimeError("Private application environment already exists; refusing overwrite")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def current_runtime_secret_keys():
    keys = set()
    for name in ("saleor_api", "saleor_celery", "saleor_bff"):
        container = inspect("container", name)
        environment = dict(
            item.split("=", 1) for item in container["Config"].get("Env", [])
            if "=" in item
        )
        key = environment.get("SECRET_KEY")
        if not key:
            raise RuntimeError(f"Missing current authentication configuration for {name}")
        keys.add(key)
    return keys


def require_database_ready():
    ready = subprocess.run(
        ["podman", "exec", CONTAINER, "pg_isready", "-U", DATABASE, "-d", DATABASE],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    if ready.returncode:
        raise RuntimeError("Parallel database is not ready")


def switch_application():
    values = read_private_config()
    require_owned_runtime(values)
    if values["INIT_STATUS"] != "READY":
        raise RuntimeError("Parallel database must be READY before switching the application")
    require_database_ready()
    present = [
        path for path in (DATABASE_ENV, AUTH_ENV)
        if path.is_symlink() or path.exists()
    ]
    if len(present) == 2:
        raise RuntimeError(
            "Private application environments already exist; refusing overwrite or key rotation"
        )
    if present:
        raise RuntimeError(
            "Partial private application environment preserved; inspect it locally before retrying"
        )
    for path in (DATABASE_ENV, AUTH_ENV):
        run(["git", "-C", str(ROOT), "check-ignore", "-q", str(path)])
        if run(["git", "-C", str(ROOT), "ls-files", "--", str(path)]).strip():
            raise RuntimeError("Private application environment is tracked")
    # Verify the actual database before creating the one-time application configuration.
    core_runner("verify")
    previous_keys = current_runtime_secret_keys()
    secret_key = secrets.token_urlsafe(64)
    if secret_key in previous_keys:
        raise RuntimeError("Generated authentication key did not rotate")
    envs = render_application_envs(values, secret_key)
    created = []
    try:
        write_private_env(DATABASE_ENV, envs["database.env"])
        created.append(DATABASE_ENV)
        write_private_env(AUTH_ENV, envs["auth.env"])
        created.append(AUTH_ENV)
    except BaseException:
        for path in created:
            path.unlink(missing_ok=True)
        raise
    print("Private application environment prepared for the parallel database.")
    print("Recreate only api, celery, and bff to apply it; no application containers were changed.")


def run(args, *, input=None, interactive=False):
    result = subprocess.run(
        args, input=input, text=True,
        stdout=None if interactive else subprocess.PIPE,
        stderr=None if interactive else subprocess.PIPE,
    )
    if result.returncode:
        # Do not echo subprocess output: database errors can contain credentials.
        raise RuntimeError(f"Local operation failed: {args[0]} {args[1]} (exit {result.returncode})")
    return result.stdout


def exists(kind, name):
    return subprocess.run(
        ["podman", kind, "exists", name], stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def inspect(kind, name):
    return json.loads(run(["podman", kind, "inspect", name]))[0]


def require_owned_runtime(values):
    container = inspect("container", CONTAINER)
    volume = inspect("volume", VOLUME)
    network = inspect("network", NETWORK)
    if (
        container["Config"]["Labels"].get("local.bootstrap") != OWNER
        or volume["Labels"].get("local.bootstrap") != OWNER
        or network["labels"].get("local.bootstrap") != OWNER
        or not network["internal"]
        or container["State"]["Status"] != "running"
        or not any(m.get("Name") == VOLUME and m["Destination"] == "/var/lib/postgresql/data"
                   for m in container["Mounts"])
        or container["NetworkSettings"]["Ports"].get("5432/tcp") != [
            {"HostIp": "127.0.0.1", "HostPort": values["LOCAL_PORT"]}
        ]
    ):
        raise RuntimeError("Parallel runtime ownership, persistence or isolation mismatch")


def core_runner(action, *, catalog=None):
    name = "bgg_shop_parallel_runner_" + uuid.uuid4().hex
    args = [
        "podman", "run", "--rm", "--pull=never", "--name", name,
        "--network", "container:" + CONTAINER, "--workdir", "/source",
        "--env", "PYTHONDONTWRITEBYTECODE=1",
    ]
    for source, destination in (
        (ROOT / "bgg-shop-core/saleor", "/source/saleor"),
        (ROOT / "bgg-shop-core/opkeys", "/source/opkeys"),
        (ROOT / "scripts/create_parallel_database.py", "/source/scripts/create_parallel_database.py"),
        (ROOT / "scripts/sql/parallel_baseline.sql", "/baseline.sql"),
        (CONFIG, "/connection.env"),
    ):
        args += ["--volume", f"{source}:{destination}:ro"]
    args += ["-it" if action == "admin-password" else "-i", "--entrypoint", "python",
             CORE_IMAGE, "/source/scripts/create_parallel_database.py", "_worker", action]
    try:
        return run(args, input=catalog, interactive=action == "admin-password")
    finally:
        if exists("container", name):
            run(["podman", "rm", "-f", name])


def create(port):
    catalog = catalog_insert((ROOT / "import_catalog.sql").read_text())
    guard_new_state(exists("container", CONTAINER), exists("volume", VOLUME), CONFIG.exists())
    if exists("network", NETWORK):
        raise RuntimeError("Refusing existing parallel network")
    for image in (PG_IMAGE, CORE_IMAGE):
        run(["podman", "image", "exists", image])
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", port))
    run(["git", "-C", str(ROOT), "check-ignore", "-q", str(CONFIG)])
    tracked = run(["git", "-C", str(ROOT), "ls-files", "--", str(CONFIG)])
    if tracked.strip():
        raise RuntimeError("Private config is tracked")
    for directory in (ROOT / ".local", CONFIG.parent):
        if directory.is_symlink():
            raise RuntimeError("Private directory cannot be a symlink")
        directory.mkdir(mode=0o700, exist_ok=True)
    os.chmod(CONFIG.parent, 0o700)
    values = {
        "POSTGRES_USER": DATABASE, "POSTGRES_DB": DATABASE,
        "POSTGRES_PASSWORD": secrets.token_urlsafe(48),
        "LOCAL_PORT": str(port), "INIT_STATUS": "CREATING",
    }
    write_config(values, new=True)
    try:
        run(["podman", "network", "create", "--internal", "--label",
             "local.bootstrap=" + OWNER, NETWORK])
        run(["podman", "volume", "create", "--label", "local.bootstrap=" + OWNER, VOLUME])
        run([
            "podman", "run", "-d", "--pull=never", "--name", CONTAINER,
            "--label", "local.bootstrap=" + OWNER, "--network", NETWORK,
            "--publish", f"127.0.0.1:{port}:5432", "--env-file", str(CONFIG),
            "--volume", VOLUME + ":/var/lib/postgresql/data", PG_IMAGE,
        ])
        for _ in range(60):
            ready = subprocess.run(
                ["podman", "exec", CONTAINER, "pg_isready", "-U", DATABASE, "-d", DATABASE],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            if ready.returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError("Parallel PostgreSQL did not become ready")
        require_owned_runtime(values)
        print(core_runner("bootstrap", catalog=catalog).strip())
        values["INIT_STATUS"] = "READY"
        write_config(values)
    except BaseException:
        values["INIT_STATUS"] = "FAILED"
        write_config(values)
        print("Partial state preserved in the new database only; do not rerun create.", file=sys.stderr)
        raise


def resume_empty():
    """Recover only our failed initialization with no commercial/Django tables."""
    values = read_private_config()
    require_owned_runtime(values)
    if values["INIT_STATUS"] != "FAILED":
        raise RuntimeError("Only a failed, empty initialization can be resumed")
    tables = run([
        "podman", "exec", CONTAINER, "psql", "-U", DATABASE, "-d", DATABASE, "-Atqc",
        "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'",
    ]).strip()
    if tables != "0":
        raise RuntimeError("Nonempty partial database preserved; automatic recovery refused")
    catalog = catalog_insert((ROOT / "import_catalog.sql").read_text())
    values["INIT_STATUS"] = "CREATING"
    write_config(values)
    try:
        print(core_runner("bootstrap", catalog=catalog).strip())
        values["INIT_STATUS"] = "READY"
        write_config(values)
    except BaseException:
        values["INIT_STATUS"] = "FAILED"
        write_config(values)
        raise


def configure_worker():
    from django.conf import settings
    values = read_private_config(Path("/connection.env"))
    settings.configure(
        SECRET_KEY=secrets.token_urlsafe(64),
        CHAT_ASSERTION_SECRET=secrets.token_urlsafe(64),
        SECRET_KEY_FALLBACKS=[], USE_TZ=True, TIME_ZONE="UTC",
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        INSTALLED_APPS=[
            "django.contrib.contenttypes", "django.contrib.auth", "django.contrib.sessions",
            "saleor.graphql", "saleor.promotions", "saleor.catalog_events", "opkeys",
        ],
        DATABASES={"default": {
            "ENGINE": "django.db.backends.postgresql", "NAME": DATABASE,
            "USER": DATABASE, "PASSWORD": values["POSTGRES_PASSWORD"],
            "HOST": "127.0.0.1", "PORT": "5432",
            "OPTIONS": {"connect_timeout": 5},
        }},
    )
    sys.path.insert(0, "/source")
    import django
    django.setup()
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database(), current_user")
        if cursor.fetchone() != (DATABASE, DATABASE):
            raise RuntimeError("Worker must connect only to the parallel database")


def seed():
    from datetime import timedelta
    from django.contrib.auth.models import User
    from django.db import connection, transaction
    from django.utils import timezone
    with transaction.atomic():
        admin = User.objects.create_user(
            username=ADMIN, email=ADMIN, password=None,
            is_active=True, is_staff=True, is_superuser=True,
        )
        with connection.cursor() as cursor:
            cursor.execute("UPDATE product_boardgame SET quantity = 10")
            cursor.execute("SELECT bgg_id, name, price_amount FROM product_boardgame ORDER BY bgg_id LIMIT 16")
            products = cursor.fetchall()
            for index, days in enumerate([0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 17, 20, 23, 26, 29]):
                product, name, price = products[index]
                order = uuid.uuid4()
                quantity = 1 + index % 3
                total = price * quantity
                paid = timezone.now() - timedelta(days=days, minutes=1)
                cursor.execute(
                    "INSERT INTO purchase_order (id,user_id,status,total,currency,shipping_mode,"
                    "payment_status,created_at,paid_at) VALUES (%s,%s,'paid',%s,'ARS','pickup',"
                    "'approved',%s,%s)", [order, admin.pk, total, paid, paid],
                )
                cursor.execute(
                    "INSERT INTO purchase_order_line (order_id,bgg_id,name,unit_price,quantity,subtotal)"
                    " VALUES (%s,%s,%s,%s,%s,%s)", [order, product, name, price, quantity, total],
                )
                cursor.execute("INSERT INTO invoice (order_id,issued_at,total) VALUES (%s,%s,%s)",
                               [order, paid, total])


def verify_worker(*, expect_unusable=False):
    from datetime import timedelta
    from decimal import Decimal
    from io import StringIO
    from django.conf import settings
    from django.contrib.auth.models import User
    from django.core.management import call_command
    from django.db import connection, transaction
    from django.db.migrations.executor import MigrationExecutor
    from django.test import RequestFactory
    from django.utils import timezone
    import jwt
    from saleor.graphql.api import schema

    executor = MigrationExecutor(connection)
    assert not executor.migration_plan(executor.loader.graph.leaf_nodes())
    plan = StringIO()
    call_command("migrate", plan=True, stdout=plan, verbosity=1)
    assert "No planned migration operations." in plan.getvalue()
    admin = User.objects.get(username=ADMIN)
    assert admin.is_active and admin.is_staff and admin.is_superuser
    if expect_unusable:
        assert not admin.has_usable_password()
    with connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM product_boardgame")
        assert cursor.fetchone()[0] == 49
        cursor.execute("SELECT count(*), sum(total) FROM purchase_order WHERE status='paid'")
        count, total = cursor.fetchone()
        assert count == 16 and total > 0
        cursor.execute(
            "SELECT count(*) FROM purchase_order o WHERE o.total <> "
            "(SELECT sum(subtotal) FROM purchase_order_line l WHERE l.order_id=o.id)"
        )
        assert cursor.fetchone()[0] == 0
        cursor.execute("SELECT count(*) FROM purchase_order_line WHERE subtotal<>unit_price*quantity")
        assert cursor.fetchone()[0] == 0
        for table in ("chat_conversation", "chat_message", "credit_account", "credit_payment",
                      "credit_transaction", "stock_movement_details", "coupon_checkout_reservation"):
            cursor.execute("SELECT to_regclass(%s)", [table])
            assert cursor.fetchone()[0] is not None

    token = jwt.encode({"sub": str(admin.pk), "token_type": "access",
                        "exp": timezone.now() + timedelta(minutes=2)},
                       settings.SECRET_KEY, algorithm="HS256")
    request = RequestFactory().post("/graphql/", HTTP_AUTHORIZATION="Bearer " + token)
    metrics = """query($from:String,$to:String) { adminSalesMetrics(from:$from,to:$to) {
      revenueTotal ordersCount revenueByDay { date revenue }
      topProducts { bggId units revenue } } }"""
    result = schema.execute(metrics, context_value=request)
    assert not result.errors
    sales = result.data["adminSalesMetrics"]
    assert sales["ordersCount"] == count
    assert Decimal(str(sales["revenueTotal"])) == total
    assert sum(Decimal(str(day["revenue"])) for day in sales["revenueByDay"]) == total
    result = schema.execute(metrics, context_value=request, variable_values={
        "from": (timezone.now() - timedelta(days=7)).isoformat(),
        "to": timezone.now().isoformat(),
    })
    assert not result.errors and result.data["adminSalesMetrics"]["ordersCount"] == 7

    def chat(query, variables=None, context=request):
        result = schema.execute(query, variable_values=variables, context_value=context)
        assert not result.errors
        return next(iter(result.data.values()))

    # All verification chat writes roll back, leaving no synthetic conversation behind.
    with transaction.atomic():
        created = chat("mutation { createChatConversation { conversation { id } userErrors { code } } }")
        assert not created["userErrors"]
        conversation = created["conversation"]["id"]
        recorded = chat("""mutation($id:ID!) { recordChatExchange(conversationId:$id,
          userMessage:"What games are available?",assistantMessage:"Browse the catalog.") {
          conversation { messages { role content } } userErrors { code } } }""", {"id": conversation})
        assert not recorded["userErrors"] and len(recorded["conversation"]["messages"]) == 2
        query = """query($id:ID!) { chatConversation(id:$id) {
          conversation { messages { role content } } userErrors { code } } }"""
        assert len(chat(query, {"id": conversation})["conversation"]["messages"]) == 2
        now = int(time.time())
        assertion = jwt.encode({
            "sub": "a" * 64, "iss": "bgg-shop-bff", "aud": "bgg-shop-core",
            "scope": "chat:conversations", "iat": now, "exp": now + 60,
        }, settings.CHAT_ASSERTION_SECRET, algorithm="HS256", headers={"typ": "chat-assertion"})
        other = RequestFactory().post("/graphql/", HTTP_X_CHAT_ASSERTION=assertion)
        denied = chat(query, {"id": conversation}, context=other)
        assert denied["conversation"] is None and denied["userErrors"]
        deleted = chat("""mutation($id:ID!) { deleteChatConversation(conversationId:$id) {
          success userErrors { code } } }""", {"id": conversation})
        assert deleted["success"] and not deleted["userErrors"]
        assert chat(query, {"id": conversation})["conversation"] is None
        transaction.set_rollback(True)
    drift = StringIO()
    try:
        call_command("makemigrations", check=True, dry_run=True, stdout=drift, verbosity=1)
        drift_status = "none"
    except SystemExit:
        drift_status = "existing model/migration drift detected (no files written)"
    print(f"Verified: 49 products, {count} paid orders, ARS {total}; 7/30-day sales, chat ownership/delete,"
          f" credit schema, real migrations complete. Model drift: {drift_status}.")


def worker(action):
    configure_worker()
    from django.core.management import call_command
    from django.db import connection, transaction
    if action == "bootstrap":
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")
            if cursor.fetchone()[0]:
                raise RuntimeError("Bootstrap refuses nonempty database")
        call_command("migrate", "auth", interactive=False, verbosity=0)
        call_command("migrate", "promotions", "0001", interactive=False, verbosity=0)
        baseline = Path("/baseline.sql").read_text()
        catalog = sys.stdin.read()
        # Validate again inside the isolated worker before executing any catalog SQL.
        catalog_insert(catalog + "\n\n-- Development catalog seed inventory;")
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(baseline)
            cursor.execute(catalog)
        call_command("migrate", interactive=False, verbosity=0)
        seed()
        verify_worker(expect_unusable=True)
    elif action == "verify":
        verify_worker()
    elif action == "admin-password":
        call_command("changepassword", ADMIN)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=[
        "create", "resume-empty", "status", "access", "verify", "admin-password",
        "switch-application", "_worker",
    ])
    parser.add_argument("worker_action", nargs="?", choices=["bootstrap", "verify", "admin-password"])
    parser.add_argument("--port", type=int, default=55432)
    args = parser.parse_args()
    if not 55432 <= args.port <= 55499:
        parser.error("--port must be between 55432 and 55499")
    if args.command == "_worker":
        if Path("/connection.env").is_file() and args.worker_action:
            worker(args.worker_action)
            return
        parser.error("Internal worker requires its isolated container mounts")
    if args.worker_action:
        parser.error("Worker action is internal only")
    if args.command == "create":
        create(args.port)
    elif args.command == "resume-empty":
        resume_empty()
    elif args.command == "switch-application":
        switch_application()
        return
    values = read_private_config()
    require_owned_runtime(values)
    if args.command in {"verify", "admin-password"}:
        if values["INIT_STATUS"] != "READY":
            raise RuntimeError("Initialization is incomplete; database preserved, no automatic recovery")
        if args.command == "admin-password" and not sys.stdin.isatty():
            raise RuntimeError("admin-password requires an interactive local terminal")
        output = core_runner(args.command)
        if output:
            print(output.strip())
    print(f"State: {values['INIT_STATUS']}; {CONTAINER}; persistent volume {VOLUME}")
    print(f"Local access: 127.0.0.1:{values['LOCAL_PORT']}; database/user: {DATABASE}")
    print("Private settings: .local/parallel-db/connection.env (never print or commit)")
    print("Set the unusable admin password: python3 scripts/create_parallel_database.py admin-password")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Parallel database operation failed ({type(error).__name__}). "
              "No live-stack changes; inspect initialization state with status.", file=sys.stderr)
        sys.exit(1)
