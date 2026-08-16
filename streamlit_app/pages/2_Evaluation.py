from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import client
import ui

st.set_page_config(page_title="Evaluation · DocLens", layout="wide")
ui.apply()
st.title("Evaluation laboratory")
st.caption("Ground-truth field accuracy, latency, and strategy comparison.")

try:
    reports = client.list_experiments()
except Exception as exc:
    st.error(f"Could not load experiment reports. ({exc})")
    st.stop()

run_col, model_col = st.columns([1, 1])
strategy = run_col.selectbox("Run strategy", ["heuristic", "v1", "v2", "v3"])
model = model_col.text_input("Model (v1/v2/v3)", value="")
log_mlflow = st.checkbox("Log to MLflow", value=False)

if st.button("Run experiment", type="primary"):
    with st.spinner("Evaluating the demo corpus…"):
        chosen_model = None if strategy == "heuristic" else (model.strip() or None)
        try:
            report = client.evaluate(strategy, chosen_model, log_mlflow)
        except Exception as exc:
            st.error(f"Evaluation failed: {exc}")
            st.stop()
    st.success(f"{strategy} accuracy: {report['accuracy']}%")
    reports = client.list_experiments()

if not reports:
    st.info("No saved experiments yet. Run the heuristic strategy to generate a baseline without an API key.")
    st.stop()

summaries = []
for report in reports:
    summaries.append(
        {
            "file": report.get("filename"),
            "strategy": report["strategy"],
            "model": report["model"],
            "accuracy": report["accuracy"],
            "latency_ms": report["latency_ms_mean"],
            "correct": report["correct"],
            "incorrect": report["incorrect"],
            "missing": report["missing"],
        }
    )
st.dataframe(pd.DataFrame(summaries), width="stretch", hide_index=True)

if len(reports) >= 2:
    best = max(reports, key=lambda item: item["accuracy"])
    worst = min(reports, key=lambda item: item["accuracy"])
    delta = best["accuracy"] - worst["accuracy"]
    st.success(
        f"**{best['strategy']}** ({best['model']}) improved overall field accuracy by "
        f"**{delta:.1f} points** versus {worst['strategy']}."
    )

selected_name = st.selectbox("Inspect report", [item.get("filename") for item in reports])
report = next(item for item in reports if item.get("filename") == selected_name)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Accuracy", f"{report['accuracy']}%")
c2.metric("Correct", report["correct"])
c3.metric("Incorrect", report["incorrect"])
c4.metric("Missing", report["missing"])

field_acc = pd.DataFrame(
    [{"field": key, "accuracy": value} for key, value in report["field_accuracy"].items()]
)
st.subheader("Field accuracy")
st.dataframe(field_acc, width="stretch", hide_index=True)

st.subheader("Failure counts")
st.json(report.get("failure_counts") or {})
