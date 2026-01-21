import streamlit as st
import os
import json

# ----------------- IMPORT YOUR SRC MODULES ----------------- #
import retrieval as retrieval
import extraction as extraction
import generation as generation
import review as review

# ---------------- PAGE CONFIG & STYLING ---------------- #
st.set_page_config(page_title="AI Research Reviewer", layout="wide", page_icon="🔬")

st.markdown("""
    <style>
    .stButton>button { border-radius: 8px; font-weight: bold; }
    .stExpander { border: 1px solid #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

# ---------------- SESSION STATE ---------------- #
if "task" not in st.session_state: st.session_state.task = "task1"
if "selected_paper" not in st.session_state: st.session_state.selected_paper = None
if "current_profile" not in st.session_state: st.session_state.current_profile = None

# Track Task Completion
for i in range(1, 5): 
    if f"task{i}_done" not in st.session_state: st.session_state[f"task{i}_done"] = False

# ---------------- SIDEBAR: SELECTION CONTROLLER ---------------- #
with st.sidebar:
    st.header("⚙️ Pipeline Settings")
    topic = st.text_input("Research Topic", "Transformers in Healthcare")
    num_papers = st.slider("Download Limit", 1, 5, 3)
    
    st.divider()
    
    # Selection Logic: Only active if PDFs exist
    pdf_path = "data/pdfs"
    if os.path.exists(pdf_path):
        files = [f for f in os.listdir(pdf_path) if f.endswith(".pdf")]
        if files:
            st.subheader("🎯 Active Selection")
            st.session_state.selected_paper = st.selectbox(
                "Choose Paper to Process:", 
                files,
                help="The drafting and review tasks will focus ONLY on this paper."
            )
            st.success(f"Focused on: **{st.session_state.selected_paper}**")
    
    if st.button("🔄 Reset Entire Pipeline"):
        st.session_state.clear()
        st.rerun()

# ---------------- TOP NAVIGATION (Matches your UI) ---------------- #
st.title("📄 AI Research Review System")
nav_cols = st.columns(4)
btn_labels = [("🔍", "Retrieval"), ("🧠", "Extraction"), ("✍️", "Drafting"), ("⚖️", "Review")]

for idx, (icon, name) in enumerate(btn_labels):
    t_num = idx + 1
    with nav_cols[idx]:
        is_active = st.session_state.task == f"task{t_num}"
        # Using red 'primary' color for active state as per your image
        btn_type = "primary" if is_active else "secondary"
        if st.button(f"{icon} {name}", key=f"nav_{t_num}", type=btn_type, use_container_width=True):
            st.session_state.task = f"task{t_num}"

st.divider()

# ====================================================
# TASK 1: RETRIEVAL (Multi-Paper Discovery)
# ====================================================
if st.session_state.task == "task1":
    st.subheader("📡 Paper Sourcing Pipeline")
    if st.button("🚀 Start Discovery", use_container_width=True):
        with st.status("Searching Semantic Scholar...", expanded=True) as status:
            retrieval.download_until_n_pdfs(topic, required=num_papers)
            status.update(label="Retrieval Complete!", state="complete")
        st.session_state.task1_done = True
        st.rerun()
        
    if os.path.exists("data/pdfs"):
        all_files = [f for f in os.listdir("data/pdfs") if f.endswith(".pdf")]
        st.info(f"Found {len(all_files)} papers. Please select one in the sidebar to proceed.")
        for f in all_files:
            icon = "✅" if f == st.session_state.selected_paper else "⚪"
            st.markdown(f"- {icon} {f}")

# ====================================================
# TASK 2: EXTRACTION (Single-Paper Focus)
# ====================================================
elif st.session_state.task == "task2":
    if not st.session_state.selected_paper:
        st.warning("⚠️ Please select a paper from the sidebar first.")
    else:
        st.subheader(f"🧠 Extracting: {st.session_state.selected_paper}")
        if st.button("▶ Run Single-Paper Analysis", use_container_width=True):
            with st.spinner("Executing extraction logic..."):
                extraction.extract_text_from_pdfs()
                
                # Filter for selected paper
                target_txt = st.session_state.selected_paper.replace(".pdf", ".txt")
                txt_path = os.path.join("data", "extracted", target_txt)
                
                with open(txt_path, "r", encoding="utf-8") as f:
                    raw = f.read()
                
                cleaned = extraction.clean_text(raw)
                sections = extraction.normalize_sections(extraction.split_sections(cleaned))
                profile = extraction.build_paper_profile(target_txt, sections)
                profile['validation'] = extraction.validate_sections(sections)
                
                st.session_state.current_profile = profile
                st.session_state.task2_done = True

        if st.session_state.task2_done:
            p = st.session_state.current_profile
            col_val1, col_val2 = st.columns([2, 1])
            with col_val1:
                st.markdown("### 📋 Semantic Profile")
                st.write("**Abstract:**", p['abstract'])
                st.write("**Findings:**", p['key_findings'])
            with col_val2:
                st.markdown("### ✅ Validation Report")
                st.json(p['validation'])

# ====================================================
# TASK 3: DRAFTING (Selected Paper Only)
# ====================================================
elif st.session_state.task == "task3":
    if not st.session_state.task2_done:
        st.error("Extract the selected paper first!")
    else:
        st.subheader(f"✍️ Drafting Synthesis for: {st.session_state.selected_paper}")
        if st.button("🪄 Generate Draft with Gemini", use_container_width=True):
            with st.spinner("Synthesizing content..."):
                # Pass the specific profile to the modified function
                generation.generate_everything(st.session_state.current_profile)
                st.session_state.task3_done = True
        
        if st.session_state.task3_done:
            drafts = review.load_local_drafts()
            st.success("Draft created successfully!")
            d_tabs = st.tabs(list(drafts.keys()))
            for i, (name, content) in enumerate(drafts.items()):
                d_tabs[i].markdown(content)

# ====================================================
# TASK 4: REVIEW & POLISH
# ====================================================
elif st.session_state.task == "task4":
    st.subheader(f"⚖️ Final Peer Review: {st.session_state.selected_paper}")
    if st.button("🔍 Critique & Refine", use_container_width=True):
        with st.spinner("Running AI Reviewer..."):
            review.run_milestone_4()
            st.session_state.task4_done = True
            
    if st.session_state.task4_done:
        with open("outputs/analysis/review_feedback.json", "r") as f:
            fb = json.load(f)
        
        c1, c2 = st.columns([1, 2])
        with c1:
            st.warning("### 🧐 Peer Reviewer Notes")
            st.write(fb.get("peer_review_notes"))
        with c2:
            st.success("### ✨ Refined synthesis")
            st.markdown(fb.get("refined_draft"))
            st.download_button("⬇️ Download Final Summary", fb.get("refined_draft"), file_name="final_review.md")