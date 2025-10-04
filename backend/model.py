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
    """Generate a basic analysis when API is not available"""
    return f"""
    <h3>Medical Report Analysis</h3>
    <p><strong>Note:</strong> This is a basic analysis. For full AI-powered analysis, please configure the GROQ_API_KEY environment variable.</p>
    
    <h4>Extracted Text Summary:</h4>
    <p>The uploaded document contains {len(text.split())} words of medical information.</p>
    
    <h4>Key Observations:</h4>
    <ul>
        <li>Document successfully processed</li>
        <li>Text extraction completed</li>
        <li>Ready for manual review</li>
    </ul>
    
    <div class="important-note">
        <i class="fas fa-exclamation-circle"></i> 
        <strong>Important:</strong> This analysis is basic and for informational purposes only. 
        Always consult with your healthcare provider for medical advice.
    </div>
    """

if __name__ == "__main__":
    try:
        print("Testing Groq model...")
        test_output = model_inference("Hello, what can you do?")
        print("Groq response:", test_output)
    except Exception as e:
        print("Groq connection failed:", str(e))
