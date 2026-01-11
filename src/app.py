import streamlit as st
from retrieval import retrieve_and_filter_papers_stream

st.set_page_config(
    page_title="AI Research Paper Retrieval System",
    layout="wide"   # 🔥 THIS is the key change
)

st.title("📄 AI Research Paper Retrieval System")
st.caption("Milestone 1 – Automated Paper Discovery & Filtering")

# Optional: constrain header but not content
header_col, spacer, content_col = st.columns([1, 0.1, 2])

with header_col:
    topic = st.text_input(
        "Enter Research Topic",
        placeholder="e.g. NLP, Transformers, LLMs"
    )
    search_clicked = st.button("🔍 Search & Download Papers")

with content_col:
    if search_clicked:
        if not topic.strip():
            st.warning("Please enter a research topic.")
        else:
            log_container = st.container()
            st.divider()

            accepted = []
            rejected = []

            with st.spinner("Processing papers one by one..."):
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

            # Final grouped output
            result_left, result_right = st.columns(2)

            with result_left:
                st.subheader("✅ Accepted Papers")
                for title in accepted:
                    st.write("•", title)

            with result_right:
                st.subheader("❌ Rejected Papers")
                for title, reason in rejected:
                    st.write(f"• {title} — *{reason}*")

            st.success(f"Finished: {len(accepted)} valid papers downloaded")
