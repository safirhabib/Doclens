import streamlit as st

import ui

st.set_page_config(
    page_title="DocLens",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)
ui.apply()

st.title("DocLens")
st.subheader("Auditable AI document intelligence")

st.markdown(
    """
Upload a messy engineering document, extract structured equipment data, see **exactly
where each value came from**, score confidence, evaluate extraction quality, and run
an evidence-backed **compliance agent**.

This is not a chat-with-PDF demo. The interesting problem is reliability:

**Can you trust an extraction when the input is messy?**
"""
)

cols = st.columns(4)
cols[0].metric("Pipeline", "PDF → OCR/VLM → JSON")
cols[1].metric("Grounding", "page + bbox")
cols[2].metric("Eval", "field accuracy")
cols[3].metric("Agent", "deterministic checks")

st.markdown("### Demo path")
st.markdown(
    """
1. **Extract** — choose `challenge_messy.pdf`, run extraction, click **AHU-01** and check capacity is **25,000 CFM** (not 250 kW). Answers: `docs/ANSWER_KEY.md`.
2. **Evaluation** — run the heuristic strategy on the labeled corpus.
3. **Failures** — inspect mismatches vs ground truth.
4. **Compliance** — demo PDFs: G-01 is **450 kW** vs a **500 kW** minimum → fail.
"""
)

st.info(
    "Full walkthrough: `docs/USER_GUIDE.md`. "
    "One command: `streamlit run streamlit_app/Home.py` (uvicorn is optional). "
    "Heuristic works with no model key."
)
