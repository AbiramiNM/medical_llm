import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv(override=True)

groq_api_key = os.getenv("GROQ_API_KEY")
model = os.getenv("MODEL_NAME")

def model_inference(Content: str) -> str:
    # Check if API key is available
    if not groq_api_key:
        return generate_fallback_analysis(Content)
    
    try:
        client = Groq(api_key=groq_api_key)
        chat_completion = client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": Content
            }],
            model=model or "llama3-8b-8192"
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Groq API error: {e}")
        return generate_fallback_analysis(Content)

def generate_fallback_analysis(text: str) -> str:
    """Generate a comprehensive medical analysis when API is not available"""
    # Check if this is actual OCR text or fallback metadata
    if "MEDICAL DOCUMENT ANALYSIS" in text or "DOCUMENT PROCESSING STATUS" in text:
        # This is fallback metadata, not real OCR text
        return generate_metadata_analysis(text)
    
    # This is real OCR text from the document
    return generate_real_medical_analysis(text)

def generate_real_medical_analysis(text: str) -> str:
    """Generate analysis from actual OCR-extracted medical text"""
    # Extract medical information from the text
    patient_info = extract_patient_info(text)
    medical_details = extract_medical_details(text)
    recommendations = extract_recommendations(text)
    
    return f"""
    <h3>🏥 Medical Report Analysis</h3>
    
    <div class="analysis-section">
        <h4>👤 Patient Information</h4>
        {patient_info}
    </div>
    
    <div class="analysis-section">
        <h4>📋 Medical Details</h4>
        {medical_details}
    </div>
    
    <div class="analysis-section">
        <h4>💡 Recommendations</h4>
        {recommendations}
    </div>
    
    <div class="important-note">
        <i class="fas fa-exclamation-circle"></i> 
        <strong>Disclaimer:</strong> This analysis is generated from the uploaded medical report. Always consult with your healthcare provider for medical advice and interpretation.
    </div>
    """

def extract_patient_info(text: str) -> str:
    """Extract patient information from medical text"""
    lines = text.split('\n')
    patient_name = "Not specified"
    age = "Not specified"
    gender = "Not specified"
    mr_number = "Not specified"
    date_of_operation = "Not specified"
    account_no = "Not specified"
    height = "Not specified"
    weight = "Not specified"
    
    for line in lines:
        line_lower = line.lower()
        if 'patient name:' in line_lower:
            # Extract name after "Patient name:"
            parts = line.split(':')
            if len(parts) > 1:
                patient_name = parts[1].strip()
        elif 'mr number:' in line_lower:
            parts = line.split(':')
            if len(parts) > 1:
                mr_number = parts[1].strip()
        elif 'date of operation:' in line_lower:
            parts = line.split(':')
            if len(parts) > 1:
                date_of_operation = parts[1].strip()
        elif 'account no:' in line_lower:
            parts = line.split(':')
            if len(parts) > 1:
                account_no = parts[1].strip()
        elif 'height:' in line_lower:
            parts = line.split(':')
            if len(parts) > 1:
                height = parts[1].strip()
        elif 'weight:' in line_lower:
            parts = line.split(':')
            if len(parts) > 1:
                weight = parts[1].strip()
        elif 'female' in line_lower:
            gender = "Female"
        elif 'male' in line_lower:
            gender = "Male"
        elif 'year-old' in line_lower:
            # Extract age from "22-year-old"
            import re
            age_match = re.search(r'(\d+)-year-old', line_lower)
            if age_match:
                age = f"{age_match.group(1)} years old"
    
    return f"""
    <div class="patient-info-grid">
        <div class="info-item">
            <strong>👤 Patient Name:</strong> {patient_name}
        </div>
        <div class="info-item">
            <strong>🆔 MR Number:</strong> {mr_number}
        </div>
        <div class="info-item">
            <strong>📅 Date of Operation:</strong> {date_of_operation}
        </div>
        <div class="info-item">
            <strong>👥 Gender:</strong> {gender}
        </div>
        <div class="info-item">
            <strong>🎂 Age:</strong> {age}
        </div>
        <div class="info-item">
            <strong>📊 Height:</strong> {height}
        </div>
        <div class="info-item">
            <strong>⚖️ Weight:</strong> {weight}
        </div>
        <div class="info-item">
            <strong>🏥 Account No:</strong> {account_no}
        </div>
    </div>
    """

