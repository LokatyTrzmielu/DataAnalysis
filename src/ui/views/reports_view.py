"""Reports view - reports generation and download tab."""

from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st


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

    # List of reports
    st.subheader("Available reports")

    reports = []

    # Main report - always available if there's any data
    reports.append({
        "name": "Report_Main",
        "description": "Main summary report",
        "available": True,
        "category": "Summary",
    })

    # DQ reports - available if quality_result exists
    if has_quality:
        dq_reports = [
            ("DQ_Summary", "Data quality summary"),
            ("DQ_MissingCritical", "List of SKUs with missing critical data"),
            ("DQ_SuspectOutliers", "List of SKUs with suspect values (outliers)"),
            ("DQ_HighRiskBorderline", "List of SKUs with dimensions near limits"),
            ("DQ_Duplicates", "List of duplicate SKUs"),
            ("DQ_Conflicts", "List of SKUs with value conflicts"),
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
            "description": "Capacity analysis results (SKU fit to carriers)",
            "available": True,
            "category": "Capacity",
        })

    # Display list of reports with download buttons
    for category in ["Summary", "Data Quality", "Capacity"]:
        category_reports = [r for r in reports if r["category"] == category]
        if category_reports:
            st.markdown(f"**{category}:**")

            for report in category_reports:
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(f"- **{report['name']}**: {report['description']}")

                with col2:
                    if report["available"]:
                        if st.button("Download", key=f"download_{report['name']}"):
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

    st.markdown("---")

    # Button to download all reports as ZIP
    st.subheader("Download all reports")

    if st.button("Generate ZIP reports", type="primary"):
        with st.spinner("Generating reports..."):
            try:
                from src.reporting import export_reports

                with tempfile.TemporaryDirectory() as tmp_dir:
                    output_dir = Path(tmp_dir)

                    zip_path = export_reports(
                        output_dir,
                        client_name=st.session_state.client_name or "Client",
                        quality_result=st.session_state.quality_result,
                        capacity_result=st.session_state.capacity_result,
                        performance_result=st.session_state.performance_result,
                    )

                    # Prepare for download
                    with open(zip_path, "rb") as f:
                        zip_data = f.read()

                    st.download_button(
                        label="Download reports (ZIP)",
                        data=zip_data,
                        file_name=zip_path.name,
                        mime="application/zip",
                    )

                    st.success("Reports generated!")

            except Exception as e:
                st.error(f"Generation error: {e}")

    # Main report preview
    st.markdown("---")
    st.subheader("Data preview")

    if has_quality:
        with st.expander("Data Quality", expanded=False):
            qr = st.session_state.quality_result
            st.write(f"- **Quality Score:** {qr.quality_score:.1f}%")
            st.write(f"- **Records:** {qr.total_records}")
            st.write(f"- **Valid:** {qr.valid_records}")
            st.write(f"- **Imputed:** {qr.imputed_records}")

            st.markdown("**Data coverage after imputation:**")
            st.write(f"- Dimensions: {qr.metrics_after.dimensions_coverage_pct:.1f}%")
            st.write(f"- Weight: {qr.metrics_after.weight_coverage_pct:.1f}%")

    if has_capacity:
        with st.expander("Capacity Analysis", expanded=False):
            cr = st.session_state.capacity_result
            st.write(f"- **Total SKU:** {cr.total_sku}")
            st.write(f"- **Carriers:** {', '.join(cr.carriers_analyzed)}")

            st.markdown("**Results per carrier:**")
            for carrier_id in cr.carriers_analyzed:
                stats = cr.carrier_stats.get(carrier_id)
                if stats:
                    st.markdown(f"**{stats.carrier_name}:**")
                    st.write(f"  - FIT: {stats.fit_count} | BORDERLINE: {stats.borderline_count} | NOT_FIT: {stats.not_fit_count}")
                    st.write(f"  - Fit %: {stats.fit_percentage:.1f}% | Volume: {stats.total_volume_m3:.2f} m³")

    if has_performance:
        with st.expander("Performance Analysis", expanded=False):
            pr = st.session_state.performance_result
            kpi = pr.kpi
            st.write(f"- **Lines:** {kpi.total_lines}")
            st.write(f"- **Orders:** {kpi.total_orders}")
            st.write(f"- **Units:** {kpi.total_units}")
            st.write(f"- **Avg lines/h:** {kpi.avg_lines_per_hour:.1f}")
            st.write(f"- **Peak lines/h:** {kpi.peak_lines_per_hour}")
            st.write(f"- **P95 lines/h:** {kpi.p95_lines_per_hour:.1f}")
