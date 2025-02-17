import streamlit as st
from typing import Dict, Any

# Predefined color schemes
COLOR_SCHEMES = {
    "Default": {
        "primary": "#FF4B4B",
        "background": "#FFFFFF",
        "secondary": "#0068C9",
        "text": "#262730",
        "highlight": "#FFEF5B"
    },
    "Dark Professional": {
        "primary": "#00C0F2",
        "background": "#0E1117",
        "secondary": "#31333F",
        "text": "#FAFAFA",
        "highlight": "#17C37B"
    },
    "Calm Nature": {
        "primary": "#4CAF50",
        "background": "#F5F7F9",
        "secondary": "#2E7D32",
        "text": "#1B5E20",
        "highlight": "#81C784"
    },
    "Ocean Breeze": {
        "primary": "#039BE5",
        "background": "#E3F2FD",
        "secondary": "#0277BD",
        "text": "#01579B",
        "highlight": "#4FC3F7"
    }
}

def initialize_theme():
    """Initialize theme settings in session state"""
    if 'theme' not in st.session_state:
        st.session_state.theme = "Default"

def apply_theme(theme_name: str) -> Dict[str, Any]:
    """Apply selected theme and return theme configuration"""
    if theme_name not in COLOR_SCHEMES:
        theme_name = "Default"
    
    theme = COLOR_SCHEMES[theme_name]
    
    # Apply theme colors using custom CSS
    css = f"""
        <style>
            .stButton button {{
                background-color: {theme["primary"]};
                color: {theme["background"]};
            }}
            .stTextInput input {{
                border-color: {theme["secondary"]};
            }}
            .stSelectbox select {{
                border-color: {theme["secondary"]};
            }}
            div.stMarkdown p {{
                color: {theme["text"]};
            }}
            div[data-testid="stMetricValue"] {{
                color: {theme["primary"]};
            }}
        </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    return theme
