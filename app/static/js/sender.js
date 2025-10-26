// /secure-file-sender/app/static/js/sender.js
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('send-form');
    const statusEl = document.getElementById('status');
    const errorEl = document.getElementById('error');

    // Helper to send file and ip to local server with an 'encrypted' flag
    async function sendFile(encrypted) {
        statusEl.textContent = 'Uploading to local server for processing...';
        errorEl.textContent = '';

        const ip = document.getElementById('ip').value;
        const file = document.getElementById('file').files[0];

        if (!ip || !file) {
            errorEl.textContent = 'IP and file are required.';
            statusEl.textContent = '';
            return;
        }

        // Create a FormData object to send the file, IP and encrypted flag
        const formData = new FormData();
        formData.append('ip', ip);
        formData.append('file', file);
        formData.append('encrypted', encrypted ? 'true' : 'false');

        try {
            const response = await fetch('/send-to-peer', {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.message || 'Unknown error');
            }

            statusEl.textContent = `Success! ${result.message}`;
        } catch (err) {
            console.error(err);
            errorEl.textContent = `Error: ${err.message}`;
            statusEl.textContent = '';
        }
    }

    // Wire the two buttons
    const encryptedBtn = document.getElementById('send-encrypted');
    const plainBtn = document.getElementById('send-plain');

    encryptedBtn.addEventListener('click', (e) => {
        e.preventDefault();
        sendFile(true);
    });

    plainBtn.addEventListener('click', (e) => {
        e.preventDefault();
        sendFile(false);
    });
});