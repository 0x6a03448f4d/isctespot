import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class SecurityService:
    def __init__(self):
        # Em produção, isto deve vir de um Vault/Secrets Manager
        # Para este exercício, lê de variável de ambiente ou usa um fallback seguro
        key_env = os.getenv('PAYMENT_ENCRYPTION_KEY', 'my-super-secret-master-key-change-me')
        self._cipher = self._get_cipher(key_env)

    def _get_cipher(self, key_string):
        """Gera uma chave válida para AES-256 (Fernet) baseada na string fornecida"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'static_salt_change_in_prod', # Em produção, o salt deve ser dinâmico ou gerido pelo KMS
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(key_string.encode()))
        return Fernet(key)

    def encrypt_sensitive_data(self, plaintext):
        """Encripta dados (ex: IBAN) para armazenamento na DB"""
        if not plaintext:
            return None
        return self._cipher.encrypt(plaintext.encode()).decode()

    def decrypt_sensitive_data(self, ciphertext):
        """Decifra dados para envio ao processador de pagamentos"""
        if not ciphertext:
            return None
        return self._cipher.decrypt(ciphertext.encode()).decode()

    @staticmethod
    def mask_data(data, visible_chars=4):
        """Masking para Logs (Requisito: mostrar só 4 últimos dígitos)"""
        if not data or len(data) <= visible_chars:
            return "****"
        return "*" * (len(data) - visible_chars) + data[-visible_chars:]

# Instância singleton para ser usada na app
security_service = SecurityService()
