// /secure-file-sender/app/static/js/sender.js
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('send-form');
    const statusEl = document.getElementById('status');
    const errorEl = document.getElementById('error');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        statusEl.textContent = 'Starting...';
        errorEl.textContent = '';

        const ip = document.getElementById('ip').value;
        const file = document.getElementById('file').files[0];
        const recipientUrl = `http://${ip}:5000`;

        try {
            // 1. Fetch the recipient's public key
            statusEl.textContent = 'Fetching recipient public key...';
            const keyResponse = await fetch(`${recipientUrl}/public-key`);
            if (!keyResponse.ok) throw new Error('Could not fetch public key. Is the IP correct?');
            
            const recipientPublicKeyArmored = await keyResponse.text();

            // 2. Read the file from the browser
            const fileData = await file.arrayBuffer();

            // 3. --- Hybrid Encryption (Client-Side) ---
            statusEl.textContent = 'Encrypting file...';

            // 3a. Generate a random session key & IV for AES
            const sessionKey = window.crypto.getRandomValues(new Uint8Array(32)); // 256-bit
            const iv = window.crypto.getRandomValues(new Uint8Array(16)); // 128-bit

            // 3b. Encrypt the file data with AES-CFB
            const cryptoKey = await window.crypto.subtle.importKey('raw', sessionKey, { name: 'AES-CFB' }, false, ['encrypt']);
            const ciphertext = await window.crypto.subtle.encrypt({ name: 'AES-CFB', iv: iv }, cryptoKey, fileData);
            
            // 3c. Encrypt the session key with RSA-OAEP
            // We need to use the WebCrypto API, as openpgp.js is complex for *just* RSA-OAEP.
            const importedPublicKey = await window.crypto.subtle.importKey(
                'spki',
                _pemToBinary(recipientPublicKeyArmored), // Use helper function
                { name: 'RSA-OAEP', hash: 'SHA-256' },
                false,
                ['encrypt']
            );
            
            const encryptedSessionKey = await window.crypto.subtle.encrypt(
                { name: 'RSA-OAEP' },
                importedPublicKey,
                sessionKey
            );

            // 4. Send all parts in a FormData object
            statusEl.textContent = 'Uploading...';
            const formData = new FormData();
            formData.append('filename', file.name);
            formData.append('session_key', new Blob([encryptedSessionKey]));
            formData.append('iv', new Blob([iv]));
            formData.append('ciphertext', new Blob([ciphertext]));

            const uploadResponse = await fetch(`${recipientUrl}/upload`, {
                method: 'POST',
                body: formData,
            });

            if (!uploadResponse.ok) {
                const errData = await uploadResponse.json();
                throw new Error(`Upload failed: ${errData.message}`);
            }

            const result = await uploadResponse.json();
            statusEl.textContent = `Success! ${result.message}`;

        } catch (err) {
            console.error(err);
            errorEl.textContent = `Error: ${err.message}`;
            statusEl.textContent = '';
        }
    });

    /**
     * Helper function to convert a PEM-formatted public key
     * to the binary (SPKI) format that WebCrypto API understands.
     */
    function _pemToBinary(pem) {
        const base64String = pem
            .replace('-----BEGIN PUBLIC KEY-----', '')
            .replace('-----END PUBLIC KEY-----', '')
            .replace(/\n/g, '')
            .trim();
        const binaryDer = window.atob(base64String);
        const bytes = new Uint8Array(binaryDer.length);
        for (let i = 0; i < binaryDer.length; i++) {
            bytes[i] = binaryDer.charCodeAt(i);
        }
        return bytes.buffer;
    }
});