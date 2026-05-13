"""API Redirect V1 (/api_redirect/v1/...)."""

from __future__ import annotations

import json
import os
import threading
from typing import Any, Callable, Optional
from urllib.parse import urlencode

import httpx

from gocuotas.client_v1 import (
    DEFAULT_BASE_URL,
    PRODUCTION_BASE_URL,
    SANDBOX_BASE_URL,
    encode_path_segment,
)
from gocuotas.errors import GoCuotasApiError, OrderNotFoundError

PATH_AUTHENTICATION = "/api_redirect/v1/authentication"
PATH_CHECKOUTS = "/api_redirect/v1/checkouts"
PATH_ORDERS = "/api_redirect/v1/orders"

ENV_JWT = "GOCUOTAS_JWT"
ENV_EMAIL = "GOCUOTAS_EMAIL"
ENV_API_KEY = "GOCUOTAS_API_KEY"
ENV_DELIVERED_START = "GOCUOTAS_DELIVERED_START"
ENV_DELIVERED_END = "GOCUOTAS_DELIVERED_END"


def _truncate(s: str, max_len: int = 500) -> str:
    return s if len(s) <= max_len else s[:max_len] + "…"


def _default_panel_key() -> str:
    k = (os.environ.get(ENV_API_KEY) or "").strip()
    if not k:
        raise OSError(f"set environment variable {ENV_API_KEY}")
    return k


def parse_auth_token(obj: dict[str, Any]) -> str:
    for k in ("token", "access_token", "accessToken", "jwt"):
        v = obj.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


