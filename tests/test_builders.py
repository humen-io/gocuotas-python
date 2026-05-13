from gocuotas import (
    ClientV1Builder,
    PRODUCTION_BASE_URL,
    SANDBOX_BASE_URL,
    RedirectClientBuilder,
)


def test_client_v1_builder_default_sandbox():
    c = ClientV1Builder().get_commerce_api_key(lambda: "x").build()
    assert c._client.base_url.host == "sandbox.gocuotas.com"


def test_client_v1_builder_production():
    c = ClientV1Builder().production().get_commerce_api_key(lambda: "x").build()
    assert c._client.base_url.host == "www.gocuotas.com"


def test_redirect_builder_default_sandbox():
    c = RedirectClientBuilder().get_panel_api_key(lambda: "x").build()
    assert c._client.base_url.host == "sandbox.gocuotas.com"


def test_redirect_builder_production():
    c = RedirectClientBuilder().production().get_panel_api_key(lambda: "x").build()
    assert c._client.base_url.host == "www.gocuotas.com"


def test_constants():
    assert "sandbox" in SANDBOX_BASE_URL
    assert "www" in PRODUCTION_BASE_URL
