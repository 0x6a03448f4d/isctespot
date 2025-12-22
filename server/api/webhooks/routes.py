from flask import Blueprint, request, jsonify
from services.fastpay_service import fastpay_service

webhooks = Blueprint('webhooks', __name__)

@webhooks.route('/fastpay', methods=['POST'])
def fastpay_webhook():
    """
    Endpoint para receber atualizações de estado do FastPay.
    Mitigação: Validação estrita de assinatura HMAC.
    """
    signature = request.headers.get('FastPay-Signature')
    payload = request.get_data() # Raw bytes

    # 1. Verificar Assinatura (Tampering / Spoofing)
    if not fastpay_service.verify_webhook_signature(payload, signature):
        print("[SECURITY] Invalid webhook signature detected.")
        return jsonify({"error": "Invalid signature"}), 400

    # 2. Processar Evento
    data = request.get_json()
    event_type = data.get('type')
    
    if event_type == 'payment.success':
        # Atualizar estado na DB para 'Paid'
        tx_id = data.get('data', {}).get('transaction_id')
        print(f"[AUDIT] Payment confirmed via Webhook for TX: {tx_id}")
        
    elif event_type == 'payment.failed':
        # Logar erro e notificar admin
        print(f"[AUDIT] Payment FAILED via Webhook: {data.get('data')}")

    return jsonify({"status": "received"}), 200