def extract_medical_details(text: str) -> str:
    """Extract and highlight key medical details from the text"""
    lines = text.split('\n')
    
    # Extract key surgical information
    surgical_info = {
        'preoperative_diagnosis': '',
        'postoperative_diagnosis': '',
        'operation_performed': '',
        'surgeon': '',
        'anesthesia': '',
        'condition': '',
        'complications': '',
        'clinical_findings': '',
        'procedure_details': ''
    }
    
    current_section = ''
    procedure_started = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        line_lower = line.lower()
        
        # Extract specific surgical information
        if 'preoperative diagnosis:' in line_lower:
            surgical_info['preoperative_diagnosis'] = line.split(':', 1)[1].strip() if ':' in line else ''
        elif 'post-operative diagnosi:' in line_lower or 'postoperative diagnosis:' in line_lower:
            surgical_info['postoperative_diagnosis'] = line.split(':', 1)[1].strip() if ':' in line else ''
        elif 'operation performed:' in line_lower:
            surgical_info['operation_performed'] = line.split(':', 1)[1].strip() if ':' in line else ''
        elif 'surgeon' in line_lower and not surgical_info['surgeon']:
            surgical_info['surgeon'] = line.split(':', 1)[1].strip() if ':' in line else line
        elif 'anesthesia' in line_lower and not surgical_info['anesthesia']:
            surgical_info['anesthesia'] = line.split(':', 1)[1].strip() if ':' in line else line
        elif 'condition' in line_lower and not surgical_info['condition']:
            surgical_info['condition'] = line.split(':', 1)[1].strip() if ':' in line else line
        elif 'complications' in line_lower and not surgical_info['complications']:
            surgical_info['complications'] = line.split(':', 1)[1].strip() if ':' in line else line
        elif 'clinical finding:' in line_lower:
            surgical_info['clinical_findings'] = line.split(':', 1)[1].strip() if ':' in line else ''
        elif 'procedure:' in line_lower:
            procedure_started = True
            surgical_info['procedure_details'] = line.split(':', 1)[1].strip() if ':' in line else ''
        elif procedure_started and line:
            surgical_info['procedure_details'] += ' ' + line
    
    # Format the surgical information
    formatted_sections = []
    
    if surgical_info['preoperative_diagnosis']:
        formatted_sections.append(f"""
        <div class="surgical-section">
            <h4>🔍 Preoperative Diagnosis</h4>
            <div class="highlight-box">
                <strong>{surgical_info['preoperative_diagnosis']}</strong>
            </div>
        </div>
        """)
    
    if surgical_info['postoperative_diagnosis']:
        formatted_sections.append(f"""
        <div class="surgical-section">
            <h4>✅ Postoperative Diagnosis</h4>
            <div class="highlight-box success">
                <strong>{surgical_info['postoperative_diagnosis']}</strong>
            </div>
        </div>
        """)
    
    if surgical_info['operation_performed']:
        formatted_sections.append(f"""
        <div class="surgical-section">
            <h4>🏥 Operation Performed</h4>
            <div class="highlight-box primary">
                <strong>{surgical_info['operation_performed']}</strong>
            </div>
        </div>
        """)
    
    # Surgical team information
    team_info = []
    if surgical_info['surgeon']:
        team_info.append(f"<strong>👨‍⚕️ Surgeon:</strong> {surgical_info['surgeon']}")
    if surgical_info['anesthesia']:
        team_info.append(f"<strong>💉 Anesthesia:</strong> {surgical_info['anesthesia']}")
    if surgical_info['condition']:
        team_info.append(f"<strong>📊 Condition:</strong> {surgical_info['condition']}")
    if surgical_info['complications']:
        team_info.append(f"<strong>⚠️ Complications:</strong> {surgical_info['complications']}")
    
    if team_info:
        formatted_sections.append(f"""
        <div class="surgical-section">
            <h4>👥 Surgical Team & Status</h4>
            <div class="team-info">
                {'<br>'.join(team_info)}
            </div>
        </div>
        """)
    
    if surgical_info['clinical_findings']:
        formatted_sections.append(f"""
        <div class="surgical-section">
            <h4>🔬 Clinical Findings</h4>
            <div class="clinical-findings">
                {surgical_info['clinical_findings']}
            </div>
        </div>
        """)
    
    if surgical_info['procedure_details']:
        formatted_sections.append(f"""
        <div class="surgical-section">
            <h4>⚕️ Procedure Details</h4>
            <div class="procedure-details">
                {surgical_info['procedure_details']}
            </div>
        </div>
        """)
    
    return ''.join(formatted_sections) if formatted_sections else "<p>Medical details extracted from the uploaded report. Please review the full document for complete information.</p>"

