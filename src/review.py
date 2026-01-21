import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# --------------------------------------------------
# Setup
# --------------------------------------------------
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use 1.5-flash for stability
model = genai.GenerativeModel("gemini-flash-lite-latest")

# Define paths (matching your folder structure)
DRAFTS_DIR = os.path.join("outputs", "drafts")
ANALYSIS_DIR = os.path.join("outputs", "analysis")
os.makedirs(ANALYSIS_DIR, exist_ok=True)

def load_local_drafts():
    """Reads the .txt files generated in Milestone 3."""
    sections = {}
    for part in ["abstract", "methodology", "results"]:
        path = os.path.join(DRAFTS_DIR, f"{part}.txt")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                sections[part] = f.read().strip()
        else:
            sections[part] = "[Missing Section]"
    return sections

def run_milestone_4():
    # 1. Load the generated text
    drafts = load_local_drafts()
    
    # 2. Construct a single optimized prompt
    # This combines Review + Synthesis to save API calls
    prompt = f"""
    You are an academic peer reviewer and editor. 
    Below is a draft for a single paper. Perform two tasks:
    
    TASK 1: CRITICAL REVIEW
    Evaluate clarity, structure, and logical flow. Provide 3-4 bullet points.
    
    TASK 2: REFINED SYNTHESIS
    Rewrite the Abstract, Methodology, and Results into a polished, professional version.
    Use '###SPLIT###' between Task 1 and Task 2.
    Use '---' between the refined sections in Task 2.

    DRAFT CONTENT:
    ABSTRACT: {drafts['abstract']}
    METHODOLOGY: {drafts['methodology']}
    RESULTS: {drafts['results']}
    """

    print("🚀 Running combined Review and Synthesis...")
    try:
        # Increased tokens to allow for both the review and the new draft
        response = model.generate_content(
            prompt,
            generation_config={"max_output_tokens": 1500, "temperature": 0.2}
        )
        
        full_text = response.text
        
        # 3. Save the full raw analysis for reference
        with open(os.path.join(ANALYSIS_DIR, "full_review.txt"), "w", encoding="utf-8") as f:
            f.write(full_text)

        # 4. Split and save the feedback separately (JSON)
        if "###SPLIT###" in full_text:
            review_part, synthesis_part = full_text.split("###SPLIT###")
        else:
            review_part, synthesis_part = full_text, "Synthesis failed to split."

        feedback = {
            "peer_review_notes": review_part.strip(),
            "refined_draft": synthesis_part.strip()
        }

        with open(os.path.join(ANALYSIS_DIR, "review_feedback.json"), "w", encoding="utf-8") as f:
            json.dump(feedback, f, indent=4)

        print(f"✅ Milestone 4 Complete. Feedback saved to: {ANALYSIS_DIR}")

    except Exception as e:
        print(f"❌ Error during review: {e}")

if __name__ == "__main__":
    run_milestone_4()