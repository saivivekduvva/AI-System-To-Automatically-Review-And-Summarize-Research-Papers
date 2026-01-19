import streamlit as st

# ---------------- MILESTONE 1 ---------------- #
from retrieval import retrieve_and_filter_papers_stream

# ---------------- MILESTONE 2 ---------------- #
from extraction import extract_text_from_pdfs, extract_sections_from_text
from analysis import extract_key_findings, cross_paper_comparison
from validation import validate_extraction

# ---------------- PAGE CONFIG ---------------- #

st.set_page_config(
    page_title="AI Research Paper Review System",
    layout="wide"
)

st.title("📄 AI Research Paper Review System")
st.caption("Task-driven research paper processing pipeline")

st.divider()

# ---------------- SESSION STATE INIT ---------------- #

if "task" not in st.session_state:
    st.session_state.task = None

if "task1_done" not in st.session_state:
    st.session_state.task1_done = False

# ====================================================
# 🧭 TASK NAVIGATION
# ====================================================

st.subheader("🧭 Project Tasks")

nav_col1, nav_col2 = st.columns(2)

with nav_col1:
    if st.button("🔹 Task 1: Paper Retrieval", use_container_width=True):
        st.session_state.task = "task1"

with nav_col2:
    if st.button("🔹 Task 2: Extraction & Analysis", use_container_width=True):
        if not st.session_state.task1_done:
            st.error("❌ Task 1 must be completed before starting Task 2.")
        else:
            st.session_state.task = "task2"

st.divider()

# ====================================================
# 🟢 TASK 1 PAGE — PAPER RETRIEVAL
# ====================================================

if st.session_state.task == "task1":

    st.subheader("🔍 Task 1: Automated Paper Discovery & Filtering")

    topic = st.text_input(
        "Enter Research Topic",
        placeholder="e.g. NLP, Transformers, Large Language Models"
    )

    search_clicked = st.button("🔍 Search & Download Papers")

    if search_clicked:
        if not topic.strip():
            st.warning("Please enter a research topic.")
        else:
            log_container = st.container()
            accepted, rejected = [], []

            with st.spinner("Searching, filtering, and downloading papers..."):
                for idx, title, status, reason in retrieve_and_filter_papers_stream(topic):

                    if status == "accepted":
                        accepted.append(title)
                        log_container.success(
                            f"Paper {idx}: {title} — Downloaded"
                        )
                    else:
                        rejected.append((title, reason))
                        log_container.error(
                            f"Paper {idx}: {title} — {reason}"
                        )

            st.divider()

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### ✅ Accepted Papers")
                for t in accepted:
                    st.write("•", t)

            with col2:
                st.markdown("### ❌ Rejected Papers")
                for t, r in rejected:
                    st.write(f"• {t} — *{r}*")

            if accepted:
                st.session_state.task1_done = True

                st.success(
                    f"Task 1 completed successfully. {len(accepted)} paper(s) downloaded."
                )

                # 👉 Proceed to Task 2
                if st.button("➡️ Proceed to Task 2: Extraction & Analysis"):
                    st.session_state.task = "task2"

            else:
                st.warning("No valid papers downloaded. Task 1 not completed.")

# ====================================================
# 🟣 TASK 2 PAGE — EXTRACTION & ANALYSIS
# ====================================================

elif st.session_state.task == "task2":

    st.subheader("🧠 Task 2: Text Extraction, Analysis & Validation")

    st.info("This task processes the papers downloaded in Task 1.")

    run_task2 = st.button("▶ Run Extraction & Analysis")

    if run_task2:
        with st.spinner("Running Milestone 2 pipeline..."):
            extract_text_from_pdfs()
            extract_sections_from_text()
            extract_key_findings()
            cross_paper_comparison()
            validate_extraction()

        st.success("✅ Task 2 completed successfully.")

        st.markdown("### 📂 Generated Outputs")
        st.write("• Section-wise extracted text")
        st.write("• Key findings per paper")
        st.write("• Cross-paper comparison")
        st.write("• Validation report")