class RedirectClient:
    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        get_panel_api_key: Optional[Callable[[], str]] = None,
        client: Optional[httpx.Client] = None,
    ) -> None:
        self._own_client = client is None
        bu = base_url.rstrip("/")
        self._get_panel_api_key = get_panel_api_key or _default_panel_key
        self._client = client or httpx.Client(base_url=bu, timeout=timeout)
        self._lock = threading.Lock()
        self._cached_jwt: Optional[str] = None

    def close(self) -> None:
        if self._own_client:
            self._client.close()

    def __enter__(self) -> RedirectClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _panel_key(self) -> str:
        return self._get_panel_api_key()

    def _bearer_for_order_requests(self) -> str:
        j = (os.environ.get(ENV_JWT) or "").strip()
        if j:
            return j
        with self._lock:
            if self._cached_jwt:
                return self._cached_jwt
            email = (os.environ.get(ENV_EMAIL) or "").strip()
            if not email:
                raise OSError(
                    f"for order calls without explicit bearer, set {ENV_JWT} or {ENV_EMAIL} + {ENV_API_KEY}",
                )
            pw = self._panel_key()
            auth = self.authenticate(email, pw)
            token = parse_auth_token(auth)
            if not token:
                raise RuntimeError("gocuotas: authenticate response had no token")
            self._cached_jwt = token
            return token

    def _delivered_from_env(self) -> tuple[str, str]:
        a = (os.environ.get(ENV_DELIVERED_START) or "").strip()
        b = (os.environ.get(ENV_DELIVERED_END) or "").strip()
        if not a or not b:
            raise OSError(
                f"set {ENV_DELIVERED_START} and {ENV_DELIVERED_END} (format YYYY-MM-DD HH:mm)",
            )
        return a, b

    def authenticate(self, email: str, password: str) -> dict[str, Any]:
        r = self._client.post(
            PATH_AUTHENTICATION,
            json={"email": email, "password": password},
            headers={"Accept": "application/json"},
        )
        if 200 <= r.status_code < 300:
            return r.json()
        raise GoCuotasApiError(
            r.status_code,
            r.text,
            f"GoCuotas API error HTTP {r.status_code}: {_truncate(r.text)}",
        )

    def create_checkout(self, bearer_token: str, checkout: dict[str, Any]) -> dict[str, Any]:
        r = self._client.post(
            PATH_CHECKOUTS,
            json=checkout,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {bearer_token.strip()}",
            },
        )
        if 200 <= r.status_code < 300:
            return r.json()
        raise GoCuotasApiError(
            r.status_code,
            r.text,
            f"GoCuotas API error HTTP {r.status_code}: {_truncate(r.text)}",
        )

    def create_checkout_from_env(self, checkout: dict[str, Any]) -> dict[str, Any]:
        return self.create_checkout(self._panel_key(), checkout)

    def list_orders(self, bearer_token: str, delivered_start: str, delivered_end: str) -> str:
        q = urlencode(
            {"delivered_start": delivered_start.strip(), "delivered_end": delivered_end.strip()},
        )
        path = f"{PATH_ORDERS}?{q}"
        r = self._client.get(
            path,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {bearer_token.strip()}",
            },
        )
        if 200 <= r.status_code < 300:
            return r.text
        raise GoCuotasApiError(
            r.status_code,
            r.text,
            f"GoCuotas API error HTTP {r.status_code}: {_truncate(r.text)}",
        )

    def list_orders_from_env_delivered(self, bearer_token: str) -> str:
        a, b = self._delivered_from_env()
        return self.list_orders(bearer_token, a, b)

    def list_orders_auto(self) -> str:
        return self.list_orders_from_env_delivered(self._bearer_for_order_requests())

    def list_orders_json(self, bearer_token: str, delivered_start: str, delivered_end: str) -> Any:
        return json.loads(self.list_orders(bearer_token, delivered_start, delivered_end))

    def get_order(self, bearer_token: str, order_id: str) -> str:
        path = f"{PATH_ORDERS}/{encode_path_segment(order_id)}"
        r = self._client.get(
            path,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {bearer_token.strip()}",
            },
        )
        if 200 <= r.status_code < 300:
            return r.text
        if r.status_code == 404:
            raise OrderNotFoundError(order_id, r.text)
        raise GoCuotasApiError(
            r.status_code,
            r.text,
            f"GoCuotas API error HTTP {r.status_code}: {_truncate(r.text)}",
        )

    def get_order_auto(self, order_id: str) -> str:
        return self.get_order(self._bearer_for_order_requests(), order_id)

    def get_order_json(self, bearer_token: str, order_id: str) -> Any:
        return json.loads(self.get_order(bearer_token, order_id))

    def get_order_json_auto(self, order_id: str) -> Any:
        return json.loads(self.get_order_auto(order_id))

    def refund_order(self, bearer_token: str, order_id: str) -> str:
        path = f"{PATH_ORDERS}/{encode_path_segment(order_id)}"
        r = self._client.request(
            "DELETE",
            path,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {bearer_token.strip()}",
            },
        )
        if 200 <= r.status_code < 300:
            return r.text
        if r.status_code == 404:
            raise OrderNotFoundError(order_id, r.text)
        raise GoCuotasApiError(
            r.status_code,
            r.text,
            f"GoCuotas API error HTTP {r.status_code}: {_truncate(r.text)}",
        )

    def refund_order_auto(self, order_id: str) -> str:
        return self.refund_order(self._bearer_for_order_requests(), order_id)

    def refund_order_json(self, bearer_token: str, order_id: str) -> Any:
        return json.loads(self.refund_order(bearer_token, order_id))

    def refund_order_json_auto(self, order_id: str) -> Any:
        return json.loads(self.refund_order_auto(order_id))


class RedirectClientBuilder:
    """Sandbox by default; :meth:`production` for www.gocuotas.com."""

    def __init__(self) -> None:
        self._base_url = SANDBOX_BASE_URL
        self._timeout = 30.0
        self._get_panel_api_key: Optional[Callable[[], str]] = None

    def production(self) -> RedirectClientBuilder:
        self._base_url = PRODUCTION_BASE_URL
        return self

    def sandbox(self) -> RedirectClientBuilder:
        self._base_url = SANDBOX_BASE_URL
        return self

    def base_url(self, url: str) -> RedirectClientBuilder:
        self._base_url = url.rstrip("/")
        return self

    def timeout(self, seconds: float) -> RedirectClientBuilder:
        self._timeout = seconds
        return self

    def get_panel_api_key(self, fn: Callable[[], str]) -> RedirectClientBuilder:
        self._get_panel_api_key = fn
        return self

    def build(self) -> RedirectClient:
        return RedirectClient(
            base_url=self._base_url,
            timeout=self._timeout,
            get_panel_api_key=self._get_panel_api_key,
        )
