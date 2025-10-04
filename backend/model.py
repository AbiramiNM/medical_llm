import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv(override=True)


groq_api_key = os.getenv("GROQ_API_KEY")
model = os.getenv("MODEL_NAME")

def model_inference(Content:str) -> str:
    client = Groq(
    api_key=groq_api_key,
    )
    chat_completion = client.chat.completions.create(
        messages = [
            {
                "role": "user",
                "content" : Content
            }
        ],
        model = model
    )
    return chat_completion.choices[0].message.content


if __name__ == "__main__":
    try:
        print("Testing Groq model...")
        test_output = model_inference("Hello, what can you do?")
        print("Groq response:", test_output)
    except Exception as e:
        print("Groq connection failed:", str(e))

# response = model_inference("Explain the importance of fast language models")
# print(response)
