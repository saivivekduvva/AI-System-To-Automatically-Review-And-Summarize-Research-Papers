import streamlit as st
import os
import json

# ----------------- IMPORT YOUR SRC MODULES ----------------- #
import retrieval as retrieval
import extraction as extraction
import generation as generation
import review as review

# ---------------- PAGE CONFIG & STYLING ---------------- #
st.set_page_config(page_title="AI Research Reviewer", layout="wide", page_icon="📄")

# Professional UI Styling
st.markdown("""
    <style>
    /* Main Button Styling */
    .stButton>button {
        border-radius: 4px;
        font-weight: 500;
        height: 3em;
        transition: all 0.3s ease;
    }
    
    /* Active Task Highlight */
    div[data-testid="column"] button[kind="primary"] {
        background-color: #4F46E5 !important;
        border-color: #4F46E5 !important;
        color: white !important;
    }
    
    /* Secondary/Normal Button Hover */
    div[data-testid="column"] button[kind="secondary"]:hover {
        border-color: #4F46E5 !important;
        color: #4F46E5 !important;
    }

    /* Sidebar Clean-up */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Remove unnecessary padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------- SESSION STATE ---------------- #
if "task" not in st.session_state: st.session_state.task = "task1"
if "selected_paper" not in st.session_state: st.session_state.selected_paper = None
if "current_profile" not in st.session_state: st.session_state.current_profile = None

for i in range(1, 5): 
    if f"task{i}_done" not in st.session_state: st.session_state[f"task{i}_done"] = False

# ---------------- SIDEBAR: CONTROL PANEL ---------------- #
with st.sidebar:
    st.title("Control Panel")
    st.markdown("---")
    
    # MOVED: Download Limit is now in the sidebar
    st.subheader("Configuration")
    num_papers = st.slider("Download Limit", 1, 10, 3)
    
    st.markdown("---")
    
    # Active Selection Logic
    pdf_path = "data/pdfs"
    if os.path.exists(pdf_path):
        files = [f for f in os.listdir(pdf_path) if f.endswith(".pdf")]
        if files:
            st.subheader("Selection")
            st.session_state.selected_paper = st.selectbox(
                "Active Paper", 
                files,
                index=0,
                help="Drafting and review will focus on this file."
            )
            
            # Status Indicator
            if st.session_state.selected_paper:
                st.info(f"Ready: {st.session_state.selected_paper}")
    
    st.button("Reset Pipeline", on_click=lambda: st.session_state.clear(), use_container_width=True)

# ---------------- TOP NAVIGATION ---------------- #
st.title("AI Research Review System")

# Clean Navigation Bar
nav_cols = st.columns(4)
nav_labels = ["Retrieval", "Extraction", "Drafting", "Review"]

for idx, name in enumerate(nav_labels):
    t_num = idx + 1
    with nav_cols[idx]:
        is_active = (st.session_state.task == f"task{t_num}")
        if st.button(name, key=f"nav_{t_num}", type="primary" if is_active else "secondary", use_container_width=True):
            st.session_state.task = f"task{t_num}"
            st.rerun()

st.markdown("---")

# ====================================================
# TASK 1: RETRIEVAL
# ====================================================
if st.session_state.task == "task1":
    st.subheader("Sourcing Pipeline")
    
    col_input, col_action = st.columns([4, 1])
    with col_input:
        topic = st.text_input("Research Topic", "Transformers in Healthcare", label_visibility="collapsed")
    with col_action:
        start_search = st.button("Start Discovery", use_container_width=True)

    if start_search:
        with st.status("Searching Semantic Scholar...", expanded=False) as status:
            retrieval.download_until_n_pdfs(topic, required=num_papers)
            status.update(label="Retrieval Complete", state="complete")
        st.session_state.task1_done = True
        st.rerun()
        
    if os.path.exists("data/pdfs"):
        all_files = [f for f in os.listdir("data/pdfs") if f.endswith(".pdf")]
        if all_files:
            st.write(f"**Found {len(all_files)} papers.** Select your target file in the sidebar.")
            
            # Clean list display
            for f in all_files:
                is_selected = f == st.session_state.selected_paper
                label = f"✓ {f}" if is_selected else f"  {f}"
                st.text(label)
            
            if st.button("Proceed to Extraction", type="primary", use_container_width=True):
                st.session_state.task = "task2"
                st.rerun()

# ====================================================
# TASK 2: EXTRACTION
# ====================================================
elif st.session_state.task == "task2":
    if not st.session_state.selected_paper:
        st.warning("Please select a paper from the sidebar to continue.")
    else:
        st.subheader(f"Extracting: {st.session_state.selected_paper}")
        if st.button("Run Analysis", use_container_width=True):
            with st.spinner("Processing document..."):
                extraction.extract_text_from_pdfs()
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
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown("### Profile Summary")
                st.write("**Abstract:**", p['abstract'])
                st.write("**Findings:**", p['key_findings'])
            with c2:
                st.markdown("### Validation")
                st.json(p['validation'])
            
            if st.button("Proceed to Drafting", type="primary", use_container_width=True):
                st.session_state.task = "task3"
                st.rerun()

# ====================================================
# TASK 3: DRAFTING
# ====================================================
elif st.session_state.task == "task3":
    if not st.session_state.task2_done:
        st.error("Please complete the extraction step first.")
    else:
        st.subheader(f"Drafting: {st.session_state.selected_paper}")
        if st.button("Generate Draft", use_container_width=True):
            with st.spinner("Generating synthesis..."):
                generation.generate_everything(st.session_state.current_profile)
                st.session_state.task3_done = True
        
        if st.session_state.task3_done:
            drafts = review.load_local_drafts()
            st.success("Draft generated.")
            d_tabs = st.tabs(list(drafts.keys()))
            for i, (name, content) in enumerate(drafts.items()):
                d_tabs[i].markdown(content)
            
            if st.button("Proceed to Review", type="primary", use_container_width=True):
                st.session_state.task = "task4"
                st.rerun()

# ====================================================
# TASK 4: REVIEW
# ====================================================
elif st.session_state.task == "task4":
    st.subheader(f"Final Review: {st.session_state.selected_paper}")
    if st.button("Critique and Refine", use_container_width=True):
        with st.spinner("Reviewing draft..."):
            review.run_milestone_4()
            st.session_state.task4_done = True
            
    if st.session_state.task4_done:
        with open("outputs/analysis/review_feedback.json", "r") as f:
            fb = json.load(f)
        
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("### Reviewer Notes")
            st.info(fb.get("peer_review_notes"))
        with c2:
            st.markdown("### Refined Synthesis")
            st.markdown(fb.get("refined_draft"))
            st.download_button("Download Final Report", fb.get("refined_draft"), file_name="final_review.md")