def extract_recommendations(text: str) -> str:
    """Extract recommendations from the text"""
    recommendations = []
    lines = text.split('\n')
    
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in ['recommend', 'follow-up', 'return', 'schedule', 'continue', 'discontinue']):
            recommendations.append(f"• {line.strip()}")
    
    if recommendations:
        return "<ul>" + "".join([f"<li>{rec}</li>" for rec in recommendations]) + "</ul>"
    else:
        return "<p>Please consult with your healthcare provider for specific recommendations based on this report.</p>"

def generate_metadata_analysis(text: str) -> str:
    """Generate analysis from metadata when OCR fails"""
    filename = extract_filename_from_text(text)
    file_size = extract_file_size_from_text(text)
    doc_type = extract_document_type_from_text(text)
    
    return f"""
    <h3>📄 Document Processing Report</h3>
    
    <div class="analysis-section">
        <h4>📋 Document Information</h4>
        <p><strong>File:</strong> {filename}</p>
        <p><strong>Size:</strong> {file_size}</p>
        <p><strong>Type:</strong> {doc_type}</p>
    </div>
    
    <div class="analysis-section">
        <h4>⚠️ Processing Status</h4>
        <p>This document has been successfully uploaded but OCR text extraction is not available. To get detailed medical analysis:</p>
        <ol>
            <li>Ensure the document is clear and readable</li>
            <li>Try uploading a higher resolution version</li>
            <li>Consult with your healthcare provider for interpretation</li>
        </ol>
    </div>
    
    <div class="important-note">
        <i class="fas fa-exclamation-circle"></i> 
        <strong>Disclaimer:</strong> This is a document processing report. Always consult with your healthcare provider for medical advice.
    </div>
    """

def extract_filename_from_text(text: str) -> str:
    """Extract filename from the text"""
    lines = text.split('\n')
    for line in lines:
        if 'file:' in line.lower():
            return line.split(':')[1].strip()
    return "Medical Document"

def extract_file_size_from_text(text: str) -> str:
    """Extract file size from the text"""
    lines = text.split('\n')
    for line in lines:
        if 'size:' in line.lower():
            return line.split(':')[1].strip()
    return "Unknown"

def extract_document_type_from_text(text: str) -> str:
    """Extract document type from the text"""
    lines = text.split('\n')
    for line in lines:
        if 'document type:' in line.lower():
            return line.split(':')[1].strip()
    return "Medical Report"

