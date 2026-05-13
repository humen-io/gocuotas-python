import httpx
import pytest

from gocuotas.client_v1 import ClientV1
from gocuotas.errors import GoCuotasApiError


def test_encode_path_segment():
    from gocuotas.client_v1 import encode_path_segment

    assert encode_path_segment("a/b") == "a%2Fb"


def test_get_commerce():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer api-key-x"
        assert request.headers["accept"] == "application/json"
        assert str(request.url).endswith("/api_client/v1/client")
        body = {
            "id": 1000001,
            "name": "Comercio de ejemplo S.R.L.",
            "cuit": "20987654321",
            "surcharge_percentage_to_online_orders": "0.0",
            "max_number_of_installments": 3,
        }
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport, base_url="http://test") as hc:
        c = ClientV1(client=hc, get_commerce_api_key=lambda: "unused")
        info = c.get_commerce("api-key-x")
    assert info["id"] == 1000001
    assert info["name"] == "Comercio de ejemplo S.R.L."


def test_go_cuotas_api_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="{}")

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport, base_url="http://test") as hc:
        c = ClientV1(client=hc, get_commerce_api_key=lambda: "k")
        with pytest.raises(GoCuotasApiError) as ei:
            c.get_commerce("k")
        assert ei.value.status_code == 401


def test_list_settlements_plain_text_accept():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["accept"] == "text/plain"
        return httpx.Response(200, text="ID\n9001001\n")

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport, base_url="http://test") as hc:
        c = ClientV1(client=hc, get_commerce_api_key=lambda: "k")
        body = c.list_settlements_plain_text("k")
    assert "9001001" in body
