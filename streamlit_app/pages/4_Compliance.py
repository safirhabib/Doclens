from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import client
import ui

st.set_page_config(page_title="Compliance · DocLens", layout="wide")
ui.apply()
st.title("Compliance agent")
st.caption("Requirements → retrieval → extraction → deterministic comparison → evidence.")

strategy = st.sidebar.selectbox("Extraction strategy", ["heuristic", "v1", "v2", "v3"], index=0)
model = st.sidebar.text_input("Model (optional)", value="")

st.markdown(
    "Default demo: **Emergency generator ≥ 500 kW** vs scheduled **G-01 = 450 kW**."
)

use_demo = st.checkbox("Use demo PDFs", value=True)
req_file = st.file_uploader("Requirements PDF", type=["pdf"], disabled=use_demo)
sched_file = st.file_uploader("Equipment schedule PDF", type=["pdf"], disabled=use_demo)

req_bytes = req_name = sched_bytes = sched_name = None
if use_demo:
    req_bytes = client.download_demo("requirements.pdf")
    req_name = "requirements.pdf"
    sched_bytes = client.download_demo("generator_schedule.pdf")
    sched_name = "generator_schedule.pdf"
elif req_file and sched_file:
    req_bytes, req_name = req_file.getvalue(), req_file.name
    sched_bytes, sched_name = sched_file.getvalue(), sched_file.name

if st.button("Run compliance", type="primary", disabled=not (req_bytes and sched_bytes)):
    with st.spinner("Checking requirements against the schedule…"):
        try:
            report = client.compliance(
                req_bytes,
                req_name,
                sched_bytes,
                sched_name,
                strategy,
                model or None,
            )
        except Exception as exc:
            st.error(f"Compliance check failed: {exc}")
            st.stop()
    st.session_state["compliance"] = report
    st.session_state["sched_bytes"] = sched_bytes
    st.session_state["sched_name"] = sched_name
    st.session_state["req_bytes"] = req_bytes
    st.session_state["req_name"] = req_name

report = st.session_state.get("compliance")
if not report:
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Passed", report["passed"])
c2.metric("Needs review", report["needs_review"])
c3.metric("Failed", report["failed"])

status_color = {"pass": "green", "fail": "red", "needs_review": "orange"}

for finding in report["findings"]:
    result = finding["result"]
    title = finding["requirement"]["text"][:90]
    with st.expander(f"{result.upper()} · {title}", expanded=result != "pass"):
        st.markdown(finding["narrative"])
        st.write(
            f"**Detected:** `{finding['detected_tag']}` = `{finding['detected_value']}`  \n"
            f"**Confidence:** {finding['confidence']:.2f}"
        )
        st.write("Evidence chain")
        for step in finding["evidence_chain"]:
            st.markdown(f"- **{step['step']}** — {step['detail']}")
        source = None
        for step in reversed(finding["evidence_chain"]):
            if step.get("source"):
                source = step["source"]
                break
        if source and st.session_state.get("sched_bytes"):
            png = client.render_page(
                st.session_state["sched_bytes"],
                st.session_state["sched_name"],
                page=source["page"],
                bbox=list(source["bbox"]),
            )
            st.image(png, caption=f"Evidence · page {source['page']}")
