import json
import os
from config import OUTPUT_DIR

SECTIONS_DIR = os.path.join(OUTPUT_DIR, "sections")
ANALYSIS_OUT = os.path.join(OUTPUT_DIR, "analysis")
os.makedirs(ANALYSIS_OUT, exist_ok=True)

KEYWORDS = [
    "propose",
    "introduce",
    "improve",
    "outperform",
    "achieve",
    "demonstrate",
    "increase",
    "reduce"
]

# ---------------- KEY FINDING EXTRACTION ---------------- #

def extract_key_findings():
    input_file = os.path.join(SECTIONS_DIR, "all_sections.json")

    with open(input_file, "r", encoding="utf-8") as f:
        papers = json.load(f)

    findings = {}

    for paper_id, paper_data in papers.items():
        sections = paper_data.get("sections", {})
        original_title = paper_data.get("original_title", paper_id)

        paper_findings = []

        for sec in ["abstract", "results", "conclusion"]:
            if sec not in sections:
                continue

            sentences = sections[sec].split(".")
            for sent in sentences:
                if any(k in sent.lower() for k in KEYWORDS):
                    clean = sent.strip()
                    if len(clean) > 30:
                        paper_findings.append(clean)

        findings[paper_id] = {
            "original_title": original_title,
            "key_findings": list(set(paper_findings))
        }

    out_path = os.path.join(ANALYSIS_OUT, "key_findings.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, indent=2)

    return findings


# ---------------- CROSS PAPER COMPARISON ---------------- #

def cross_paper_comparison():
    with open(
        os.path.join(ANALYSIS_OUT, "key_findings.json"),
        "r",
        encoding="utf-8"
    ) as f:
        findings = json.load(f)

    all_findings_lists = [
        set(v["key_findings"])
        for v in findings.values()
        if v["key_findings"]
    ]

    common = set.intersection(*all_findings_lists) if all_findings_lists else set()

    comparison = {
        "common_findings": list(common),
        "paper_wise_findings": findings
    }

    out_path = os.path.join(ANALYSIS_OUT, "cross_paper_comparison.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2)

    return comparison
