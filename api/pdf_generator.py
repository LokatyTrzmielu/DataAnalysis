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
    KeepTogether,
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
    fig.savefig(buf, format='png', dpi=200, bbox_inches='tight', facecolor='white')
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
    fig, ax = plt.subplots(figsize=(_PAGE_W / 2.54, 6))
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
    return _fig_to_rl_image(fig, 9)


def _chart_volume_dist(rows: list) -> Image | None:
    vals = [r.get('volume_m3') for r in rows if r.get('volume_m3') is not None]
    if not vals:
        return None
    fig, ax = plt.subplots(figsize=(_PAGE_W / 2.54, 5.5))
    ax.hist(vals, bins=40, color=_C_PRIMARY, edgecolor='white', linewidth=0.4, zorder=3)
    ax.set_xlabel('Volume (m³)')
    ax.set_ylabel('SKU Count')
    _style_ax(ax)
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return _fig_to_rl_image(fig, 8)


def _chart_weight_dist(rows: list) -> Image | None:
    vals = [r.get('weight_kg') for r in rows if r.get('weight_kg') is not None]
    if not vals:
        return None
    fig, ax = plt.subplots(figsize=(_PAGE_W / 2.54, 5.5))
    ax.hist(vals, bins=40, color=_C_PRIMARY, edgecolor='white', linewidth=0.4, zorder=3)
    ax.set_xlabel('Weight (kg)')
    ax.set_ylabel('SKU Count')
    _style_ax(ax)
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return _fig_to_rl_image(fig, 8)


def _chart_margin_dist(rows: list) -> Image | None:
    vals = [
        r.get('margin_mm')
        for r in rows
        if r.get('fit_status') in ('FIT', 'BORDERLINE') and r.get('margin_mm') is not None
    ]
    if not vals:
        return None
    fig, ax = plt.subplots(figsize=(_PAGE_W / 2.54, 5.5))
    ax.hist(vals, bins=40, color=_C_PURPLE, edgecolor='white', linewidth=0.4, zorder=3)
    ax.set_xlabel('Margin (mm)')
    ax.set_ylabel('SKU Count')
    _style_ax(ax)
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return _fig_to_rl_image(fig, 8)


def _chart_dims_dist(rows: list) -> Image | None:
    l_vals = [r.get('length_mm') for r in rows if r.get('length_mm') is not None]
    w_vals = [r.get('width_mm') for r in rows if r.get('width_mm') is not None]
    h_vals = [r.get('height_mm') for r in rows if r.get('height_mm') is not None]
    if not (l_vals or w_vals or h_vals):
        return None
    fig, ax = plt.subplots(figsize=(_PAGE_W / 2.54, 5.5))
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
    return _fig_to_rl_image(fig, 8)


# ── Performance charts ───────────────────────────────────────────────────────

