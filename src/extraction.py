import os
import re
import json
import fitz

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# --------------------------------------------------
# Paths (Relative to src/)
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIR = os.path.join(BASE_DIR, "data", "pdfs")
TEXT_DIR = os.path.join(BASE_DIR, "data", "extracted")

os.makedirs(TEXT_DIR, exist_ok=True)

# --------------------------------------------------
# PDF Text Extraction
# --------------------------------------------------

def extract_text_from_pdfs():
    for pdf in os.listdir(PDF_DIR):
        if not pdf.endswith(".pdf"):
            continue

        doc = fitz.open(os.path.join(PDF_DIR, pdf))
        text = ""

        for page in doc:
            text += page.get_text()

        out_path = os.path.join(
            TEXT_DIR,
            pdf.replace(".pdf", ".txt")
        )

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"Extracted text → {out_path}")

# --------------------------------------------------
# Text Cleaning
# --------------------------------------------------

def clean_text(text: str) -> str:
    text = re.sub(r"-\n", "", text)
    text = re.sub(r"\n+", "\n", text)

    lines = text.split("\n")
    merged = []

    for line in lines:
        if line.strip().isupper():
            merged.append("\n" + line.strip() + "\n")
        else:
            merged.append(line.strip() + " ")

    text = "".join(merged)
    text = re.sub(r"\s+", " ", text)

    return text.strip()

# --------------------------------------------------
# Section Detection
# --------------------------------------------------

SECTION_PATTERNS = {
    "abstract": r"\babstract\b",
    "introduction": r"\bintroduction\b",
    "methodology": r"\b(methodology|methods|approach|model|architecture)\b",
    "experiments": r"\b(experiments|experimental setup|evaluation)\b",
    "results": r"\b(results|analysis)\b",
    "conclusion": r"\b(conclusion|discussion|future work)\b"
}

def split_sections(text: str):
    sections = {k: "" for k in SECTION_PATTERNS}
    sections["full_text"] = text

    text_lower = text.lower()
    indices = {}

    for sec, pattern in SECTION_PATTERNS.items():
        match = re.search(pattern, text_lower)
        if match:
            indices[sec] = match.start()

    if not indices:
        return sections

    sorted_sections = sorted(indices.items(), key=lambda x: x[1])

    for i, (sec, start) in enumerate(sorted_sections):
        end = (
            sorted_sections[i + 1][1]
            if i + 1 < len(sorted_sections)
            else len(text)
        )
        content = text[start:end].strip()

        if len(content.split()) > 100:
            sections[sec] = content

    return sections

# --------------------------------------------------
# Section Normalization & Validation
# --------------------------------------------------

def recover_abstract(text: str) -> str:
    if "abstract" in text.lower():
        idx = text.lower().find("abstract")
        return text[idx: idx + 1500]
    return ""

def normalize_sections(sections: dict):
    if not sections.get("methodology"):
        sections["methodology"] = sections.get("introduction", "")

    if not sections.get("results"):
        sections["results"] = sections.get("experiments", "")

    if not sections.get("abstract"):
        sections["abstract"] = recover_abstract(sections["full_text"])

    return sections

def validate_sections(sections: dict):
    report = {
        "abstract_ok": False,
        "methodology_ok": False,
        "results_ok": False,
        "overall_valid": False,
        "issues": []
    }

    if sections.get("abstract") and len(sections["abstract"].split()) >= 80:
        report["abstract_ok"] = True
    else:
        report["issues"].append("Abstract missing or too short")

    if sections.get("methodology") and len(sections["methodology"].split()) >= 300:
        report["methodology_ok"] = True
    else:
        report["issues"].append("Methodology missing or too short")

    if sections.get("results") and len(sections["results"].split()) >= 300:
        report["results_ok"] = True
    else:
        report["issues"].append("Results missing or too short")

    if report["abstract_ok"] or (
        report["methodology_ok"] and report["results_ok"]
    ):
        report["overall_valid"] = True

    return report

