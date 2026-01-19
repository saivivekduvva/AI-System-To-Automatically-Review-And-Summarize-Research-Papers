import json
import os
from config import OUTPUT_DIR

SECTIONS_DIR = os.path.join(OUTPUT_DIR, "sections")
VALIDATION_OUT = os.path.join(OUTPUT_DIR, "validation")
os.makedirs(VALIDATION_OUT, exist_ok=True)

REQUIRED_SECTIONS = ["abstract", "methods", "results"]


def validate_extraction():
    input_file = os.path.join(SECTIONS_DIR, "all_sections.json")

    with open(input_file, "r", encoding="utf-8") as f:
        papers = json.load(f)

    report = {}

    for paper_id, paper_data in papers.items():
        sections = paper_data.get("sections", {})
        original_title = paper_data.get("original_title", paper_id)

        missing = []
        empty = []

        for sec in REQUIRED_SECTIONS:
            if sec not in sections:
                missing.append(sec)
            elif len(sections[sec].strip()) < 200:
                empty.append(sec)

        if not missing and not empty:
            report[paper_id] = {
                "original_title": original_title,
                "status": "VALID"
            }
        else:
            report[paper_id] = {
                "original_title": original_title,
                "status": "INVALID",
                "missing_sections": missing,
                "empty_sections": empty
            }

    out_path = os.path.join(VALIDATION_OUT, "validation_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report
