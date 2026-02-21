"""PDF report generator using reportlab (pure-Python, cross-platform)."""

import io
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_capacity_pdf(
    client_name: str,
    capacity_data: dict[str, Any],
    run_id: str,
) -> bytes:
    """Generate a PDF report for capacity analysis results.

    Args:
        client_name: Client/project name for the report header
        capacity_data: Serialized CapacityAnalysisResult dict (from JSONB)
        run_id: Run identifier for footer

    Returns:
        PDF file bytes
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Title"], fontSize=16, spaceAfter=6)
    heading_style = ParagraphStyle("heading", parent=styles["Heading2"], fontSize=12, spaceAfter=4)
    body_style = styles["BodyText"]
    small_style = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, textColor=colors.grey)

    story = []

    # ── Header ──────────────────────────────────────────────────────────────
    story.append(Paragraph(f"Capacity Analysis Report", title_style))
    story.append(Paragraph(f"Client: {client_name}", heading_style))
    story.append(
        Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  Run ID: {run_id}",
            small_style,
        )
    )
    story.append(Spacer(1, 0.5 * cm))

    # ── KPI Summary ──────────────────────────────────────────────────────────
    story.append(Paragraph("Summary", heading_style))
    kpi_data = [
        ["Metric", "Value"],
        ["Total SKU", str(capacity_data.get("total_sku", "-"))],
        ["Fit %", f"{capacity_data.get('fit_percentage', 0):.1f}%"],
        ["FIT", str(capacity_data.get("fit_count", "-"))],
        ["BORDERLINE", str(capacity_data.get("borderline_count", "-"))],
        ["NOT FIT", str(capacity_data.get("not_fit_count", "-"))],
    ]
    kpi_table = Table(kpi_data, colWidths=[8 * cm, 6 * cm])
    kpi_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(kpi_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── Per-carrier breakdown ─────────────────────────────────────────────────
    carrier_stats: dict[str, Any] = capacity_data.get("carrier_stats", {})
    if carrier_stats:
        story.append(Paragraph("Carrier Breakdown", heading_style))
        header = ["Carrier", "Fit %", "FIT", "BORDERLINE", "NOT FIT", "Locations", "Avg Fill"]
        rows = [header]
        for cid, cs in carrier_stats.items():
            rows.append(
                [
                    cs.get("carrier_name", cid),
                    f"{cs.get('fit_percentage', 0):.1f}%",
                    str(cs.get("fit_count", 0)),
                    str(cs.get("borderline_count", 0)),
                    str(cs.get("not_fit_count", 0)),
                    str(cs.get("total_locations_required", 0)),
                    f"{cs.get('avg_filling_rate', 0) * 100:.1f}%",
                ]
            )

        col_widths = [5 * cm, 2 * cm, 1.8 * cm, 2.5 * cm, 2 * cm, 2.5 * cm, 2 * cm]
        carrier_table = Table(rows, colWidths=col_widths)
        carrier_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#374151")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
                    ("PADDING", (0, 0), (-1, -1), 5),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ]
            )
        )
        story.append(carrier_table)
        story.append(Spacer(1, 0.5 * cm))

    # ── Footer note ───────────────────────────────────────────────────────────
    story.append(
        Paragraph(
            "This report was generated by DataAnalysis. "
            "Borderline items fit within tolerance threshold. "
            "Locations required assume full stock stored on single carrier type.",
            small_style,
        )
    )

    doc.build(story)
    return buf.getvalue()
