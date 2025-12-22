import requests
import uuid
from datetime import datetime
from .security_service import security_service

class FastPayService:
    BASE_URL = "https://api.fastpay-mock.com/v1" # URL Fictício
    API_TOKEN = "fp_live_secret_token_123" # Viria do Secrets Manager

    def associate_card(self, pan, expiry, holder):
        """
        Tokenização: Envia dados do cartão, recebe token.
        NUNCA guarda o PAN ou CVV na nossa base de dados.
        """
        # Simulação da chamada à API do FastPay
        # POST /associate/card
        
        # Na realidade farias: requests.post(..., json={...})
        
        # Mock Response
        return {
            "token": f"tok_fp_{uuid.uuid4().hex[:16]}",
            "last4": pan[-4:],
            "customer_id": f"cus_{uuid.uuid4().hex[:8]}"
        }

    def process_bulk_payment(self, company_token, targets):
        """
        Processa pagamentos em lote.
        targets: lista de dicts {'iban': 'pt50...', 'amount': 100}
        """
        headers = {
            "Authorization": f"Bearer {self.API_TOKEN}",
            "Idempotency-Key": str(uuid.uuid4()), # Previne pagamentos duplicados (Requisito T - Tampering)
            "Content-Type": "application/json"
        }

        # O FastPay recebe os dados decifrados em memória e processa
        payload = {
            "source_token": company_token,
            "targets": targets # IBANs já decifrados aqui
        }

        # Simulação de Log de Auditoria Seguro (Requisito E - Logging)
        # Atenção: Logamos o facto, mas MASCARAMOS os dados
        masked_targets = [
            {"iban": security_service.mask_data(t['iban']), "amount": t['amount']} 
            for t in targets
        ]
        
        print(f"[AUDIT] Enviando pagamento FastPay. ID Transação: {headers['Idempotency-Key']}")
        print(f"[AUDIT] Targets: {masked_targets}")

        # Simulação de sucesso
        return {
            "status": "success",
            "transaction_id": f"tx_{uuid.uuid4()}",
            "timestamp": datetime.utcnow().isoformat()
        }

fastpay_service = FastPayService()
