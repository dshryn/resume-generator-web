from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os
import openai
import tempfile
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

openai.api_key = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)
CORS(app)

def generate_text(prompt: str) -> str:
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1500,
    )
    return resp.choices[0].message.content.strip()

def compose_resume_prompt(profile: dict, job_desc: str) -> str:
    return (
        "You're an expert resume writer. Using the user profile and job description, "
        "generate a professional resume formatted with clear sections (Contact Info, Education, Skills, Experience, Projects) "
        "tailored to the job description. Output plain text.\n\n"
        f"User Profile:\nName: {profile['name']}\nContact: {profile['contact']}\n"
        f"Education: {profile['education']}\nSkills: {profile['skills']}\n"
        f"Experience: {profile['experience']}\n\n"
        f"Job Description:\n{job_desc}\n"
    )

def compose_cover_letter_prompt(profile: dict, job_desc: str) -> str:
    return (
        "You're an expert cover letter writer. Using the user profile and job description, "
        "generate a personalized cover letter. Include greeting, introduction, why the candidate is a good fit, "
        "and closing. Output plain text.\n\n"
        f"User Profile:\nName: {profile['name']}\nContact: {profile['contact']}\nEducation: {profile['education']}\n"
        f"Skills: {profile['skills']}\nExperience: {profile['experience']}\n\n"
        f"Job Description:\n{job_desc}\n"
    )

def text_to_pdf(text: str, title: str) -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
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
    text = generate_text(prompt)
    if output_type == 'text':
        return jsonify({ "text": text })
    else:
        pdf_path = text_to_pdf(text, title)
        return send_file(pdf_path, as_attachment=True, download_name=f"{title}.pdf")

@app.route('/generate-resume', methods=['POST'])
def generate_resume():
    data = request.get_json() or {}
    profile = data.get('profile')
    jd = data.get('jobDesc')
    output = data.get('outputType', 'pdf')
    if not profile or not jd:
        return jsonify({'error': 'Missing profile or jobDesc'}), 400
    return handle_generation(profile, jd, compose_resume_prompt, output, "Resume")

@app.route('/generate-cover-letter', methods=['POST'])
def generate_cover_letter():
    data = request.get_json() or {}
    profile = data.get('profile')
    jd = data.get('jobDesc')
    output = data.get('outputType', 'pdf')
    if not profile or not jd:
        return jsonify({'error': 'Missing profile or jobDesc'}), 400
    return handle_generation(profile, jd, compose_cover_letter_prompt, output, "Cover_Letter")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
