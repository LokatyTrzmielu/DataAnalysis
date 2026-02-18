"""Theme configuration for the Streamlit app - light theme with gold accent."""

# Paleta kolorów - jasny motyw ze złotym akcentem
COLORS = {
    # === TŁA ===
    "background": "#f0ede8",       # ciepły jasny beż — sidebar
    "surface": "#faf9f6",          # prawie-biały — główne tło
    "surface_elevated": "#ffffff", # czysty biały — karty, inputy
    "surface_light": "#e8e4de",    # ciepły jasny — hover, wyróżnienia

    # === AKCENTY ===
    "accent": "#c9a227",           # złoty — główny akcent (bez zmian)
    "accent_dark": "#a8861f",      # ciemniejsze złoto — hover
    "accent_muted": "#e8d9a0",     # jasne złoto — subtelne bordery

    # === FUNKCJONALNE ===
    "primary": "#2e7d32",          # ciemniejszy zielony (lepszy kontrast na jasnym)
    "error": "#c62828",            # ciemniejszy czerwony
    "warning": "#e6a817",          # ciepły bursztynowy (odrębny od accent)
    "info": "#8a817c",             # ciepły szary

    # === TEKST ===
    "text": "#2d2926",             # ciemny brąz — tekst główny
    "text_secondary": "#6b6560",   # ciepły ciemnoszary — tekst drugorzędny

    # === BORDERY ===
    "border": "#d5d0c8",           # jasny ciepły border
}

# Kolory dla 7 typów statusu (ciemniejsze warianty dla jasnego tła)
STATUS_COLORS = {
    "pending": "#e6a817",       # ciemniejszy żółty
    "in_progress": "#1976D2",   # ciemniejszy niebieski
    "submitted": "#7B1FA2",     # ciemniejszy fioletowy
    "in_review": "#E65100",     # ciemniejszy pomarańczowy
    "success": "#2E7D32",       # ciemniejszy zielony
    "failed": "#C62828",        # ciemniejszy czerwony
    "expired": "#546E7A",       # ciemniejszy szary
}

# Ikony SVG dla statusów
STATUS_ICONS = {
    "pending": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/></svg>',
    "in_progress": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="4 2"><circle cx="12" cy="12" r="10"/></svg>',
    "submitted": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>',
    "in_review": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>',
    "success": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9 12l2 2 4-4"/></svg>',
    "failed": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6M9 9l6 6"/></svg>',
    "expired": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>',
}


