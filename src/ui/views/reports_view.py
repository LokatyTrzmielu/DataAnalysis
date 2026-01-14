"""Reports view - reports generation and download tab."""

from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from src.ui.layout import (
    render_bold_label,
    render_divider,
    render_kpi_section,
    render_section_header,
    render_status_badge,
    render_status_badges_inline,
    render_status_button,
    render_status_buttons_inline,
)
from src.ui.theme import COLORS


def generate_individual_report(report_type: str) -> tuple[str | None, bytes | None]:
    """Generate individual report and return (name, data).

    Args:
        report_type: Type of report to generate

    Returns:
        Tuple (filename, csv_data) or (None, None) if report not available
    """
    from src.reporting.csv_writer import CSVWriter
    from src.reporting.main_report import MainReportGenerator
    from src.reporting.dq_reports import DQReportGenerator

    writer = CSVWriter()

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir)

        if report_type == "Report_Main":
            generator = MainReportGenerator()
            file_path = generator.generate(
                output_dir / "Report_Main.csv",
                quality_result=st.session_state.quality_result,
                capacity_result=st.session_state.capacity_result,
                performance_result=st.session_state.performance_result,
                client_name=st.session_state.client_name or "Client",
            )

        elif report_type == "DQ_Summary":
            generator = DQReportGenerator()
            file_path = generator.generate_summary(
                output_dir / "DQ_Summary.csv",
                st.session_state.quality_result.metrics_after,
            )

        elif report_type == "DQ_MissingCritical":
            generator = DQReportGenerator()
            file_path = generator.generate_missing_critical(
                output_dir / "DQ_MissingCritical.csv",
                st.session_state.quality_result.dq_lists,
            )

        elif report_type == "DQ_SuspectOutliers":
            generator = DQReportGenerator()
            file_path = generator.generate_suspect_outliers(
                output_dir / "DQ_SuspectOutliers.csv",
                st.session_state.quality_result.dq_lists,
            )

        elif report_type == "DQ_HighRiskBorderline":
            generator = DQReportGenerator()
            file_path = generator.generate_high_risk_borderline(
                output_dir / "DQ_HighRiskBorderline.csv",
                st.session_state.quality_result.dq_lists,
            )

        elif report_type == "DQ_Duplicates":
            generator = DQReportGenerator()
            file_path = generator.generate_duplicates(
                output_dir / "DQ_Masterdata_Duplicates.csv",
                st.session_state.quality_result.dq_lists,
            )

        elif report_type == "DQ_Conflicts":
            generator = DQReportGenerator()
            file_path = generator.generate_conflicts(
                output_dir / "DQ_Masterdata_Conflicts.csv",
                st.session_state.quality_result.dq_lists,
            )

        elif report_type == "Capacity_Results":
            if st.session_state.capacity_result:
                file_path = output_dir / "Capacity_Results.csv"
                writer.write(st.session_state.capacity_result.df, file_path)
            else:
                return None, None

        else:
            return None, None

        with open(file_path, "rb") as f:
            data = f.read()

        return file_path.name, data


def render_reports_view() -> None:
    """Render the Reports tab content."""
    st.header("Report generation")

    # Check available data
    has_quality = st.session_state.quality_result is not None
    has_capacity = st.session_state.capacity_result is not None
    has_performance = st.session_state.performance_result is not None

    if not (has_quality or has_capacity or has_performance):
        st.info("First run validation or analysis in the appropriate tabs")
        return

    # KPI Section - Report availability summary
    _render_reports_kpi(has_quality, has_capacity, has_performance)

    render_divider()

    # Report categories section
    _render_report_categories(has_quality, has_capacity, has_performance)

    render_divider()

    # Bulk download section
    _render_bulk_download()

    render_divider()

    # Preview section
    _render_data_preview(has_quality, has_capacity, has_performance)


def _render_reports_kpi(has_quality: bool, has_capacity: bool, has_performance: bool) -> None:
    """Render KPI section showing report availability summary."""
    render_section_header("Report Summary", "📊")

    # Count available reports
    summary_count = 1  # Main report always available
    dq_count = 6 if has_quality else 0
    capacity_count = 1 if has_capacity else 0
    total_count = summary_count + dq_count + capacity_count

    # Count available data sources
    sources_count = sum([has_quality, has_capacity, has_performance])

    metrics = [
        {
            "title": "Total Reports",
            "value": str(total_count),
            "icon": "📄",
            "help_text": "Number of reports available for download",
        },
        {
            "title": "Data Sources",
            "value": f"{sources_count}/3",
            "icon": "📁",
            "help_text": "Quality, Capacity, Performance data available",
        },
        {
            "title": "DQ Reports",
            "value": str(dq_count),
            "icon": "🔍",
            "help_text": "Data quality reports (requires validation)",
        },
        {
            "title": "Analysis Reports",
            "value": str(capacity_count),
            "icon": "📦",
            "help_text": "Capacity analysis results",
        },
    ]

    render_kpi_section(metrics)


