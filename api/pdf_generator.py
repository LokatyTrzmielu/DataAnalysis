"""PDF report generator using reportlab (pure-Python) + matplotlib charts."""

import io
from datetime import datetime
from typing import Any

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

_C_FIT = '#22c55e'
_C_BORDERLINE = '#f59e0b'
_C_NOTFIT = '#ef4444'
_C_PRIMARY = '#0071e3'
_C_PURPLE = '#8b5cf6'
_C_ORANGE = '#f97316'
_C_GREEN = '#16a34a'

_PAGE_W = 16  # chart width in cm (fits A4 with 2cm margins)


def _fig_to_rl_image(fig, height_cm: float) -> Image:
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=_PAGE_W * cm, height=height_cm * cm)


def _style_ax(ax):
    ax.set_facecolor('white')
    ax.grid(axis='y', color='#e5e7eb', linewidth=0.8, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#d1d5db')
    ax.spines['bottom'].set_color('#d1d5db')
    ax.tick_params(colors='#6b7280', labelsize=8)
    ax.xaxis.label.set_color('#6b7280')
    ax.yaxis.label.set_color('#6b7280')


# ── Capacity charts ─────────────────────────────────────────────────────────

def _chart_carrier_fit(capacity_data: dict) -> Image | None:
    carrier_stats = capacity_data.get('carrier_stats', {})
    if not carrier_stats:
        return None
    names = [cs.get('carrier_name', cid) for cid, cs in carrier_stats.items()]
    fit = [cs.get('fit_count', 0) for cs in carrier_stats.values()]
    brd = [cs.get('borderline_count', 0) for cs in carrier_stats.values()]
    nft = [cs.get('not_fit_count', 0) for cs in carrier_stats.values()]
    x = list(range(len(names)))
    fig, ax = plt.subplots(figsize=(_PAGE_W / 2.54, 5))
    ax.bar(x, fit, label='FIT', color=_C_FIT, zorder=3)
    ax.bar(x, brd, bottom=fit, label='BORDERLINE', color=_C_BORDERLINE, zorder=3)
    ax.bar(x, nft, bottom=[f + b for f, b in zip(fit, brd)], label='NOT FIT', color=_C_NOTFIT, zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=30, ha='right', fontsize=8)
    ax.set_ylabel('SKU Count')
    ax.legend(fontsize=8)
    _style_ax(ax)
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return _fig_to_rl_image(fig, 7)


def _chart_volume_dist(rows: list) -> Image | None:
    vals = [r.get('volume_m3') for r in rows if r.get('volume_m3') is not None]
    if not vals:
        return None
    fig, ax = plt.subplots(figsize=(_PAGE_W / 2.54, 4))
    ax.hist(vals, bins=40, color=_C_PRIMARY, edgecolor='white', linewidth=0.4, zorder=3)
    ax.set_xlabel('Volume (m³)')
    ax.set_ylabel('SKU Count')
    _style_ax(ax)
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return _fig_to_rl_image(fig, 6)


def _chart_weight_dist(rows: list) -> Image | None:
    vals = [r.get('weight_kg') for r in rows if r.get('weight_kg') is not None]
    if not vals:
        return None
    fig, ax = plt.subplots(figsize=(_PAGE_W / 2.54, 4))
    ax.hist(vals, bins=40, color=_C_PRIMARY, edgecolor='white', linewidth=0.4, zorder=3)
    ax.set_xlabel('Weight (kg)')
    ax.set_ylabel('SKU Count')
    _style_ax(ax)
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return _fig_to_rl_image(fig, 6)


def _chart_margin_dist(rows: list) -> Image | None:
    vals = [
        r.get('margin_mm')
        for r in rows
        if r.get('fit_status') in ('FIT', 'BORDERLINE') and r.get('margin_mm') is not None
    ]
    if not vals:
        return None
    fig, ax = plt.subplots(figsize=(_PAGE_W / 2.54, 4))
    ax.hist(vals, bins=40, color=_C_PURPLE, edgecolor='white', linewidth=0.4, zorder=3)
    ax.set_xlabel('Margin (mm)')
    ax.set_ylabel('SKU Count')
    _style_ax(ax)
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return _fig_to_rl_image(fig, 6)


def _chart_dims_dist(rows: list) -> Image | None:
    l_vals = [r.get('length_mm') for r in rows if r.get('length_mm') is not None]
    w_vals = [r.get('width_mm') for r in rows if r.get('width_mm') is not None]
    h_vals = [r.get('height_mm') for r in rows if r.get('height_mm') is not None]
    if not (l_vals or w_vals or h_vals):
        return None
    fig, ax = plt.subplots(figsize=(_PAGE_W / 2.54, 4))
    if l_vals:
        ax.hist(l_vals, bins=40, alpha=0.6, label='Length', color=_C_PRIMARY, edgecolor='white', linewidth=0.3, zorder=3)
    if w_vals:
        ax.hist(w_vals, bins=40, alpha=0.6, label='Width', color=_C_ORANGE, edgecolor='white', linewidth=0.3, zorder=3)
    if h_vals:
        ax.hist(h_vals, bins=40, alpha=0.6, label='Height', color=_C_GREEN, edgecolor='white', linewidth=0.3, zorder=3)
    ax.set_xlabel('Dimension (mm)')
    ax.set_ylabel('SKU Count')
    ax.legend(fontsize=8)
    _style_ax(ax)
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return _fig_to_rl_image(fig, 6)


# ── Performance charts ───────────────────────────────────────────────────────

def _chart_daily(daily_metrics: list) -> Image | None:
    if not daily_metrics:
        return None
    dates = [m['date'] for m in daily_metrics]
    lines = [m['lines'] for m in daily_metrics]
    fig, ax = plt.subplots(figsize=(_PAGE_W / 2.54, 4))
    ax.bar(range(len(dates)), lines, color=_C_PRIMARY, zorder=3)
    step = max(1, len(dates) // 12)
    ax.set_xticks(range(0, len(dates), step))
    ax.set_xticklabels([dates[i] for i in range(0, len(dates), step)], rotation=45, ha='right', fontsize=7)
    ax.set_ylabel('Lines')
    _style_ax(ax)
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return _fig_to_rl_image(fig, 6)


def _chart_hourly(hourly_metrics: list) -> Image | None:
    if not hourly_metrics:
        return None
    hours = [f"{m['hour']:02d}:00" for m in hourly_metrics]
    lines = [m['lines'] for m in hourly_metrics]
    fig, ax = plt.subplots(figsize=(_PAGE_W / 2.54, 4))
    ax.bar(range(len(hours)), lines, color=_C_PRIMARY, zorder=3)
    ax.set_xticks(range(len(hours)))
    ax.set_xticklabels(hours, rotation=45, ha='right', fontsize=7)
    ax.set_ylabel('Lines')
    _style_ax(ax)
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return _fig_to_rl_image(fig, 6)


def _chart_weekly(weekly_trends: list) -> Image | None:
    if len(weekly_trends) < 2:
        return None
    labels = [f"W{m['week']:02d} {m['year']}" for m in weekly_trends]
    lines = [m['lines'] for m in weekly_trends]
    fig, ax = plt.subplots(figsize=(_PAGE_W / 2.54, 4))
    ax.bar(range(len(labels)), lines, color=_C_PRIMARY, zorder=3)
    step = max(1, len(labels) // 12)
    ax.set_xticks(range(0, len(labels), step))
    ax.set_xticklabels([labels[i] for i in range(0, len(labels), step)], rotation=45, ha='right', fontsize=7)
    ax.set_ylabel('Lines')
    _style_ax(ax)
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return _fig_to_rl_image(fig, 6)


def _chart_weekday(weekday_profile: list) -> Image | None:
    if not weekday_profile:
        return None
    days = [m['day'] for m in weekday_profile]
    vals = [m['avg_lines'] for m in weekday_profile]
    fig, ax = plt.subplots(figsize=(_PAGE_W / 2.54, 4))
    ax.bar(range(len(days)), vals, color=_C_PRIMARY, zorder=3)
    ax.set_xticks(range(len(days)))
    ax.set_xticklabels(days, fontsize=8)
    ax.set_ylabel('Avg Lines / Day')
    _style_ax(ax)
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return _fig_to_rl_image(fig, 6)


def _chart_lpo_dist(lpo_dist: list) -> Image | None:
    if not lpo_dist:
        return None
    bins = [m['bin'] for m in lpo_dist]
    counts = [m['count'] for m in lpo_dist]
    fig, ax = plt.subplots(figsize=(_PAGE_W / 2.54, 4))
    ax.bar(range(len(bins)), counts, color=_C_PRIMARY, zorder=3)
    ax.set_xticks(range(len(bins)))
    ax.set_xticklabels(bins, fontsize=8)
    ax.set_xlabel('Lines per Order')
    ax.set_ylabel('Order Count')
    _style_ax(ax)
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return _fig_to_rl_image(fig, 6)


def _chart_heatmap(datehour_metrics: list) -> Image | None:
    if not datehour_metrics:
        return None
    dates = sorted(set(m['date'] for m in datehour_metrics))
    data = {(m['date'], m['hour']): m['lines'] for m in datehour_metrics}
    z = [[data.get((date, h), 0) for h in range(24)] for date in dates]
    n_dates = len(dates)
    fig_h = max(4, min(9, n_dates * 0.22 + 2))
    fig, ax = plt.subplots(figsize=(_PAGE_W / 2.54, fig_h))
    im = ax.pcolormesh(
        list(range(24)), list(range(n_dates)), z,
        cmap='Blues', vmin=0, shading='auto',
    )
    ax.set_yticks(range(n_dates))
    ax.set_yticklabels(dates, fontsize=max(5, 8 - n_dates // 20))
    ax.set_xticks(range(24))
    ax.set_xticklabels([f'{h:02d}' for h in range(24)], fontsize=7)
    ax.set_xlabel('Hour')
    plt.colorbar(im, ax=ax, label='Lines', fraction=0.02, pad=0.02)
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return _fig_to_rl_image(fig, fig_h * 2.54)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _section(title: str, heading_style) -> list:
    return [PageBreak(), Paragraph(title, heading_style), Spacer(1, 0.3 * cm)]


def _add_chart(story: list, img: Image | None, caption: str, small_style) -> None:
    if img is None:
        return
    story.append(Paragraph(caption, small_style))
    story.append(Spacer(1, 0.2 * cm))
    story.append(img)
    story.append(Spacer(1, 0.6 * cm))


# ── Public API ───────────────────────────────────────────────────────────────

def generate_capacity_pdf(
    client_name: str,
    capacity_data: dict[str, Any],
    run_id: str,
    performance_data: dict[str, Any] | None = None,
) -> bytes:
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
    title_style = ParagraphStyle('title', parent=styles['Title'], fontSize=16, spaceAfter=6)
    heading_style = ParagraphStyle('heading', parent=styles['Heading2'], fontSize=12, spaceAfter=4)
    subheading_style = ParagraphStyle('subheading', parent=styles['Heading3'], fontSize=10, spaceAfter=3)
    body_style = styles['BodyText']
    small_style = ParagraphStyle('small', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
    caption_style = ParagraphStyle('caption', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#374151'), fontName='Helvetica-Bold')

    story: list = []

    # ── Header ──────────────────────────────────────────────────────────────
    story.append(Paragraph('Capacity &amp; Performance Report', title_style))
    story.append(Paragraph(f'Client: {client_name}', heading_style))
    story.append(Paragraph(
        f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}  |  Run ID: {run_id}',
        small_style,
    ))
    story.append(Spacer(1, 0.5 * cm))

    # ── Capacity KPI Summary ─────────────────────────────────────────────────
    story.append(Paragraph('Capacity Analysis', heading_style))
    kpi_data = [
        ['Metric', 'Value'],
        ['Total SKU', str(capacity_data.get('total_sku', '-'))],
        ['Fit %', f"{capacity_data.get('fit_percentage', 0):.1f}%"],
        ['FIT', str(capacity_data.get('fit_count', '-'))],
        ['BORDERLINE', str(capacity_data.get('borderline_count', '-'))],
        ['NOT FIT', str(capacity_data.get('not_fit_count', '-'))],
    ]
    kpi_table = Table(kpi_data, colWidths=[8 * cm, 6 * cm])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1d4ed8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── Carrier Breakdown table ──────────────────────────────────────────────
    carrier_stats: dict[str, Any] = capacity_data.get('carrier_stats', {})
    if carrier_stats:
        story.append(Paragraph('Carrier Breakdown', subheading_style))
        header = ['Carrier', 'Fit %', 'FIT', 'BORDERLINE', 'NOT FIT', 'Locations', 'Avg Fill']
        rows_table = [header]
        for cid, cs in carrier_stats.items():
            rows_table.append([
                cs.get('carrier_name', cid),
                f"{cs.get('fit_percentage', 0):.1f}%",
                str(cs.get('fit_count', 0)),
                str(cs.get('borderline_count', 0)),
                str(cs.get('not_fit_count', 0)),
                str(cs.get('total_locations_required', 0)),
                f"{cs.get('avg_filling_rate', 0) * 100:.1f}%",
            ])
        col_widths = [5 * cm, 2 * cm, 1.8 * cm, 2.5 * cm, 2 * cm, 2.5 * cm, 2 * cm]
        ct = Table(rows_table, colWidths=col_widths)
        ct.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(ct)
        story.append(Spacer(1, 0.5 * cm))

    # ── Capacity Charts ──────────────────────────────────────────────────────
    story.extend(_section('Capacity Charts', heading_style))

    sku_rows: list = capacity_data.get('rows', [])
    _add_chart(story, _chart_carrier_fit(capacity_data), 'Carrier Fit — SKU distribution per carrier', caption_style)
    _add_chart(story, _chart_volume_dist(sku_rows), 'Volume Distribution (m³)', caption_style)
    _add_chart(story, _chart_weight_dist(sku_rows), 'Weight Distribution (kg)', caption_style)
    _add_chart(story, _chart_margin_dist(sku_rows), 'Margin Distribution — FIT & BORDERLINE SKUs (mm)', caption_style)
    _add_chart(story, _chart_dims_dist(sku_rows), 'Dimensions Distribution — Length / Width / Height (mm)', caption_style)

    # ── Performance section ──────────────────────────────────────────────────
    if performance_data:
        story.extend(_section('Performance Analysis', heading_style))

        kpi = performance_data.get('kpi', {})
        d_from = performance_data.get('date_from', '-')
        d_to = performance_data.get('date_to', '-')
        story.append(Paragraph(f'Period: {d_from} – {d_to}', small_style))
        story.append(Spacer(1, 0.3 * cm))

        perf_kpi_data = [
            ['Metric', 'Value', 'Metric', 'Value'],
            ['Total Orders', f"{kpi.get('total_orders', 0):,}", 'Total Lines', f"{kpi.get('total_lines', 0):,}"],
            ['Avg Lines/Order', f"{kpi.get('avg_lines_per_order', 0):.1f}", 'Avg Lines/Hour', f"{kpi.get('avg_lines_per_hour', 0):.1f}"],
            ['Peak Lines/Hour', f"{kpi.get('peak_lines_per_hour', 0):,}", 'P90 Lines/Hour', f"{kpi.get('p90_lines_per_hour', 0):.0f}"],
            ['Total Pieces', f"{kpi.get('total_units', 0):,}", 'Unique SKU', f"{kpi.get('unique_sku', 0):,}"],
        ]
        pk_table = Table(perf_kpi_data, colWidths=[5 * cm, 3 * cm, 5 * cm, 3 * cm])
        pk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1d4ed8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
        ]))
        story.append(pk_table)
        story.append(Spacer(1, 0.5 * cm))

        story.extend(_section('Performance Charts', heading_style))
        _add_chart(story, _chart_daily(performance_data.get('daily_metrics', [])), 'Daily Activity — Lines per Day', caption_style)
        _add_chart(story, _chart_heatmap(performance_data.get('datehour_metrics', [])), 'Hourly Heatmap — Lines by Date × Hour', caption_style)
        _add_chart(story, _chart_hourly(performance_data.get('hourly_metrics', [])), 'Hourly Throughput Profile — Avg Lines by Hour of Day', caption_style)
        _add_chart(story, _chart_weekly(performance_data.get('weekly_trends', [])), 'Weekly Trend — Lines per Week', caption_style)
        _add_chart(story, _chart_weekday(performance_data.get('weekday_profile', [])), 'Day-of-Week Profile — Avg Lines per Day', caption_style)
        _add_chart(story, _chart_lpo_dist(performance_data.get('lines_per_order_dist', [])), 'Lines per Order Distribution', caption_style)

    # ── Footer ───────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        'This report was generated by Datavisor. '
        'Borderline items fit within tolerance threshold. '
        'Locations required assume full stock stored on single carrier type.',
        small_style,
    ))

    doc.build(story)
    return buf.getvalue()
