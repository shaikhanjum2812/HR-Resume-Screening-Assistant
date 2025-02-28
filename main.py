import os
import sys
import logging
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "src")
if src_path not in sys.path:
    sys.path.append(src_path)
    logger.info(f"Added {src_path} to Python path")

try:
    from src.database import Database
    from src.ai_evaluator import AIEvaluator
    from src.pdf_processor import PDFProcessor
    from src.docx_processor import DOCXProcessor
    from src.analytics import Analytics
    from src.utils import extract_text_from_upload
    from src.report_generator import generate_evaluation_report, generate_summary_report
    logger.info("Successfully imported all required modules")
except Exception as e:
    logger.error(f"Error importing modules: {str(e)}")
    raise

def initialize_components():
    """Initialize all required components with proper error handling"""
    try:
        logger.info("Initializing components...")

        # Initialize database with graceful fallback
        db = Database(require_db=False)
        if not db.is_connected():
            st.warning("Database connection not available. Some features may be limited.")

        components = {
            'db': db,
            'ai_evaluator': AIEvaluator(),
            'pdf_processor': PDFProcessor(),
            'docx_processor': DOCXProcessor(),
            'analytics': Analytics()
        }
        logger.info("All components initialized successfully")
        return components
    except Exception as e:
        logger.error(f"Failed to initialize components: {str(e)}")
        st.error(f"Error initializing components: {str(e)}")
        return None

def show_home():
    st.title("HR Assistant")
    st.write("Welcome to the HR Assistant application!")

    # Only show metrics if database is available
    if st.session_state.components['db'].is_connected():
        try:
            db = st.session_state.components['db']
            # Display metrics...  (This section was omitted in the edited snippet)
        except Exception as e:
            st.error(f"Error loading dashboard metrics: {str(e)}")
            logger.error(f"Dashboard metrics error: {str(e)}")
    else:
        st.info("Database connection not available. Metrics cannot be displayed.")

def show_jobs():
    st.title("Jobs")
    st.write("Jobs page content will go here")

def show_evaluation():
    st.title("Evaluation")
    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx"])
    if uploaded_file is not None:
        try:
            file_content = uploaded_file.getvalue()
            if uploaded_file.name.lower().endswith(".pdf"):
                text = st.session_state.components['pdf_processor'].process(file_content)
            elif uploaded_file.name.lower().endswith(".docx"):
                text = st.session_state.components['docx_processor'].process(file_content)
            else:
                text = extract_text_from_upload(file_content)
            st.write("Extracted text:")
            st.text_area("Text", text, height=200)
            evaluation_result = st.session_state.components['ai_evaluator'].evaluate(text)
            st.write("Evaluation Result:")
            st.json(evaluation_result)
        except Exception as e:
            logger.error(f"Error during evaluation: {str(e)}")
            st.error(f"An error occurred during evaluation: {str(e)}")

def show_analytics():
    st.title("Analytics")
    st.write("Analytics page content will go here")

def show_past_evaluations():
    st.title("Past Evaluations")
    st.write("Past Evaluations page content will go here")

def main():
    try:
        # Configure Streamlit page
        st.set_page_config(
            page_title="HR Assistant",
            page_icon="👔",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Initialize session state
        if 'components' not in st.session_state:
            st.session_state.components = initialize_components()
            if not st.session_state.components:
                st.error("Failed to initialize application components. Please check the logs.")
                return

        # Navigation
        pages = {
            "Home": show_home,
            "Jobs": show_jobs,
            "Evaluation": show_evaluation,
            "Analytics": show_analytics,
            "Past Evaluations": show_past_evaluations
        }

        # Sidebar navigation
        selected_page = st.sidebar.selectbox("Select a page", list(pages.keys()))

        # Execute selected page function
        pages[selected_page]()

        logger.info(f"Page {selected_page} rendered successfully")

    except Exception as e:
        logger.error(f"Application startup error: {str(e)}")
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    try:
        logger.info("Starting HR Assistant application...")
        main()
    except Exception as e:
        logger.error(f"Critical application error: {str(e)}")
        st.error("Failed to start the application. Please check the logs.")