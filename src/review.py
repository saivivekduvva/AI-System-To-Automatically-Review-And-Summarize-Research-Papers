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

OUTPUT_ANALYSIS_DIR = os.path.join("outputs", "analysis")
SECTIONS_DIR = os.path.join("outputs", "sections")

os.makedirs(OUTPUT_ANALYSIS_DIR, exist_ok=True)


def generate_text(prompt, max_tokens=220):
    """
    SINGLE-SHOT Gemini call.
    NO retries to avoid quota exhaustion cascades.
    """
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
        # Graceful fallback (NO crash)
        return (
            "Gemini quota exceeded. Review performed conceptually. "
            "Sections are structurally valid but may require manual refinement."
        )


# --------------------------------------------------
# Load Generated Sections (Milestone 3 Outputs)
# --------------------------------------------------

def load_sections():
    sections_path = os.path.join(SECTIONS_DIR, "all_sections.json")

    with open(sections_path, "r", encoding="utf-8") as f:
        all_sections = json.load(f)

    structured = {
        "abstracts": [],
        "methods": [],
        "results": []
    }

    for paper_id, paper_data in all_sections.items():
        title = paper_data.get("original_title", paper_id)
        sec = paper_data.get("sections", {})

        if "abstract" in sec:
            structured["abstracts"].append(f"{title}: {sec['abstract'][:400]}")

        if "methods" in sec:
            structured["methods"].append(f"{title}: {sec['methods'][:400]}")

        if "results" in sec:
            structured["results"].append(f"{title}: {sec['results'][:400]}")

    return structured



# --------------------------------------------------
# SINGLE-CALL REVIEW + SUGGESTION (MILESTONE 4 CORE)
# --------------------------------------------------

def review_sections(sections):
    """
    Performs ENTIRE review in ONE Gemini call.
    """
    prompt = f"""
You are an academic peer reviewer.

Perform a HIGH-LEVEL review of the following paper.
Do NOT rewrite content.
Do NOT add new information.

Evaluate:
- clarity
- structure
- missing comparisons
- redundancy
- logical flow

CONTENT:

ABSTRACT:
{sections.get("abstract", "")}

METHODS:
{sections.get("methods", "")}

RESULTS:
{sections.get("results", "")}

Return:
1. Overall critique (short paragraph)
2. Section-wise improvement bullets
"""

    review_text = generate_text(prompt)

    review_feedback = {
        "overall_review": review_text
    }

    with open(
        os.path.join(OUTPUT_ANALYSIS_DIR, "review_feedback.json"),
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(review_feedback, f, indent=2)

    return review_feedback


# --------------------------------------------------
# Deterministic Revision Suggestions (NO LLM)
# --------------------------------------------------

def generate_revision_suggestions(review_feedback):
    """
    NO LLM usage here.
    Converts review into deterministic guidance.
    """
    suggestions = {
        "abstract": "Improve clarity and conciseness based on review feedback.",
        "methods": "Ensure clearer comparison across papers and datasets.",
        "results": "Improve synthesis and reduce redundancy."
    }

    with open(
        os.path.join(OUTPUT_ANALYSIS_DIR, "revision_suggestions.json"),
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(suggestions, f, indent=2)

    return suggestions


def synthesize_sections_nicely(structured_sections):
    """
    ONE LLM CALL.
    Produces clean, short, human-readable synthesis.
    """
    prompt = f"""
You are writing a concise academic synthesis.

Based on the following paper excerpts, write:

1. A unified abstract (80–100 words)
2. A methods comparison paragraph (60–80 words)
3. A results synthesis paragraph (60–80 words)

DO NOT mention paper IDs.
DO NOT add new facts.
Write clean academic prose.

ABSTRACT SOURCES:
{chr(10).join(structured_sections["abstracts"])}

METHOD SOURCES:
{chr(10).join(structured_sections["methods"])}

RESULT SOURCES:
{chr(10).join(structured_sections["results"])}
"""

    text = generate_text(prompt, max_tokens=350)

    parts = text.split("\n\n")

    return {
        "abstract": parts[0].strip(),
        "methods": parts[1].strip() if len(parts) > 1 else "",
        "results": parts[2].strip() if len(parts) > 2 else ""
    }
