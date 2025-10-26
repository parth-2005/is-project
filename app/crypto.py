# /secure-file-sender/app/crypto.py
import os
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Define absolute paths for the key files
PRIVATE_KEY_FILE = os.path.join(PROJECT_ROOT, "my_private_key.pem")
PUBLIC_KEY_FILE = os.path.join(PROJECT_ROOT, "my_public_key.pem")
def generate_keys():
    """Generates a new key pair if they don't exist."""
    if not os.path.exists(PRIVATE_KEY_FILE):
        print(f"Generating new key pair...")
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        with open(PRIVATE_KEY_FILE, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        public_key = private_key.public_key()
        with open(PUBLIC_KEY_FILE, "wb") as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
    print(f"Keys are ready: {PUBLIC_KEY_FILE}, {PRIVATE_KEY_FILE}")

def get_private_key():
    """Loads the server's private key from its file."""
    with open(PRIVATE_KEY_FILE, "rb") as key_file:
        return serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )

def decrypt_file_data(encrypted_session_key, iv, ciphertext):
    """Decrypts file data using the server's private key."""
    
    # 1. Load our private key to decrypt the session key
    private_key = get_private_key()
    session_key = private_key.decrypt(
        encrypted_session_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # 2. Use the decrypted session key to decrypt the file
    cipher = Cipher(algorithms.AES(session_key), modes.CFB(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    
    return plaintext