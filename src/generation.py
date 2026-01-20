import os
import json
import time
from dotenv import load_dotenv
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

# --------------------------------------------------
# Environment & Gemini Configuration
# --------------------------------------------------

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-flash-lite-latest")


def generate_text(prompt, max_tokens=300, retries=3):
    """
    SINGLE Gemini wrapper.
    Used only ONCE in Milestone 3.
    """
    for attempt in range(retries):
        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": max_tokens
                }
            )
            return response.text.strip()

        except ResourceExhausted:
            if attempt < retries - 1:
                time.sleep(5)
            else:
                raise RuntimeError("Gemini API quota exceeded.")


# --------------------------------------------------
# Load Milestone 2 Outputs
# --------------------------------------------------

def load_analysis_outputs():
    with open("outputs/analysis/cross_paper_comparison.json", "r", encoding="utf-8") as f:
        cross_comparison = json.load(f)

    with open("outputs/analysis/key_findings.json", "r", encoding="utf-8") as f:
        key_findings = json.load(f)

    return cross_comparison, key_findings


# --------------------------------------------------
# Deterministic Draft Construction (NO LLM)
# --------------------------------------------------

def build_abstract_draft(key_findings):
    return "\n".join(
        f"- {paper}: {finding}"
        for paper, finding in key_findings.items()
    )


def build_methods_draft(cross_comparison):
    lines = []

    for paper, details in cross_comparison.get("method_comparison", {}).items():
        dataset = details.get("dataset", "N/A")
        model_name = details.get("model", "N/A")
        metric = details.get("evaluation", "N/A")

        lines.append(
            f"{paper} uses {model_name} on {dataset} and evaluates performance using {metric}."
        )

    return " ".join(lines)


def build_results_draft(key_findings):
    return " ".join(
        f"{paper} reports that {finding}."
        for paper, finding in key_findings.items()
    )


# --------------------------------------------------
# ONE-CALL POLISHING (MAJOR QUOTA REDUCTION)
# --------------------------------------------------

def polish_all_sections_once(abstract, methods, results):
    """
    Uses ONLY ONE Gemini call for all sections.
    """
    prompt = f"""
Lightly polish the following academic sections.

Rules:
- Do NOT add new information
- Preserve factual meaning
- Improve clarity and academic tone only
- Keep abstract under 100 words

ABSTRACT:
{abstract}

METHODS:
{methods}

RESULTS:
{results}

Return in the SAME ORDER, separated by '---'.
"""

    response = generate_text(prompt, max_tokens=350)

    parts = response.split("---")

    return {
        "abstract": parts[0].strip() if len(parts) > 0 else abstract,
        "methods": parts[1].strip() if len(parts) > 1 else methods,
        "results": parts[2].strip() if len(parts) > 2 else results,
    }


# --------------------------------------------------
# Save Generated Sections
# --------------------------------------------------

def save_outputs(abstract, methods, results):
    os.makedirs("outputs/sections", exist_ok=True)

    with open("outputs/sections/abstract.txt", "w", encoding="utf-8") as f:
        f.write(abstract)

    with open("outputs/sections/methods.txt", "w", encoding="utf-8") as f:
        f.write(methods)

    with open("outputs/sections/results.txt", "w", encoding="utf-8") as f:
        f.write(results)

    with open("outputs/sections/references.txt", "w", encoding="utf-8") as f:
        f.write("References derived from provided paper metadata.")


# --------------------------------------------------
# Milestone 3 Pipeline Controller (FINAL)
# --------------------------------------------------

def run_generation():
    """
    Milestone 3:
    - Deterministic draft creation
    - ONLY ONE Gemini call total
    """
    try:
        cross_comparison, key_findings = load_analysis_outputs()

        # Step 1: Deterministic drafts
        abstract_draft = build_abstract_draft(key_findings)
        methods_draft = build_methods_draft(cross_comparison)
        results_draft = build_results_draft(key_findings)

        # Step 2: ONE Gemini call
        polished = polish_all_sections_once(
            abstract_draft,
            methods_draft,
            results_draft
        )

        save_outputs(
            polished["abstract"],
            polished["methods"],
            polished["results"]
        )

        return True, "Milestone 3 completed (quota-safe)."

    except RuntimeError as e:
        return False, str(e)


# --------------------------------------------------
# Entry Point
# --------------------------------------------------

if __name__ == "__main__":
    success, message = run_generation()
    print(message)


# ==================================================
# Milestone 4 — Final Assembly (NO LLM HERE)
# ==================================================

def revise_sections(sections, revision_suggestions):
    """
    NO-LLM revision.
    Applies suggestions as annotations only.
    """
    refined = {}

    for section, text in sections.items():
        notes = revision_suggestions.get(section, "")
        refined[section] = f"{text}\n\n[Revision Notes]\n{notes}"

    return refined


def assemble_final_paper(refined_sections):
    """
    Combines sections into final paper.
    References are added deterministically to avoid file dependency issues.
    """

    references_text = (
        "References\n"
        "----------\n"
        "The references used in this review correspond to the research papers "
        "retrieved and analyzed in Task 1 and Task 2 of the system. "
        "Full bibliographic details can be reconstructed from the "
        "cross_paper_comparison and paper metadata outputs."
    )

    final_paper = f"""
ABSTRACT
--------
{refined_sections.get("abstract", "")}

METHODS COMPARISON
------------------
{refined_sections.get("methods", "")}

RESULTS SYNTHESIS
-----------------
{refined_sections.get("results", "")}

{references_text}
"""

    os.makedirs("outputs", exist_ok=True)
    with open("outputs/final_paper.txt", "w", encoding="utf-8") as f:
        f.write(final_paper)

    return final_paper