# --------------------------------------------------
# Key Findings Extraction
# --------------------------------------------------

KEY_PHRASES = [
    "we find",
    "our results",
    "results show",
    "results indicate",
    "demonstrate",
    "outperform",
    "significant",
    "improves",
    "achieves"
]

def extract_key_findings(sections: dict):
    findings = []
    text = sections.get("results", "") + sections.get("conclusion", "")

    sentences = re.split(r'(?<=[.!?])\s+', text)

    for s in sentences:
        s_low = s.lower()
        if any(k in s_low for k in KEY_PHRASES) and len(s.split()) > 12:
            findings.append(s.strip())

    return findings[:10]

# --------------------------------------------------
# Paper Profile Builder
# --------------------------------------------------

def build_paper_profile(paper_id: str, sections: dict):
    return {
        "paper_id": paper_id,
        "abstract": sections.get("abstract", "")[:600],
        "methodology": sections.get("methodology", "")[:800],
        "key_findings": extract_key_findings(sections)
    }

# --------------------------------------------------
# Cross-Paper Semantic Comparison
# --------------------------------------------------

def compare_papers_semantic(paper_profiles, threshold=0.35):
    findings, meta = [], []

    for paper in paper_profiles:
        for f in paper["key_findings"]:
            findings.append(f)
            meta.append(paper["paper_id"])

    if len(findings) < 2:
        return {"common_findings": {}, "paper_wise_findings": {}}

    tfidf = TfidfVectorizer(stop_words="english").fit_transform(findings)
    similarity = cosine_similarity(tfidf)

    common = {}

    for i in range(len(findings)):
        for j in range(i + 1, len(findings)):
            if similarity[i][j] >= threshold and meta[i] != meta[j]:
                key = findings[i][:80]
                common.setdefault(key, set()).update([meta[i], meta[j]])

    return {
        "common_findings": {k: list(v) for k, v in common.items()},
        "paper_wise_findings": {
            p["paper_id"]: p["key_findings"] for p in paper_profiles
        }
    }

# --------------------------------------------------
# Theme-Based Comparison
# --------------------------------------------------

THEMES = {
    "performance_improvement": [
        "improves", "outperforms", "accuracy", "bleu", "state-of-the-art", "achieves"
    ],
    "bias_fairness": [
        "bias", "fairness", "political", "ideological", "partisan"
    ],
    "dataset_artifacts": [
        "dataset", "artifacts", "benchmark", "spurious", "corpus"
    ],
    "generalization_limits": [
        "overestimated", "fails", "limitations", "does not generalize"
    ]
}

def theme_based_comparison(paper_profiles):
    theme_map = {t: [] for t in THEMES}

    for paper in paper_profiles:
        pid = paper["paper_id"]
        for finding in paper["key_findings"]:
            f_low = finding.lower()
            for theme, keys in THEMES.items():
                if any(k in f_low for k in keys):
                    theme_map[theme].append(pid)
                    break

    return {
        t: list(set(pids))
        for t, pids in theme_map.items()
        if len(set(pids)) > 1
    }

# --- Move the JSON saving logic INSIDE the main block ---

if __name__ == "__main__":
    extract_text_from_pdfs()

    paper_profiles = []

    for idx, txt in enumerate(os.listdir(TEXT_DIR)):
        with open(os.path.join(TEXT_DIR, txt), "r", encoding="utf-8") as f:
            raw = f.read()

        cleaned = clean_text(raw)
        sections = normalize_sections(split_sections(cleaned))
        profile = build_paper_profile(f"paper_{idx+1}", sections)
        paper_profiles.append(profile)

    # NOW these lines are protected and won't crash your app
    ANALYSIS_DIR = os.path.join(BASE_DIR, "data", "analysis")
    os.makedirs(ANALYSIS_DIR, exist_ok=True)

    with open(os.path.join(ANALYSIS_DIR, "paper_profiles.json"), "w", encoding="utf-8") as f:
        json.dump(paper_profiles, f, indent=2)