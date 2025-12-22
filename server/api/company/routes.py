import os
import json
from flask import Blueprint, request, jsonify, abort, send_file
from db.db_connector import DBConnector
from services.process_file import ProcessFile
from services.process_cash_flow import ProcessCashFlow
from services.process_sales import ProcessSales
from api.auth.jwt_utils import validate_token

# Importar serviços de segurança e pagamentos
from services.fastpay_service import fastpay_service
from services.security_service import security_service

company = Blueprint('company', __name__)

# --- AUDIT LOGGING (Requisito DDT: Monitorização) ---
@company.after_request
def audit_log(response):
    """
    Middleware que interceta todos os pedidos à API da empresa e grava logs de auditoria.
    Regista: Quem, O quê, Quando, IP e Estado.
    """
    # Ignorar logs para o método OPTIONS (CORS preflight) ou analytics pesados se necessário
    if request.method == 'OPTIONS':
        return response

    try:
        user_id = None
        # Tentar extrair UserID do Token (se presente no body JSON)
        if request.is_json:
            data = request.get_json(silent=True)
            if data and 'token' in data:
                valid, payload = validate_token(data['token'])
                if valid:
                    user_id = payload.get('user_id')

        # Mascarar dados sensíveis no body para o log
        body_content = request.get_data(as_text=True)
        if 'token' in body_content:
            # Simplificação: num sistema real usaríamos regex para mascarar apenas o valor
            body_content = "HIDDEN_SENSITIVE_DATA"

        dbc = DBConnector()
        # Grava na tabela AuditLogs (criada no passo anterior)
        dbc.execute_query('create_audit_log', args={
            'user_id': user_id,
            'endpoint': request.path,
            'method': request.method,
            'ip': request.remote_addr,
            'headers': str(dict(request.headers)), # Converter headers para string
            'body': body_content[:1000], # Limitar tamanho
            'status': response.status_code
        })
    except Exception as e:
        # Falha no log não deve parar a resposta, mas deve ser notada no console
        print(f"[AUDIT SYSTEM ERROR] Failed to log request: {e}")

    return response

# --- NOVAS ROTAS (DDT) ---

@company.route('/add-card', methods=['POST'])
def add_company_card():
    ''' 
    Associa o cartão de crédito da empresa para pagamentos.
    Envia dados para FastPay e guarda apenas o TOKEN.
    '''
    data = request.get_json()
    is_valid, payload = validate_token(data.get('token'))
    if not is_valid or not payload.get('is_admin'):
        return jsonify({'status': 'Unauthorized'}), 403

    # Simulação: Enviar dados sensíveis (PAN, CVV) para FastPay
    # fastpay_token = fastpay_service.tokenize_card(data)
    # Aqui geramos um token mock seguro
    comp_id = payload['comp_id']
    mock_token = f"tok_company_{comp_id}_secure"

    dbc = DBConnector()
    dbc.execute_query('update_company_card_token', args={
        'token': mock_token,
        'company_id': comp_id
    })

    return jsonify({"message": "Card successfully associated", "token_mask": "****" + mock_token[-4:]}), 200

@company.route('/schedule-pay', methods=['POST'])
def schedule_pay():
    ''' Configura a frequência de pagamentos automáticos '''
    data = request.get_json()
    is_valid, payload = validate_token(data.get('token'))
    if not is_valid or not payload.get('is_admin'):
        return jsonify({'status': 'Unauthorized'}), 403

    frequency = data.get('frequency_type') # 'Weekly', 'Monthly', 'Manual'
    
    dbc = DBConnector()
    dbc.execute_query('update_company_schedule', args={
        'schedule': frequency,
        'company_id': payload['comp_id']
    })

    return jsonify({"message": f"Schedule updated to {frequency}"}), 200

