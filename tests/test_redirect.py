import json

import httpx
import pytest

from gocuotas.errors import GoCuotasApiError, OrderNotFoundError
from gocuotas.redirect import RedirectClient, parse_auth_token


def test_parse_auth_token():
    assert parse_auth_token({"token": "a"}) == "a"
    assert parse_auth_token({"access_token": "b"}) == "b"


def test_get_order_encodes_path():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "%2F" in str(request.url)
        return httpx.Response(200, json={"ok": 1})

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport, base_url="http://test") as hc:
        c = RedirectClient(client=hc, get_panel_api_key=lambda: "x")
        body = c.get_order("tok", "a/b")
    assert json.loads(body)["ok"] == 1


def test_get_order_404():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "not found"})

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport, base_url="http://test") as hc:
        c = RedirectClient(client=hc, get_panel_api_key=lambda: "x")
        with pytest.raises(OrderNotFoundError) as ei:
            c.get_order("tok", "absent-99")
        assert ei.value.order_id == "absent-99"


def test_list_orders_404_not_order_not_found():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport, base_url="http://test") as hc:
        c = RedirectClient(client=hc, get_panel_api_key=lambda: "x")
        with pytest.raises(GoCuotasApiError) as ei:
            c.list_orders("tok", "2020-01-01 00:00", "2020-02-01 00:00")
        assert not isinstance(ei.value, OrderNotFoundError)


def test_authenticate_no_authorization_header():
    def handler(request: httpx.Request) -> httpx.Response:
        auth = request.headers.get("authorization")
        assert auth is None
        return httpx.Response(200, json={"token": "jwt-from-server"})

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport, base_url="http://test") as hc:
        c = RedirectClient(client=hc, get_panel_api_key=lambda: "x")
        ar = c.authenticate("e@e", "pw")
    assert parse_auth_token(ar) == "jwt-from-server"


def test_refund_order_json_auto_uses_jwt(monkeypatch):
    monkeypatch.setenv("GOCUOTAS_JWT", "jwt-x")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "DELETE" and "/orders/r1" in str(request.url):
            assert request.headers.get("authorization") == "Bearer jwt-x"
            return httpx.Response(200, json=[{"id": 1}])
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport, base_url="http://test") as hc:
        c = RedirectClient(client=hc, get_panel_api_key=lambda: "panel")
        data = c.refund_order_json_auto("r1")
    assert data == [{"id": 1}]
