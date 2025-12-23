import os
import uuid
from flask import Flask, request, jsonify

# Simple FastPay mock server for local development
# Endpoints replicate the expected auth and structure

app = Flask(__name__)

API_KEY = os.getenv("FASTPAY_API_TOKEN") or os.getenv("FASTPAY_API_KEY") or "sk_test_fastpay_dummy_123456"
WEBHOOK_SECRET = os.getenv("FASTPAY_WEBHOOK_SECRET", "whsec_fastpay_dummy_abcdef")


def auth_ok(req):
    return req.headers.get("Authorization") == f"Bearer {API_KEY}"


@app.route("/associate/card/<customer_id>", methods=["POST"])
def associate_card(customer_id):
    if not auth_ok(request):
        return jsonify({"error": "unauthorized"}), 401

    token = f"card_tok_{uuid.uuid4().hex}"
    return jsonify({
        "customer_id": customer_id,
        "token": token,
        "status": "associated"
    })


@app.route("/process/multiple-payments/<customer_id>", methods=["POST"])
def process_payments(customer_id):
    if not auth_ok(request):
        return jsonify({"error": "unauthorized"}), 401

    tx_id = f"fp_tx_{uuid.uuid4().hex}"
    return jsonify({
        "transaction_id": tx_id,
        "status": "processing"
    })


if __name__ == "__main__":
    # Run on localhost:9000
    app.run(port=9000)