@company.route('/pay', methods=['POST'])
def process_company_payments():
    ''' 
    Endpoint Crítico: Executa pagamentos automáticos com cálculo REAL.
    Mitigação S (Spoofing): Valida token e permissões de admin.
    Mitigação R (Repudiation): Exige Assinatura Digital (Criptografia Assimétrica).
    '''
    # 1. Autenticação e Autorização
    dict_data = request.get_json()
    if not dict_data:
        return jsonify({'status': 'Bad Request', 'message': 'No data provided'}), 400

    token = dict_data.get('token')
    is_valid, payload = validate_token(token)
    
    if not is_valid or not payload.get('is_admin'):
        return jsonify({'status': 'Unauthorised'}), 403

    user_id = payload['user_id']
    comp_id = payload['comp_id']

    # 2. Verificação de Assinatura Digital (Criptografia Assimétrica)
    signature_hex = request.headers.get('X-Admin-Signature')
    data_to_verify = token 

    if not signature_hex:
        return jsonify({"error": "Missing Digital Signature (X-Admin-Signature)"}), 403

    if not security_service.verify_payment_signature(data_to_verify, signature_hex):
        print(f"[SECURITY] Payment rejected: Invalid Digital Signature from User {user_id}")
        return jsonify({"error": "Invalid Digital Signature. Non-repudiation check failed."}), 403

    try:
        dbc = DBConnector()

        # 3. Obter token da empresa (Payment Source) da DB
        company_card_token = dbc.execute_query('get_company_card_token', args=comp_id)
        if not company_card_token:
            return jsonify({"error": "Company has no payment card configured. Use /add-card first."}), 400

        # 4. Calcular Pagamentos Pendentes (Lógica Real)
        # Vai buscar comissões baseadas nas Vendas * %Comissão
        pending_commissions = dbc.execute_query('get_pending_commissions', args=comp_id)

        if not pending_commissions:
            return jsonify({"message": "No pending commissions found to pay."}), 200

        # 5. Preparar Payload (Decifrar em memória -> Enviar)
        targets = []
        for comm in pending_commissions:
            # comm = {'UserID': 1, 'EncryptedIBAN': '...', 'TotalToPay': 123.45}
            encrypted_iban = comm.get('EncryptedIBAN')
            amount = float(comm.get('TotalToPay', 0))

            if encrypted_iban and amount > 0:
                clear_iban = security_service.decrypt_sensitive_data(encrypted_iban)
                if clear_iban:
                    targets.append({
                        "iban": clear_iban,
                        "amount": amount
                    })
                else:
                    print(f"[ERROR] Could not decrypt IBAN for UserID {comm['UserID']}")

        if not targets:
            return jsonify({"error": "Found commissions but failed to prepare targets (Decryption error?)"}), 500

        # 6. Chamar FastPay
        result = fastpay_service.process_bulk_payment(company_card_token, targets)

        # 7. Responder e Logar na DB
        if result['status'] in ['success', 'processing']:
            
            total_amount = sum(t['amount'] for t in targets)
            
            dbc.execute_query('create_payment', args={
                'company_id': comp_id,
                'user_id': user_id,
                'transaction_id': result.get('transaction_id'),
                'amount': total_amount,
                'signature': signature_hex 
            })

            print(f"[AUDIT] Payment processed for Admin {user_id}. Transaction ID: {result.get('transaction_id')}")
            
            return jsonify({
                "message": "Payments processed successfully",
                "details": result,
                "total_paid": total_amount,
                "recipients_count": len(targets)
            }), 200
        else:
            return jsonify({"error": "Payment processor rejected the request"}), 500

    except Exception as e:
        print(f"[ERROR] Payment processing failed: {str(e)}") 
        return jsonify({"error": "Internal Server Error"}), 500

# --- Rotas Existentes ---

@company.route('/analytics', methods=['GET', 'POST'])
def list_sales_analytics():
    ''' List Sales function'''
    dbc = DBConnector()
    dict_data = request.get_json()
    is_valid, payload = validate_token(dict_data.get('token'))
    if not is_valid or not payload.get('is_admin'):
        return jsonify({'status': 'Unauthorised'}), 403
    results = dbc.execute_query(query='get_company_sales', args=payload['comp_id'])
    pcf = ProcessCashFlow(payload['comp_id'], 'PT', month=7)
    revenue = pcf.revenue
    ps = ProcessSales(results, payload['user_id'])
    ps.get_3_most_recent_sales()
    if isinstance(results, list):
        return jsonify({'status': 'Ok', 'last_3_sales': ps.last_3_sales, 'revenue': revenue, 'sales': results}), 200
    return jsonify({'status': 'Bad request'}), 403

