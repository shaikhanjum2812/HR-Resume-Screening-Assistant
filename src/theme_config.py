import streamlit as st
from typing import Dict, Any

# Dark blue theme configuration
DEFAULT_THEME = {
    "primary": "#0068C9",  # Dark blue
    "background": "#0E1117",
    "secondary": "#31333F",
    "text": "#FFFFFF",  # Changed to pure white for better visibility
    "highlight": "#00C0F2"
}

def apply_theme() -> Dict[str, Any]:
    """Apply the default dark blue theme"""
    theme = DEFAULT_THEME

    # Apply theme colors using custom CSS
    css = f"""
        <style>
            .stButton button {{
                background-color: {theme["primary"]};
                color: {theme["text"]};
            }}
            .stTextInput input {{
                border-color: {theme["secondary"]};
            }}
            .stSelectbox select {{
                border-color: {theme["secondary"]};
            }}
            div.stMarkdown p {{
                color: {theme["text"]} !important;
                opacity: 1 !important;
            }}
            div[data-testid="stMetricValue"] {{
                color: {theme["primary"]};
            }}
            .welcome-text {{
                color: {theme["text"]} !important;
                font-size: 1.2em !important;
                opacity: 1 !important;
            }}
        </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    return theme