def _chart_daily(daily_metrics: list) -> Image | None:
    if not daily_metrics:
        return None
    dates = [m['date'] for m in daily_metrics]
    lines = [m['lines'] for m in daily_metrics]
    fig, ax = plt.subplots(figsize=(_PAGE_W / 2.54, 5.5))
    ax.bar(range(len(dates)), lines, color=_C_PRIMARY, zorder=3)
    step = max(1, len(dates) // 12)
    ax.set_xticks(range(0, len(dates), step))
    ax.set_xticklabels([dates[i] for i in range(0, len(dates), step)], rotation=45, ha='right', fontsize=7)
    ax.set_ylabel('Lines')
    _style_ax(ax)
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return _fig_to_rl_image(fig, 8)


def _chart_hourly(hourly_metrics: list) -> Image | None:
    if not hourly_metrics:
        return None
    hours = [f"{m['hour']:02d}:00" for m in hourly_metrics]
    lines = [m['lines'] for m in hourly_metrics]
    fig, ax = plt.subplots(figsize=(_PAGE_W / 2.54, 5.5))
    ax.bar(range(len(hours)), lines, color=_C_PRIMARY, zorder=3)
    ax.set_xticks(range(len(hours)))
    ax.set_xticklabels(hours, rotation=45, ha='right', fontsize=7)
    ax.set_ylabel('Lines')
    _style_ax(ax)
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return _fig_to_rl_image(fig, 8)


def _chart_weekly(weekly_trends: list) -> Image | None:
    if len(weekly_trends) < 2:
        return None
    labels = [f"W{m['week']:02d} {m['year']}" for m in weekly_trends]
    lines = [m['lines'] for m in weekly_trends]
    fig, ax = plt.subplots(figsize=(_PAGE_W / 2.54, 5.5))
    ax.bar(range(len(labels)), lines, color=_C_PRIMARY, zorder=3)
    step = max(1, len(labels) // 12)
    ax.set_xticks(range(0, len(labels), step))
    ax.set_xticklabels([labels[i] for i in range(0, len(labels), step)], rotation=45, ha='right', fontsize=7)
    ax.set_ylabel('Lines')
    _style_ax(ax)
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return _fig_to_rl_image(fig, 8)


def _chart_weekday(weekday_profile: list) -> Image | None:
    if not weekday_profile:
        return None
    days = [m['day'] for m in weekday_profile]
    vals = [m['avg_lines'] for m in weekday_profile]
    fig, ax = plt.subplots(figsize=(_PAGE_W / 2.54, 5.5))
    ax.bar(range(len(days)), vals, color=_C_PRIMARY, zorder=3)
    ax.set_xticks(range(len(days)))
    ax.set_xticklabels(days, fontsize=8)
    ax.set_ylabel('Avg Lines / Day')
    _style_ax(ax)
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return _fig_to_rl_image(fig, 8)


def _chart_lpo_dist(lpo_dist: list) -> Image | None:
    if not lpo_dist:
        return None
    bins = [m['bin'] for m in lpo_dist]
    counts = [m['count'] for m in lpo_dist]
    fig, ax = plt.subplots(figsize=(_PAGE_W / 2.54, 5.5))
    ax.bar(range(len(bins)), counts, color=_C_PRIMARY, zorder=3)
    ax.set_xticks(range(len(bins)))
    ax.set_xticklabels(bins, fontsize=8)
    ax.set_xlabel('Lines per Order')
    ax.set_ylabel('Order Count')
    _style_ax(ax)
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return _fig_to_rl_image(fig, 8)


def _chart_heatmap(datehour_metrics: list) -> Image | None:
    if not datehour_metrics:
        return None
    dates = sorted(set(m['date'] for m in datehour_metrics))
    data = {(m['date'], m['hour']): m['lines'] for m in datehour_metrics}
    z = [[data.get((date, h), 0) for h in range(24)] for date in dates]
    n_dates = len(dates)
    fig_h = max(5, min(8, n_dates * 0.25 + 2.5))
    fig, ax = plt.subplots(figsize=(_PAGE_W / 2.54, fig_h))
    im = ax.pcolormesh(
        list(range(24)), list(range(n_dates)), z,
        cmap='Blues', vmin=0, shading='auto',
    )
    step = max(1, n_dates // 10)
    tick_positions = list(range(0, n_dates, step))
    ax.set_yticks(tick_positions)
    ax.set_yticklabels([dates[i] for i in tick_positions], fontsize=8)
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


def _add_chart(story: list, img: Image | None, caption: str, caption_style, keep_together: bool = True) -> None:
    if img is None:
        return
    elements = [
        Paragraph(caption, caption_style),
        Spacer(1, 0.2 * cm),
        img,
        Spacer(1, 0.6 * cm),
    ]
    if keep_together:
        story.append(KeepTogether(elements))
    else:
        story.extend(elements)


def _kpi_4col_table(pairs: list[tuple[str, str]], col_widths: list) -> Table:
    """Build a 4-column (Metric, Value, Metric, Value) KPI table from a list of (metric, value) pairs."""
    header = ['Metric', 'Value', 'Metric', 'Value']
    rows = [header]
    for i in range(0, len(pairs), 2):
        if i + 1 < len(pairs):
            rows.append([pairs[i][0], pairs[i][1], pairs[i + 1][0], pairs[i + 1][1]])
        else:
            rows.append([pairs[i][0], pairs[i][1], '', ''])
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
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
    return t


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

    avg_l = capacity_data.get('avg_length_mm', 0) or 0
    avg_w = capacity_data.get('avg_width_mm', 0) or 0
    avg_h = capacity_data.get('avg_height_mm', 0) or 0
    avg_wt = capacity_data.get('avg_weight_kg', 0) or 0

    borderline_mm = capacity_data.get('borderline_threshold_mm')
    brd_label = f"BORDERLINE ({borderline_mm:g}mm)" if borderline_mm is not None else "BORDERLINE"

    kpi_data = [
        ['Metric', 'Value'],
        ['Total SKU', str(capacity_data.get('total_sku', '-'))],
        ['Fit %', f"{capacity_data.get('fit_percentage', 0):.1f}%"],
        ['FIT', str(capacity_data.get('fit_count', '-'))],
        [brd_label, str(capacity_data.get('borderline_count', '-'))],
        ['NOT FIT', str(capacity_data.get('not_fit_count', '-'))],
        ['Avg Length (mm)', f"{avg_l:.1f}"],
        ['Avg Width (mm)', f"{avg_w:.1f}"],
        ['Avg Height (mm)', f"{avg_h:.1f}"],
        ['Avg Weight (kg)', f"{avg_wt:.3f}"],
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

    # ── Carrier Settings table ───────────────────────────────────────────────
    carrier_settings: dict[str, Any] = capacity_data.get('carrier_settings', {})
    carrier_stats: dict[str, Any] = capacity_data.get('carrier_stats', {})
    active_carrier_ids = [cid for cid in carrier_stats if cid != 'NONE']
    if carrier_settings and active_carrier_ids:
        story.append(Paragraph('Carrier Settings', subheading_style))
        cs_header = ['Carrier', 'Length (mm)', 'Width (mm)', 'Height (mm)', 'Max Weight (kg)']
        cs_rows = [cs_header]
        for cid in active_carrier_ids:
            if cid in carrier_settings:
                cfg = carrier_settings[cid]
                cs_rows.append([
                    cfg.get('name', cid),
                    f"{cfg.get('inner_length_mm', 0):.0f}",
                    f"{cfg.get('inner_width_mm', 0):.0f}",
                    f"{cfg.get('inner_height_mm', 0):.0f}",
                    f"{cfg.get('max_weight_kg', 0):.1f}",
                ])
        col_widths_cs = [4.5 * cm, 2.8 * cm, 2.8 * cm, 2.8 * cm, 3.1 * cm]
        cs_table = Table(cs_rows, colWidths=col_widths_cs)
        cs_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ]))
        story.append(cs_table)
        story.append(Spacer(1, 0.5 * cm))

    # ── Carrier Breakdown table ──────────────────────────────────────────────
    if carrier_stats:
        story.append(Paragraph('Carrier Breakdown', subheading_style))
        header = ['Carrier', 'Fit %', 'FIT', 'BRDLN', 'NOT FIT', 'Locations', 'Avg Fill', 'Total Vol (m³)', 'Stock Vol (m³)']
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
                f"{cs.get('total_volume_m3', 0):.2f}",
                f"{cs.get('stock_volume_m3', 0):.2f}",
            ])
        col_widths = [3.5 * cm, 1.5 * cm, 1.4 * cm, 1.5 * cm, 1.5 * cm, 2.0 * cm, 1.5 * cm, 2.1 * cm, 2.0 * cm]
        ct = Table(rows_table, colWidths=col_widths)
        ct.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ('PADDING', (0, 0), (-1, -1), 4),
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

        col_w = [5 * cm, 3 * cm, 5 * cm, 3 * cm]

        # Productive hours & Data scope info block
        prod_hours = performance_data.get('productive_hours_per_shift', 7.0)
        scope_info = performance_data.get('data_scope', {})
        if scope_info.get('type') == 'carriers':
            cids = scope_info.get('carrier_ids', [])
            c_settings = capacity_data.get('carrier_settings', {}) if capacity_data else {}
            scope_label = ', '.join(
                c_settings.get(cid, {}).get('name', cid) for cid in cids
            ) or ', '.join(cids)
        else:
            scope_label = 'Entire file'
        info_data = [
            ['Productive hours / shift', f'{prod_hours:g}h'],
            ['Data scope', scope_label],
        ]
        info_table = Table(info_data, colWidths=[6 * cm, 10 * cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#f0f4ff'), colors.white]),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.4 * cm))

        # Totals & Per Order
        story.append(Paragraph('Totals', subheading_style))
        totals_pairs = [
            ('Total Lines', f"{kpi.get('total_lines', 0):,}"),
            ('Total Orders', f"{kpi.get('total_orders', 0):,}"),
            ('Total Pieces', f"{kpi.get('total_units', 0):,}"),
            ('Unique SKU', f"{kpi.get('unique_sku', 0):,}"),
            ('Avg Lines / Order', f"{kpi.get('avg_lines_per_order', 0):.2f}"),
            ('Avg Units / Order', f"{kpi.get('avg_units_per_order', 0):.2f}"),
        ]
        story.append(_kpi_4col_table(totals_pairs, col_w))
        story.append(Spacer(1, 0.4 * cm))

        # Hourly Throughput
        story.append(Paragraph('Hourly Throughput', subheading_style))
        hourly_pairs = [
            ('Avg Lines / Hour', f"{kpi.get('avg_lines_per_hour', 0):.1f}"),
            ('Avg Orders / Hour', f"{kpi.get('avg_orders_per_hour', 0):.1f}"),
            ('Avg Units / Hour', f"{kpi.get('avg_units_per_hour', 0):.1f}"),
            ('Median Lines / Hour', f"{kpi.get('median_lines_per_hour', 0):.1f}"),
            ('Median Orders / Hour', f"{kpi.get('median_orders_per_hour', 0):.1f}"),
            ('Median Units / Hour', f"{kpi.get('median_units_per_hour', 0):.1f}"),
            ('Peak Lines / Hour', f"{kpi.get('peak_lines_per_hour', 0):,}"),
            ('Peak Orders / Hour', f"{kpi.get('peak_orders_per_hour', 0):,}"),
            ('Peak Units / Hour', f"{kpi.get('peak_units_per_hour', 0):,}"),
            ('P90 Lines / Hour', f"{kpi.get('p90_lines_per_hour', 0):.0f}"),
            ('P95 Lines / Hour', f"{kpi.get('p95_lines_per_hour', 0):.0f}"),
            ('P99 Lines / Hour', f"{kpi.get('p99_lines_per_hour', 0):.0f}"),
        ]
        story.append(_kpi_4col_table(hourly_pairs, col_w))
        story.append(Spacer(1, 0.4 * cm))

        # Daily
        story.append(Paragraph('Daily', subheading_style))
        daily_pairs = [
            ('Avg Lines / Day', f"{kpi.get('avg_lines_per_day', 0):.1f}"),
            ('Avg Orders / Day', f"{kpi.get('avg_orders_per_day', 0):.1f}"),
            ('Avg Units / Day', f"{kpi.get('avg_units_per_day', 0):.1f}"),
            ('Median Lines / Day', f"{kpi.get('median_lines_per_day', 0):.1f}"),
            ('Median Orders / Day', f"{kpi.get('median_orders_per_day', 0):.1f}"),
            ('Median Units / Day', f"{kpi.get('median_units_per_day', 0):.1f}"),
            ('Max Lines / Day', f"{kpi.get('max_lines_per_day', 0):,}"),
            ('Max Orders / Day', f"{kpi.get('max_orders_per_day', 0):,}"),
            ('Max Units / Day', f"{kpi.get('max_units_per_day', 0):,}"),
        ]
        story.append(_kpi_4col_table(daily_pairs, col_w))
        story.append(Spacer(1, 0.4 * cm))

        # Per Shift
        story.append(Paragraph('Per Shift', subheading_style))
        shift_pairs = [
            ('Avg Lines / Shift', f"{kpi.get('avg_lines_per_shift', 0):.1f}"),
            ('Avg Orders / Shift', f"{kpi.get('avg_orders_per_shift', 0):.1f}"),
            ('Avg Units / Shift', f"{kpi.get('avg_units_per_shift', 0):.1f}"),
            ('Median Lines / Shift', f"{kpi.get('median_lines_per_shift', 0):.1f}"),
            ('Median Orders / Shift', f"{kpi.get('median_orders_per_shift', 0):.1f}"),
            ('Median Units / Shift', f"{kpi.get('median_units_per_shift', 0):.1f}"),
            ('Max Lines / Shift', f"{kpi.get('max_lines_per_shift', 0):.0f}"),
            ('Max Orders / Shift', f"{kpi.get('max_orders_per_shift', 0):.0f}"),
            ('Max Units / Shift', f"{kpi.get('max_units_per_shift', 0):.0f}"),
        ]
        story.append(_kpi_4col_table(shift_pairs, col_w))
        story.append(Spacer(1, 0.5 * cm))

        # Pareto Concentration — start on a new page so the table is never clipped
        pareto_bands = performance_data.get('pareto_bands', [])
        if pareto_bands:
            story.append(PageBreak())
            story.append(Paragraph('Pareto Concentration', subheading_style))
            pareto_header = ['MovedSKU', 'CumulSKU%', 'Lines/Day', 'Lines%', 'Cumul.Lines%', 'Pieces/Day', 'Pieces%', 'Cumul.Pieces%']
            pareto_rows = [pareto_header]
            for b in pareto_bands:
                pareto_rows.append([
                    str(b.get('moved_sku', '')),
                    f"{b.get('cumulated_sku_pct', 0):.1f}%",
                    f"{b.get('lines_day', 0):.1f}",
                    f"{b.get('lines_day_pct', 0):.1f}%",
                    f"{b.get('cumulated_lines_pct', 0):.1f}%",
                    f"{b.get('pieces_day', 0):.1f}",
                    f"{b.get('pieces_day_pct', 0):.1f}%",
                    f"{b.get('cumulated_pieces_pct', 0):.1f}%",
                ])
            col_w_pareto = [2.1*cm, 2.0*cm, 2.2*cm, 1.8*cm, 2.5*cm, 2.3*cm, 1.8*cm, 2.3*cm]
            pt = Table(pareto_rows, colWidths=col_w_pareto)
            pt.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e5e7eb')),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(pt)
            story.append(Spacer(1, 0.4 * cm))

        story.extend(_section('Performance Charts', heading_style))
        _add_chart(story, _chart_daily(performance_data.get('daily_metrics', [])), 'Daily Activity — Lines per Day', caption_style)
        _add_chart(story, _chart_heatmap(performance_data.get('datehour_metrics', [])), 'Hourly Heatmap — Lines by Date × Hour', caption_style)
        _add_chart(story, _chart_hourly(performance_data.get('hourly_metrics', [])), 'Hourly Throughput Profile — Avg Lines by Hour of Day', caption_style)
        _add_chart(story, _chart_weekly(performance_data.get('weekly_trends', [])), 'Weekly Trend — Lines per Week', caption_style)
        _add_chart(story, _chart_weekday(performance_data.get('weekday_profile', [])), 'Day-of-Week Profile — Avg Lines per Day', caption_style)
        _add_chart(story, _chart_lpo_dist(performance_data.get('lines_per_order_dist', [])), 'Lines per Order Distribution', caption_style)

    doc.build(story)
    return buf.getvalue()


# ── Container Order Calculator (Tools › second tile) ────────────────────────

def _chart_bins_per_variant(summaries: list) -> Image | None:
    """Bar chart: bins to order per variant code, coloured by height tier."""
    if not summaries:
        return None
    codes = [s.code for s in summaries]
    bins = [s.bins_required for s in summaries]
    heights = [s.bin_height_mm for s in summaries]
    height_colors = {138: '#93c5fd', 188: '#60a5fa', 238: '#3b82f6', 288: '#1d4ed8'}
    bar_colors = [height_colors.get(h, _C_PRIMARY) for h in heights]

    fig, ax = plt.subplots(figsize=(_PAGE_W / 2.54, 5))
    ax.bar(range(len(codes)), bins, color=bar_colors, zorder=3)
    ax.set_xticks(range(len(codes)))
    ax.set_xticklabels(codes, rotation=35, ha='right', fontsize=8)
    ax.set_ylabel('Bins to order')
    _style_ax(ax)
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return _fig_to_rl_image(fig, 7.5)


def generate_container_order_pdf(plan, params, run, user=None) -> bytes:
    """Two-page summary PDF for a container order plan.

    Args:
        plan: api.schemas.container_order.ContainerPlanResponse
        params: PlanParamsRequest
        run: SQLAlchemy AnalysisRun (used for client name + analysis context)
        user: SQLAlchemy User who triggered the export; surfaced as the
              "Generated by" row in the parameters block.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=2 * cm, leftMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'title', parent=styles['Title'], fontSize=20, textColor=colors.HexColor('#111827'),
        spaceAfter=6,
    )
    sub_style = ParagraphStyle(
        'sub', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#6b7280'),
        spaceAfter=14,
    )
    heading_style = ParagraphStyle(
        'h', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#111827'),
        spaceAfter=8,
    )
    caption_style = ParagraphStyle(
        'cap', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#6b7280'),
    )

    story: list = []
    story.append(Paragraph('Container Order — Kardex VBM Box', title_style))
    story.append(Paragraph(
        f"Client: <b>{run.client_name}</b> · Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        sub_style,
    ))

    # KPI block
    kpi_pairs = [
        ('Total bins to order', f"{plan.total_bins:,}"),
        ('SKUs planned', f"{plan.total_sku_planned:,}"),
        ('SKUs covered', f"{plan.total_sku_covered:,}  ({plan.coverage_pct:.1f}%)"),
        ('Avg cell fill', f"{plan.avg_fill_pct:.1f}%"),
        ('Variants selected', str(len(plan.summaries))),
        ('Orphans (no variant)', str(len(plan.orphans))),
    ]
    story.append(_kpi_4col_table(kpi_pairs, [4.2 * cm, 3.8 * cm, 4.2 * cm, 3.8 * cm]))
    story.append(Spacer(1, 0.6 * cm))

    # Bar chart
    _add_chart(story, _chart_bins_per_variant(plan.summaries),
               'Bins required per variant', caption_style)

    # Variant table — Bases + Frames columns give the procurement breakdown.
    story.append(Paragraph('Order summary', heading_style))
    table_data = [['Variant', 'Footprint', 'Height', 'Cell (mm)', 'Locs/bin',
                   'SKU', 'Locations', 'Bins', 'Bases', 'Frames', 'Avg fill']]
    for s in plan.summaries:
        cell = f"{s.cell_length_mm}×{s.cell_width_mm}×{s.cell_height_mm}"
        table_data.append([
            s.code, s.footprint_label, str(s.bin_height_mm), cell,
            str(s.locations_per_bin), str(s.sku_count), str(s.total_locations),
            str(s.bins_required),
            str(s.bins_required),               # Bases = bins
            str(s.total_frames_required),       # Frames
            f"{s.avg_fill_pct:.0f}%",
        ])
    total_locations = sum(s.total_locations for s in plan.summaries)
    table_data.append(['TOTAL', '', '', '', '', str(plan.total_sku_covered),
                       str(total_locations), str(plan.total_bins),
                       str(plan.total_bins),                # Bases total
                       str(plan.total_frames),              # Frames total
                       f"{plan.avg_fill_pct:.0f}%"])
    t = Table(table_data, colWidths=[2.0 * cm, 2.8 * cm, 1.3 * cm, 2.0 * cm, 1.3 * cm,
                                      1.2 * cm, 1.7 * cm, 1.2 * cm, 1.2 * cm, 1.2 * cm,
                                      1.4 * cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#d1d5db')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f9fafb')]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e5e7eb')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (4, 0), (-1, -1), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.6 * cm))

    # Parameters echo
    story.append(PageBreak())
    story.append(Paragraph('Parameters used', heading_style))
    if user is not None:
        _u_name = getattr(user, "name", None) or ""
        _u_email = getattr(user, "email", None) or ""
        generated_by = f"{_u_name} <{_u_email}>" if _u_name and _u_email else (_u_name or _u_email or "—")
    else:
        generated_by = "—"

    param_rows = [
        ['Generated by', generated_by],
        ['Mode', params.mode],
        ['Goal', params.auto_goal if params.mode == 'auto' else (params.guided_preset if params.mode == 'guided' else 'manual')],
        ['ABC filter', ', '.join(params.abc_classes) or 'all'],
        ['Only Machine', 'Yes' if params.only_machine else 'No'],
        ['Stock multiplier', f"{params.stock_multiplier:.2f}"],
        ['Location fill rate', f"{params.location_fill_rate * 100:.0f}%"],
        ['Locations per SKU (min / max)', f"{params.min_locations_per_sku} / {params.max_locations_per_sku}"],
    ]
    pt = Table(param_rows, colWidths=[6 * cm, 10 * cm])
    pt.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#e5e7eb')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6b7280')),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(pt)

    if plan.orphans:
        story.append(Spacer(1, 0.6 * cm))
        story.append(Paragraph(
            f"<b>{len(plan.orphans)} SKU(s) without an assigned variant</b> "
            "— see the .xlsx export, sheet 'Orphans', for the full list.",
            caption_style,
        ))

    doc.build(story)
    return buf.getvalue()
