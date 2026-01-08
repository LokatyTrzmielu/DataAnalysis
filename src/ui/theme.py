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
    </style>
    """


def apply_theme() -> None:
    """Apply custom CSS theme to the Streamlit app."""
    import streamlit as st
    st.markdown(get_custom_css(), unsafe_allow_html=True)
