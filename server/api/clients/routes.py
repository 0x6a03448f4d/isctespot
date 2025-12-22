from flask import Blueprint, request, jsonify
from db.db_connector import DBConnector
from api.auth.jwt_utils import validate_token
# Import corrigido para funcionar dentro do container
from services.security_service import security_service

clients = Blueprint('clients', __name__)

@clients.route('/clients', methods=['GET', 'POST'])
def list_clients():
    ''' List clients function'''
    dbc = DBConnector()
    dict_data = request.get_json()
    token = dict_data.get('token')
    is_valid, payload = validate_token(token)
    if not is_valid or not payload.get('is_admin'):
        return jsonify({'status': 'Unauthorised'}), 403
    comp_id = dbc.execute_query(query='get_compnay_id_by_user', args=payload['user_id'])
    results = dbc.execute_query(query='get_clients_list', args=comp_id)
    if isinstance(results, list):
        return jsonify({'status': 'Ok', 'clients': results}), 200
    return jsonify({'status': 'Bad credentials'}), 403

@clients.route('/clients/new', methods=['POST'])
def new_client():
    ''' Create a new client with IBAN '''
    dbc = DBConnector()
    dict_data = request.get_json()
    token = dict_data.get('token')
    
    is_valid, payload = validate_token(token)
    if not is_valid:
        return jsonify({'status': 'Unauthorised'}), 403
    
    comp_id = payload['comp_id']
    
    # Tratamento do IBAN
    iban = dict_data.get('iban')
    encrypted_iban = None
    
    if iban:
        # Validação simples
        if not iban.startswith("PT50") or len(iban) != 25:
             return jsonify({'status': 'Bad request', 'error': 'Invalid IBAN format'}), 400
        
        # Encriptar
        try:
            encrypted_iban = security_service.encrypt_sensitive_data(iban)
        except Exception as e:
            return jsonify({'status': 'Server Error', 'error': 'Encryption failed'}), 500

    result = dbc.execute_query('create_client', args={
        'comp_id': comp_id,
        'first_name': dict_data['first_name'],
        'last_name': dict_data['last_name'],
        'email': dict_data['email'],
        'phone_number': dict_data['phone_number'],
        'address': dict_data['address'],
        'city': dict_data['city'],
        'country': dict_data['country'],
        'encrypted_iban': encrypted_iban  # Passamos o valor encriptado
    })
    
    if isinstance(result, int):
        return jsonify({'status': 'Ok', 'client_id': result}), 200
    else:
        return jsonify({'status': 'Bad request'}), 400
@clients.route('/clients/delete', methods=['POST'])
def delete_client():
    ''' Delete client '''
    dbc = DBConnector()
    dict_data = request.get_json()
    token = dict_data.get('token')
    is_valid, payload = validate_token(token)
    if not is_valid:
        return jsonify({'status': 'Unauthorised'}), 403
    result = dbc.execute_query(query='delete_client_by_id', args=dict_data['client_id'])
    if isinstance(result, int):
        return jsonify({'status': 'Ok', 'client_id':result}), 200
    else:
        return jsonify({'status': 'Bad request'}), 400

# --- Nova Rota Segura para IBAN ---

@clients.route('/<int:client_id>/payment-info', methods=['PUT'])
def update_payment_info(client_id):
    ''' Update client payment info securely '''
    # 1. Autenticação (Padronizada)
    dict_data = request.get_json()
    token = dict_data.get('token')
    
    is_valid, payload = validate_token(token)
    if not is_valid:
        return jsonify({'status': 'Unauthorised'}), 403

    # Opcional: Verificar se o user tem permissão para editar este cliente específico
    # if payload['comp_id'] != client_company_id: return ..., 403

    iban = dict_data.get('iban')

    # 2. Validação de Entrada (Input Validation)
    # Regra simples para PT. Em produção usar uma biblioteca de validação de IBAN.
    if not iban or not iban.startswith("PT50") or len(iban) != 25:
        return jsonify({"error": "Invalid IBAN format"}), 400

    # 3. Encriptação (Data at Rest Protection)
    # O IBAN 'clear text' é cifrado imediatamente antes de qualquer persistência
    try:
        encrypted_iban = security_service.encrypt_sensitive_data(iban)
    except Exception as e:
        return jsonify({"error": "Encryption failed"}), 500

    # 4. Guardar na DB
    dbc = DBConnector()
    # Nota: Garante que a query 'update_client_iban' existe no teu ficheiro de queries SQL
    # Exemplo SQL: UPDATE clients SET encrypted_iban = :encrypted_iban WHERE id = :client_id
    result = dbc.execute_query('update_client_payment_info', args={
        'client_id': client_id,
        'encrypted_iban': encrypted_iban
    })

    # 5. Auditoria (Masking)
    masked = security_service.mask_data(iban)
    print(f"[AUDIT] User {payload['user_id']} updated IBAN for Client {client_id} to {masked}")

    if result is not None: # Assumindo que o conector retorna algo em sucesso
        return jsonify({"message": "Payment info updated securely"}), 200
    else:
        return jsonify({"error": "Database update failed"}), 500
