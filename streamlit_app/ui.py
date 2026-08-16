"""Shared Streamlit theme. Forces light paper colors so Cloud dark mode cannot
leave white labels on a cream background."""

from __future__ import annotations

import streamlit as st

CSS = """
<style>
html, body { color-scheme: light !important; }
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
  background-color: #F4F0E6 !important;
  color: #1A2332 !important;
}
[data-testid="stHeader"] { background: rgba(244, 240, 230, 0.92) !important; }
[data-testid="stToolbar"] { color: #1A2332 !important; }
[data-testid="stSidebar"] {
  background-color: #E8E2D4 !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
  color: #1A2332 !important;
}
h1, h2, h3, h4, h5 { color: #1B3A4B !important; }
p, li, span, label, .stMarkdown, .stCaption, .stText {
  color: #1A2332 !important;
}
[data-testid="stMetricValue"], [data-testid="stMetricLabel"], [data-testid="stMetricDelta"] {
  color: #1A2332 !important;
}
div[data-testid="stAlert"] p, div[data-testid="stAlert"] span {
  color: #1A2332 !important;
}
.stSelectbox label, .stTextInput label, .stRadio label, .stFileUploader label {
  color: #1A2332 !important;
}
[data-testid="stWidgetLabel"] p { color: #1A2332 !important; }
[data-baseweb="select"] > div, [data-baseweb="input"] > div, input, textarea {
  color: #1A2332 !important;
  background-color: #FFFCF6 !important;
}
.stButton > button {
  color: #FFFFFF !important;
  background-color: #1B3A4B !important;
  border: 0 !important;
}
.stButton > button:hover {
  background-color: #C45C26 !important;
  color: #FFFFFF !important;
}
[data-testid="stExpander"] summary { color: #1A2332 !important; }
footer, footer * { color: #5C6570 !important; }
</style>
"""


def apply() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
