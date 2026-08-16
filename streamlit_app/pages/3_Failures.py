from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import client
import ui

st.set_page_config(page_title="Failures · DocLens", layout="wide")
ui.apply()
st.title("Failure analysis")
st.caption("Why a field was wrong — not just that it was wrong.")

try:
    reports = client.list_experiments()
except Exception as exc:
    st.error(f"Could not load experiment reports. ({exc})")
    st.stop()

if not reports:
    st.info("Run an experiment on the Evaluation page first.")
    st.stop()

selected_name = st.selectbox("Report", [item.get("filename") for item in reports])
report = next(item for item in reports if item.get("filename") == selected_name)

failures = [row for row in report["comparisons"] if not row["match"]]
st.metric("Mismatched fields", len(failures))

if not failures:
    st.success("No mismatches in this report.")
    st.stop()

frame = pd.DataFrame(
    [
        {
            "document": row["document_id"],
            "tag": row["record_key"],
            "field": row["field"],
            "predicted": row["predicted"],
            "ground_truth": row["ground_truth"],
            "failure_type": row["failure_type"],
            "confidence": row["confidence"],
        }
        for row in failures
    ]
)
st.dataframe(frame, width="stretch", hide_index=True)

labels = [
    f"{row['document_id']} · {row['record_key']} · {row['field']}"
    for row in failures
]
choice = st.selectbox("Inspect", labels)
row = failures[labels.index(choice)]

left, right = st.columns(2)
left.write("**Model output**")
left.code(str(row["predicted"]))
right.write("**Ground truth**")
right.code(str(row["ground_truth"]))

st.write(f"**Failure type:** `{row['failure_type']}`")
st.write(f"**Confidence:** {row['confidence']}")

source = row.get("source")
if source:
    try:
        pdf = client.download_demo(f"{row['document_id']}.pdf")
        png = client.render_page(
            pdf,
            f"{row['document_id']}.pdf",
            page=source["page"],
            bbox=list(source["bbox"]),
        )
        st.image(png, caption=f"{row['document_id']} page {source['page']}")
    except Exception as exc:
        st.warning(f"Could not render source highlight ({exc})")
        st.json(source)
else:
    st.info("No grounded bbox on this prediction — often a hallucination or missed table cell.")
