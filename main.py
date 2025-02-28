import os
import sys
import streamlit as st

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# Import the main application code
from src.main import show_home, show_jobs, show_evaluation, show_analytics, initialize_components

def main():
    """Main function to run the Streamlit application"""
    st.set_page_config(
        page_title="HR Assistant",
        page_icon="👥",
        layout="wide"
    )

    # Initialize session state for page navigation if not exists
    if 'page' not in st.session_state:
        st.session_state.page = 'home'

    # Initialize components if not already done
    if 'components' not in st.session_state:
        components = initialize_components()
        if components:
            st.session_state.components = components
        else:
            st.error("Failed to initialize application components")
            return

    # Sidebar navigation
    st.sidebar.title("Navigation")
    pages = {
        'home': 'Home',
        'jobs': 'Job Descriptions',
        'evaluation': 'Resume Evaluation',
        'analytics': 'Analytics'
    }

    for page_id, page_name in pages.items():
        if st.sidebar.button(page_name, key=f"nav_{page_id}"):
            st.session_state.page = page_id
            st.experimental_rerun()

    # Render the selected page
    try:
        if st.session_state.page == 'home':
            show_home()
        elif st.session_state.page == 'jobs':
            show_jobs()
        elif st.session_state.page == 'evaluation':
            show_evaluation()
        elif st.session_state.page == 'analytics':
            show_analytics()

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()