# /secure-file-sender/app/routes.py
from flask import current_app, render_template, send_file, request, jsonify
from .crypto import decrypt_file_data, PUBLIC_KEY_FILE

@current_app.route("/")
def home():
    """Serves the main HTML page for the sender UI."""
    return render_template("index.html")

@current_app.route("/public-key", methods=['GET'])
def get_public_key_endpoint():
    """API endpoint to send this server's public key."""
    print("Request for public key received. Sending...")
    return send_file(PUBLIC_KEY_FILE, as_attachment=True)

@current_app.route("/upload", methods=['POST'])
def upload_file_endpoint():
    """API endpoint to receive an encrypted file."""
    try:
        # 1. Get all the parts from the request
        data = request.files
        encrypted_session_key = data['session_key'].read()
        iv = data['iv'].read()
        ciphertext = data['ciphertext'].read()
        original_filename = request.form['filename']

        print(f"Received encrypted file: {original_filename}")

        # 2. Pass to the crypto module for decryption
        plaintext = decrypt_file_data(encrypted_session_key, iv, ciphertext)

        # 3. Save the decrypted file
        save_filename = f"DECRYPTED_{original_filename}"
        with open(save_filename, "wb") as f:
            f.write(plaintext)

        print(f"Success! File decrypted and saved as: {save_filename}")
        return jsonify({"message": "File received and decrypted successfully."}), 200

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"message": f"Error: {e}"}), 500