import streamlit as st
import os
import json

# ----------------- IMPORT YOUR SRC MODULES ----------------- #
import retrieval as retrieval
import extraction as extraction
import generation as generation
import review as review

# ---------------- PAGE CONFIG & STYLING ---------------- #
st.set_page_config(page_title="Cloudy Reviewer", layout="wide", page_icon="☁️")

# Enhanced Cute, Chubby, and Blue UI Styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;600&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Quicksand', sans-serif;
        background: linear-gradient(135deg, #eef9ff 0%, #daefff 100%);
    }

    /* --- SIDEBAR ALIGNMENT & GLASS-MORPHISM --- */
    section[data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.4) !important;
        backdrop-filter: blur(12px) !important;
        border-right: 2px solid rgba(255, 255, 255, 0.5);
        padding: 2rem 1rem !important;
    }
    
    /* Sidebar widget spacing */
    div[data-testid="stSidebarNav"] + div {
        margin-top: -50px;
    }

    /* --- EXTRACTION PAGE & CARD STYLING --- */
    .extraction-card {
        background: white;
        padding: 25px;
        border-radius: 25px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.05);
        border: 2px solid #f0f9ff;
        margin-bottom: 20px;
    }

    /* --- CHUBBY BUTTONS --- */
    .stButton>button {
        border-radius: 30px !important;
        border: 2px solid #bae6fd !important;
        background-color: white !important;
        color: #0369a1 !important;
        font-weight: 600 !important;
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05) !important;
        width: 100%;
    }
    
    .stButton>button:hover {
        transform: translateY(-3px) scale(1.02);
        background-color: #f0f9ff !important;
        border-color: #7dd3fc !important;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1) !important;
    }

    /* Active Task Highlight */
    div[data-testid="column"] button[kind="primary"] {
        background: linear-gradient(45deg, #38bdf8, #60a5fa) !important;
        color: white !important;
        border: none !important;
    }

    /* Success/Alert boxes rounding */
    div[data-testid="stNotification"] {
        border-radius: 20px !important;
        border: none !important;
    }

    /* Slider styling */
    .stSlider [data-baseweb="slider"] {
        margin-bottom: 20px;
    }
    
    h1, h2, h3 {
        color: #075985 !important;
        font-weight: 700 !important;
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
    st.markdown("## ☁️ Settings")
    st.write("---")
    
    st.markdown("### ⚙️ Config")
    num_papers = st.slider("Download Limit", 1, 10, 3)
    
    st.write("---")
    
    pdf_path = "data/pdfs"
    if os.path.exists(pdf_path):
        files = [f for f in os.listdir(pdf_path) if f.endswith(".pdf")]
        if files:
            st.markdown("### 📚 Library")
            st.session_state.selected_paper = st.selectbox(
                "Active Document", 
                files,
                index=0,
                label_visibility="collapsed"
            )
            
            if st.session_state.selected_paper:
                st.success(f"Selected: {st.session_state.selected_paper}")
    
    st.markdown("##") # Spacer
    st.button("✨ Reset Pipeline", on_click=lambda: st.session_state.clear(), use_container_width=True)

# ---------------- TOP NAVIGATION ---------------- #
st.title("💠 AI Research Reviewer")
st.write("Let's help you process those papers with ease!")

nav_cols = st.columns(4)
nav_labels = ["🔍 Retrieval", "🧪 Extraction", "📝 Drafting", "✅ Review"]

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
    st.subheader("Step 1: Sourcing Papers")
    
    col_input, col_action = st.columns([4, 1])
    with col_input:
        topic = st.text_input("What are we looking for?", "Transformers in Healthcare")
    with col_action:
        st.write("##")
        start_search = st.button("Find Papers", use_container_width=True)

    if start_search:
        with st.status("Searching the clouds...", expanded=False) as status:
            retrieval.download_until_n_pdfs(topic, required=num_papers)
            status.update(label="Found them!", state="complete")
        st.session_state.task1_done = True
        st.rerun()
        
    if os.path.exists("data/pdfs"):
        all_files = [f for f in os.listdir("data/pdfs") if f.endswith(".pdf")]
        if all_files:
            st.info(f"✨ Found {len(all_files)} papers in your library.")
            for f in all_files:
                is_selected = f == st.session_state.selected_paper
                st.markdown(f"{'🔵' if is_selected else '⚪'} **{f}**")
            
            if st.button("Go to Extraction →", type="primary", use_container_width=True):
                st.session_state.task = "task2"
                st.rerun()

# ====================================================
# TASK 2: EXTRACTION
# ====================================================
elif st.session_state.task == "task2":
    if not st.session_state.selected_paper:
        st.warning("Pick a paper in the sidebar first! ☝️")
    else:
        # Heading Section
        st.markdown(f"### 🧪 Analyzing: `{st.session_state.selected_paper}`")
        
        # Action Bar
        col_btn, col_spacer = st.columns([1, 2])
        with col_btn:
            run_extract = st.button("Start Extraction 🚀")

        if run_extract:
            with st.spinner("Reading carefully..."):
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
            
            # --- REDESIGNED EXTRACTION UI ---
            col_main, col_side = st.columns([2, 1])
            
            with col_main:
                st.markdown('<div class="extraction-card">', unsafe_allow_html=True)
                st.markdown("#### 📋 Abstract Summary")
                st.write(p['abstract'])
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<div class="extraction-card">', unsafe_allow_html=True)
                st.markdown("#### 💡 Key Findings")
                for finding in p['key_findings']:
                    st.write(f"• {finding}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_side:
                st.markdown('<div class="extraction-card">', unsafe_allow_html=True)
                st.markdown("#### 🔍 Validation Check")
                st.json(p['validation'])
                st.markdown('</div>', unsafe_allow_html=True)
            
            if st.button("Go to Drafting →", type="primary", use_container_width=True):
                st.session_state.task = "task3"
                st.rerun()

# ====================================================
# TASK 3: DRAFTING
# ====================================================
elif st.session_state.task == "task3":
    if not st.session_state.task2_done:
        st.error("Extract the paper first! 🧪")
    else:
        st.subheader(f"Writing Draft for: {st.session_state.selected_paper}")
        if st.button("Write Draft ✍️", use_container_width=True):
            with st.spinner("Putting thoughts on paper..."):
                generation.generate_everything(st.session_state.current_profile)
                st.session_state.task3_done = True
        
        if st.session_state.task3_done:
            drafts = review.load_local_drafts()
            st.success("Draft is ready!")
            d_tabs = st.tabs([f"📖 {name}" for name in drafts.keys()])
            for i, (name, content) in enumerate(drafts.items()):
                d_tabs[i].markdown(content)
            
            if st.button("Go to Review →", type="primary", use_container_width=True):
                st.session_state.task = "task4"
                st.rerun()

# ====================================================
# TASK 4: REVIEW
# ====================================================
elif st.session_state.task == "task4":
    st.subheader(f"Polishing: {st.session_state.selected_paper}")
    if st.button("Final Critique 💎", use_container_width=True):
        with st.spinner("Making it perfect..."):
            review.run_milestone_4()
            st.session_state.task4_done = True
            
    if st.session_state.task4_done:
        with open("outputs/analysis/review_feedback.json", "r") as f:
            fb = json.load(f)
        
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("### 🎈 Reviewer Notes")
            st.info(fb.get("peer_review_notes"))
        with c2:
            st.markdown("### ✨ Final Report")
            st.markdown(fb.get("refined_draft"))
            st.download_button("Download Report 📥", fb.get("refined_draft"), file_name="final_review.md", use_container_width=True)