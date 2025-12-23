from flask import current_app
import jwt
import traceback
from db.db_connector import DBConnector  # <--- [FIX] Importar para aceder à BD

def issue_token(user_id: int, comp_id: int, is_admin: bool, is_agent: bool) -> str:
    """ Create a new token with user information """
    payload = {
        'user_id': user_id,
        'comp_id': comp_id,
        'is_admin': is_admin,
        'is_agent': is_agent,
    }
    private_key = current_app.config.get('JWT_PRIVATE_PEM')
    if private_key:
        try:
            token = jwt.encode(payload, key=private_key, algorithm='RS256')
            str_token = token.decode('utf-8') if isinstance(token, (bytes, bytearray)) else token
            return str_token
        except Exception as e:
            raise Exception('Issue RS256 token failed', e) from e

def validate_token(token: str):
    """ Validate JWT token with Database Check """
    if not token:
        return False, None
    try:
        jwt.get_unverified_header(token)
    except Exception as e:
        print("Error decoding header", e, traceback.format_exc())
        return False, None

    try:
        public_key_pem = current_app.config.get('JWT_PUBLIC_PEM', '')
        if public_key_pem:
            # 1. Validação Criptográfica (Assinatura)
            payload = jwt.decode(
                token,
                key=public_key_pem,
                algorithms=['RS256']
            )

            # --- [FIX START] VALIDAÇÃO DE ESTADO NA BASE DE DADOS ---
            # Verifica se o token pertence a um utilizador que fez logout (isActive=0)
            user_id = payload.get('user_id')
            if user_id:
                dbc = DBConnector()
                # Usa a query existente 'get_user_by_id' que retorna {UserID, isActive, ...}
                user_data = dbc.execute_query('get_user_by_id', args=user_id)
                
                # Se o utilizador não for encontrado ou isActive for 0/False
                if not user_data or not user_data.get('isActive'):
                    print(f"[AUTH SECURITY] Token rejected: User {user_id} is inactive (Logged out).")
                    return False, None
            # --- [FIX END] ---

            return True, payload
    except Exception as e:
        print("Error decoding RS256 with public key", e)
        pass
    return False, None