def _render_report_categories(
    has_quality: bool, has_capacity: bool, has_performance: bool
) -> None:
    """Render report list organized by categories."""
    render_section_header("Available Reports", "📋")

    # Build reports list
    reports = _build_reports_list(has_quality, has_capacity)

    # Display by category with styled cards
    categories = [
        ("Summary", "📊", "Main summary of all analyses"),
        ("Data Quality", "🔍", "Data quality validation reports"),
        ("Capacity", "📦", "Capacity analysis results"),
    ]

    for cat_name, cat_icon, cat_desc in categories:
        category_reports = [r for r in reports if r["category"] == cat_name]
        if category_reports:
            _render_category_section(cat_name, cat_icon, cat_desc, category_reports)


def _build_reports_list(has_quality: bool, has_capacity: bool) -> list[dict]:
    """Build list of available reports."""
    reports = []

    # Main report - always available if there's any data
    reports.append({
        "name": "Report_Main",
        "description": "Main summary report with all analysis results",
        "available": True,
        "category": "Summary",
    })

    # DQ reports - available if quality_result exists
    if has_quality:
        dq_reports = [
            ("DQ_Summary", "Data quality summary - overall metrics and scores"),
            ("DQ_MissingCritical", "SKUs with missing critical data (dimensions, weight)"),
            ("DQ_SuspectOutliers", "SKUs with suspect values flagged as outliers"),
            ("DQ_HighRiskBorderline", "SKUs with dimensions near carrier limits"),
            ("DQ_Duplicates", "Duplicate SKU entries found in masterdata"),
            ("DQ_Conflicts", "SKUs with conflicting values across records"),
        ]
        for name, desc in dq_reports:
            reports.append({
                "name": name,
                "description": desc,
                "available": True,
                "category": "Data Quality",
            })

    # Capacity report - available if capacity_result exists
    if has_capacity:
        reports.append({
            "name": "Capacity_Results",
            "description": "Full capacity analysis - SKU fit status per carrier",
            "available": True,
            "category": "Capacity",
        })

    return reports


def _render_category_section(
    cat_name: str, cat_icon: str, cat_desc: str, category_reports: list[dict]
) -> None:
    """Render a category section with its reports."""
    # Category header
    st.markdown(
        f"""
        <div class="report-category-header">
            <span class="category-icon">{cat_icon}</span>
            <span class="category-name">{cat_name}</span>
            <span class="category-count">{len(category_reports)} report(s)</span>
        </div>
        <p class="category-desc">{cat_desc}</p>
        """,
        unsafe_allow_html=True,
    )

    # Reports in this category
    for report in category_reports:
        _render_report_card(report)


def _render_report_card(report: dict) -> None:
    """Render a single report card with download button."""
    col1, col2 = st.columns([4, 1])

    with col1:
        st.markdown(
            f"""
            <div class="report-card">
                <div class="report-name">{report['name']}</div>
                <div class="report-desc">{report['description']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        if report["available"]:
            if st.button("Download", key=f"download_{report['name']}", width="stretch"):
                try:
                    filename, data = generate_individual_report(report["name"])
                    if data:
                        st.download_button(
                            label=f"Save {filename}",
                            data=data,
                            file_name=filename,
                            mime="text/csv",
                            key=f"save_{report['name']}",
                        )
                except Exception as e:
                    st.error(f"Error: {e}")


def _render_bulk_download() -> None:
    """Render the bulk download section with ZIP generation."""
    render_section_header("Bulk Download", "📦")

    st.markdown(
        f"""
        <p style="color: {COLORS['text_secondary']}; margin-bottom: 1rem;">
            Download all available reports in a single ZIP archive with SHA256 manifest.
        </p>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Generate ZIP Package", type="primary", width="stretch"):
            _generate_zip_package()


def _generate_zip_package() -> None:
    """Generate and offer ZIP package for download."""
    progress_bar = st.progress(0, text="Initializing...")

    try:
        from src.reporting import export_reports

        progress_bar.progress(20, text="Creating temporary directory...")

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)

            progress_bar.progress(40, text="Generating reports...")

            zip_path = export_reports(
                output_dir,
                client_name=st.session_state.client_name or "Client",
                quality_result=st.session_state.quality_result,
                capacity_result=st.session_state.capacity_result,
                performance_result=st.session_state.performance_result,
            )

            progress_bar.progress(80, text="Preparing download...")

            with open(zip_path, "rb") as f:
                zip_data = f.read()

            progress_bar.progress(100, text="Complete!")

            st.download_button(
                label="Download Reports (ZIP)",
                data=zip_data,
                file_name=zip_path.name,
                mime="application/zip",
                width="stretch",
            )

            st.success("Reports generated successfully!")

    except Exception as e:
        progress_bar.empty()
        st.error(f"Generation error: {e}")


