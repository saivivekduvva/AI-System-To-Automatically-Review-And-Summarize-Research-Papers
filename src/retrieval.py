import os
import requests
from dotenv import load_dotenv

# --------------------------------------------------
# Environment Setup
# --------------------------------------------------

load_dotenv()

SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIR = os.path.join(BASE_DIR, "data", "pdfs")

os.makedirs(PDF_DIR, exist_ok=True)

SEMANTIC_SCHOLAR_API_URL = (
    "https://api.semanticscholar.org/graph/v1/paper/search"
)

# --------------------------------------------------
# Semantic Scholar Search
# --------------------------------------------------

def search_papers(topic: str, limit: int = 20, offset: int = 0):
    params = {
        "query": topic,
        "limit": limit,
        "offset": offset,
        "fields": "title,year,citationCount,openAccessPdf"
    }

    headers = {
        "x-api-key": SEMANTIC_SCHOLAR_API_KEY
    }

    response = requests.get(
        SEMANTIC_SCHOLAR_API_URL,
        params=params,
        headers=headers,
        timeout=20
    )

    if response.status_code != 200:
        print("Semantic Scholar API error:", response.status_code)
        return []

    return response.json().get("data", [])

# --------------------------------------------------
# Paper Ranking
# --------------------------------------------------

def rank_papers(papers, top_k: int = 3):
    return sorted(
        papers,
        key=lambda p: (
            p.get("citationCount", 0),
            p.get("year", 0)
        ),
        reverse=True
    )[:top_k]

# --------------------------------------------------
# PDF Validation
# --------------------------------------------------

def is_valid_pdf(content: bytes) -> bool:
    return content[:4] == b"%PDF"

# --------------------------------------------------
# Download Logic (Search Until Valid PDF Found)
# --------------------------------------------------

def download_until_n_pdfs(
    topic: str,
    required: int = 3,
    batch_size: int = 20
):
    downloaded = 0
    offset = 0
    checked_titles = set()

    while downloaded < required:
        papers = search_papers(
            topic,
            limit=batch_size,
            offset=offset
        )

        if not papers:
            print("No more papers available.")
            break

        for paper in papers:
            if downloaded >= required:
                break

            title = paper.get("title", "Unknown")

            if title in checked_titles:
                continue
            checked_titles.add(title)

            pdf_info = paper.get("openAccessPdf")
            if not pdf_info or not pdf_info.get("url"):
                continue

            pdf_url = pdf_info["url"]

            try:
                response = requests.get(
                    pdf_url,
                    timeout=20,
                    headers={"User-Agent": "Mozilla/5.0"}
                )

                if response.status_code != 200:
                    continue

                if not is_valid_pdf(response.content):
                    print(f"Invalid PDF skipped → {title}")
                    continue

                downloaded += 1
                pdf_path = os.path.join(
                    PDF_DIR,
                    f"paper_{downloaded}.pdf"
                )

                with open(pdf_path, "wb") as f:
                    f.write(response.content)

                print(f"Downloaded valid PDF → {pdf_path}")

            except Exception as e:
                print("Download error:", e)

        offset += batch_size

    print(f"\nTotal valid PDFs downloaded: {downloaded}")

# --------------------------------------------------
# Entry Point
# --------------------------------------------------

if __name__ == "__main__":
    topic = input("Enter research topic: ").strip()
    print(f"Searching best papers related to: {topic}")
    download_until_n_pdfs(topic, required=1)
