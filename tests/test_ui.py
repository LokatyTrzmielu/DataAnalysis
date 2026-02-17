"""Unit tests for UI module - layout helpers, theme, and insight generation."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.ui.theme import COLORS, STATUS_COLORS
from src.ui.layout import get_plotly_layout_defaults
from src.ui.insights import Insight


# ============================================================================
# Theme tests
# ============================================================================


class TestColors:
    """Verify color definitions are valid."""

    @pytest.mark.parametrize("name", list(COLORS.keys()))
    def test_color_is_valid_hex(self, name: str):
        """Each COLORS entry should be a valid hex color."""
        color = COLORS[name]
        assert isinstance(color, str)
        assert color.startswith("#"), f"COLORS['{name}'] = '{color}' is not a hex color"
        # Strip '#' and check hex digits (3, 4, 6, or 8 chars)
        hex_part = color[1:]
        assert len(hex_part) in (3, 4, 6, 8), f"COLORS['{name}'] has invalid length"
        assert all(c in "0123456789abcdefABCDEF" for c in hex_part)

    @pytest.mark.parametrize("name", list(STATUS_COLORS.keys()))
    def test_status_color_is_valid_hex(self, name: str):
        """Each STATUS_COLORS entry should be a valid hex color."""
        color = STATUS_COLORS[name]
        assert isinstance(color, str)
        assert color.startswith("#")

    def test_required_colors_present(self):
        """Core color keys must exist."""
        required = ["primary", "error", "warning", "info", "text", "surface", "border"]
        for key in required:
            assert key in COLORS, f"Missing required color: {key}"

    def test_warning_differs_from_accent(self):
        """Warning color should be distinct from accent (bug caught in TIER 1)."""
        assert COLORS["warning"] != COLORS["accent"]


# ============================================================================
# Layout helper tests
# ============================================================================


class TestPlotlyDefaults:
    """Verify Plotly layout defaults."""

    def test_returns_dict(self):
        defaults = get_plotly_layout_defaults()
        assert isinstance(defaults, dict)

    def test_has_standard_height(self):
        """All charts should use consistent height."""
        defaults = get_plotly_layout_defaults()
        assert "height" in defaults
        assert defaults["height"] == 400

    def test_has_margin(self):
        defaults = get_plotly_layout_defaults()
        assert "margin" in defaults

    def test_has_colors(self):
        defaults = get_plotly_layout_defaults()
        assert "paper_bgcolor" in defaults
        assert "plot_bgcolor" in defaults
        assert "font" in defaults

    def test_grid_colors_set(self):
        defaults = get_plotly_layout_defaults()
        assert "xaxis" in defaults
        assert "gridcolor" in defaults["xaxis"]
        assert "yaxis" in defaults
        assert "gridcolor" in defaults["yaxis"]


# ============================================================================
# Insight model tests
# ============================================================================


class TestInsight:
    """Test Insight dataclass."""

    def test_create_insight(self):
        i = Insight(message="Test message", type="positive")
        assert i.message == "Test message"
        assert i.type == "positive"

    def test_insight_types(self):
        for t in ("positive", "warning", "info"):
            i = Insight(message="x", type=t)
            assert i.type == t


# ============================================================================
# Insight generation tests (with mocked session_state)
# ============================================================================


class TestCapacityInsights:
    """Test generate_capacity_insights with mocked session state."""

    def _make_carrier_stats(self, fit_pct: float, borderline: int = 0, not_fit: int = 0):
        """Create a mock carrier stats object."""
        stats = MagicMock()
        stats.fit_percentage = fit_pct
        stats.carrier_name = "TestCarrier"
        stats.borderline_count = borderline
        stats.not_fit_count = not_fit
        stats.fit_count = 80
        return stats

    @patch("src.ui.insights.st")
    def test_no_result_returns_empty(self, mock_st):
        from src.ui.insights import generate_capacity_insights
        mock_st.session_state = MagicMock()
        mock_st.session_state.get.return_value = None
        assert generate_capacity_insights() == []

    @patch("src.ui.insights.st")
    def test_high_fit_rate_positive(self, mock_st):
        from src.ui.insights import generate_capacity_insights
        result = MagicMock()
        result.carrier_stats = {"C1": self._make_carrier_stats(95.0)}
        result.total_sku = 100
        mock_st.session_state = MagicMock()
        mock_st.session_state.get.return_value = result

        insights = generate_capacity_insights()
        assert any("Excellent" in i.message for i in insights)

    @patch("src.ui.insights.st")
    def test_low_fit_rate_warning(self, mock_st):
        from src.ui.insights import generate_capacity_insights
        result = MagicMock()
        result.carrier_stats = {"C1": self._make_carrier_stats(50.0)}
        result.total_sku = 100
        mock_st.session_state = MagicMock()
        mock_st.session_state.get.return_value = result

        insights = generate_capacity_insights()
        assert any(i.type == "warning" for i in insights)

    @patch("src.ui.insights.st")
    def test_borderline_warning_above_threshold(self, mock_st):
        from src.ui.insights import generate_capacity_insights
        result = MagicMock()
        stats = self._make_carrier_stats(80.0, borderline=20)
        result.carrier_stats = {"C1": stats}
        result.total_sku = 100
        mock_st.session_state = MagicMock()
        mock_st.session_state.get.return_value = result

        insights = generate_capacity_insights()
        assert any("borderline" in i.message for i in insights)

    @patch("src.ui.insights.st")
    def test_warnings_sorted_first(self, mock_st):
        from src.ui.insights import generate_capacity_insights
        result = MagicMock()
        result.carrier_stats = {
            "C1": self._make_carrier_stats(50.0, borderline=20),
            "C2": self._make_carrier_stats(40.0),
        }
        result.total_sku = 100
        mock_st.session_state = MagicMock()
        mock_st.session_state.get.return_value = result

        insights = generate_capacity_insights()
        if len(insights) >= 2:
            # First insight should be warning type
            assert insights[0].type == "warning"


class TestPerformanceInsights:
    """Test generate_performance_insights with mocked session state."""

    def _make_kpi(self, **overrides):
        kpi = MagicMock()
        kpi.total_orders = overrides.get("total_orders", 1000)
        kpi.total_lines = overrides.get("total_lines", 5000)
        kpi.unique_sku = overrides.get("unique_sku", 200)
        kpi.avg_lines_per_hour = overrides.get("avg_lines_per_hour", 50.0)
        kpi.p95_lines_per_hour = overrides.get("p95_lines_per_hour", 100.0)
        kpi.avg_lines_per_order = overrides.get("avg_lines_per_order", 3.0)
        return kpi

    @patch("src.ui.insights.st")
    def test_no_result_returns_empty(self, mock_st):
        from src.ui.insights import generate_performance_insights
        mock_st.session_state = MagicMock()
        mock_st.session_state.get.return_value = None
        assert generate_performance_insights() == []

    @patch("src.ui.insights.st")
    def test_basic_volume_insight(self, mock_st):
        from src.ui.insights import generate_performance_insights
        result = MagicMock()
        result.kpi = self._make_kpi()
        result.has_hourly_data = False
        result.sku_pareto = []
        result.weekday_profile = {}
        mock_st.session_state = MagicMock()
        mock_st.session_state.get.return_value = result

        insights = generate_performance_insights()
        assert len(insights) >= 1
        assert "1,000 orders" in insights[0].message

    @patch("src.ui.insights.st")
    def test_high_variability_warning(self, mock_st):
        from src.ui.insights import generate_performance_insights
        result = MagicMock()
        result.kpi = self._make_kpi(avg_lines_per_hour=30.0, p95_lines_per_hour=100.0)
        result.has_hourly_data = True
        result.sku_pareto = []
        result.weekday_profile = {}
        mock_st.session_state = MagicMock()
        mock_st.session_state.get.return_value = result

        insights = generate_performance_insights()
        assert any("variability" in i.message.lower() for i in insights)

    @patch("src.ui.insights.st")
    def test_complex_orders_insight(self, mock_st):
        from src.ui.insights import generate_performance_insights
        result = MagicMock()
        result.kpi = self._make_kpi(avg_lines_per_order=8.0)
        result.has_hourly_data = False
        result.sku_pareto = []
        result.weekday_profile = {}
        mock_st.session_state = MagicMock()
        mock_st.session_state.get.return_value = result

        insights = generate_performance_insights()
        assert any("complex" in i.message.lower() for i in insights)
