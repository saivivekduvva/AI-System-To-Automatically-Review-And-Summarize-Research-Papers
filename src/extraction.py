import os
import re
import json
import hashlib
import fitz  # PyMuPDF
from config import PDF_DIR, EXTRACTED_DIR, OUTPUT_DIR

SECTIONS = [
    "abstract",
    "introduction",
    "related work",
    "methodology",
    "methods",
    "experiments",
    "results",
    "discussion",
    "conclusion"
]

SECTIONS_OUT = os.path.join(OUTPUT_DIR, "sections")
os.makedirs(SECTIONS_OUT, exist_ok=True)


# ---------------- SAFE PAPER ID ---------------- #

def safe_paper_id(title: str, max_len: int = 50):
    clean = re.sub(r"[^a-zA-Z0-9_]", "_", title)
    clean = clean[:max_len]
    hash_suffix = hashlib.md5(title.encode()).hexdigest()[:6]
    return f"{clean}_{hash_suffix}"


# ---------------- PDF TO TEXT ---------------- #

def extract_text_from_pdfs():
    os.makedirs(EXTRACTED_DIR, exist_ok=True)

    id_map_path = os.path.join(OUTPUT_DIR, "paper_id_map.json")
    paper_id_map = {}

    for pdf in os.listdir(PDF_DIR):
        if not pdf.lower().endswith(".pdf"):
            continue

        original_title = pdf.replace(".pdf", "")
        paper_id = safe_paper_id(original_title)

        pdf_path = os.path.join(PDF_DIR, pdf)
        doc = fitz.open(pdf_path)

        full_text = ""
        for page in doc:
            full_text += page.get_text()

        out_path = os.path.join(EXTRACTED_DIR, f"{paper_id}.txt")

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(full_text)

        paper_id_map[paper_id] = original_title

    # Save ID → title mapping
    with open(id_map_path, "w", encoding="utf-8") as f:
        json.dump(paper_id_map, f, indent=2)


# ---------------- SECTION EXTRACTION ---------------- #

def split_into_sections(text: str):
    sections = {}
    current_section = None

    for line in text.split("\n"):
        clean = line.strip().lower()

        for sec in SECTIONS:
            if clean == sec:
                current_section = sec
                sections[current_section] = ""
                break

        if current_section:
            sections[current_section] += line + "\n"

    return sections


def extract_sections_from_text():
    all_papers = {}

    id_map_path = os.path.join(OUTPUT_DIR, "paper_id_map.json")
    with open(id_map_path, "r", encoding="utf-8") as f:
        paper_id_map = json.load(f)

    for file in os.listdir(EXTRACTED_DIR):
        if not file.endswith(".txt"):
            continue

        paper_id = file.replace(".txt", "")
        original_title = paper_id_map.get(paper_id, paper_id)

        with open(os.path.join(EXTRACTED_DIR, file), "r", encoding="utf-8") as f:
            text = f.read()

        sections = split_into_sections(text)

        all_papers[paper_id] = {
            "original_title": original_title,
            "sections": sections
        }

        paper_dir = os.path.join(SECTIONS_OUT, paper_id)
        os.makedirs(paper_dir, exist_ok=True)

        for sec, content in sections.items():
            with open(
                os.path.join(paper_dir, f"{sec}.txt"),
                "w",
                encoding="utf-8"
            ) as f:
                f.write(content)

    with open(
        os.path.join(SECTIONS_OUT, "all_sections.json"),
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(all_papers, f, indent=2)

    return all_papers
