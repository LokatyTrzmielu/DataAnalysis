"""Views module - individual tab views for the Streamlit app."""

from src.ui.views.components_demo import render_components_demo

__all__ = ["render_components_demo"]

# Views will be added in subsequent stages:
# - import_view.py (Stage 3, 4)
# - capacity_view.py (Stage 3, 5)
# - performance_view.py (Stage 3, 6)
# - reports_view.py (Stage 3, 7)
