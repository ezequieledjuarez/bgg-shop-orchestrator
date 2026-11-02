import json as json_module
import os
from datetime import timedelta
from pathlib import Path
import sys
import uuid
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import django
import yaml
from django.test import RequestFactory, override_settings
from django.utils import timezone
from django.db import connections
from flask import Flask
from graphql import build_schema, get_variable_values, parse, validate

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bgg-shop-core"))
sys.path.insert(0, str(ROOT / "bgg-shop-bff"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
django.setup()

from opkeys import views
from django.contrib.auth.models import AnonymousUser, User
from opkeys.middleware import OpKeyAuthMiddleware
from opkeys.utils import key_hash
from saleor.graphql import api
from saleor.graphql.api import _authenticated_user, schema
from src import opkey_middleware, proxy
from src.auth import admin_required


def test_promotion_and_coupon_documents_match_core_schemas():
    reference = build_schema((ROOT / "bgg-shop-core/specs/schema.graphql").read_text(encoding="utf-8"))
    responses = {
        "ListPromotions": {"promotions": []},
        "AvailableCoupons": {"availableCoupons": []},
        "CreatePromotion": {"createPromotion": {"promotion": {"id": "1", "name": "Sale"}, "userErrors": []}},
        "UpdatePromotion": {"updatePromotion": {"promotion": {"id": "1", "name": "Sale"}, "userErrors": []}},
    }
    seen = []

    def inspect_request(query, variables, token=None, **kwargs):
        document = parse(query)
        operation = document.definitions[0]
        for current_schema in (reference, schema.graphql_schema):
            assert validate(current_schema, document) == []
            assert isinstance(get_variable_values(current_schema, operation.variable_definitions or (), variables), dict)
        name = operation.name.value
        seen.append(name)
        return {"data": responses[name]}

    with patch.object(proxy, "_graphql_request", side_effect=inspect_request):
        assert proxy.list_promotions() == []
        assert proxy.list_available_coupons() == []
        assert proxy.create_promotion({"name": "Sale", "discount_percent": 20, "active": True})["id"] == "1"
        assert proxy.update_promotion("1", {"discount_percent": 20, "active": False})["id"] == "1"
    assert seen == ["ListPromotions", "AvailableCoupons", "CreatePromotion", "UpdatePromotion"]


def test_admin_product_detail_integrates_with_core_schema():
    from app import app as bff_app

    cursor = MagicMock()
    columns = ("bgg_id", "name", "release_year", "min_players", "max_players", "playing_time_minutes", "min_age", "weight", "category", "price_amount", "publisher", "image_url", "quantity")
    cursor.description = [(column,) for column in columns]
    cursor.fetchone.return_value = (13, "Catan", 1995, 3, 4, 90, 10, 2.3, "Strategy", 49.99, "Kosmos", "/catan.jpg", 8)
    cursor.fetchall.return_value = []
    database = MagicMock()
    database.cursor.return_value.__enter__.return_value = cursor

    def call_core(query, variables, token=None, **kwargs):
        result = schema.execute(query, variable_values=variables)
        assert result.errors is None
        return {"data": result.data}

    with patch.object(api, "connection", database), patch.object(proxy, "check_admin", return_value=True), \
            patch.object(proxy, "_graphql_request", side_effect=call_core):
        response = bff_app.test_client().get("/api/v1/admin/products/13", headers={"Authorization": "Bearer token"})
    assert response.status_code == 200
    assert response.get_json()["bgg_id"] == 13
    assert response.get_json()["quantity"] == 8
    assert response.get_json()["price"] == 49.99


def test_compose_limits_core_host_port_to_loopback():
    with (ROOT / "podman-compose.yaml").open(encoding="utf-8") as config:
        services = yaml.safe_load(config)["services"]
    assert services["api"]["ports"] == ["127.0.0.1:8000:8000"]
    assert services["bff"]["environment"]["SALEOR_BASE_URL"] == "http://api:8000"
    assert services["api"]["environment"]["OPKEYS_ISSUE_ON_LOGIN"] == '${OPKEYS_ISSUE_ON_LOGIN:-false}'
    assert services["frontend"]["environment"]["VITE_USE_OPKEY"] == '${VITE_USE_OPKEY:-false}'


def test_compose_has_opt_in_audit_retention_worker():
    with (ROOT / "podman-compose.yaml").open(encoding="utf-8") as config:
        service = yaml.safe_load(config)["services"]["opkey-audit-retention"]
    assert service["profiles"] == ["opkey-audit"]
    assert service["command"] == "python manage.py run_opkey_audit_retention"
    assert "ports" not in service


@override_settings(OPKEY_INTERNAL_SECRET="synthetic-internal-secret-0123456789-abcdef")
def test_bff_and_core_enforce_operation_permissions_without_network(monkeypatch):
    monkeypatch.setenv("OPKEY_INTERNAL_SECRET", "synthetic-internal-secret-0123456789-abcdef")
    app = Flask(__name__)
    opkey_middleware.init_app(app)

    @app.route("/api/v1/admin/allowed", methods=["GET", "POST"])
    @app.route("/api/v1/admin/other", methods=["GET"])
    @admin_required
    def protected():
        return "ok"

    session = SimpleNamespace(
        id="synthetic-session", user_id=1, ops=["GET:/api/v1/admin/allowed"], expires_at=timezone.now(),
        user=SimpleNamespace(is_active=True, is_staff=True, is_superuser=False),
        revoked=False, touch=lambda: None, save=lambda **kwargs: None,
    )
    session.is_valid = lambda: not session.revoked

    def call_core(url, json, headers, timeout, allow_redirects):
        assert allow_redirects is False
        request = RequestFactory().post(
            "/internal/op-validate", data=json_module.dumps(json),
            content_type="application/json", HTTP_X_INTERNAL_SECRET=headers["X-Internal-Secret"],
        )
        response = views.op_validate(request)
        return SimpleNamespace(status_code=response.status_code, json=lambda: json_module.loads(response.content))

    with patch.object(views.OpSession.objects, "get", return_value=session), patch.object(
        views.OpSession.objects, "filter"
    ) as filter_sessions, patch.object(opkey_middleware.requests, "post", side_effect=call_core) as post, patch(
        "opkeys.views.transaction.atomic", return_value=nullcontext()
    ), patch.object(views.OpKeyAudit.objects, "create"):
        filter_sessions.return_value.select_for_update.return_value = [session]
        client = app.test_client()
        headers = {"X-Op-Key": "synthetic-operation-key"}
        assert client.get("/api/v1/admin/allowed", headers=headers).status_code == 200
        assert client.get("/api/v1/admin/allowed", headers=headers).status_code == 200
        assert client.get("/api/v1/admin/other", headers=headers).status_code == 401
        assert client.post("/api/v1/admin/allowed", headers=headers).status_code == 401
        revoke_request = RequestFactory().post(
            "/internal/op-revoke", data=json_module.dumps({"session_id": session.id}),
            content_type="application/json", HTTP_X_INTERNAL_SECRET="synthetic-internal-secret-0123456789-abcdef",
        )
        assert views.op_revoke(revoke_request).status_code == 200
        assert client.get("/api/v1/admin/allowed", headers=headers).status_code == 401
        assert post.call_count == 5


@override_settings(OPKEY_INTERNAL_SECRET="synthetic-internal-secret-0123456789-abcdef")
def test_bff_delegates_authenticated_administrator_to_core(monkeypatch):
    monkeypatch.setenv("OPKEY_INTERNAL_SECRET", "synthetic-internal-secret-0123456789-abcdef")
    app = Flask(__name__)
    opkey_middleware.init_app(app)
    user = SimpleNamespace(pk=123, is_active=True, is_staff=True, is_superuser=False)
    session = SimpleNamespace(
        id="synthetic-session", user_id=123, user=user, ops=["POST:/api/v1/admin/products"],
        expires_at=timezone.now(), is_valid=lambda: True, touch=lambda: None,
    )

    @app.post("/api/v1/admin/products")
    @admin_required
    def admin_product():
        return proxy._graphql_request("mutation Test { test }", {})

    def call_core(url, json, headers, timeout, allow_redirects):
        assert allow_redirects is False
        if url.endswith("/internal/op-validate"):
            request = RequestFactory().post(
                "/internal/op-validate", data=json_module.dumps(json), content_type="application/json",
                HTTP_X_INTERNAL_SECRET=headers["X-Internal-Secret"],
            )
            response = views.op_validate(request)
            return SimpleNamespace(status_code=response.status_code, json=lambda: json_module.loads(response.content))
        request = RequestFactory().post(
            "/graphql/", data=json_module.dumps(json), content_type="application/json",
            HTTP_X_OP_KEY=headers["X-Op-Key"], HTTP_X_INTERNAL_SECRET=headers["X-Internal-Secret"],
            HTTP_X_OP_METHOD=headers["X-Op-Method"], HTTP_X_OP_PATH=headers["X-Op-Path"],
        )
        request.user = AnonymousUser()
        OpKeyAuthMiddleware(lambda value: None).process_request(request)
        actor = _authenticated_user(SimpleNamespace(context=request))
        return SimpleNamespace(status_code=200, raise_for_status=lambda: None,
                               json=lambda: {"data": {"actor": actor.pk if actor else None}})

    with patch.object(views.OpSession.objects, "get", return_value=session), patch.object(
        views.OpSession.objects, "filter"
    ) as sessions, patch("opkeys.middleware.get_user_model") as users, patch.object(
        opkey_middleware.requests, "post", side_effect=call_core
    ):
        sessions.return_value.first.return_value = session
        users.return_value.objects.filter.return_value.first.return_value = user
        response = app.test_client().post("/api/v1/admin/products", headers={"X-Op-Key": "synthetic-op-key"})
    assert response.status_code == 200
    assert response.get_json() == {"data": {"actor": 123}}


@override_settings(OPKEYS_ISSUE_ON_LOGIN=True, OPKEY_INTERNAL_SECRET="synthetic-internal-secret-0123456789-abcdef",
                   SECRET_KEY="synthetic-signing-key-0123456789-abcdefghijklmnopqrstuvwxyz")
def test_login_operation_and_logout_with_isolated_database(monkeypatch):
    from app import app as bff_app

    monkeypatch.setenv("OPKEY_INTERNAL_SECRET", "synthetic-internal-secret-0123456789-abcdef")
    alias = f"isolated_opkey_flow_{uuid.uuid4().hex}"
    connections.databases[alias] = {
        **connections.databases["default"], "ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:", "OPTIONS": {},
    }
    database = connections[alias]
    try:
        with database.schema_editor() as editor:
            editor.create_model(User)
            editor.create_model(views.OpSession)
            editor.create_model(views.OpKeyAudit)
        user = User.objects.db_manager(alias).create_user(
            username="synthetic-admin", email="admin@example.test", password="synthetic-password", is_staff=True,
        )
        manager = views.OpSession.objects.db_manager(alias)
        audits = views.OpKeyAudit.objects.db_manager(alias)
        user_manager = User.objects.db_manager(alias)

        def reply(status, payload):
            return SimpleNamespace(status_code=status, json=lambda: payload, raise_for_status=lambda: None)

        def call_core(url, json, headers=None, timeout=None, allow_redirects=None):
            headers = headers or {}
            if url.endswith("/internal/op-validate") or url.endswith("/internal/op-revoke"):
                request = RequestFactory().post(
                    "/internal/test", data=json_module.dumps(json), content_type="application/json",
                    HTTP_X_INTERNAL_SECRET=headers.get("X-Internal-Secret", ""),
                )
                response = views.op_validate(request) if url.endswith("op-validate") else views.op_revoke(request)
                return reply(response.status_code, json_module.loads(response.content))
            request = RequestFactory().post(
                "/graphql/", data=json_module.dumps(json), content_type="application/json",
                HTTP_X_OP_KEY=headers.get("X-Op-Key", ""), HTTP_X_INTERNAL_SECRET=headers.get("X-Internal-Secret", ""),
                HTTP_X_OP_METHOD=headers.get("X-Op-Method", ""), HTTP_X_OP_PATH=headers.get("X-Op-Path", ""),
            )
            request.user = AnonymousUser()
            OpKeyAuthMiddleware(lambda value: None).process_request(request)
            if "IssueGiftCard" in json["query"]:
                actor = _authenticated_user(SimpleNamespace(context=request))
                if not actor or actor.pk != user.pk:
                    return reply(200, {"data": {"createGiftCard": {"giftCard": None,
                        "userErrors": [{"code": "UNAUTHENTICATED", "message": "Denied"}]}}})
                card = {"id": str(uuid.uuid4()), "code": "a" * 64, "amount": "1.00", "currency": "ARS"}
                return reply(200, {"data": {"createGiftCard": {"giftCard": card, "userErrors": []}}})
            result = schema.execute(json["query"], variable_values=json.get("variables"), context_value=request)
            return reply(200, {"data": result.data, "errors": [str(error) for error in result.errors or []]})

        with patch.object(views.OpSession, "objects", manager), patch.object(views.OpKeyAudit, "objects", audits), patch(
            "django.contrib.auth.authenticate", return_value=user
        ), patch("opkeys.middleware.get_user_model", return_value=SimpleNamespace(objects=user_manager)), patch.object(
            opkey_middleware.requests, "post", side_effect=call_core
        ), patch("app._append_incoming_log"):
            client = bff_app.test_client()
            login = client.post("/api/v1/auth/login", json={"email": user.email, "password": "synthetic-password"})
            assert login.status_code == 200
            op_key = login.get_json()["session"]["op_key"]
            headers = {"X-Op-Key": op_key}
            other = manager.create(user=user, key_hash=key_hash("synthetic-other-key"), ops=[],
                                   expires_at=timezone.now() + timedelta(minutes=30))
            listed = client.get("/api/v1/admin/op-sessions", headers=headers)
            assert listed.status_code == 200
            assert len(listed.get_json()["items"]) == 2
            assert op_key not in listed.get_data(as_text=True)
            assert client.post(f"/api/v1/admin/op-sessions/{other.pk}/expire", headers=headers).status_code == 204
            other.refresh_from_db(using=alias)
            assert other.is_expired()
            issued = client.post("/api/v1/admin/gift-cards", json={"amount": "1.00"}, headers=headers)
            assert issued.status_code == 201
            assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
            denied = client.post("/api/v1/admin/gift-cards", json={"amount": "1.00"}, headers=headers)
            assert denied.status_code == 401
            assert manager.get(key_hash=key_hash(op_key)).revoked is True
    finally:
        database.close()
        del connections.databases[alias]