# /secure-file-sender/app/routes.py
from flask import current_app, render_template, send_file, request, jsonify
# We now import the new encryption function
from .crypto import decrypt_file_data, encrypt_and_send_file, PUBLIC_KEY_FILE

@current_app.route("/")
def home():
    """Serves the main HTML page for the sender UI."""
    return render_template("index.html")

@current_app.route("/public-key", methods=['GET'])
def get_public_key_endpoint():
    """API endpoint to send this server's public key."""
    print("Request for public key received. Sending...")
    return send_file(PUBLIC_KEY_FILE, as_attachment=True)

# --- NEW ROUTE FOR SENDING ---

@current_app.route("/send-to-peer", methods=['POST'])
def send_to_peer():
    """
    Receives a *plaintext* file and IP from its own browser,
    encrypts it, and forwards it to the recipient.
    """
    try:
        recipient_ip = request.form['ip']
        file_to_send = request.files['file']
        
        if not recipient_ip or not file_to_send:
            raise Exception("IP address and file are required.")

        print(f"Got file for {recipient_ip} from local browser.")
        
        # Read the file data
        plaintext_data = file_to_send.read()
        original_filename = file_to_send.filename
        
        # Call the crypto function to do all the work
        result = encrypt_and_send_file(recipient_ip, plaintext_data, original_filename)
        
        return jsonify({"success": True, "message": f"Successfully sent to {recipient_ip}"}), 200

    except Exception as e:
        print(f"Error in /send-to-peer: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

# --- UPLOAD ROUTE (No change) ---

@current_app.route("/upload", methods=['POST'])
def upload_file_endpoint():
    """API endpoint to receive an encrypted file."""
    try:
        data = request.files
        encrypted_session_key = data['session_key'].read()
        iv = data['iv'].read()
        ciphertext = data['ciphertext'].read()
        original_filename = request.form['filename']

        print(f"Received encrypted file: {original_filename}")
        plaintext = decrypt_file_data(encrypted_session_key, iv, ciphertext)
        save_filename = f"DECRYPTED_{original_filename}"
        
        with open(save_filename, "wb") as f:
            f.write(plaintext)

        print(f"Success! File decrypted and saved as: {save_filename}")
        return jsonify({"message": "File received and decrypted successfully."}), 200

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"message": f"Error: {e}"}), 500