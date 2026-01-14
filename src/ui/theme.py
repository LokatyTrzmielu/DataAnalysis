"""Theme configuration for the Streamlit app - dark mode inspired by n8n."""

# Paleta kolorów - ciepła kawowo-brązowa
COLORS = {
    # === TŁA ===
    "background": "#20100e",      # coffee-bean
    "surface": "#323232",         # graphite
    "surface_light": "#5f605b",   # dim-grey

    # === AKCENTY ===
    "accent": "#b7622c",          # burnt-caramel - główny
    "accent_dark": "#923b1b",     # rust-brown - hover
    "accent_muted": "#5e3123",    # espresso - subtle

    # === FUNKCJONALNE ===
    "primary": "#4CAF50",         # Zielony sukces (zachowany)
    "error": "#E57373",           # Ciepły czerwony
    "warning": "#b7622c",         # burnt-caramel
    "info": "#8D6E63",            # Ciepły brąz

    # === TEKST ===
    "text": "#F5F0E8",            # Ciepła biel
    "text_secondary": "#A89F94",  # Ciepły taupe

    # === BORDERY ===
    "border": "#5e3123",          # espresso
}

# Kolory dla 7 typów statusu
STATUS_COLORS = {
    "pending": "#FFB74D",       # żółty
    "in_progress": "#64B5F6",   # niebieski
    "submitted": "#BA68C8",     # fioletowy
    "in_review": "#FF8A65",     # pomarańczowy
    "success": "#81C784",       # zielony
    "failed": "#E57373",        # czerwony
    "expired": "#90A4AE",       # szary
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
    """Return custom CSS for dark theme styling."""
    return f"""
    <style>
    /* Główne tło i tekst */
    .stApp {{
        background-color: {COLORS["background"]};
    }}

    /* Karty KPI */
    .kpi-card {{
        background-color: {COLORS["surface"]};
        border-radius: 8px;
        padding: 1rem 1.25rem;
        border: 1px solid {COLORS["border"]};
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
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
        background-color: rgba(255, 183, 77, 0.15);
        border-color: rgba(255, 183, 77, 0.4);
        color: {STATUS_COLORS["pending"]};
    }}

    .status-btn.in_progress {{
        background-color: rgba(100, 181, 246, 0.15);
        border-color: rgba(100, 181, 246, 0.4);
        color: {STATUS_COLORS["in_progress"]};
    }}

    .status-btn.submitted {{
        background-color: rgba(186, 104, 200, 0.15);
        border-color: rgba(186, 104, 200, 0.4);
        color: {STATUS_COLORS["submitted"]};
    }}

    .status-btn.in_review {{
        background-color: rgba(255, 138, 101, 0.15);
        border-color: rgba(255, 138, 101, 0.4);
        color: {STATUS_COLORS["in_review"]};
    }}

    .status-btn.success {{
        background-color: rgba(129, 199, 132, 0.15);
        border-color: rgba(129, 199, 132, 0.4);
        color: {STATUS_COLORS["success"]};
    }}

    .status-btn.failed {{
        background-color: rgba(229, 115, 115, 0.15);
        border-color: rgba(229, 115, 115, 0.4);
        color: {STATUS_COLORS["failed"]};
    }}

    .status-btn.expired {{
        background-color: rgba(144, 164, 174, 0.15);
        border-color: rgba(144, 164, 174, 0.4);
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
        background-color: rgba(129, 199, 132, 0.15);
        border-color: rgba(129, 199, 132, 0.4);
        color: {STATUS_COLORS["success"]};
    }}

    .status-badge.warning {{
        background-color: rgba(255, 183, 77, 0.15);
        border-color: rgba(255, 183, 77, 0.4);
        color: {STATUS_COLORS["pending"]};
    }}

    .status-badge.error {{
        background-color: rgba(229, 115, 115, 0.15);
        border-color: rgba(229, 115, 115, 0.4);
        color: {STATUS_COLORS["failed"]};
    }}

    .status-badge.info {{
        background-color: rgba(100, 181, 246, 0.15);
        border-color: rgba(100, 181, 246, 0.4);
        color: {STATUS_COLORS["in_progress"]};
    }}

    /* Stylizacja tabel */
    .stDataFrame {{
        background-color: {COLORS["surface"]};
    }}

    .stDataFrame [data-testid="stDataFrameResizable"] {{
        background-color: {COLORS["surface"]};
    }}

    /* Expanders */
    .streamlit-expanderHeader {{
        background-color: {COLORS["surface"]};
        border-radius: 8px;
    }}

    .streamlit-expanderContent {{
        background-color: {COLORS["surface"]};
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
        background-color: {COLORS["surface"]};
        border-right: 1px solid {COLORS["border"]};
    }}

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: {COLORS["surface"]};
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

    /* File uploader */
    [data-testid="stFileUploader"] {{
        background-color: {COLORS["surface"]};
        border-radius: 8px;
        border: 1px dashed {COLORS["border"]};
    }}

    /* Selectbox */
    .stSelectbox [data-baseweb="select"] {{
        background-color: {COLORS["surface"]};
    }}

    /* Number input */
    .stNumberInput input {{
        background-color: {COLORS["surface"]};
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
        background-color: {COLORS["surface"]};
        border-radius: 8px;
        padding: 1.5rem;
        border: 1px solid {COLORS["border"]};
        margin-bottom: 1rem;
    }}

    /* Chart containers */
    .chart-container {{
        background-color: {COLORS["surface"]};
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
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
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
        background-color: {COLORS["surface"]};
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
        background-color: rgba(141, 110, 99, 0.15);
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
        background-color: rgba(183, 98, 44, 0.15);
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
        background-color: rgba(229, 115, 115, 0.15);
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
        background-color: rgba(129, 199, 132, 0.15);
        border-left: 3px solid {COLORS["primary"]};
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }}

    .success-box p {{
        color: {COLORS["text"]};
        margin: 0;
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

    /* Scrollbar styling for dark theme */
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
        background-color: {COLORS["surface"]};
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
        background-color: {COLORS["surface"]};
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

    /* Hover state - rust-brown color */
    [data-testid="stSidebar"] .stRadio > div > label:hover {{
        background-color: transparent !important;
    }}

    [data-testid="stSidebar"] .stRadio > div > label:hover > div:last-child {{
        color: {COLORS["accent_dark"]} !important;
        font-weight: 600 !important;
    }}

    /* Selected state - dim-grey rectangle with accent border */
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

    /* Alerty (st.success, st.info) w sidebarze */
    [data-testid="stSidebar"] .stAlert {{
        background-color: {COLORS["background"]} !important;
        border-radius: 6px !important;
        padding: 0.5rem 0.75rem !important;
        margin: 0.25rem 0 !important;
        border: none !important;
    }}

    [data-testid="stSidebar"] .stAlert p {{
        color: {COLORS["text"]} !important;
        font-size: 0.85rem !important;
    }}
    </style>
    """


def apply_theme() -> None:
    """Apply custom CSS theme to the Streamlit app."""
    import streamlit as st
    st.markdown(get_custom_css(), unsafe_allow_html=True)
