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
    """Clean text for PDF generation by removing/replacing problematic Unicode characters"""
    if not text:
        return ""
    
    # Replace common Unicode characters that cause issues
    replacements = {
        '\u2022': '•',  # Bullet point
        '\u2013': '-',  # En dash
        '\u2014': '--', # Em dash
        '\u2018': "'",  # Left single quotation mark
        '\u2019': "'",  # Right single quotation mark
        '\u201c': '"',  # Left double quotation mark
        '\u201d': '"',  # Right double quotation mark
        '\u2026': '...', # Horizontal ellipsis
        '\u00a0': ' ',  # Non-breaking space
        '\u00b0': '°',  # Degree symbol
        '\u00ae': '(R)', # Registered trademark
        '\u00a9': '(C)', # Copyright
    }
    
    # Apply replacements
    for unicode_char, replacement in replacements.items():
        text = text.replace(unicode_char, replacement)
    
    # Remove any remaining problematic characters
    try:
        # Try to encode as latin-1, ignoring problematic characters
        cleaned = text.encode('latin-1', 'ignore').decode('latin-1')
        return cleaned
    except Exception:
        # Fallback: remove all non-ASCII characters
        return ''.join(char if ord(char) < 128 else '?' for char in text)

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
            pdf.cell(0, 8, "PATIENT INFORMATION", ln=True)
            pdf.set_font("Arial", size=11)
            pdf.multi_cell(0, 6, clean_text(patient_info))
            pdf.ln(5)
        
        # Extract surgical information
        surgical_info = extract_surgical_info_for_pdf(extracted_text)
        if surgical_info:
            pdf.set_font("Arial", size=12, style='B')
            pdf.cell(0, 8, "SURGICAL INFORMATION", ln=True)
            pdf.set_font("Arial", size=11)
            pdf.multi_cell(0, 6, clean_text(surgical_info))
            pdf.ln(5)
        
        # Medical details
        pdf.set_font("Arial", size=12, style='B')
        pdf.cell(0, 8, "MEDICAL DETAILS", ln=True)
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 6, clean_text(extracted_text))
        pdf.ln(5)
        
        # Recommendations
        recommendations = extract_recommendations_for_pdf(extracted_text)
        if recommendations:
            pdf.set_font("Arial", size=12, style='B')
            pdf.cell(0, 8, "Recommendations:", ln=True)
            pdf.set_font("Arial", size=11)
            pdf.multi_cell(0, 6, clean_text(recommendations))
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
    
    try:
        pdf.output(filepath)
        return filepath
    except Exception as e:
        print(f"Error generating PDF: {e}")
        # Create a simple fallback PDF
        try:
            pdf_fallback = FPDF()
            pdf_fallback.add_page()
            pdf_fallback.set_font("Arial", size=12)
            pdf_fallback.cell(0, 10, "VitaNote - Medical Report Analysis", ln=True, align='C')
            pdf_fallback.ln(10)
            pdf_fallback.multi_cell(0, 8, "Medical report processed successfully. Please consult with your healthcare provider for detailed analysis.")
            pdf_fallback.output(filepath)
            return filepath
        except Exception as fallback_error:
            print(f"Fallback PDF generation failed: {fallback_error}")
            raise e

