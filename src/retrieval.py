import os
import requests
import fitz  # PyMuPDF
from langdetect import detect
from dotenv import load_dotenv

load_dotenv()

SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
MAX_PAPERS = 12

PDF_DIR = "data/pdfs"

API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY")


def is_valid_english_pdf(pdf_bytes: bytes) -> bool:
    """
    Checks:
    - PDF is readable
    - Contains text
    - Language is English
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""

        for page in doc[:2]:
            text += page.get_text()

        if not text.strip():
            return False

        return detect(text) == "en"

    except Exception:
        return False


def retrieve_and_filter_papers_stream(topic: str):
    """
    Generator version:
    Yields result for EACH paper immediately
    """

    headers = {"x-api-key": API_KEY} if API_KEY else {}

    params = {
        "query": topic,
        "limit": MAX_PAPERS,
        "fields": "title,authors,year,abstract,openAccessPdf"
    }

    response = requests.get(
        SEMANTIC_SCHOLAR_API_URL,
        params=params,
        headers=headers,
        timeout=20
    )
    response.raise_for_status()

    papers = response.json().get("data", [])

    os.makedirs(PDF_DIR, exist_ok=True)

    for idx, paper in enumerate(papers, start=1):
        title = paper.get("title", "Unknown Title")
        pdf_info = paper.get("openAccessPdf")

        # Case 1: Paid or no PDF
        if not pdf_info or not pdf_info.get("url"):
            yield idx, title, "rejected", "Paid / No open-access PDF"
            continue

        try:
            pdf_response = requests.get(pdf_info["url"], timeout=20)

            # Case 2: Broken link
            if pdf_response.status_code != 200:
                yield idx, title, "rejected", "Broken PDF link"
                continue

            # Case 3: Invalid / non-English PDF
            if not is_valid_english_pdf(pdf_response.content):
                yield idx, title, "rejected", "Non-English or invalid PDF"
                continue

            safe_title = (
                title.replace("/", "_")
                .replace(":", "")
                .replace(" ", "_")
            )

            file_path = os.path.join(PDF_DIR, f"{safe_title}.pdf")

            with open(file_path, "wb") as f:
                f.write(pdf_response.content)

            yield idx, title, "accepted", "Downloaded successfully"

        except Exception:
            yield idx, title, "rejected", "PDF download failed"
