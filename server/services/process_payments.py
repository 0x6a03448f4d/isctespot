from typing import Any, Dict, List

from db.db_connector import DBConnector
from services.fastpay_client import FastPayClient, FastPayError
from api.utils.crypto_utils import decrypt_with_private_key


class ProcessPayments:
    """
    Serviço que:
    - Lê os dados bancários cifrados (NIB/cartão) da BD
    - Decifra com a chave privada (crypto_utils)
    - Envia pagamentos para o FastPay
    """

    def __init__(self, comp_id: int):
        self.comp_id = comp_id
        self.db = DBConnector()
        self.fastpay = FastPayClient()

    def _get_company_source_iban(self) -> str:
        """
        Para simplificar, assumimos que o IBAN de origem fica guardado cifrado
        como nib_encrypted do utilizador admin da empresa.
        Podes adaptar para uma tabela própria de contas.
        """
        encrypted_nib = self.db.execute_query("get_company_nib_encrypted", args=self.comp_id)
        if not encrypted_nib:
            raise FastPayError("No NIB configured for this company")

        source_iban = decrypt_with_private_key(encrypted_nib)
        return source_iban

    def pay_single(self, destination_iban_encrypted: str, amount_cents: int) -> Dict[str, Any]:
        source_iban = self._get_company_source_iban()
        destination_iban = decrypt_with_private_key(destination_iban_encrypted)

        resp = self.fastpay.pay_now(
            source_iban=source_iban,
            destination_iban=destination_iban,
            amount_cents=amount_cents,
        )

        self.db.execute_query(
            "insert_payment_history",
            args={
                "comp_id": self.comp_id,
                "dest_iban_masked": self._mask_iban(destination_iban),
                "amount_cents": amount_cents,
                "status": resp.get("status", "unknown"),
                "external_id": resp.get("id"),
            },
        )
        return resp

    def schedule_payment(self, destination_iban_encrypted: str, amount_cents: int, schedule_at_iso: str) -> Dict[str, Any]:
        source_iban = self._get_company_source_iban()
        destination_iban = decrypt_with_private_key(destination_iban_encrypted)

        resp = self.fastpay.schedule_payment(
            source_iban=source_iban,
            destination_iban=destination_iban,
            amount_cents=amount_cents,
            schedule_at_iso=schedule_at_iso,
        )

        self.db.execute_query(
            "insert_scheduled_payment",
            args={
                "comp_id": self.comp_id,
                "dest_iban_masked": self._mask_iban(destination_iban),
                "amount_cents": amount_cents,
                "schedule_at": schedule_at_iso,
                "status": resp.get("status", "scheduled"),
                "external_id": resp.get("id"),
            },
        )
        return resp

    @staticmethod
    def _mask_iban(iban: str) -> str:
        iban = iban.replace(" ", "")
        if len(iban) <= 8:
            return "***"
        return iban[:4] + "****" + iban[-4:]