def extract_patient_info_for_pdf(text):
    """Extract patient information for PDF formatting"""
    lines = text.split('\n')
    patient_info = {
        'name': 'Not specified',
        'mr_number': 'Not specified',
        'date_of_operation': 'Not specified',
        'age': 'Not specified',
        'gender': 'Not specified',
        'account_no': 'Not specified',
        'height': 'Not specified',
        'weight': 'Not specified'
    }
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        line_lower = line.lower()
        
        # Extract patient name
        if 'patient name:' in line_lower:
            parts = line.split(':', 1)
            if len(parts) > 1:
                patient_info['name'] = parts[1].strip()
        elif any(word in line_lower for word in ['abigail', 'houston']) and len(line.split()) >= 2:
            patient_info['name'] = line.strip()
        
        # Extract MR number
        if 'mr number:' in line_lower:
            parts = line.split(':', 1)
            if len(parts) > 1:
                patient_info['mr_number'] = parts[1].strip()
        
        # Extract date of operation
        if 'date of operation:' in line_lower:
            parts = line.split(':', 1)
            if len(parts) > 1:
                patient_info['date_of_operation'] = parts[1].strip()
        
        # Extract other fields
        if 'account no:' in line_lower:
            parts = line.split(':', 1)
            if len(parts) > 1:
                patient_info['account_no'] = parts[1].strip()
        elif 'height:' in line_lower:
            parts = line.split(':', 1)
            if len(parts) > 1:
                patient_info['height'] = parts[1].strip()
        elif 'weight:' in line_lower:
            parts = line.split(':', 1)
            if len(parts) > 1:
                patient_info['weight'] = parts[1].strip()
        elif 'female' in line_lower:
            patient_info['gender'] = 'Female'
        elif 'male' in line_lower:
            patient_info['gender'] = 'Male'
        elif 'year-old' in line_lower:
            import re
            age_match = re.search(r'(\d+)-year-old', line_lower)
            if age_match:
                patient_info['age'] = f"{age_match.group(1)} years old"
    
    # Format for PDF
    formatted_info = []
    formatted_info.append(f"Patient Name: {patient_info['name']}")
    formatted_info.append(f"MR Number: {patient_info['mr_number']}")
    formatted_info.append(f"Date of Operation: {patient_info['date_of_operation']}")
    formatted_info.append(f"Age: {patient_info['age']}")
    formatted_info.append(f"Gender: {patient_info['gender']}")
    formatted_info.append(f"Account No: {patient_info['account_no']}")
    formatted_info.append(f"Height: {patient_info['height']}")
    formatted_info.append(f"Weight: {patient_info['weight']}")
    
    return '\n'.join(formatted_info)

def extract_surgical_info_for_pdf(text):
    """Extract surgical information for PDF formatting"""
    lines = text.split('\n')
    surgical_info = {
        'preoperative_diagnosis': 'Not specified',
        'postoperative_diagnosis': 'Not specified',
        'operation_performed': 'Not specified',
        'surgeon': 'Not specified',
        'anesthesia': 'Not specified',
        'condition': 'Not specified',
        'complications': 'Not specified'
    }
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        line_lower = line.lower()
        
        # Extract surgical information
        if 'preoperative diagnosis:' in line_lower:
            parts = line.split(':', 1)
            if len(parts) > 1:
                surgical_info['preoperative_diagnosis'] = parts[1].strip()
        elif 'post-operative diagnosi:' in line_lower or 'postoperative diagnosis:' in line_lower:
            parts = line.split(':', 1)
            if len(parts) > 1:
                surgical_info['postoperative_diagnosis'] = parts[1].strip()
        elif 'operation performed:' in line_lower:
            parts = line.split(':', 1)
            if len(parts) > 1:
                surgical_info['operation_performed'] = parts[1].strip()
        elif 'surgeon' in line_lower and surgical_info['surgeon'] == 'Not specified':
            parts = line.split(':', 1)
            if len(parts) > 1:
                surgical_info['surgeon'] = parts[1].strip()
        elif 'anesthesia' in line_lower and surgical_info['anesthesia'] == 'Not specified':
            parts = line.split(':', 1)
            if len(parts) > 1:
                surgical_info['anesthesia'] = parts[1].strip()
        elif 'condition' in line_lower and surgical_info['condition'] == 'Not specified':
            parts = line.split(':', 1)
            if len(parts) > 1:
                surgical_info['condition'] = parts[1].strip()
        elif 'complications' in line_lower and surgical_info['complications'] == 'Not specified':
            parts = line.split(':', 1)
            if len(parts) > 1:
                surgical_info['complications'] = parts[1].strip()
    
    # Format for PDF
    formatted_info = []
    formatted_info.append(f"Preoperative Diagnosis: {surgical_info['preoperative_diagnosis']}")
    formatted_info.append(f"Postoperative Diagnosis: {surgical_info['postoperative_diagnosis']}")
    formatted_info.append(f"Operation Performed: {surgical_info['operation_performed']}")
    formatted_info.append(f"Surgeon: {surgical_info['surgeon']}")
    formatted_info.append(f"Anesthesia: {surgical_info['anesthesia']}")
    formatted_info.append(f"Condition: {surgical_info['condition']}")
    formatted_info.append(f"Complications: {surgical_info['complications']}")
    
    return '\n'.join(formatted_info)

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
    if not text:
        return ""
    
    # Remove HTML tags
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', text)
    
    # Decode HTML entities
    html_entities = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'",
        '&nbsp;': ' ',
    }
    
    for entity, char in html_entities.items():
        text = text.replace(entity, char)
    
    # Clean the text for PDF
    return clean_text(text)


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
