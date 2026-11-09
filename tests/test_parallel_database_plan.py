import importlib.util
import re
from pathlib import Path
from unittest.mock import Mock

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_script():
    spec = importlib.util.spec_from_file_location(
        "parallel_database", ROOT / "scripts/create_parallel_database.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_catalog_extracts_only_reviewed_49_products():
    module = load_script()
    sql = module.catalog_insert((ROOT / "import_catalog.sql").read_text())
    assert sql.startswith("INSERT INTO product_boardgame (")
    assert sql.count("/media/portadas/") == 49
    assert "auth_user" not in sql
    assert "gift_card" not in sql
    assert "DELETE " not in sql


def test_catalog_media_uses_canonical_ids_without_inventing_missing_images():
    sql = load_script().catalog_insert((ROOT / "import_catalog.sql").read_text())
    rows = re.findall(
        r"\(\s*(\d+),[^\n]*?'/media/portadas/(\d+)\.webp', '(\d+)\.webp'\)",
        sql,
    )
    assert len(rows) == 49
    catalog_ids = {bgg_id for bgg_id, _, _ in rows}
    assert len(catalog_ids) == 49
    assert all(bgg_id == image_url_id == filename_id for bgg_id, image_url_id, filename_id in rows)

    assets = list((ROOT / "bgg-shop-frontend/public/media/portadas").glob("*.webp"))
    assert len(assets) == 49
    assert all(re.fullmatch(r"[1-9]\d*", asset.stem) for asset in assets)
    asset_ids = {asset.stem for asset in assets}
    assert asset_ids == set(
        """142379 184267 216600 230244 232414 241451 242684 246900 248065
        251247 256730 256960 257283 262712 265188 265402 266192 266810
        266830 269144 269207 269511 270633 270844 270970 271324 272409
        272453 272739 274364 274637 276025 279254 281259 283355 283948
        284083 284378 286096 291457 291508 295486 296151 296912 297030
        306735 312484 314040 316554""".split()
    )
    assert len(catalog_ids & asset_ids) == 16
    assert len(catalog_ids - asset_ids) == 33


@pytest.mark.parametrize("extra", ["; DELETE FROM auth_user", "-- unsafe", "/* unsafe */"])
def test_catalog_rejects_changed_statement(extra):
    source = (ROOT / "import_catalog.sql").read_text()
    source = source.replace(") VALUES\n", ") VALUES\n" + extra, 1)
    with pytest.raises(ValueError):
        load_script().catalog_insert(source)


@pytest.mark.parametrize(
    "container,volume,config",
    [(True, False, False), (False, True, False), (False, False, True),
     (True, True, True)],
)
def test_create_refuses_any_prior_state(container, volume, config):
    with pytest.raises(RuntimeError, match="existing"):
        load_script().guard_new_state(container, volume, config)


def test_empty_state_is_allowed():
    load_script().guard_new_state(False, False, False)


def test_baseline_is_legacy_and_does_not_duplicate_django_tables():
    sql = (ROOT / "scripts/sql/parallel_baseline.sql").read_text()
    assert "'APPROVED', 'HIDDEN', 'DELETED'" in sql
    assert "idx_product_review_approved_game" in sql
    assert "is_deleted" not in sql
    for table in (
        "auth_user", "promotion", "coupon", "coupon_counter", "audit_log",
        "stock_reservation", "credit_account", "credit_transaction",
        "stock_movement_status", "opkeys_opsession", "chat_conversation",
    ):
        assert f"CREATE TABLE {table} (" not in sql


def test_private_settings_reject_symlink_and_insecure_permissions():
    module = load_script()
    target = Mock()
    target.is_symlink.return_value = False
    target.stat.return_value.st_mode = 0o100644
    with pytest.raises(RuntimeError):
        module.read_private_config(target)
    target.is_symlink.return_value = True
    with pytest.raises(RuntimeError):
        module.read_private_config(target)


def test_application_environment_separates_database_credentials_and_rotated_auth_key():
    module = load_script()
    values = {
        "POSTGRES_USER": "bgg_shop_parallel",
        "POSTGRES_DB": "bgg_shop_parallel",
        "POSTGRES_PASSWORD": "safe-test-password_1234567890123456789012345",
    }

    files = module.render_application_envs(
        values, "safe-test-rotated-key-1234567890123456789012345678901234567890"
    )

    assert set(files) == {"database.env", "auth.env"}
    assert files["database.env"] == (
        "DATABASE_URL=postgresql://bgg_shop_parallel:"
        "safe-test-password_1234567890123456789012345"
        "@bgg_shop_parallel_db:5432/bgg_shop_parallel\n"
    )
    assert files["auth.env"] == (
        "SECRET_KEY=safe-test-rotated-key-1234567890123456789012345678901234567890\n"
        "SECRET_KEY_FALLBACKS=[]\n"
    )
    assert values["POSTGRES_PASSWORD"] not in files["auth.env"]
    assert "SECRET_KEY" not in files["database.env"]


def test_private_environment_writer_uses_exclusive_nofollow_mode_0600(monkeypatch):
    import os

    module = load_script()
    read_fd, write_fd = os.pipe()
    opened = {}

    def fake_open(path, flags, mode):
        opened.update(path=path, flags=flags, mode=mode)
        return write_fd

    original_exists = module.Path.exists
    monkeypatch.setattr(
        module.Path,
        "exists",
        lambda path: False if path == module.AUTH_ENV else original_exists(path),
    )
    monkeypatch.setattr(module.os, "open", fake_open)
    monkeypatch.setattr(module.os, "fsync", lambda fd: None)
    try:
        module.write_private_env(ROOT / ".local/parallel-db/auth.env", "private=test\n")
        content = os.read(read_fd, 100)
    finally:
        os.close(read_fd)

    assert content == b"private=test\n"
    assert opened["mode"] == 0o600
    assert opened["flags"] & os.O_CREAT
    assert opened["flags"] & os.O_EXCL
    assert opened["flags"] & os.O_NOFOLLOW
    assert not opened["flags"] & os.O_TRUNC


def test_switch_application_refuses_incomplete_database_before_writing(monkeypatch):
    module = load_script()
    writes = Mock()
    monkeypatch.setattr(module, "read_private_config", lambda: {
        "POSTGRES_USER": "bgg_shop_parallel",
        "POSTGRES_DB": "bgg_shop_parallel",
        "POSTGRES_PASSWORD": "safe-test-password_123",
        "INIT_STATUS": "FAILED",
    })
    monkeypatch.setattr(module, "require_owned_runtime", Mock())
    monkeypatch.setattr(module, "write_private_env", writes)

    with pytest.raises(RuntimeError, match="READY"):
        module.switch_application()

    writes.assert_not_called()


def test_plan_uses_real_dependency_order_and_no_fake():
    source = (ROOT / "scripts/create_parallel_database.py").read_text()
    assert source.index('"auth", interactive=False') < source.index('"promotions", "0001"')
    assert source.index('"promotions", "0001"') < source.index('cursor.execute(baseline)')
    assert source.index('cursor.execute(baseline)') < source.index('call_command("migrate", interactive=False')
    assert "--fake" not in source
    assert "MigrationRecorder" not in source
    assert "--pull=never" in source
    assert "127.0.0.1:" in source
    assert "--internal" in source
    assert 'CORE_IMAGE, "/source/scripts/create_parallel_database.py"' in source


def test_empty_recovery_refuses_ready_or_nonempty_state():
    from unittest.mock import patch
    module = load_script()
    with patch.object(module, "read_private_config", return_value={"INIT_STATUS": "READY"}), \
            patch.object(module, "require_owned_runtime"):
        with pytest.raises(RuntimeError, match="failed, empty"):
            module.resume_empty()
    with patch.object(module, "read_private_config", return_value={"INIT_STATUS": "FAILED"}), \
            patch.object(module, "require_owned_runtime"), \
            patch.object(module, "run", return_value="1"):
        with pytest.raises(RuntimeError, match="Nonempty"):
            module.resume_empty()


def test_subprocess_failures_do_not_echo_secret_output():
    from subprocess import CompletedProcess
    from unittest.mock import patch
    module = load_script()
    result = CompletedProcess(["podman", "run"], 1, "private-value", "private-value")
    with patch.object(module.subprocess, "run", return_value=result):
        with pytest.raises(RuntimeError) as error:
            module.run(["podman", "run"])
    assert "private-value" not in str(error.value)
