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


# ==================================================
# Milestone 4 — Review & Refinement Validation
# ==================================================

def validate_milestone_4():
    """
    Validates completion of Milestone 4 pipeline:
    - Review feedback generated
    - Revision suggestions generated
    - Refined sections created
    - Final paper assembled
    """

    report = {
        "review_feedback_exists": os.path.exists(
            os.path.join(OUTPUT_DIR, "analysis", "review_feedback.json")
        ),
        "revision_suggestions_exists": os.path.exists(
            os.path.join(OUTPUT_DIR, "analysis", "revision_suggestions.json")
        ),
        "refined_sections": {
            "abstract_v2": os.path.exists(os.path.join(SECTIONS_DIR, "abstract_v2.txt")),
            "methods_v2": os.path.exists(os.path.join(SECTIONS_DIR, "methods_v2.txt")),
            "results_v2": os.path.exists(os.path.join(SECTIONS_DIR, "results_v2.txt")),
        },
        "final_paper_exists": os.path.exists(
            os.path.join(OUTPUT_DIR, "final_paper.txt")
        ),
    }

    report["status"] = (
        "VALID"
        if all(report["refined_sections"].values())
        and report["review_feedback_exists"]
        and report["revision_suggestions_exists"]
        and report["final_paper_exists"]
        else "INCOMPLETE"
    )

    out_path = os.path.join(VALIDATION_OUT, "milestone4_validation.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report
