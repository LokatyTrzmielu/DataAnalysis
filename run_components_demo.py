"""Run the UI components demo page."""

import streamlit as st

from src.ui.views.components_demo import render_components_demo

if __name__ == "__main__":
    st.set_page_config(
        page_title="UI Components Demo",
        page_icon="🎨",
        layout="wide",
    )
    render_components_demo()