def _render_data_preview(
    has_quality: bool, has_capacity: bool, has_performance: bool
) -> None:
    """Render data preview section with styled expanders."""
    render_section_header("Data Preview", "👁️")

    st.markdown(
        f"""
        <p style="color: {COLORS['text_secondary']}; margin-bottom: 1rem;">
            Preview the data that will be included in the reports.
        </p>
        """,
        unsafe_allow_html=True,
    )

    if has_quality:
        _render_quality_preview()

    if has_capacity:
        _render_capacity_preview()

    if has_performance:
        _render_performance_preview()


def _render_quality_preview() -> None:
    """Render data quality preview expander."""
    with st.expander("🔍 Data Quality", expanded=False):
        qr = st.session_state.quality_result

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                f"""
                <div class="preview-metric">
                    <span class="metric-label">Quality Score</span>
                    <span class="metric-value" style="color: {COLORS['primary']};">{qr.quality_score:.1f}%</span>
                </div>
                <div class="preview-metric">
                    <span class="metric-label">Total Records</span>
                    <span class="metric-value">{qr.total_records:,}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f"""
                <div class="preview-metric">
                    <span class="metric-label">Valid Records</span>
                    <span class="metric-value">{qr.valid_records:,}</span>
                </div>
                <div class="preview-metric">
                    <span class="metric-label">Imputed Records</span>
                    <span class="metric-value">{qr.imputed_records:,}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        render_divider()
        render_bold_label("Data coverage after imputation:", "📊")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Dimensions",
                f"{qr.metrics_after.dimensions_coverage_pct:.1f}%",
                help="Percentage of SKU with complete L×W×H dimensions",
            )
        with col2:
            st.metric(
                "Weight",
                f"{qr.metrics_after.weight_coverage_pct:.1f}%",
                help="Percentage of SKU with weight data",
            )


def _render_capacity_preview() -> None:
    """Render capacity analysis preview expander."""
    with st.expander("📦 Capacity Analysis", expanded=False):
        cr = st.session_state.capacity_result

        st.markdown(
            f"""
            <div class="preview-metric">
                <span class="metric-label">Total SKU analyzed</span>
                <span class="metric-value">{cr.total_sku:,}</span>
            </div>
            <div class="preview-metric">
                <span class="metric-label">Carriers</span>
                <span class="metric-value">{', '.join(cr.carriers_analyzed)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        render_divider()
        render_bold_label("Results per carrier:", "📦")

        for carrier_id in cr.carriers_analyzed:
            stats = cr.carrier_stats.get(carrier_id)
            if stats:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**{stats.carrier_name}**")
                with col2:
                    render_status_buttons_inline([
                        (f"FIT: {stats.fit_count}", "success"),
                        (f"BORDER: {stats.borderline_count}", "pending"),
                        (f"NOT: {stats.not_fit_count}", "failed"),
                    ])
                with col3:
                    st.metric(
                        "Fit %",
                        f"{stats.fit_percentage:.1f}%",
                        help="Percentage of SKU fitting this carrier",
                    )


def _render_performance_preview() -> None:
    """Render performance analysis preview expander."""
    with st.expander("⚡ Performance Analysis", expanded=False):
        pr = st.session_state.performance_result
        kpi = pr.kpi

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                f"""
                <div class="preview-metric">
                    <span class="metric-label">Total Lines</span>
                    <span class="metric-value">{kpi.total_lines:,}</span>
                </div>
                <div class="preview-metric">
                    <span class="metric-label">Total Orders</span>
                    <span class="metric-value">{kpi.total_orders:,}</span>
                </div>
                <div class="preview-metric">
                    <span class="metric-label">Total Units</span>
                    <span class="metric-value">{kpi.total_units:,}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f"""
                <div class="preview-metric">
                    <span class="metric-label">Avg Lines/h</span>
                    <span class="metric-value">{kpi.avg_lines_per_hour:.1f}</span>
                </div>
                <div class="preview-metric">
                    <span class="metric-label">Peak Lines/h</span>
                    <span class="metric-value" style="color: {COLORS['warning']};">{kpi.peak_lines_per_hour}</span>
                </div>
                <div class="preview-metric">
                    <span class="metric-label">P95 Lines/h</span>
                    <span class="metric-value">{kpi.p95_lines_per_hour:.1f}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
