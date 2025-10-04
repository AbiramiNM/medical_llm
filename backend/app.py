import os
import uuid
from flask import Flask, request, jsonify, render_template, send_file
from ocr_utils import extract_text_from_file
from model import model_inference
from dotenv import load_dotenv
from fpdf import FPDF
import traceback
import unicodedata
from flask_cors import CORS

load_dotenv()

UPLOAD_FOLDER = 'uploads'

app = Flask(__name__)
CORS(app)
# ---------------------------------------------
# PDF Generation
def clean_text(text):
    return unicodedata.normalize("NFKD", text).encode("latin-1", "ignore").decode("latin-1")

def generate_pdf(extracted_text, analysis, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Header
    pdf.cell(0, 10, "VitaNote - Medical Report Analysis", ln=True, align='C')
    pdf.ln(10)

    # Check if this is real OCR text or metadata
    if "MEDICAL DOCUMENT ANALYSIS" not in extracted_text and "DOCUMENT PROCESSING STATUS" not in extracted_text:
        # This is real OCR text - create proper medical report
        pdf.set_font("Arial", size=14, style='B')
        pdf.cell(0, 10, "Medical Report Summary", ln=True, align='C')
        pdf.ln(10)
        
        pdf.set_font("Arial", size=12)
        
        # Extract and format patient information
        patient_info = extract_patient_info_for_pdf(extracted_text)
        if patient_info:
            pdf.set_font("Arial", size=12, style='B')
            pdf.cell(0, 8, "Patient Information:", ln=True)
            pdf.set_font("Arial", size=11)
            pdf.multi_cell(0, 6, patient_info)
            pdf.ln(5)
        
        # Medical details
        pdf.set_font("Arial", size=12, style='B')
        pdf.cell(0, 8, "Medical Details:", ln=True)
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 6, clean_text(extracted_text))
        pdf.ln(5)
        
        # Recommendations
        recommendations = extract_recommendations_for_pdf(extracted_text)
        if recommendations:
            pdf.set_font("Arial", size=12, style='B')
            pdf.cell(0, 8, "Recommendations:", ln=True)
            pdf.set_font("Arial", size=11)
            pdf.multi_cell(0, 6, recommendations)
            pdf.ln(5)
        
        # Analysis
        pdf.set_font("Arial", size=12, style='B')
        pdf.cell(0, 8, "AI Analysis:", ln=True)
        pdf.set_font("Arial", size=11)
        # Remove HTML tags from analysis for PDF
        clean_analysis = clean_html_tags(analysis)
        pdf.multi_cell(0, 6, clean_text(clean_analysis))
        
    else:
        # This is metadata fallback
        pdf.set_font("Arial", size=12, style='B')
        pdf.cell(0, 8, "Document Processing Report", ln=True)
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 6, clean_text(extracted_text))
        pdf.ln(5)
        pdf.multi_cell(0, 6, clean_text(analysis))

    # Disclaimer
    pdf.ln(10)
    pdf.set_font("Arial", size=10, style='I')
    pdf.multi_cell(0, 5, "DISCLAIMER: This analysis is generated from the uploaded medical report. Always consult with your healthcare provider for medical advice and interpretation.")

    filepath = os.path.join("output", filename)
    os.makedirs("output", exist_ok=True)
    pdf.output(filepath)

    return filepath

def extract_patient_info_for_pdf(text):
    """Extract patient information for PDF formatting"""
    lines = text.split('\n')
    info_lines = []
    
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in ['patient', 'name', 'age', 'sex', 'gender', 'dob', 'date of birth']):
            if line.strip():
                info_lines.append(line.strip())
    
    return '\n'.join(info_lines[:5])  # Limit to first 5 relevant lines

def extract_recommendations_for_pdf(text):
    """Extract recommendations for PDF formatting"""
    lines = text.split('\n')
    recommendations = []
    
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in ['recommend', 'follow-up', 'return', 'schedule', 'continue', 'discontinue', 'advise']):
            if line.strip():
                recommendations.append(f"• {line.strip()}")
    
    return '\n'.join(recommendations[:10])  # Limit to first 10 recommendations

def clean_html_tags(text):
    """Remove HTML tags from text for PDF"""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


# ---------------------------------------------
# Home page
@app.route('/', methods=['GET'])
def home():
    return render_template('upload.html')

# ---------------------------------------------
# Upload route
@app.route('/uploads', methods=['POST'])
def ocr_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty file'}), 400

    # Ensure uploads directory exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    print(f"File successfully saved at: {filepath}")  # debug log

    try:
        extracted_text = extract_text_from_file(filepath)
        analysis = model_inference(extracted_text)

        # Generate PDF
        result_filename = f"{uuid.uuid4().hex}_summary.pdf"
        result_path = generate_pdf(extracted_text, analysis, result_filename)

        return jsonify({
            'extracted_text': extracted_text,
            'analysis': analysis,
            'download_url': f"/download/{result_filename}"
        })

    except Exception as e:
        traceback.print_exc()  # ✅ Prints full error trace
        return jsonify({'error': str(e)}), 500

#----
# Chat route
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get("message")
    context = data.get("context")  # the summary from previous step

    if not message or not context:
        return jsonify({'error': 'Missing message or context'}), 400

    prompt = f"You are a helpful medical assistant. The user was shown this summary:\n\n{context}\n\nNow they asked: {message}\n\nReply accordingly."

    try:
        reply = model_inference(prompt)
        return jsonify({'response': reply})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---------------------------------------------
# Download route
@app.route('/download/<filename>', methods=['GET'])
def download_result(filename):
    filepath = os.path.join("output", filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        return "File not found", 404

# ---------------------------------------------
if __name__ == '__main__':
    print("Starting OCR API ...")
    app.run(debug=True, port=5050)
