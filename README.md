# GoCuotas — cliente Python (`python/`)

Paquete **`gocuotas`** con **httpx**: **API Client V1** y **API Redirect V1**, alineado con [Java (`java/`)](../java/README.md) y [Go (`go/`)](../go/README.md).

Otros SDKs: [Node.js (`nodejs/`)](../nodejs/README.md).

## Requisitos

- Python **3.10+** (`requires-python` en `pyproject.toml`)
- Dependencia: `httpx`

## Sandbox y producción

Por defecto, `ClientV1()` y `RedirectClient()` usan **sandbox** (`https://sandbox.gocuotas.com`). Para **producción**:

```python
from gocuotas import ClientV1Builder, RedirectClientBuilder

client = ClientV1Builder().production().build()
redirect = RedirectClientBuilder().production().build()
```

Los builders también ofrecen `sandbox()`, `base_url(url)`, `timeout(seconds)` y proveedores de clave (`get_commerce_api_key`, `get_panel_api_key`). Constantes: `SANDBOX_BASE_URL`, `PRODUCTION_BASE_URL`, `DEFAULT_BASE_URL` (sandbox).

## Instalación y tests

```bash
cd python
python -m venv .venv && . .venv/bin/activate
pip install -U pip && pip install -e ".[dev]"
pytest
```

Uso del paquete en modo editable desde el monorepo: `pip install -e .` con `PYTHONPATH` resuelto por el entorno o ejecutando tests con la config de pytest (`pythonpath = ["src"]`).

## Módulos

| Área | Descripción |
|------|-------------|
| `gocuotas.client_v1` | `ClientV1`, `ClientV1Builder`, rutas Client V1, `encode_path_segment`. |
| `gocuotas.redirect` | `RedirectClient`, `RedirectClientBuilder`, `parse_auth_token`. |
| `gocuotas.errors` | `GoCuotasApiError`, `OrderNotFoundError`. |

`ClientV1` y `RedirectClient` aceptan un `httpx.Client` inyectado (`client=`) para tests; si no, crean uno con `base_url` y `timeout`, y pueden usarse como context manager (`with ClientV1() as c:`) para cerrar el cliente.

## Equivalencia Java → Python

### Client V1

| Java (`GoCuotasClientV1`) | Python (`ClientV1`) |
|---------------------------|----------------------|
| `obtenerInformacionComercio(key)` | `get_commerce(commerce_api_key)` |
| `obtenerInformacionComercio()` | `get_commerce_from_env()` |
| `listarLiquidaciones(key)` | `list_settlements(commerce_api_key)` |
| `listarLiquidaciones()` | `list_settlements_from_env()` |
| `obtenerInformacionLiquidacion(key, id)` | `get_settlement(commerce_api_key, settlement_id)` |
| `obtenerInformacionLiquidacion()` | `get_settlement_from_env_ids()` |
| CSV resumen / por id | `list_settlements_plain_text`, `get_settlement_plain_text`, variantes `*_from_env` |

### Redirect V1

| Java (`GoCuotasRedirectClient`) | Python (`RedirectClient`) |
|--------------------------------|---------------------------|
| `authenticate` | `authenticate` |
| `createCheckout` | `create_checkout`, `create_checkout_from_env` |
| `listOrders` (string) | `list_orders`, `list_orders_from_env_delivered`, `list_orders_auto` |
| JSON listado | `list_orders_json` |
| Detalle orden | `get_order`, `get_order_json`, `get_order_auto`, `get_order_json_auto` |
| Reembolso | `refund_order`, `refund_order_json`, `refund_order_auto`, `refund_order_json_auto` |

`parse_auth_token` reconoce `token`, `access_token`, `accessToken`, `jwt` en el dict devuelto por `authenticate`.

## Variables de entorno

Igual que en [README Java](../java/README.md): `GOCUOTAS_COMMERCE_API_KEY`, `GOCUOTAS_LIQUIDACION_ID`, `GOCUOTAS_API_KEY`, `GOCUOTAS_EMAIL`, `GOCUOTAS_JWT`, `GOCUOTAS_DELIVERED_START`, `GOCUOTAS_DELIVERED_END`.

## Snippets

**Client V1**

```python
from gocuotas import ClientV1

with ClientV1() as client:
    info = client.get_commerce_from_env()
```

**Redirect con builder de producción**

```python
from gocuotas import RedirectClientBuilder

with RedirectClientBuilder().production().build() as r:
    auth = r.authenticate("comercio@example.com", "…")
```

## Errores

- `GoCuotasApiError` para respuestas no 2xx genéricas.
- `OrderNotFoundError` en **404** al obtener o reembolsar una orden por id (no aplica al listado con 404).

## Documentación de API

- [API Redirect V1 (Stoplight)](https://gocuotas-api.stoplight.io/docs/gocuotas/dae8814842a1e-api-redirect-v1)

## Licencia

[MIT License](LICENSE) — Copyright (c) 2026 humen-io.
