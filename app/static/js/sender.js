// /secure-file-sender/app/static/js/sender.js
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('send-form');
    const statusEl = document.getElementById('status');
    const errorEl = document.getElementById('error');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        statusEl.textContent = 'Uploading to local server for processing...';
        errorEl.textContent = '';

        const ip = document.getElementById('ip').value;
        const file = document.getElementById('file').files[0];

        // Create a FormData object to send the file and IP
        const formData = new FormData();
        formData.append('ip', ip);
        formData.append('file', file);

        try {
            // Send the RAW file to our *own* server
            const response = await fetch('/send-to-peer', {
                method: 'POST',
                body: formData, // No more complex crypto!
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.message);
            }

            statusEl.textContent = `Success! ${result.message}`;
        } catch (err) {
            console.error(err);
            errorEl.textContent = `Error: ${err.message}`;
            statusEl.textContent = '';
        }
    });
});