@company.route('/employees', methods=['GET', 'POST'])
def list_employees():
    ''' List employees function'''
    dbc = DBConnector()
    dict_data = request.get_json()
    is_valid, payload = validate_token(dict_data.get('token'))
    if not is_valid or not payload.get('is_admin'):
        return jsonify({'status': 'Unauthorised'}), 403
    results = dbc.execute_query(query='get_employees_list', args=payload['comp_id'])
    if isinstance(results, list):
        return jsonify({'status': 'Ok', 'employees': results}), 200
    return jsonify({'status': 'Bad request'}), 403

@company.route('/products', methods=['GET', 'POST'])
def list_products():
    ''' List products for given company '''
    dbc = DBConnector()
    dict_data = request.get_json()
    is_valid, _payload = validate_token(dict_data.get('token'))
    if not is_valid:
        return jsonify({'status': 'Unauthorised'}), 403
    results = dbc.execute_query(query='get_products_list', args=_payload['comp_id'])
    if isinstance(results, list):
        return jsonify({'status': 'Ok', 'products': results}), 200
    return jsonify({'status': 'Bad request'}), 403

@company.route('/invoice', methods=['GET', 'POST'])
def invoice():
    ''' List products for given company '''
    filename = request.args.get('filename')
    _dir = os.path.join(os.path.dirname(__file__), 'invoices')
    file_path = os.path.join(_dir, filename)

    if os.path.exists(file_path):
        try:
            return send_file(file_path, as_attachment=True)
        except Exception as e:
            return str(e), 500
    else:
        abort(404, description="File not found")

@company.route('/seller/update-commission', methods=['GET', 'POST'])
def update_commission():
    ''' Update seller commission '''
    dict_data = request.get_json()
    token = dict_data['token']
    seller_id = dict_data['seller_id']
    new_commission = dict_data['new_commission']
    is_valid, payload = validate_token(token)
    if not is_valid or not payload.get('is_admin'):
        return jsonify({'status': 'Unauthorized'}), 403
    dbc = DBConnector()
    dbc.execute_query(query='update_seller_commission', args={'seller_id': seller_id, 'new_commission':new_commission})
    return jsonify({'status': 'Ok','message': 'File successfully uploaded'}), 200

@company.route('/update_products', methods=['POST'])
def upload_excel():
    ''' Update company products from csv or xlsx '''
    token = request.form.get('token')
    is_valid, payload = validate_token(token)
    if not is_valid or not payload.get('is_admin'):
        return jsonify({'status': 'Unauthorized'}), 403
    comp_id = payload.get('comp_id')
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    pf = ProcessFile(file, comp_id)
    if not pf.is_updated:
        return jsonify({'error': 'File processing failed'}), 400

    return jsonify({'status': 'Ok','message': 'File successfully uploaded'}), 200

@company.route('/cash-flow', methods=['POST'])
def cash_flow():
    ''' Calculate company's cash flow '''
    dict_data = request.get_json()
    is_valid, payload = validate_token(dict_data.get('token'))
    if not is_valid or not payload.get('is_admin'):
        return jsonify({'status': 'Unauthorised'}), 403
    
    pcf7 = ProcessCashFlow(country_code=dict_data['country_code'], company_id=payload['comp_id'], month=7)
    pcf8 = ProcessCashFlow(country_code=dict_data['country_code'], company_id=payload['comp_id'], month=8)
    pcf9 = ProcessCashFlow(country_code=dict_data['country_code'], company_id=payload['comp_id'], month=9)
    
    return jsonify(
        {
        'profit': pcf7.profit + pcf8.profit + pcf9.profit,
        'status': 'Ok',
        'July': pcf7.__dict__, 
        'August': pcf8.__dict__,
        'September': pcf9.__dict__
        }
            
    ), 200
