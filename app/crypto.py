# /secure-file-sender/app/crypto.py
import os
import requests
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding as sym_padding

# --- (PROJECT_ROOT, key paths, generate_keys, get_private_key are all the same) ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PRIVATE_KEY_FILE = os.path.join(PROJECT_ROOT, "my_private_key.pem")
PUBLIC_KEY_FILE = os.path.join(PROJECT_ROOT, "my_public_key.pem")

def generate_keys():
    if not os.path.exists(PRIVATE_KEY_FILE):
        print(f"Generating new key pair in {PROJECT_ROOT}...")
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
    with open(PRIVATE_KEY_FILE, "rb") as key_file:
        return serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )

# --- NEW ENCRYPTION FUNCTION ---

def encrypt_and_send_file(recipient_ip, plaintext_file, original_filename):
    """
    Encrypts a file and sends it to a recipient.
    This function runs entirely on the server.
    """
    
    # 1. Get the recipient's public key
    key_url = f"http://{recipient_ip}:5000/public-key"
    print(f"Fetching public key from {key_url}...")
    try:
        response = requests.get(key_url, timeout=5)
        response.raise_for_status()
        recipient_public_key = serialization.load_pem_public_key(
            response.content,
            backend=default_backend()
        )
    except requests.exceptions.RequestException as e:
        print(f"Error fetching public key: {e}")
        raise Exception(f"Could not connect to recipient at {recipient_ip}")

    print("Fetched key. Starting encryption...")
    
    # 2. Generate a one-time session key and IV
    session_key = os.urandom(32) # 256-bit
    iv = os.urandom(16) # 128-bit

    # 3. Pad the file content to be a multiple of the block size
    padder = sym_padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(plaintext_file) + padder.finalize()

    # 4. Encrypt the *file* with the symmetric session key (AES-CBC)
    cipher = Cipher(algorithms.AES(session_key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    # 5. Encrypt the *session key* with the recipient's public key (RSA-OAEP)
    encrypted_session_key = recipient_public_key.encrypt(
        session_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # 6. Send the encrypted bundle to the recipient
    upload_url = f"http://{recipient_ip}:5000/upload"
    files = {
        'session_key': encrypted_session_key,
        'iv': iv,
        'ciphertext': ciphertext
    }
    data = {
        'filename': original_filename
    }
    
    print(f"Uploading encrypted file to {upload_url}...")
    response = requests.post(upload_url, files=files, data=data)
    response.raise_for_status()
    print("Upload successful.")
    return response.json()


def send_plain_file(recipient_ip, plaintext_file, original_filename):
    """
    Sends a plaintext file to the recipient's /receive-plain endpoint.
    """
    upload_url = f"http://{recipient_ip}:5000/receive-plain"
    files = {
        'file': (original_filename, plaintext_file)
    }
    data = {
        'filename': original_filename
    }

    print(f"Uploading plain file to {upload_url}...")
    response = requests.post(upload_url, files=files, data=data)
    response.raise_for_status()
    print("Plain upload successful.")
    return response.json()

# --- DECRYPTION FUNCTION (Updated) ---

def decrypt_file_data(encrypted_session_key, iv, ciphertext):
    """Decrypts file data using the server's private key."""
    
    private_key = get_private_key()
    session_key = private_key.decrypt(
        encrypted_session_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    cipher = Cipher(algorithms.AES(session_key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    
    # Remove the PKCS#7 padding
    unpadder = sym_padding.PKCS7(algorithms.AES.block_size).unpadder()
    plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
    
    return plaintext