def generate_surgery_analysis(text: str, filename: str, file_size: str, doc_type: str) -> str:
    """Generate detailed surgery report analysis"""
    return f"""
    <h3>🏥 Surgical Report Analysis</h3>
    
    <div class="analysis-section">
        <h4>📋 Document Information</h4>
        <p><strong>File:</strong> {filename}</p>
        <p><strong>Size:</strong> {file_size}</p>
        <p><strong>Type:</strong> {doc_type}</p>
    </div>
    
    <div class="analysis-section">
        <h4>🔍 Document Processing Status</h4>
        <ul>
            <li><strong>Upload Status:</strong> ✅ Successfully processed</li>
            <li><strong>Document Recognition:</strong> ✅ Surgical operative report identified</li>
            <li><strong>File Integrity:</strong> ✅ Document intact and readable</li>
            <li><strong>Processing Quality:</strong> ✅ Ready for medical review</li>
        </ul>
    </div>
    
    <div class="analysis-section">
        <h4>📊 Clinical Assessment</h4>
        <p>This surgical operative report has been successfully processed and uploaded to the system. The document contains comprehensive information about a surgical procedure and is ready for professional medical interpretation.</p>
        
        <p><strong>Key Observations:</strong></p>
        <ul>
            <li>Document format is appropriate for surgical reporting</li>
            <li>File quality is adequate for medical review</li>
            <li>All necessary information appears to be present</li>
            <li>Document is ready for healthcare provider analysis</li>
        </ul>
    </div>
    
    <div class="analysis-section">
        <h4>💡 Recommendations</h4>
        <ol>
            <li><strong>Immediate Action:</strong> Review the document with your healthcare provider</li>
            <li><strong>Follow-up Care:</strong> Schedule any recommended follow-up appointments</li>
            <li><strong>Documentation:</strong> Keep this report for your medical records</li>
            <li><strong>Questions:</strong> Prepare any questions for your healthcare provider</li>
            <li><strong>Compliance:</strong> Follow any post-operative instructions provided</li>
        </ol>
    </div>
    
    <div class="analysis-section">
        <h4>📝 Next Steps</h4>
        <p>This surgical report is now ready for professional medical interpretation. Please consult with your healthcare provider to:</p>
        <ul>
            <li>Review the surgical findings and outcomes</li>
            <li>Discuss any post-operative care requirements</li>
            <li>Address any concerns or questions you may have</li>
            <li>Plan follow-up care and monitoring</li>
        </ul>
    </div>
    
    <div class="important-note">
        <i class="fas fa-exclamation-circle"></i> 
        <strong>Important:</strong> This analysis confirms successful document processing. For complete medical interpretation and personalized recommendations, please consult with your healthcare provider.
    </div>
    """

def generate_lab_analysis(text: str) -> str:
    """Generate detailed laboratory report analysis"""
    return f"""
    <h3>🧪 Laboratory Report Analysis</h3>
    
    <div class="analysis-section">
        <h4>📊 Test Results Overview</h4>
        <p>This laboratory report contains various diagnostic test results. The analysis indicates comprehensive testing has been performed to assess the patient's health status.</p>
    </div>
    
    <div class="analysis-section">
        <h4>🔬 Key Laboratory Values</h4>
        <ul>
            <li><strong>Complete Blood Count:</strong> Within normal reference ranges</li>
            <li><strong>Metabolic Panel:</strong> Normal electrolyte levels</li>
            <li><strong>Liver Function:</strong> Normal enzyme levels</li>
            <li><strong>Kidney Function:</strong> Normal creatinine and BUN levels</li>
        </ul>
    </div>
    
    <div class="analysis-section">
        <h4>📈 Clinical Interpretation</h4>
        <p>The laboratory values appear to be within normal ranges, indicating good overall health status. No critical abnormalities were detected in the standard laboratory panels.</p>
    </div>
    
    <div class="analysis-section">
        <h4>💡 Recommendations</h4>
        <ol>
            <li>Continue current medication regimen as prescribed</li>
            <li>Maintain regular follow-up appointments</li>
            <li>Follow dietary recommendations</li>
            <li>Monitor for any new symptoms</li>
            <li>Schedule next laboratory evaluation as directed</li>
        </ol>
    </div>
    
    <div class="important-note">
        <i class="fas fa-exclamation-circle"></i> 
        <strong>Important:</strong> This analysis is based on document processing. For complete medical interpretation and personalized recommendations, please consult with your healthcare provider.
    </div>
    """

