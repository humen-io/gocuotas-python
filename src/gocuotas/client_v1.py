"""API Client V1 (/api_client/v1/...)."""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Optional
from urllib.parse import quote

import httpx

from gocuotas.errors import GoCuotasApiError

SANDBOX_BASE_URL = "https://sandbox.gocuotas.com"
PRODUCTION_BASE_URL = "https://www.gocuotas.com"
DEFAULT_BASE_URL = SANDBOX_BASE_URL
PATH_CLIENT = "/api_client/v1/client"
PATH_EXPENSE_SETTLEMENTS = "/api_client/v1/expense_settlements"
PATH_EXPENSE_SETTLEMENTS_CSVS = "/api_client/v1/expense_settlements_csvs"

ENV_COMMERCE_API_KEY = "GOCUOTAS_COMMERCE_API_KEY"
ENV_LIQUIDACION_ID = "GOCUOTAS_LIQUIDACION_ID"


def encode_path_segment(s: str) -> str:
    """Match Java URLEncoder + replace '+' with '%20' for path segments."""
    return quote(s, safe="").replace("+", "%20")


def _truncate(s: str, max_len: int = 500) -> str:
    return s if len(s) <= max_len else s[:max_len] + "…"


def _default_commerce_key() -> str:
    k = (os.environ.get(ENV_COMMERCE_API_KEY) or "").strip()
    if not k:
        raise OSError(f"set environment variable {ENV_COMMERCE_API_KEY} (commerce API key)")
    return k


class ClientV1Builder:
    """Sandbox by default; call :meth:`production` for www.gocuotas.com."""

    def __init__(self) -> None:
        self._base_url = SANDBOX_BASE_URL
        self._timeout = 60.0
        self._get_commerce_api_key: Optional[Callable[[], str]] = None

    def production(self) -> ClientV1Builder:
        self._base_url = PRODUCTION_BASE_URL
        return self

    def sandbox(self) -> ClientV1Builder:
        self._base_url = SANDBOX_BASE_URL
        return self

    def base_url(self, url: str) -> ClientV1Builder:
        self._base_url = url.rstrip("/")
        return self

    def timeout(self, seconds: float) -> ClientV1Builder:
        self._timeout = seconds
        return self

    def get_commerce_api_key(self, fn: Callable[[], str]) -> ClientV1Builder:
        self._get_commerce_api_key = fn
        return self

    def build(self) -> ClientV1:
        return ClientV1(
            base_url=self._base_url,
            timeout=self._timeout,
            get_commerce_api_key=self._get_commerce_api_key,
        )


class ClientV1:
    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 60.0,
        get_commerce_api_key: Optional[Callable[[], str]] = None,
        client: Optional[httpx.Client] = None,
    ) -> None:
        self._own_client = client is None
        bu = base_url.rstrip("/")
        self._get_commerce_api_key = get_commerce_api_key or _default_commerce_key
        self._client = client or httpx.Client(base_url=bu, timeout=timeout)

    def close(self) -> None:
        if self._own_client:
            self._client.close()

    def __enter__(self) -> ClientV1:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _commerce_key(self) -> str:
        return self._get_commerce_api_key()

    def _do_get(self, path: str, accept: str, commerce_api_key: str) -> str:
        headers = {"Accept": accept, "Authorization": f"Bearer {commerce_api_key.strip()}"}
        r = self._client.get(path, headers=headers)
        if 200 <= r.status_code < 300:
            return r.text
        raise GoCuotasApiError(
            r.status_code,
            r.text,
            f"GoCuotas API Client V1 error HTTP {r.status_code}: {_truncate(r.text)}",
        )

    def get_commerce(self, commerce_api_key: str) -> dict[str, Any]:
        return json.loads(self._do_get(PATH_CLIENT, "application/json", commerce_api_key))

    def get_commerce_from_env(self) -> dict[str, Any]:
        return self.get_commerce(self._commerce_key())

    def list_settlements(self, commerce_api_key: str) -> list[dict[str, Any]]:
        return json.loads(self._do_get(PATH_EXPENSE_SETTLEMENTS, "application/json", commerce_api_key))

    def list_settlements_from_env(self) -> list[dict[str, Any]]:
        return self.list_settlements(self._commerce_key())

    def get_settlement(self, commerce_api_key: str, settlement_id: str) -> dict[str, Any]:
        path = f"{PATH_EXPENSE_SETTLEMENTS}/{encode_path_segment(settlement_id)}"
        return json.loads(self._do_get(path, "application/json", commerce_api_key))

    def get_settlement_from_env(self, settlement_id: str) -> dict[str, Any]:
        return self.get_settlement(self._commerce_key(), settlement_id)

    def get_settlement_from_env_ids(self) -> dict[str, Any]:
        sid = (os.environ.get(ENV_LIQUIDACION_ID) or "").strip()
        if not sid:
            raise OSError(f"set environment variable {ENV_LIQUIDACION_ID} (settlement id)")
        return self.get_settlement_from_env(sid)

    def list_settlements_plain_text(self, commerce_api_key: str) -> str:
        return self._do_get(PATH_EXPENSE_SETTLEMENTS_CSVS, "text/plain", commerce_api_key)

    def list_settlements_plain_text_from_env(self) -> str:
        return self.list_settlements_plain_text(self._commerce_key())

    def get_settlement_plain_text(self, commerce_api_key: str, settlement_id: str) -> str:
        path = f"{PATH_EXPENSE_SETTLEMENTS_CSVS}/{encode_path_segment(settlement_id)}"
        return self._do_get(path, "text/plain", commerce_api_key)

    def get_settlement_plain_text_from_env(self, settlement_id: str) -> str:
        return self.get_settlement_plain_text(self._commerce_key(), settlement_id)

    def get_settlement_plain_text_from_env_ids(self) -> str:
        sid = (os.environ.get(ENV_LIQUIDACION_ID) or "").strip()
        if not sid:
            raise OSError(f"set environment variable {ENV_LIQUIDACION_ID}")
        return self.get_settlement_plain_text_from_env(sid)
