from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import client
import ui

st.set_page_config(page_title="Extract · DocLens", layout="wide")
ui.apply()
st.title("Extract")
st.caption("PDF → structured equipment JSON with field-level confidence and visual grounding.")

try:
    demos = client.list_demo_documents()
except Exception as exc:
    st.error(f"Could not load demo documents. Run `python scripts/generate_demo_docs.py`. ({exc})")
    st.stop()

strategy = st.sidebar.selectbox("Strategy", ["heuristic", "v1", "v2", "v3"], index=0)
model = st.sidebar.text_input("Model (optional)", value="")

demo_names = [item["filename"] for item in demos]
choice = st.selectbox("Demo document", ["(upload your own)"] + demo_names)
uploaded = st.file_uploader("Or upload a PDF", type=["pdf"])

pdf_bytes: bytes | None = None
filename = "document.pdf"
if uploaded is not None:
    pdf_bytes = uploaded.getvalue()
    filename = uploaded.name
elif choice != "(upload your own)":
    pdf_bytes = client.download_demo(choice)
    filename = choice

if st.button("Run extraction", type="primary", disabled=pdf_bytes is None):
    with st.spinner("Extracting…"):
        try:
            result = client.extract(pdf_bytes, filename, strategy, model or None)
        except Exception as exc:
            st.error(f"Extraction failed: {exc}")
            st.stop()
    st.session_state["extraction"] = result
    st.session_state["pdf_bytes"] = pdf_bytes
    st.session_state["pdf_name"] = filename

result = st.session_state.get("extraction")
pdf_bytes = st.session_state.get("pdf_bytes", pdf_bytes)
filename = st.session_state.get("pdf_name", filename)

if not result:
    st.stop()

meta = st.columns(5)
meta[0].metric("Strategy", result["strategy"])
meta[1].metric("Model", result["model"])
meta[2].metric("Latency", f"{result['latency_ms']:.0f} ms")
meta[3].metric("Pages", result["page_count"])
meta[4].metric("OCR pages", ", ".join(map(str, result["ocr_pages"])) or "none")

rows = []
for item in result["equipment"]:
    rows.append(
        {
            "tag": item["tag"]["value"],
            "type": item["type"]["value"],
            "quantity": item["quantity"]["value"],
            "capacity": item["capacity"]["value"],
            "manufacturer": (item.get("manufacturer") or {}).get("value"),
            "confidence": item["tag"]["confidence"],
            "page": (item["tag"].get("source") or {}).get("page"),
        }
    )
frame = pd.DataFrame(rows)
st.dataframe(frame, width="stretch", hide_index=True)

tags = [row["tag"] for row in rows if row["tag"]]
selected = st.selectbox("Highlight source for", tags) if tags else None

left, right = st.columns([1.1, 0.9])
with left:
    st.subheader("Grounded page")
    if selected:
        record = next(item for item in result["equipment"] if item["tag"]["value"] == selected)
        field_name = st.radio("Field", ["tag", "type", "quantity", "capacity", "manufacturer"], horizontal=True)
        field = record.get(field_name) or {}
        source = field.get("source")
        if source:
            png = client.render_page(
                pdf_bytes,
                filename,
                page=source["page"],
                bbox=list(source["bbox"]),
            )
            st.image(png, caption=f"{selected} · {field_name} · p.{source['page']}")
            st.json(source)
        else:
            st.warning("No bbox for this field (confidence was penalized).")
            png = client.render_page(pdf_bytes, filename, page=1)
            st.image(png)

with right:
    st.subheader("Structured record")
    if selected:
        record = next(item for item in result["equipment"] if item["tag"]["value"] == selected)
        st.json(record)
    with st.expander("Full extraction JSON"):
        st.json(result)
