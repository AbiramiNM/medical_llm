import os
import uuid
from flask import Flask, request, jsonify, render_template, send_file
from ocr_utils import extract_text_from_file
from model import model_inference
from dotenv import load_dotenv
from fpdf import FPDF
import traceback
import unicodedata

load_dotenv()

UPLOAD_FOLDER = 'uploads'
app = Flask(__name__)

# ---------------------------------------------
# PDF Generation
def clean_text(text):
    return unicodedata.normalize("NFKD", text).encode("latin-1", "ignore").decode("latin-1")

def generate_pdf(extracted_text, analysis, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(0, 10, "Medical Report Summary", ln=True, align='C')
    pdf.ln(10)

    pdf.multi_cell(0, 10, "Extracted Text:\n" + clean_text(extracted_text))
    pdf.ln(5)
    pdf.multi_cell(0, 10, "LLM Analysis:\n" + clean_text(analysis))

    filepath = os.path.join("output", filename)
    os.makedirs("output", exist_ok=True)
    pdf.output(filepath)

    return filepath


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
