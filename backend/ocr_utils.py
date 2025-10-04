from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import os

def extract_text_from_file(filepath):
    try:
        print(f"OCR: Received file: {filepath}")

        if not os.path.exists(filepath):
            raise FileNotFoundError("File does not exist.")

        if filepath.lower().endswith(".pdf"):
            print("Converting PDF pages to images...")
            images = convert_from_path(filepath, dpi=300)
            text = ''
            for idx, img in enumerate(images):
                print(f"OCR on page {idx + 1}")
                text += pytesseract.image_to_string(img) + "\n"
            return text

        else:
            print("Converting image to text...")
            img = Image.open(filepath)
            text = pytesseract.image_to_string(img)
            return text

    except Exception as e:
        print(" Error in OCR:", e)
        return "Error processing the uploaded file."
