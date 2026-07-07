"""
SENTRY — Crime Risk Analysis & Safe Travel Recommendation System
Streamlit entrypoint.

The original deliverable was a static HTML/CSS/JS single-page app
(index.html + style.css + script.js). To keep the UI *exactly* the
same — same fonts, same glassmorphism cards, same radar/ticker
animations, same client-side navigation between Dashboard / Risk
Analysis / Safe Travel / Analytics / About — this file loads that
original markup, inlines its CSS + JS untouched, and renders it
inside a full-bleed Streamlit component. Streamlit's own default
chrome (padding, header, footer) is hidden so the embedded app reads
as a native full-page Streamlit app rather than an iframe.

All of the original interactivity (page navigation, dropdown-driven
risk scoring, safe-travel recommendations, the analytics charts) is
untouched, hand-written JavaScript from the original build — nothing
was re-implemented, so behavior matches the source 1:1.
"""

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

APP_DIR = Path(__file__).parent
HTML_PATH = APP_DIR / "app_combined.html"

st.set_page_config(
    page_title="SENTRY — Crime Risk Analysis & Safe Travel",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Strip Streamlit's default chrome (header, footer, padding, max-width)
# so the embedded app fills the whole browser viewport edge-to-edge,
# exactly like the original static site.
st.markdown(
    """
    <style>
        #MainMenu, header[data-testid="stHeader"], footer {visibility: hidden; height: 0;}
        div.block-container {padding: 0 !important; max-width: 100% !important;}
        iframe {display: block;}
        section[data-testid="stSidebar"] {display: none;}
        .stApp {background: #060a16;}
    </style>
    """,
    unsafe_allow_html=True,
)

html_source = HTML_PATH.read_text(encoding="utf-8")

# Tall fixed height with internal scrolling — the app's own sidebar is
# "position: sticky; height: 100vh" against this frame, and the page
# content (dashboard / analytics, etc.) scrolls inside it exactly as
# it did in the standalone site.
components.html(html_source, height=1600, scrolling=True)
