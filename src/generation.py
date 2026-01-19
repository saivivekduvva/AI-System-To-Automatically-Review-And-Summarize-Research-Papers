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
    Lightweight Gemini usage for polishing / rewriting only.
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
                raise RuntimeError(
                    "Gemini API quota exceeded. Please wait or use a new API key."
                )


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
    bullets = []
    for paper, findings in key_findings.items():
        bullets.append(f"- {paper}: {findings}")

    return "\n".join(bullets)


def build_methods_draft(cross_comparison):
    lines = []

    for paper, details in cross_comparison.get("method_comparison", {}).items():
        dataset = details.get("dataset", "N/A")
        model = details.get("model", "N/A")
        metric = details.get("evaluation", "N/A")

        lines.append(
            f"{paper} uses {model} on {dataset} and evaluates performance using {metric}."
        )

    return " ".join(lines)


def build_results_draft(key_findings):
    results = []

    for paper, finding in key_findings.items():
        results.append(f"{paper} reports that {finding}")

    return " ".join(results)


# --------------------------------------------------
# Light LLM Polishing (LOW TOKEN USAGE)
# --------------------------------------------------

def polish_text(text, instruction, max_tokens=200):
    prompt = f"""
    Improve the academic clarity and flow of the following text.
    Do NOT add new information.
    Keep it concise and formal.

    Instruction:
    {instruction}

    Text:
    {text}
    """
    return generate_text(prompt, max_tokens=max_tokens)


def generate_references(paper_metadata):
    prompt = f"""
    Format the following paper metadata into APA-style references.
    Do not add new references.

    Metadata:
    {paper_metadata}
    """
    return generate_text(prompt, max_tokens=250)


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
# Milestone 3 Pipeline Controller (OPTIMIZED)
# --------------------------------------------------

def run_generation():
    """
    Milestone 3:
    - Deterministic draft construction
    - Minimal LLM usage for polishing only
    """
    try:
        cross_comparison, key_findings = load_analysis_outputs()

        # Step 1: Build drafts WITHOUT LLM
        abstract_draft = build_abstract_draft(key_findings)
        methods_draft = build_methods_draft(cross_comparison)
        results_draft = build_results_draft(key_findings)

        # Step 2: Light polishing with Gemini
        abstract = polish_text(
            abstract_draft,
            "Condense into a maximum 100-word academic abstract.",
            max_tokens=180
        )

        methods = polish_text(
            methods_draft,
            "Ensure clear academic comparison of methodologies."
        )

        results = polish_text(
            results_draft,
            "Ensure clarity and coherence in results synthesis."
        )

        references = generate_references(
            cross_comparison.get("papers_metadata", [])
        )

        save_outputs(abstract, methods, results, references)

        return True, "Milestone 3 completed with optimized LLM usage."

    except RuntimeError as e:
        return False, str(e)


# --------------------------------------------------
# Entry Point
# --------------------------------------------------

if __name__ == "__main__":
    success, message = run_generation()
    print(message)
