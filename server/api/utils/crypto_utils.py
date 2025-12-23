import base64
import os
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

# Para simplificar, guardamos as chaves na pasta server/keys (podes mudar para secrets manager)
BASE_DIR = Path(__file__).resolve().parents[2]  # .../server
KEYS_DIR = BASE_DIR / "keys"
PRIVATE_KEY_FILE = KEYS_DIR / "fastpay_private_key.pem"
PUBLIC_KEY_FILE = KEYS_DIR / "fastpay_public_key.pem"


def generate_keys_if_missing():
    """Gera um par RSA 2048 se ainda não existir."""
    KEYS_DIR.mkdir(parents=True, exist_ok=True)

    if PRIVATE_KEY_FILE.exists() and PUBLIC_KEY_FILE.exists():
        return

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    # Guardar chave privada (em produção deve ser encriptada / em HSM / KMS)
    with PRIVATE_KEY_FILE.open("wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    # Guardar chave pública
    with PUBLIC_KEY_FILE.open("wb") as f:
        f.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )


def _load_public_key():
    with PUBLIC_KEY_FILE.open("rb") as f:
        return serialization.load_pem_public_key(f.read())


def _load_private_key():
    with PRIVATE_KEY_FILE.open("rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def encrypt_with_public_key(plaintext: str) -> str:
    """
    Cifra uma string com a chave pública (para guardar na BD).
    Retorna base64 para ser fácil guardar em VARCHAR/TEXT.
    """
    generate_keys_if_missing()
    public_key = _load_public_key()
    ciphertext = public_key.encrypt(
        plaintext.encode("utf-8"),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None
        ),
    )
    return base64.b64encode(ciphertext).decode("utf-8")


def decrypt_with_private_key(ciphertext_b64: str) -> str:
    """
    Decifra um valor cifrado em base64 com a chave privada (para enviar para FastPay).
    """
    generate_keys_if_missing()
    private_key = _load_private_key()
    ciphertext = base64.b64decode(ciphertext_b64.encode("utf-8"))
    plaintext = private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None
        ),
    )
    return plaintext.decode("utf-8")