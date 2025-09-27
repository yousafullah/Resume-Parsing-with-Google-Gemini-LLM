from flask import Flask, render_template, request, jsonify
from PyPDF2 import PdfReader
import google.generativeai as genai
import os
import json

# Set your API key
os.environ["GOOGLE_API_KEY"] = ""
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# app creation
app = Flask(__name__)

# load model
model = genai.GenerativeModel("models/gemini-1.5-pro")



def resumes_details(resume):
    # Prompt with detailed request
    prompt = f"""
    You are a resume parsing assistant. Given the following resume text, extract all the important details and return them in a well-structured JSON format.

    The resume text:
    {resume}

    Extract and include the following:
    - Full Name
    - Contact Number
    - Email Address
    - Location
    - Skills (Technical and Non-Technical, separately if possible)
    - Education
    - Work Experience (including company name, role, and responsibilities)
    - Certifications
    - Languages spoken
    - Suggested Resume Category (based on the skills and experience)
    - Recommended Job Roles (based on the candidate's skills and experience)

    Return the response in JSON format.
    """

    # Generate response from the model
    response = model.generate_content(prompt).text
    return response


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({"error": "No file part"})

    file = request.files['resume']

    if file.filename == '':
        return jsonify({"error": "No selected file"})

    if file and file.filename.endswith('.pdf'):
        # Extract text from the PDF
        text = ""
        reader = PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()

        # Get resume details from the model
        response = resumes_details(text)


        print(response)
        # Clean the response by removing the ```json and surrounding text
        response_clean = response.replace("```json", "").replace("```", "").strip()

        # Load the cleaned response into a dictionary
        data = json.loads(response_clean)

        # Extract details from the JSON response
        full_name = data.get("Full Name", "")
        contact_number = data.get("Contact Number", "")
        email_address = data.get("Email Address", "")
        location = data.get("Location", "")

        # Skills extraction
        skills = data.get("Skills", {})
        technical_skills = skills.get("Technical Skills", [])
        non_technical_skills = skills.get("Non-Technical Skills", [])
        technical_skills_str = ", ".join(technical_skills)
        non_technical_skills_str = ", ".join(non_technical_skills)

        # Education extraction
        education_list = data.get("Education", [])
        education_str = "\n".join([
            f"{edu.get('Degree', 'N/A')} from {edu.get('Institution', 'N/A')} (Graduated: {edu.get('Years', 'N/A')})"
            for edu in education_list
        ])

        # Work Experience extraction
        work_experience_list = data.get("Work Experience", [])
        work_experience_str = "\n".join([
            f"{job.get('Job Title', 'N/A')} at {job.get('Company Name', 'N/A')} ({job.get('Years of Experience', 'N/A')})\nResponsibilities: {', '.join(job.get('Responsibilities', []))}"
            for job in work_experience_list
        ])

        # Certifications extraction
        certifications_str = ", ".join(data.get("Certifications", []))

        # Languages extraction
        languages_str = ", ".join(data.get("Languages spoken", []))

        # Suggested Category and Recommended Job Roles extraction
        suggested_resume_category = data.get("Suggested Resume Category", "")
        recommended_job_roles_str = ", ".join(data.get("Recommended Job Roles", []))

        # Render the template and pass the extracted values to HTML
        return render_template('index.html',
                               full_name=full_name,
                               contact_number=contact_number,
                               email_address=email_address,
                               location=location,
                               technical_skills=technical_skills_str,
                               non_technical_skills=non_technical_skills_str,
                               education=education_str,
                               work_experience=work_experience_str,
                               certifications=certifications_str,
                               languages=languages_str,
                               suggested_resume_category=suggested_resume_category,
                               recommended_job_roles=recommended_job_roles_str)



# Start the Flask app
if __name__ == "__main__":
    app.run(debug=True)
