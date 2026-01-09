"""Theme configuration for the Streamlit app - dark mode inspired by n8n."""

# Paleta kolorów
COLORS = {
    "background": "#121212",
    "surface": "#1E1E1E",
    "surface_light": "#2A2A2A",
    "primary": "#4CAF50",      # Zielony - sukces
    "error": "#F44336",        # Czerwony - błędy
    "warning": "#FF9800",      # Pomarańczowy - Kardex/gabaryty
    "info": "#2196F3",         # Niebieski - info
    "text": "#EAEAEA",
    "text_secondary": "#B0B0B0",
    "border": "#333333",
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

    /* Badges statusów */
    .status-badge {{
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
    }}

    .status-badge.success {{
        background-color: rgba(76, 175, 80, 0.2);
        color: {COLORS["primary"]};
    }}

    .status-badge.warning {{
        background-color: rgba(255, 152, 0, 0.2);
        color: {COLORS["warning"]};
    }}

    .status-badge.error {{
        background-color: rgba(244, 67, 54, 0.2);
        color: {COLORS["error"]};
    }}

    .status-badge.info {{
        background-color: rgba(33, 150, 243, 0.2);
        color: {COLORS["info"]};
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
        background-color: {COLORS["primary"]};
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 500;
        transition: background-color 0.2s;
    }}

    .stButton > button:hover {{
        background-color: #43A047;
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
        background-color: {COLORS["primary"]};
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

    /* Status badge hover */
    .status-badge {{
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        cursor: default;
    }}

    .status-badge:hover {{
        transform: scale(1.05);
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
        background-color: rgba(33, 150, 243, 0.1);
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
        background-color: rgba(255, 152, 0, 0.1);
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
        background-color: rgba(244, 67, 54, 0.1);
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
        background-color: rgba(76, 175, 80, 0.1);
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
        border-top-color: {COLORS["primary"]} !important;
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
    </style>
    """


def apply_theme() -> None:
    """Apply custom CSS theme to the Streamlit app."""
    import streamlit as st
    st.markdown(get_custom_css(), unsafe_allow_html=True)
