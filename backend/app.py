import os
import requests
import tempfile
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

API_KEY     = os.getenv("IBM_API_KEY")
PROJECT_ID  = os.getenv("IBM_PROJECT_ID")
REGION      = os.getenv("IBM_REGION")
MODEL_ID    = os.getenv("IBM_MODEL_ID")
API_VERSION = os.getenv("IBM_API_VERSION")

app = Flask(__name__)
CORS(app)

def get_iam_token() -> str:
    url = "https://iam.cloud.ibm.com/identity/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": API_KEY
    }
    resp = requests.post(url, headers=headers, data=data)
    resp.raise_for_status()
    return resp.json()["access_token"]

def generate_text(prompt: str) -> str:
    token = get_iam_token()
    endpoint = (
        f"https://{REGION}.ml.cloud.ibm.com/ml/v1/text/generation"
        f"?version={API_VERSION}"
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "ML-Instance-ID": PROJECT_ID  
    }
    payload = {
        "model_id": MODEL_ID,
        "input": prompt,
        "project_id": PROJECT_ID,
        "parameters": {
            "temperature": 0.7,
            "max_new_tokens": 500,
            "decoding_method": "greedy"
        }
    }
    resp = requests.post(endpoint, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()["results"][0]["generated_text"].strip()

def compose_resume_prompt(profile: dict, job_desc: str) -> str:
    return (
        "You're an expert resume writer. Using the user profile and job description, "
        "generate a professional resume formatted with clear sections "
        "(Contact Info, Education, Skills, Experience, Projects). Output in plain text.\n\n"
        f"Name: {profile['name']}\n"
        f"Contact: {profile['contact']}\n"
        f"Education: {profile['education']}\n"
        f"Skills: {profile['skills']}\n"
        f"Experience: {profile['experience']}\n\n"
        f"Job Description:\n{job_desc}\n"
    )

def compose_cover_letter_prompt(profile: dict, job_desc: str) -> str:
    return (
        "You're an expert cover letter writer. Using the user profile and job description, "
        "generate a personalized cover letter. Include greeting, intro, fit, and closing. Output in plain text.\n\n"
        f"Name: {profile['name']}\n"
        f"Contact: {profile['contact']}\n"
        f"Education: {profile['education']}\n"
        f"Skills: {profile['skills']}\n"
        f"Experience: {profile['experience']}\n\n"
        f"Job Description:\n{job_desc}\n"
    )

def text_to_pdf(text: str, title: str) -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(tmp.name, pagesize=LETTER)
    width, height = LETTER
    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, title)
    c.setFont("Helvetica", 11)
    y -= 30
    for line in text.splitlines():
        if y < 50:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 11)
        c.drawString(50, y, line)
        y -= 15
    c.save()
    return tmp.name

def handle_generation(profile, job_desc, compose_fn, output_type, title):
    prompt = compose_fn(profile, job_desc)
    generated = generate_text(prompt)
    if output_type == "text":
        return jsonify({ "text": generated })
    pdf_path = text_to_pdf(generated, title)
    return send_file(pdf_path, as_attachment=True, download_name=f"{title}.pdf")


@app.route('/generate-resume', methods=['POST'])
def generate_resume():
    data = request.get_json(force=True)
    profile = data.get("profile")
    jd = data.get("jobDesc")
    output = data.get("outputType", "pdf")
    if not profile or not jd:
        return jsonify({ "error": "Missing profile or jobDesc" }), 400
    return handle_generation(profile, jd, compose_resume_prompt, output, "Resume")

@app.route('/generate-cover-letter', methods=['POST'])
def generate_cover_letter():
    data = request.get_json(force=True)
    profile = data.get("profile")
    jd = data.get("jobDesc")
    output = data.get("outputType", "pdf")
    if not profile or not jd:
        return jsonify({ "error": "Missing profile or jobDesc" }), 400
    return handle_generation(profile, jd, compose_cover_letter_prompt, output, "Cover_Letter")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
