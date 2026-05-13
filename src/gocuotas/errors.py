"""HTTP errors from GoCuotas APIs."""

from typing import Optional


class GoCuotasApiError(Exception):
    def __init__(self, status_code: int, response_body: str, message: Optional[str] = None) -> None:
        super().__init__(message or f"GoCuotas API error HTTP {status_code}")
        self.status_code = status_code
        self.response_body = response_body


class OrderNotFoundError(Exception):
    """404 on GET/DELETE /api_redirect/v1/orders/{id}."""

    def __init__(self, order_id: str, response_body: str) -> None:
        super().__init__(f'gocuotas: order "{order_id}" not found (HTTP 404)')
        self.order_id = order_id
        self.response_body = response_body
        self.status_code = 404
