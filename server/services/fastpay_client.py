import os
import uuid
from typing import Any, Dict, Optional

import requests


FASTPAY_BASE_URL = os.getenv("FASTPAY_BASE_URL", "https://api.fastpay.example.com")
FASTPAY_API_TOKEN = os.getenv("FASTPAY_API_TOKEN")


class FastPayError(Exception):
    pass


class FastPayClient:
    def __init__(self, base_url: str = FASTPAY_BASE_URL, api_token: Optional[str] = FASTPAY_API_TOKEN):
        if not api_token:
            raise FastPayError("FASTPAY_API_TOKEN is not configured")

        self.base_url = base_url.rstrip("/")
        self.api_token = api_token

    def _headers(self, idempotency_key: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        headers["Idempotency-Key"] = idempotency_key or str(uuid.uuid4())
        return headers

    def _post(self, path: str, payload: Dict[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = self._headers(idempotency_key)

        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        if not resp.ok:
            raise FastPayError(f"FastPay error {resp.status_code}: {resp.text}")
        return resp.json()

    def pay_now(self, source_iban: str, destination_iban: str, amount_cents: int, currency: str = "EUR") -> Dict[str, Any]:
        payload = {
            "source_iban": source_iban,
            "destination_iban": destination_iban,
            "amount": amount_cents,
            "currency": currency,
        }
        return self._post("/v1/payments", payload)

    def schedule_payment(
        self,
        source_iban: str,
        destination_iban: str,
        amount_cents: int,
        schedule_at_iso: str,
        currency: str = "EUR",
    ) -> Dict[str, Any]:
        payload = {
            "source_iban": source_iban,
            "destination_iban": destination_iban,
            "amount": amount_cents,
            "currency": currency,
            "schedule_at": schedule_at_iso,
        }
        return self._post("/v1/payments/scheduled", payload)