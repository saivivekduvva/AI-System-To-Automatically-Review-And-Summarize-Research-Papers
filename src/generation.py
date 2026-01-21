import os
import json
import time
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Using gemini-1.5-flash for the best balance of speed and free-tier quota
model = genai.GenerativeModel(
    model_name="gemini-flash-lite-latest",
    system_instruction="You are an academic writing assistant. Output the requested sections clearly. Use '###SECTION_BREAK###' as a delimiter."
)

INPUT_PATH = os.path.join("data", "analysis", "paper_profiles.json")
OUTPUT_DIR = os.path.join("outputs", "drafts")
os.makedirs(OUTPUT_DIR, exist_ok=True)
# In src/generation.py

def generate_everything(specific_profile=None):
    # If no profile is passed, fallback to the JSON file (original behavior)
    if specific_profile is None:
        with open(INPUT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            paper = data[0] if isinstance(data, list) else data
    else:
        paper = specific_profile

    p_id = paper.get("paper_id", "N/A")
    abstract_ctx = paper.get('abstract', '')[:1500] 
    method_ctx = paper.get('methodology', '')[:1500]
    findings_ctx = paper.get('key_findings', [])

    # ... (rest of your prompt logic stays the same)
    content = (
        f"Paper ID: {p_id}\n\n"
        f"ABSTRACT CONTENT:\n{abstract_ctx}\n\n"
        f"METHODOLOGY CONTENT:\n{method_ctx}\n\n"
        f"FINDINGS:\n{findings_ctx}"
    )

    prompt = f"""
    Using the provided data, generate these 4 comprehensive sections. 
    Separate them using the exact string '###SECTION_BREAK###'.

    1. A formal Academic Abstract (around 150-200 words).
    2. A Detailed Methodology Analysis focusing on the technical setup.
    3. A Results & Discussion summary based on the findings.
    4. A complete APA-style Citation.

    Paper Data:
    {content}
    """

    print(f"🚀 Generating expanded content for {p_id}...")
    try:
        # 2. SLIGHTLY INCREASED OUTPUT (Max 2000 tokens)
        response = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": 2000, 
                "temperature": 0.25
            }
        )
        
        # 3. Local processing
        sections = response.text.split("###SECTION_BREAK###")
        filenames = ["abstract.txt", "methodology.txt", "results.txt", "references.txt"]

        for i, text in enumerate(sections):
            if i < len(filenames):
                with open(os.path.join(OUTPUT_DIR, filenames[i]), "w", encoding="utf-8") as f:
                    f.write(text.strip())
        
        print(f"✅ All files saved in: {OUTPUT_DIR}")

    except Exception as e:
        if "429" in str(e):
            print("❌ Rate limit hit! Wait 60 seconds and try again.")
        else:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    generate_everything()