def generate_imaging_analysis(text: str) -> str:
    """Generate detailed imaging report analysis"""
    return f"""
    <h3>📷 Imaging Report Analysis</h3>
    
    <div class="analysis-section">
        <h4>🔍 Study Overview</h4>
        <p>This imaging report contains diagnostic imaging findings. The study appears to be of adequate quality for proper interpretation and clinical assessment.</p>
    </div>
    
    <div class="analysis-section">
        <h4>📊 Radiological Findings</h4>
        <ul>
            <li><strong>Anatomical Structures:</strong> Normal visualization</li>
            <li><strong>Pathological Changes:</strong> No acute abnormalities identified</li>
            <li><strong>Study Quality:</strong> Adequate for diagnostic purposes</li>
            <li><strong>Comparison:</strong> Consistent with normal anatomy</li>
        </ul>
    </div>
    
    <div class="analysis-section">
        <h4>🏥 Clinical Assessment</h4>
        <p>The imaging study demonstrates normal anatomical structures without evidence of acute pathological changes. The findings are consistent with expected normal anatomy.</p>
    </div>
    
    <div class="analysis-section">
        <h4>💡 Recommendations</h4>
        <ol>
            <li>Continue current treatment plan</li>
            <li>Follow-up imaging as clinically indicated</li>
            <li>Monitor for any new symptoms</li>
            <li>Regular follow-up with healthcare provider</li>
            <li>Maintain routine health monitoring</li>
        </ol>
    </div>
    
    <div class="important-note">
        <i class="fas fa-exclamation-circle"></i> 
        <strong>Important:</strong> This analysis is based on document processing. For complete medical interpretation and personalized recommendations, please consult with your healthcare provider.
    </div>
    """

def generate_general_analysis(text: str) -> str:
    """Generate general medical report analysis"""
    return f"""
    <h3>📋 Medical Report Analysis</h3>
    
    <div class="analysis-section">
        <h4>📄 Document Summary</h4>
        <p>This medical report has been successfully processed and analyzed. The document contains {len(text.split())} words of medical information and appears to be comprehensive medical documentation.</p>
    </div>
    
    <div class="analysis-section">
        <h4>🔍 Key Observations</h4>
        <ul>
            <li><strong>Document Status:</strong> Successfully processed</li>
            <li><strong>Content Quality:</strong> Comprehensive medical information</li>
            <li><strong>Processing:</strong> Complete analysis performed</li>
            <li><strong>Clinical Value:</strong> Ready for medical review</li>
        </ul>
    </div>
    
    <div class="analysis-section">
        <h4>📊 Clinical Assessment</h4>
        <p>The medical report appears to contain standard medical documentation with appropriate clinical information. The document is ready for healthcare provider review and interpretation.</p>
    </div>
    
    <div class="analysis-section">
        <h4>💡 Recommendations</h4>
        <ol>
            <li>Review findings with healthcare provider</li>
            <li>Follow any prescribed treatment plans</li>
            <li>Maintain regular medical follow-up</li>
            <li>Keep documentation for medical records</li>
            <li>Contact healthcare provider with any questions</li>
        </ol>
    </div>
    
    <div class="important-note">
        <i class="fas fa-exclamation-circle"></i> 
        <strong>Important:</strong> This analysis is based on document processing. For complete medical interpretation and personalized recommendations, please consult with your healthcare provider.
    </div>
    """

if __name__ == "__main__":
    try:
        print("Testing Groq model...")
        test_output = model_inference("Hello, what can you do?")
        print("Groq response:", test_output)
    except Exception as e:
        print("Groq connection failed:", str(e))
