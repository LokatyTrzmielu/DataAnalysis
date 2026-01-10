"""Views module - individual tab views for the Streamlit app."""

from src.ui.views.components_demo import render_components_demo
from src.ui.views.import_view import (
    render_import_view,
    render_masterdata_import,
    render_orders_import,
)
from src.ui.views.validation_view import render_validation_view
from src.ui.views.capacity_view import render_capacity_view
from src.ui.views.performance_view import render_performance_view
from src.ui.views.reports_view import render_reports_view

__all__ = [
    "render_components_demo",
    "render_import_view",
    "render_masterdata_import",
    "render_orders_import",
    "render_validation_view",
    "render_capacity_view",
    "render_performance_view",
    "render_reports_view",
]
