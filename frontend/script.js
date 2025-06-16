const form = document.getElementById('genForm');
const resultDiv = document.getElementById('result');

const BASE_URL = 'http://localhost:5000';

form.addEventListener('submit', async e => {
    e.preventDefault();
    resultDiv.textContent = '⏳ Generating…';

    const profile = {
        name: document.getElementById('name').value,
        contact: document.getElementById('contact').value,
        education: document.getElementById('education').value,
        skills: document.getElementById('skills').value,
        experience: document.getElementById('experience').value,
    };
    const jobDesc = document.getElementById('jobDesc').value;
    const mode = form.mode.value;
    const outputType = form.output.value;

    const endpoint = mode === 'resume'
        ? `${BASE_URL}/generate-resume`
        : `${BASE_URL}/generate-cover-letter`;

    try {
        const res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profile, jobDesc, outputType })
        });

        if (outputType === 'pdf' && res.ok) {
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            resultDiv.innerHTML = `
        <a href="${url}"
           download="${mode === 'resume' ? 'Resume.pdf' : 'Cover_Letter.pdf'}"
           class="download-link">
           Download ${mode === 'resume' ? 'Resume' : 'Cover Letter'} (PDF)
        </a>`;
            return;
        }

        const raw = await res.clone().text();

        if (!res.ok) {
            let errMsg;
            try {
                const errObj = JSON.parse(raw);
                errMsg = errObj.error || JSON.stringify(errObj);
            } catch {
                errMsg = raw || res.statusText;
            }
            throw new Error(`Server Error (${res.status}): ${errMsg}`);
        }

        try {
            const data = JSON.parse(raw);
            resultDiv.textContent = data.text;
        } catch {
            resultDiv.textContent = raw;
        }

    } catch (err) {
        console.error(err);
        resultDiv.textContent = 'Error: ' + err.message;
    }
});
