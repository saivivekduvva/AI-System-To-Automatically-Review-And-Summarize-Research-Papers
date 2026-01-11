import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PDF_DIR = os.path.join(BASE_DIR, "data", "pdfs")
EXTRACTED_DIR = os.path.join(BASE_DIR, "data", "extracted")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

os.makedirs(EXTRACTED_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
