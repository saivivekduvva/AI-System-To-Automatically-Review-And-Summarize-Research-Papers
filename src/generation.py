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


def generate_text(prompt, max_tokens=600, retries=3):
    """
    Safe Gemini text generation with retry and quota handling.
    Prevents application crashes due to rate limits.
    """
    for attempt in range(retries):
        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": max_tokens
                }
            )
            return response.text.strip()

        except ResourceExhausted:
            if attempt < retries - 1:
                time.sleep(5)  # wait before retry
            else:
                raise RuntimeError(
                    "Gemini API quota exceeded. Please wait or use a new API key."
                )


# --------------------------------------------------
# Load Milestone 2 Outputs
# --------------------------------------------------

def load_analysis_outputs():
    """
    Loads cross-paper comparison and key findings
    generated in Milestone 2.
    """
    with open("outputs/analysis/cross_paper_comparison.json", "r", encoding="utf-8") as f:
        cross_comparison = json.load(f)

    with open("outputs/analysis/key_findings.json", "r", encoding="utf-8") as f:
        key_findings = json.load(f)

    return cross_comparison, key_findings


# --------------------------------------------------
# Section Generators (Milestone 3 Core)
# --------------------------------------------------

def generate_abstract(key_findings):
    prompt = f"""
    Write a concise academic abstract (maximum 100 words)
    summarizing the following synthesized findings.

    Findings:
    {key_findings}
    """
    return generate_text(prompt, max_tokens=180)


def generate_methods(cross_comparison):
    prompt = f"""
    Compare and summarize the methodologies used across
    the reviewed papers. Focus on datasets, models,
    experimental design, and evaluation strategies.

    Data:
    {cross_comparison}
    """
    return generate_text(prompt)


def generate_results(key_findings):
    prompt = f"""
    Synthesize the results across all papers.
    Highlight common trends, major findings,
    and notable differences.

    Findings:
    {key_findings}
    """
    return generate_text(prompt)


def generate_references(paper_metadata):
    prompt = f"""
    Format the following paper metadata into
    APA-style references.

    Metadata:
    {paper_metadata}
    """
    return generate_text(prompt)


# --------------------------------------------------
# Save Generated Sections
# --------------------------------------------------

def save_outputs(abstract, methods, results, references):
    os.makedirs("outputs/sections", exist_ok=True)

    with open("outputs/sections/abstract.txt", "w", encoding="utf-8") as f:
        f.write(abstract)

    with open("outputs/sections/methods.txt", "w", encoding="utf-8") as f:
        f.write(methods)

    with open("outputs/sections/results.txt", "w", encoding="utf-8") as f:
        f.write(results)

    with open("outputs/sections/references.txt", "w", encoding="utf-8") as f:
        f.write(references)


# --------------------------------------------------
# Milestone 3 Pipeline Controller (FAIL-SAFE)
# --------------------------------------------------

def run_generation():
    """
    Executes Milestone 3 draft generation safely.
    Returns status for Streamlit UI handling.
    """
    try:
        cross_comparison, key_findings = load_analysis_outputs()

        abstract = generate_abstract(json.dumps(key_findings, indent=2))
        methods = generate_methods(json.dumps(cross_comparison, indent=2))
        results = generate_results(json.dumps(key_findings, indent=2))

        references = generate_references(
            cross_comparison.get("papers_metadata", [])
        )

        save_outputs(abstract, methods, results, references)

        return True, "Milestone 3 completed: Draft sections generated successfully."

    except RuntimeError as e:
        return False, str(e)


# --------------------------------------------------
# Entry Point (CLI use only)
# --------------------------------------------------

if __name__ == "__main__":
    success, message = run_generation()
    print(message)
