import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.exceptions import InvalidSignature

class SecurityService:
    def __init__(self):
        # MELHORIA: Lê a chave diretamente. Se não existir, gera uma (para dev)
        # Em produção, a variável PAYMENT_ENCRYPTION_KEY deve ser uma chave Base64 válida gerada por Fernet.generate_key()
        key_env = '0ZyfBwp_hPzGl98wbDpodnbg9SgEisUD6ftttkE3qZ4='


        
        if not key_env:
            # Fallback para desenvolvimento apenas
            print("[WARNING] Using generated ephemeral key. Data will be lost on restart.")
            self._cipher = Fernet(Fernet.generate_key())
        else:
            # Usa a chave fornecida diretamente (sem KDF/Salt estático)
            try:
                self._cipher = Fernet(key_env.encode() if isinstance(key_env, str) else key_env)
            except Exception as e:
                print(f"[CRITICAL] Invalid Fernet Key: {e}")
                raise e

        # --- Assimétrica (RSA) ---
        self._private_key, self._public_key = self._load_or_generate_rsa_keys()

    def _load_or_generate_rsa_keys(self):
        """Gera par de chaves RSA para Assinatura Digital"""
        # Em produção, carregar de ficheiros .pem ou Variáveis de Ambiente
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        return private_key, public_key

    def encrypt_sensitive_data(self, plaintext):
        if not plaintext: return None
        # O Fernet gere o IV aleatório internamente aqui
        return self._cipher.encrypt(plaintext.encode()).decode()

    def decrypt_sensitive_data(self, ciphertext):
        if not ciphertext: return None
        try:
            return self._cipher.decrypt(ciphertext.encode()).decode()
        except Exception:
            return None # Falha na desencriptação (chave errada ou dados corrompidos)

    def verify_payment_signature(self, payload_data, signature_hex):
        try:
            signature = bytes.fromhex(signature_hex)
            self._public_key.verify(
                signature,
                payload_data.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except (InvalidSignature, ValueError):
            return False

    @staticmethod
    def mask_data(data, visible_chars=4):
        if not data or len(data) <= visible_chars:
            return "****"
        return "*" * (len(data) - visible_chars) + data[-visible_chars:]

security_service = SecurityService()
