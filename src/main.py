import os
import sys
import logging
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
from database import Database
from ai_evaluator import AIEvaluator
from pdf_processor import PDFProcessor
from analytics import Analytics
from utils import extract_text_from_upload

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_components():
    """Initialize all required components with proper error handling"""
    try:
        logger.info("Initializing database connection...")
        db = Database()
        logger.info("Database connection successful")

        logger.info("Initializing AI Evaluator...")
        ai_evaluator = AIEvaluator()
        logger.info("AI Evaluator initialization successful")

        logger.info("Initializing PDF Processor and Analytics...")
        pdf_processor = PDFProcessor()
        analytics = Analytics()
        logger.info("PDF Processor and Analytics initialization successful")

        return {
            'db': db,
            'ai_evaluator': ai_evaluator,
            'pdf_processor': pdf_processor,
            'analytics': analytics
        }
    except Exception as e:
        logger.error(f"Failed to initialize components: {str(e)}")
        return None

def process_single_resume(resume_file, job_description, evaluation_criteria, components):
    """Process a single resume and show results"""
    try:
        # Extract text from PDF
        resume_text = components['pdf_processor'].extract_text(resume_file)

        # Evaluate with AI
        evaluation = components['ai_evaluator'].evaluate_resume(
            resume_text,
            job_description,
            evaluation_criteria=evaluation_criteria
        )

        # Save evaluation results
        components['db'].save_evaluation(
            job_id=job_description['id'],
            resume_name=resume_file.name,
            evaluation_result=evaluation,
            resume_file=resume_file
        )

        # Display result
        st.subheader(f"Results for {resume_file.name}")

        # Candidate Information
        st.write("#### Candidate Information")
        candidate_info = evaluation.get('candidate_info', {})
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("**Name:**", candidate_info.get('name', 'Not found'))
        with col2:
            st.write("**Email:**", candidate_info.get('email', 'Not found'))
        with col3:
            st.write("**Phone:**", candidate_info.get('phone', 'Not found'))

        # Decision with color coding
        result = evaluation.get('decision', '').upper()
        if result == 'SHORTLIST':
            st.success(f"Decision: {result}")
        else:
            st.error(f"Decision: {result}")

        # Match score
        match_score = float(evaluation.get('match_score', 0))
        st.write(f"Match Score: {match_score*100:.1f}%")
        st.progress(match_score)

        # Experience Analysis
        st.write("#### Experience Analysis")
        exp_data = evaluation.get('years_of_experience', {})
        cols = st.columns(3)
        with cols[0]:
            st.metric("Total Experience", f"{exp_data.get('total', 0)} years")
        with cols[1]:
            st.metric("Relevant Experience", f"{exp_data.get('relevant', 0)} years")
        with cols[2]:
            st.metric("Required Experience", f"{exp_data.get('required', 0)} years")

        # Download buttons
        st.write("#### Download Options")
        col1, col2 = st.columns(2)
        with col1:
            evaluation_json = json.dumps(evaluation, indent=2)
            st.download_button(
                label="📄 Download Evaluation Report",
                data=evaluation_json,
                file_name=f"evaluation_{resume_file.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        with col2:
            st.download_button(
                label="📥 Download Original Resume",
                data=resume_file.getvalue(),
                file_name=resume_file.name,
                mime=resume_file.type
            )

        st.markdown("---")
        return True

    except Exception as e:
        st.error(f"Error processing {resume_file.name}: {str(e)}")
        logger.error(f"Error processing resume: {str(e)}")
        return False

def show_evaluation():
    st.title("Resume Evaluation")

    # Job selection
    jobs = st.session_state.components['db'].get_all_jobs()
    job_titles = [job['title'] for job in jobs]

    if not job_titles:
        st.warning("Please add job descriptions first.")
        return

    selected_job = st.selectbox("Select Job Description", job_titles)

    # Resume upload
    st.write("Upload Resumes (PDF files will be processed one at a time)")
    uploaded_files = st.file_uploader(
        "Upload Resumes (PDF)",
        type=['pdf'],
        accept_multiple_files=True
    )

    if uploaded_files and selected_job:
        if st.button("Start Evaluation"):
            # Get job description and criteria
            job = next(job for job in jobs if job['title'] == selected_job)
            criteria = st.session_state.components['db'].get_evaluation_criteria(job['id']) if job['has_criteria'] else None

            # Process each resume sequentially
            success_count = 0
            for idx, uploaded_file in enumerate(uploaded_files, 1):
                st.write(f"Processing resume {idx} of {len(uploaded_files)}: {uploaded_file.name}")
                if process_single_resume(uploaded_file, job, criteria, st.session_state.components):
                    success_count += 1

            st.success(f"Completed processing {success_count} out of {len(uploaded_files)} resumes!")

def show_home():
    st.title("HR Assistant Dashboard")
    st.write("Welcome to the HR Assistant tool. Use the sidebar to navigate.")

    try:
        db = st.session_state.components['db']
        col1, col2 = st.columns(2)
        with col1:
            active_jobs = db.get_active_jobs_count()
            st.metric("Active Job Descriptions", active_jobs)
        with col2:
            today_evals = db.get_today_evaluations_count()
            st.metric("Evaluations Today", today_evals)
    except Exception as e:
        st.error(f"Error loading dashboard metrics: {str(e)}")

def show_jobs():
    st.title("Job Descriptions Management")

    # Add new job description
    st.subheader("Add New Job Description")

    # Method selection
    input_method = st.radio(
        "Choose input method",
        ["Manual Entry", "Upload File"],
        horizontal=True
    )

    if input_method == "Manual Entry":
        with st.form("job_description_form"):
            title = st.text_input("Job Title")
            description = st.text_area("Job Description")

            # Evaluation Criteria Section
            st.subheader("Evaluation Criteria")
            col1, col2 = st.columns(2)

            with col1:
                min_years = st.number_input("Minimum Years of Experience", min_value=0, value=0)
                required_skills = st.text_area(
                    "Required Skills (one per line)",
                    help="Enter each required skill on a new line"
                )
                education_req = st.text_area("Education Requirements")

            with col2:
                preferred_skills = st.text_area(
                    "Preferred Skills (one per line)",
                    help="Enter each preferred skill on a new line"
                )
                company_background = st.text_area("Company Background Requirements")
                domain_experience = st.text_area("Domain Experience Requirements")

            additional_instructions = st.text_area(
                "Additional Evaluation Instructions",
                help="Any specific instructions for the AI evaluator"
            )

            submit_button = st.form_submit_button("Save Job Description")

            if submit_button and title and description:
                try:
                    # Prepare evaluation criteria
                    evaluation_criteria = {
                        'min_years_experience': min_years,
                        'required_skills': [s.strip() for s in required_skills.split('\n') if s.strip()],
                        'preferred_skills': [s.strip() for s in preferred_skills.split('\n') if s.strip()],
                        'education_requirements': education_req,
                        'company_background_requirements': company_background,
                        'domain_experience_requirements': domain_experience,
                        'additional_instructions': additional_instructions
                    }

                    st.session_state.components['db'].add_job_description(title, description, evaluation_criteria)
                    st.success("Job description and evaluation criteria saved successfully!")
                except Exception as e:
                    st.error(f"Failed to save job description: {str(e)}")

    else:  # File Upload
        with st.form("job_description_upload_form"):
            title = st.text_input("Job Title")
            uploaded_file = st.file_uploader(
                "Upload Job Description (PDF, DOCX, or TXT)",
                type=['pdf', 'docx', 'txt']
            )

            # Evaluation Criteria Section
            st.subheader("Evaluation Criteria")
            col1, col2 = st.columns(2)

            with col1:
                min_years = st.number_input("Minimum Years of Experience", min_value=0, value=0)
                required_skills = st.text_area(
                    "Required Skills (one per line)",
                    help="Enter each required skill on a new line"
                )
                education_req = st.text_area("Education Requirements")

            with col2:
                preferred_skills = st.text_area(
                    "Preferred Skills (one per line)",
                    help="Enter each preferred skill on a new line"
                )
                company_background = st.text_area("Company Background Requirements")
                domain_experience = st.text_area("Domain Experience Requirements")

            additional_instructions = st.text_area(
                "Additional Evaluation Instructions",
                help="Any specific instructions for the AI evaluator"
            )

            submit_button = st.form_submit_button("Save Job Description")

            if submit_button:
                if not title:
                    st.error("Please provide a title for the job description.")
                    return

                if not uploaded_file:
                    st.error("Please upload a job description file.")
                    return

                try:
                    description = extract_text_from_upload(uploaded_file)
                    if description:
                        # Prepare evaluation criteria
                        evaluation_criteria = {
                            'min_years_experience': min_years,
                            'required_skills': [s.strip() for s in required_skills.split('\n') if s.strip()],
                            'preferred_skills': [s.strip() for s in preferred_skills.split('\n') if s.strip()],
                            'education_requirements': education_req,
                            'company_background_requirements': company_background,
                            'domain_experience_requirements': domain_experience,
                            'additional_instructions': additional_instructions
                        }

                        st.session_state.components['db'].add_job_description(title, description, evaluation_criteria)
                        st.success("Job description uploaded and criteria saved successfully!")
                        st.subheader("Extracted Text Preview")
                        st.text_area("Preview", description, height=200, disabled=True)
                    else:
                        st.error("No text could be extracted from the file.")
                except Exception as e:
                    st.error(f"Failed to process uploaded file: {str(e)}")

    # List existing job descriptions
    st.markdown("---")
    st.subheader("Existing Job Descriptions")
    jobs = st.session_state.components['db'].get_all_jobs()
    for job in jobs:
        with st.expander(f"{job['title']} - {job['date_created']}"):
            st.write(job['description'])

            # Show evaluation criteria if exists
            if job['has_criteria']:
                criteria = st.session_state.components['db'].get_evaluation_criteria(job['id'])
                if criteria:
                    st.subheader("Evaluation Criteria")
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write("**Required Skills:**")
                        for skill in criteria['required_skills']:
                            st.write(f"- {skill}")

                        st.write("**Education Requirements:**")
                        st.write(criteria['education_requirements'])

                    with col2:
                        st.write("**Preferred Skills:**")
                        for skill in criteria['preferred_skills']:
                            st.write(f"- {skill}")

                        st.write("**Domain Experience:**")
                        st.write(criteria['domain_experience_requirements'])

                    st.write("**Additional Instructions:**")
                    st.write(criteria['additional_instructions'])

            if st.button(f"Delete {job['title']}", key=f"del_{job['id']}"):
                st.session_state.components['db'].delete_job(job['id'])
                st.rerun()

def show_analytics():
    st.title("Analytics Dashboard")

    # Time period selection
    period = st.selectbox("Select Time Period", ["Week", "Month", "Year"])

    # Get analytics data
    data = st.session_state.components['analytics'].get_evaluation_stats(period.lower())

    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Evaluations", data['total_evaluations'])
    with col2:
        st.metric("Shortlisted", data['shortlisted'])
    with col3:
        st.metric("Rejection Rate", f"{data['rejection_rate']:.1f}%")

    # Display charts
    st.subheader("Evaluation Trends")
    st.plotly_chart(st.session_state.components['analytics'].plot_evaluation_trend(period.lower()))

    st.subheader("Job-wise Distribution")
    st.plotly_chart(st.session_state.components['analytics'].plot_job_distribution())

def init_session_state():
    if 'page' not in st.session_state:
        st.session_state.page = 'home'
    if 'components' not in st.session_state:
        st.session_state.components = None

def sidebar():
    st.sidebar.title("HR Assistant")
    pages = {
        'Home': 'home',
        'Job Descriptions': 'jobs',
        'Resume Evaluation': 'evaluation',
        'Analytics': 'analytics'
    }

    selection = st.sidebar.radio("Navigate", list(pages.keys()))
    st.session_state.page = pages[selection]

def main():
    logger.info("Starting HR Assistant application...")

    try:
        st.set_page_config(
            page_title="HR Assistant",
            page_icon="👥",
            layout="wide"
        )
        logger.info("Page configuration set successfully")

        init_session_state()
        logger.info("Session state initialized")

        if st.session_state.components is None:
            logger.info("Initializing components...")
            st.session_state.components = initialize_components()

        if st.session_state.components is None:
            logger.error("Failed to initialize application components")
            st.error("Failed to initialize application components. Please refresh the page or contact support.")
            return

        sidebar()

        if st.session_state.page == 'home':
            show_home()
        elif st.session_state.page == 'jobs':
            show_jobs()
        elif st.session_state.page == 'evaluation':
            show_evaluation()
        elif st.session_state.page == 'analytics':
            show_analytics()

        logger.info(f"Page {st.session_state.page} rendered successfully")

    except Exception as e:
        logger.error(f"Main application error: {str(e)}")
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()