def get_custom_css() -> str:
    """Return custom CSS for light theme styling."""
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Główne tło i tekst */
    .stApp {{
        background-color: {COLORS["surface"]};
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }}

    /* Karty KPI — equal height in column rows */
    [data-testid="stColumn"]:has(.kpi-card) > div,
    [data-testid="stColumn"]:has(.kpi-card) > div > div,
    [data-testid="stColumn"]:has(.kpi-card) > div > div > div,
    [data-testid="stColumn"]:has(.kpi-card) > div > div > div > div,
    [data-testid="stColumn"]:has(.kpi-card) > div > div > div > div > div {{
        height: 100%;
    }}

    .kpi-card {{
        background-color: {COLORS["surface_elevated"]};
        border-radius: 8px;
        padding: 1.25rem;
        border: 1px solid {COLORS["border"]};
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
        height: 100%;
        box-sizing: border-box;
    }}

    .kpi-card h3 {{
        color: {COLORS["text_secondary"]};
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0 0 0.5rem 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    .kpi-card .value {{
        color: {COLORS["text"]};
        font-size: 1.75rem;
        font-weight: 600;
        margin: 0;
    }}

    .kpi-card .delta {{
        font-size: 0.85rem;
        margin-top: 0.25rem;
    }}

    .kpi-card .delta.positive {{
        color: {COLORS["primary"]};
    }}

    .kpi-card .delta.negative {{
        color: {COLORS["error"]};
    }}

    .kpi-card .help-text {{
        color: {COLORS["text_secondary"]};
        font-size: 0.75rem;
        margin-top: 0.25rem;
        margin-bottom: 0;
    }}

    /* Nagłówki sekcji */
    .section-header {{
        color: {COLORS["text"]};
        font-size: 1.1rem;
        font-weight: 600;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
        border-bottom: 1px solid {COLORS["border"]};
    }}

    .section-header .icon {{
        margin-right: 0.5rem;
    }}

    /* Przyciski statusów - 7 typów */
    .status-btn {{
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-size: 0.875rem;
        font-weight: 500;
        border: 1px solid;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        cursor: default;
    }}

    .status-btn:hover {{
        transform: scale(1.02);
    }}

    .status-btn.pending {{
        background-color: rgba(230, 168, 23, 0.10);
        border-color: rgba(230, 168, 23, 0.3);
        color: {STATUS_COLORS["pending"]};
    }}

    .status-btn.in_progress {{
        background-color: rgba(25, 118, 210, 0.10);
        border-color: rgba(25, 118, 210, 0.3);
        color: {STATUS_COLORS["in_progress"]};
    }}

    .status-btn.submitted {{
        background-color: rgba(123, 31, 162, 0.10);
        border-color: rgba(123, 31, 162, 0.3);
        color: {STATUS_COLORS["submitted"]};
    }}

    .status-btn.in_review {{
        background-color: rgba(230, 81, 0, 0.10);
        border-color: rgba(230, 81, 0, 0.3);
        color: {STATUS_COLORS["in_review"]};
    }}

    .status-btn.success {{
        background-color: rgba(46, 125, 50, 0.10);
        border-color: rgba(46, 125, 50, 0.3);
        color: {STATUS_COLORS["success"]};
    }}

    .status-btn.failed {{
        background-color: rgba(198, 40, 40, 0.10);
        border-color: rgba(198, 40, 40, 0.3);
        color: {STATUS_COLORS["failed"]};
    }}

    .status-btn.expired {{
        background-color: rgba(84, 110, 122, 0.10);
        border-color: rgba(84, 110, 122, 0.3);
        color: {STATUS_COLORS["expired"]};
    }}

    /* Legacy .status-badge support (backwards compat) */
    .status-badge {{
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-size: 0.875rem;
        font-weight: 500;
        border: 1px solid;
    }}

    .status-badge.success {{
        background-color: rgba(46, 125, 50, 0.10);
        border-color: rgba(46, 125, 50, 0.3);
        color: {STATUS_COLORS["success"]};
    }}

    .status-badge.warning {{
        background-color: rgba(230, 168, 23, 0.10);
        border-color: rgba(230, 168, 23, 0.3);
        color: {STATUS_COLORS["pending"]};
    }}

    .status-badge.error {{
        background-color: rgba(198, 40, 40, 0.10);
        border-color: rgba(198, 40, 40, 0.3);
        color: {STATUS_COLORS["failed"]};
    }}

    .status-badge.info {{
        background-color: rgba(25, 118, 210, 0.10);
        border-color: rgba(25, 118, 210, 0.3);
        color: {STATUS_COLORS["in_progress"]};
    }}

    /* Stylizacja tabel */
    .stDataFrame {{
        background-color: {COLORS["surface_elevated"]};
    }}

    .stDataFrame [data-testid="stDataFrameResizable"] {{
        background-color: {COLORS["surface_elevated"]};
    }}

    /* Expanders */
    .streamlit-expanderHeader {{
        background-color: {COLORS["surface_elevated"]};
        border-radius: 8px;
    }}

    .streamlit-expanderContent {{
        background-color: {COLORS["surface_elevated"]};
        border-radius: 0 0 8px 8px;
    }}

    /* Buttons */
    .stButton > button {{
        background-color: {COLORS["accent"]};
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 500;
        transition: background-color 0.2s;
    }}

    .stButton > button:hover {{
        background-color: {COLORS["accent_dark"]};
    }}

    /* Sidebar styling */
    [data-testid="stSidebar"] {{
        background-color: {COLORS["background"]};
        border-right: 1px solid {COLORS["border"]};
    }}

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: {COLORS["surface_elevated"]};
        border-radius: 8px;
        padding: 0.25rem;
        gap: 0.5rem;
    }}

    .stTabs [data-baseweb="tab"] {{
        background-color: transparent;
        color: {COLORS["text_secondary"]};
        border-radius: 6px;
        padding: 0.5rem 1rem;
    }}

    .stTabs [aria-selected="true"] {{
        background-color: {COLORS["surface_light"]};
        color: {COLORS["text"]};
    }}

    /* File uploader - improved contrast */
    [data-testid="stFileUploader"] {{
        background-color: {COLORS["surface_elevated"]};
        border-radius: 8px;
        border: 2px dashed {COLORS["accent_muted"]};
    }}

    [data-testid="stFileUploader"]:hover {{
        border-color: {COLORS["accent"]};
        background-color: rgba(232, 217, 160, 0.2);
    }}

    /* Selectbox */
    .stSelectbox [data-baseweb="select"] {{
        background-color: {COLORS["surface_elevated"]};
    }}

    /* Number input */
    .stNumberInput input {{
        background-color: {COLORS["surface_elevated"]};
        color: {COLORS["text"]};
    }}

    /* Progress bar */
    .stProgress > div > div {{
        background-color: {COLORS["accent"]};
    }}

    /* Metric styling */
    [data-testid="stMetricValue"] {{
        color: {COLORS["text"]};
    }}

    [data-testid="stMetricLabel"] {{
        color: {COLORS["text_secondary"]};
    }}

    /* Container cards */
    .card-container {{
        background-color: {COLORS["surface_elevated"]};
        border-radius: 8px;
        padding: 1.5rem;
        border: 1px solid {COLORS["border"]};
        margin-bottom: 1rem;
    }}

    /* Chart containers */
    .chart-container {{
        background-color: {COLORS["surface_elevated"]};
        border-radius: 8px;
        padding: 1rem;
        border: 1px solid {COLORS["border"]};
    }}

    .chart-container h4 {{
        color: {COLORS["text"]};
        margin: 0 0 1rem 0;
        font-size: 1rem;
        font-weight: 500;
    }}

    /* ===== ETAP 2: Rozszerzone style ===== */

    /* KPI Card hover effects */
    .kpi-card {{
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    }}

    .kpi-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        border-color: {COLORS["surface_light"]};
    }}

    /* Status btn/badge hover */
    .status-badge, .status-btn {{
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        cursor: default;
    }}

    .status-badge:hover, .status-btn:hover {{
        transform: scale(1.02);
    }}

    /* Card container hover */
    .card-container {{
        transition: border-color 0.2s ease;
    }}

    .card-container:hover {{
        border-color: {COLORS["surface_light"]};
    }}

    /* Section header with icon alignment */
    .section-header {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}

    /* Table container styling */
    .table-container {{
        background-color: {COLORS["surface_elevated"]};
        border-radius: 8px;
        padding: 1rem;
        border: 1px solid {COLORS["border"]};
        overflow-x: auto;
    }}

    .table-container h4 {{
        color: {COLORS["text"]};
        margin: 0 0 1rem 0;
        font-size: 1rem;
        font-weight: 500;
    }}

    /* Info box styling */
    .info-box {{
        background-color: rgba(138, 129, 124, 0.10);
        border-left: 3px solid {COLORS["info"]};
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }}

    .info-box p {{
        color: {COLORS["text"]};
        margin: 0;
    }}

    /* Warning box styling */
    .warning-box {{
        background-color: rgba(201, 162, 39, 0.10);
        border-left: 3px solid {COLORS["warning"]};
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }}

    .warning-box p {{
        color: {COLORS["text"]};
        margin: 0;
    }}

    /* Error box styling */
    .error-box {{
        background-color: rgba(198, 40, 40, 0.10);
        border-left: 3px solid {COLORS["error"]};
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }}

    .error-box p {{
        color: {COLORS["text"]};
        margin: 0;
    }}

    /* Success box styling */
    .success-box {{
        background-color: rgba(46, 125, 50, 0.10);
        border-left: 3px solid {COLORS["primary"]};
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }}

    .success-box p {{
        color: {COLORS["text"]};
        margin: 0;
    }}

    /* Forward guidance banner */
    .forward-guidance {{
        background-color: rgba(201, 162, 39, 0.08);
        border: 1px solid {COLORS["accent_muted"]};
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin: 1rem 0;
        color: {COLORS["text"]};
        font-size: 0.9rem;
        font-weight: 500;
    }}

    .forward-guidance .arrow {{
        color: {COLORS["accent"]};
        margin-right: 0.5rem;
    }}

    /* Responsive grid for KPI cards */
    @media (max-width: 768px) {{
        /* Force 2 columns on tablet */
        [data-testid="stHorizontalBlock"] {{
            flex-wrap: wrap !important;
        }}

        [data-testid="stHorizontalBlock"] > [data-testid="stVerticalBlock"] {{
            flex: 0 0 calc(50% - 0.5rem) !important;
            min-width: calc(50% - 0.5rem) !important;
        }}

        .kpi-card {{
            padding: 0.75rem 1rem;
        }}

        .kpi-card .value {{
            font-size: 1.5rem;
        }}
    }}

    @media (max-width: 480px) {{
        /* Force 1 column on mobile */
        [data-testid="stHorizontalBlock"] > [data-testid="stVerticalBlock"] {{
            flex: 0 0 100% !important;
            min-width: 100% !important;
        }}

        .kpi-card {{
            padding: 0.75rem;
        }}

        .kpi-card .value {{
            font-size: 1.25rem;
        }}

        .kpi-card h3 {{
            font-size: 0.75rem;
        }}
    }}

    /* Scrollbar styling for light theme */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}

    ::-webkit-scrollbar-track {{
        background: {COLORS["background"]};
    }}

    ::-webkit-scrollbar-thumb {{
        background: {COLORS["surface_light"]};
        border-radius: 4px;
    }}

    ::-webkit-scrollbar-thumb:hover {{
        background: {COLORS["border"]};
    }}

    /* Loading spinner override */
    .stSpinner > div {{
        border-top-color: {COLORS["accent"]} !important;
    }}

    /* Toast/notification styling */
    .stAlert {{
        background-color: {COLORS["surface_elevated"]};
        border-radius: 8px;
    }}

    /* ===== ETAP 7: Report cards and preview styling ===== */

    /* Report category header */
    .report-category-header {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-top: 1.5rem;
        margin-bottom: 0.25rem;
    }}

    .report-category-header .category-icon {{
        font-size: 1.2rem;
    }}

    .report-category-header .category-name {{
        font-size: 1rem;
        font-weight: 600;
        color: {COLORS["text"]};
    }}

    .report-category-header .category-count {{
        font-size: 0.75rem;
        color: {COLORS["text_secondary"]};
        background-color: {COLORS["surface_light"]};
        padding: 0.15rem 0.5rem;
        border-radius: 10px;
        margin-left: auto;
    }}

    .category-desc {{
        font-size: 0.85rem;
        color: {COLORS["text_secondary"]};
        margin: 0 0 0.75rem 0;
    }}

    /* Report card */
    .report-card {{
        background-color: {COLORS["surface_elevated"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        transition: border-color 0.2s ease, transform 0.2s ease;
    }}

    .report-card:hover {{
        border-color: {COLORS["surface_light"]};
        transform: translateX(2px);
    }}

    .report-card .report-name {{
        font-size: 0.9rem;
        font-weight: 600;
        color: {COLORS["text"]};
        margin-bottom: 0.25rem;
    }}

    .report-card .report-desc {{
        font-size: 0.8rem;
        color: {COLORS["text_secondary"]};
        line-height: 1.3;
    }}

    /* Preview metrics */
    .preview-metric {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 0;
        border-bottom: 1px solid {COLORS["border"]};
    }}

    .preview-metric:last-child {{
        border-bottom: none;
    }}

    .preview-metric .metric-label {{
        font-size: 0.85rem;
        color: {COLORS["text_secondary"]};
    }}

    .preview-metric .metric-value {{
        font-size: 1rem;
        font-weight: 600;
        color: {COLORS["text"]};
    }}

    /* ===== Sidebar Navigation Styling ===== */

    /* Hide default radio button styling in sidebar */
    [data-testid="stSidebar"] .stRadio > div {{
        gap: 0 !important;
    }}

    [data-testid="stSidebar"] .stRadio > div > label {{
        display: block !important;
        width: 100% !important;
        padding: 0.75rem 1rem !important;
        margin: 0.15rem 0 !important;
        border-radius: 6px !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        background-color: transparent !important;
    }}

    /* Hide the radio circle */
    [data-testid="stSidebar"] .stRadio > div > label > div:first-child {{
        display: none !important;
    }}

    /* Style the text */
    [data-testid="stSidebar"] .stRadio > div > label > div:last-child {{
        color: {COLORS["text"]} !important;
        font-size: 0.95rem !important;
    }}

    /* Hover state - subtle background + dark gold color */
    [data-testid="stSidebar"] .stRadio > div > label:hover {{
        background-color: {COLORS["surface_light"]} !important;
    }}

    [data-testid="stSidebar"] .stRadio > div > label:hover > div:last-child {{
        color: {COLORS["accent_dark"]} !important;
        font-weight: 600 !important;
    }}

    /* Selected state - light rectangle with accent border */
    /* Modern CSS :has() selector for checked radio */
    [data-testid="stSidebar"] .stRadio > div > label:has(input:checked) {{
        background-color: {COLORS["surface_light"]} !important;
        border: 2px solid {COLORS["accent"]} !important;
    }}

    [data-testid="stSidebar"] .stRadio > div > label:has(input:checked) > div:last-child {{
        color: {COLORS["text"]} !important;
        font-weight: 600 !important;
    }}

    /* Fallback: aria-checked attribute */
    [data-testid="stSidebar"] .stRadio > div > label[aria-checked="true"] {{
        background-color: {COLORS["surface_light"]} !important;
        border: 2px solid {COLORS["accent"]} !important;
    }}

    [data-testid="stSidebar"] .stRadio > div > label[aria-checked="true"] > div:last-child {{
        color: {COLORS["text"]} !important;
        font-weight: 600 !important;
    }}

    /* Fallback: data-checked attribute */
    [data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] {{
        background-color: {COLORS["surface_light"]} !important;
        border: 2px solid {COLORS["accent"]} !important;
    }}

    [data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] > div:last-child {{
        color: {COLORS["text"]} !important;
        font-weight: 600 !important;
    }}

    /* ===== Sidebar Elements Visibility Fix ===== */

    /* Tytuł w sidebarze */
    [data-testid="stSidebar"] h1 {{
        color: {COLORS["text"]} !important;
    }}

    /* Nagłówki markdown w sidebarze */
    [data-testid="stSidebar"] h3 {{
        color: {COLORS["text"]} !important;
        font-size: 0.9rem !important;
    }}

    /* Alerty (st.success, st.info) w sidebarze - usunięcie obramowania */
    [data-testid="stSidebar"] .stAlert {{
        background-color: {COLORS["background"]} !important;
        border-radius: 6px !important;
        padding: 0.5rem 0.75rem !important;
        margin: 0.25rem 0 !important;
        border: none !important;
        border-left: none !important;
        box-shadow: none !important;
    }}

    [data-testid="stSidebar"] .stAlert > div {{
        border: none !important;
        border-left: none !important;
    }}

    [data-testid="stSidebar"] .stAlert p {{
        color: {COLORS["text"]} !important;
        font-size: 0.85rem !important;
    }}

    /* Alternatywne selektory dla alertów */
    [data-testid="stSidebar"] [data-testid="stAlert"] {{
        background-color: {COLORS["background"]} !important;
        border: none !important;
        border-left: none !important;
        box-shadow: none !important;
    }}

    [data-testid="stSidebar"] .element-container .stAlert,
    [data-testid="stSidebar"] [data-baseweb="notification"] {{
        border: none !important;
        border-left: none !important;
        box-shadow: none !important;
    }}

    /* Precyzyjny selektor dla stAlertContainer */
    [data-testid="stSidebar"] .stAlertContainer {{
        border: none !important;
        border-left: none !important;
        border-right: none !important;
        border-top: none !important;
        border-bottom: none !important;
        box-shadow: none !important;
        outline: none !important;
    }}

    [data-testid="stSidebar"] [data-testid="stAlertContainer"] {{
        border: none !important;
        border-left: none !important;
        box-shadow: none !important;
        outline: none !important;
    }}

    /* Wildcard - usuń border ze WSZYSTKICH elementów wewnątrz alertów w sidebarze */
    [data-testid="stSidebar"] .stAlert,
    [data-testid="stSidebar"] .stAlert *,
    [data-testid="stSidebar"] .stAlertContainer,
    [data-testid="stSidebar"] .stAlertContainer * {{
        border: none !important;
        border-left: none !important;
        border-right: none !important;
        border-top: none !important;
        border-bottom: none !important;
        box-shadow: none !important;
        outline: none !important;
    }}

    /* ===== Desktop Layout Constraint ===== */

    /* 1. Główny kontener - ograniczenie i centrowanie */
    [data-testid="block-container"],
    .block-container {{
        max-width: 1400px !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        margin: 0 auto !important;
    }}

    /* 2. Komponenty formularzy - max szerokość */
    [data-testid="stFileUploader"] {{
        max-width: 600px !important;
    }}

    .stSelectbox {{
        max-width: 400px !important;
    }}

    .stNumberInput {{
        max-width: 200px !important;
    }}

    .stTextInput {{
        max-width: 400px !important;
    }}

    /* 3. Przyciski - naturalna szerokość (bez stretch) */
    .stButton > button {{
        width: auto !important;
        min-width: 120px !important;
    }}

    /* 4. Wykresy i tabele - pełna szerokość w obrębie kontenera */
    [data-testid="stDataFrame"],
    [data-testid="stPlotlyChart"],
    .stDataFrame {{
        width: 100% !important;
    }}

    /* 5. Responsywność - na mniejszych ekranach pełna szerokość */
    @media (max-width: 1500px) {{
        [data-testid="block-container"],
        .block-container {{
            max-width: 100% !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
        }}
    }}

    @media (max-width: 768px) {{
        [data-testid="stFileUploader"],
        .stSelectbox,
        .stNumberInput,
        .stTextInput {{
            max-width: 100% !important;
        }}
    }}

    /* ===== Import Section Layout ===== */

    /* Data preview container - constrained width */
    .data-preview-container {{
        max-width: 600px !important;
    }}

    .data-preview-container .streamlit-expanderHeader {{
        max-width: 100% !important;
    }}

    /* ===== Sidebar Pipeline Status Styling ===== */

    /* Status section container */
    .sidebar-status-section {{
        background-color: {COLORS["background"]};
        border-radius: 8px;
        padding: 0.75rem;
        margin-bottom: 0.75rem;
    }}

    .sidebar-status-section .section-title {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.8rem;
        font-weight: 600;
        color: {COLORS["text"]};
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.75rem;
    }}

    .sidebar-status-section .section-icon {{
        font-size: 0.9rem;
    }}

    /* Pipeline container */
    .sidebar-pipeline {{
        display: flex;
        flex-direction: column;
        gap: 0;
        padding-left: 0.25rem;
    }}

    /* Pipeline step */
    .pipeline-step {{
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        position: relative;
        padding-bottom: 0.5rem;
    }}

    .pipeline-step:last-child {{
        padding-bottom: 0;
    }}

    /* Vertical connector line */
    .pipeline-step:not(:last-child)::before {{
        content: '';
        position: absolute;
        left: 6px;
        top: 16px;
        width: 2px;
        height: calc(100% - 4px);
        background-color: {COLORS["border"]};
        transition: background-color 0.3s ease;
    }}

    .pipeline-step.connector-success:not(:last-child)::before {{
        background-color: {STATUS_COLORS["success"]};
    }}

    /* Pipeline indicator (circle) */
    .pipeline-indicator {{
        width: 14px;
        height: 14px;
        min-width: 14px;
        border-radius: 50%;
        border: 2px solid;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-top: 2px;
        transition: all 0.3s ease;
        box-sizing: border-box;
    }}

    .pipeline-indicator.pending {{
        border-color: {STATUS_COLORS["pending"]};
        background-color: transparent;
    }}

    .pipeline-indicator.success {{
        border-color: {STATUS_COLORS["success"]};
        background-color: {STATUS_COLORS["success"]};
    }}

    .pipeline-indicator.in_progress {{
        border-color: {STATUS_COLORS["in_progress"]};
        background-color: {STATUS_COLORS["in_progress"]};
        animation: pulse-status 1.5s ease-in-out infinite;
    }}

    .pipeline-indicator.failed {{
        border-color: {STATUS_COLORS["failed"]};
        background-color: {STATUS_COLORS["failed"]};
    }}

    /* Checkmark inside success indicator */
    .pipeline-indicator.success::after {{
        content: '✓';
        font-size: 8px;
        color: white;
        font-weight: bold;
    }}

    /* Step content */
    .pipeline-step-content {{
        flex: 1;
        min-width: 0;
    }}

    .pipeline-step-name {{
        font-size: 0.8rem;
        font-weight: 500;
        color: {COLORS["text"]};
        line-height: 1.2;
    }}

    .pipeline-step-detail {{
        font-size: 0.7rem;
        color: {COLORS["text_secondary"]};
        margin-top: 0.15rem;
        line-height: 1.2;
    }}

    /* Pulse animation for in_progress state */
    @keyframes pulse-status {{
        0%, 100% {{
            opacity: 1;
            transform: scale(1);
        }}
        50% {{
            opacity: 0.6;
            transform: scale(0.9);
        }}
    }}
    </style>
    """


def apply_theme() -> None:
    """Apply custom CSS theme to the Streamlit app."""
    import streamlit as st
    st.markdown(get_custom_css(), unsafe_allow_html=True)
