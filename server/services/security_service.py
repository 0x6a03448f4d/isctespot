import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature

class SecurityService:
    def __init__(self):
        # Chave de encriptação de dados (IBANs)
        key_env = '0ZyfBwp_hPzGl98wbDpodnbg9SgEisUD6ftttkE3qZ4='
        
        if not key_env:
            print("[WARNING] Using generated ephemeral key. Data will be lost on restart.")
            self._cipher = Fernet(Fernet.generate_key())
        else:
            try:
                self._cipher = Fernet(key_env.encode() if isinstance(key_env, str) else key_env)
            except Exception as e:
                print(f"[CRITICAL] Invalid Fernet Key: {e}")
                raise e

        # --- Assimétrica (RSA) ---
        # [FIX] Agora as chaves são carregadas do ficheiro para manter a identidade do Admin
        self._private_key, self._public_key = self._load_or_generate_rsa_keys()

    def _load_or_generate_rsa_keys(self):
        """ [FIX] Implementação com Persistência em ficheiro """
        private_key_path = "private_key.pem"
        
        # 1. Tentar carregar do disco
        if os.path.exists(private_key_path):
            try:
                with open(private_key_path, "rb") as key_file:
                    private_key = serialization.load_pem_private_key(
                        key_file.read(),
                        password=None
                    )
                    return private_key, private_key.public_key()
            except Exception as e:
                print(f"[SECURITY] Erro ao ler chave do disco: {e}. A gerar nova...")

        # 2. Gerar nova se não existir ou falhar a leitura
        print("[SECURITY] Gerando novo par de chaves RSA e guardando no disco...")
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        # 3. Guardar no disco (Persistência)
        with open(private_key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
            
        return private_key, public_key

    def encrypt_sensitive_data(self, plaintext):
        if not plaintext: return None
        return self._cipher.encrypt(plaintext.encode()).decode()

    def decrypt_sensitive_data(self, ciphertext):
        if not ciphertext: return None
        try:
            return self._cipher.decrypt(ciphertext.encode()).decode()
        except Exception:
            return None

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
