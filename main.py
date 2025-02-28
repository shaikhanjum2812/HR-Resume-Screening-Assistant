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
src_path = os.path.join(os.path.dirname(__file__), "src")
if src_path not in sys.path:
    sys.path.append(src_path)

from database import Database
from ai_evaluator import AIEvaluator
from pdf_processor import PDFProcessor
from docx_processor import DOCXProcessor
from analytics import Analytics
from utils import extract_text_from_upload
from report_generator import generate_evaluation_report, generate_summary_report

def initialize_components():
    """Initialize all required components with proper error handling"""
    try:
        logger.info("Initializing database connection...")
        db = Database()
        logger.info("Database connection successful")

        logger.info("Initializing AI Evaluator...")
        ai_evaluator = AIEvaluator()
        logger.info("AI Evaluator initialization successful")

        logger.info("Initializing PDF Processor, DOCX Processor and Analytics...")
        pdf_processor = PDFProcessor()
        docx_processor = DOCXProcessor()
        analytics = Analytics()
        logger.info("Processors and Analytics initialization successful")

        return {
            'db': db,
            'ai_evaluator': ai_evaluator,
            'pdf_processor': pdf_processor,
            'docx_processor': docx_processor,
            'analytics': analytics
        }
    except Exception as e:
        logger.error(f"Failed to initialize components: {str(e)}")
        st.error(f"Application initialization error: {str(e)}")
        return None

def main():
    try:
        st.set_page_config(
            page_title="HR Assistant",
            page_icon="👔",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Initialize session state
        if 'page' not in st.session_state:
            st.session_state.page = 'home'

        if 'components' not in st.session_state:
            st.session_state.components = initialize_components()

        if not st.session_state.components:
            st.error("Failed to initialize application components. Please check the logs.")
            return

        #Start of the original main function
        selected_page = st.sidebar.selectbox("Select a page", ["Home", "Evaluation", "Analytics", "Report"])
        st.session_state.page = selected_page.lower()

        if st.session_state.page == "home":
            st.title("HR Assistant")
            st.write("Welcome to the HR Assistant application!")

        elif st.session_state.page == "evaluation":
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

        elif st.session_state.page == "analytics":
            st.title("Analytics")
            st.write("Analytics page content will go here")

        elif st.session_state.page == "report":
            st.title("Report")
            report_type = st.selectbox("Select report type", ["Evaluation Report", "Summary Report"])
            if st.button("Generate Report"):
                try:
                    if report_type == "Evaluation Report":
                        report = generate_evaluation_report()
                    else:
                        report = generate_summary_report()
                    st.download_button("Download Report", report, "report.txt", "text/plain")
                except Exception as e:
                    logger.error(f"Error generating report: {str(e)}")
                    st.error(f"An error occurred during report generation: {str(e)}")


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