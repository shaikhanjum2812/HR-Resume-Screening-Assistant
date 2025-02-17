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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_components():
    """Initialize all required components with proper error handling"""
    components = {}

    logger.info("Starting component initialization...")

    try:
        logger.info("Initializing database connection...")
        components['db'] = Database()
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        st.error(f"Failed to connect to database: {str(e)}")
        return None

    try:
        logger.info("Initializing AI Evaluator...")
        components['ai_evaluator'] = AIEvaluator()
        logger.info("AI Evaluator initialization successful")
    except Exception as e:
        logger.error(f"Failed to initialize AI Evaluator: {str(e)}")
        st.error(f"Failed to initialize AI Evaluator: {str(e)}")
        return None

    try:
        logger.info("Initializing PDF Processor and Analytics...")
        components['pdf_processor'] = PDFProcessor()
        components['analytics'] = Analytics()
        logger.info("PDF Processor and Analytics initialization successful")
    except Exception as e:
        logger.error(f"Failed to initialize other components: {str(e)}")
        st.error(f"Failed to initialize other components: {str(e)}")
        return None

    logger.info("All components initialized successfully")
    return components

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

def show_evaluation():
    st.title("Resume Evaluation")

    # Create tabs for new evaluation and evaluations list
    tab1, tab2 = st.tabs(["New Evaluation", "Evaluations"])

    with tab1:
        # Job selection
        jobs = st.session_state.components['db'].get_all_jobs()
        job_titles = [job['title'] for job in jobs]
        selected_job = st.selectbox("Select Job Description", job_titles)

        # Multiple resume upload
        st.write("Upload Resumes (Maximum 5 files)")
        uploaded_files = st.file_uploader("Upload Resumes (PDF)", type=['pdf'], accept_multiple_files=True)

        if uploaded_files and selected_job:
            if len(uploaded_files) > 5:
                st.error("Please upload a maximum of 5 resumes at a time.")
                return

            if st.button("Evaluate Resumes"):
                # Get job description and criteria
                job = next(job for job in jobs if job['title'] == selected_job)
                criteria = st.session_state.components['db'].get_evaluation_criteria(job['id']) if job['has_criteria'] else None

                # Create a progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Container for results
                results_container = st.container()

                for index, uploaded_file in enumerate(uploaded_files):
                    try:
                        # Update progress
                        progress = (index + 1) / len(uploaded_files)
                        progress_bar.progress(progress)
                        status_text.text(f"Processing {uploaded_file.name}... ({index + 1}/{len(uploaded_files)})")

                        with st.spinner(f"Processing {uploaded_file.name}..."):
                            # Extract text from PDF
                            resume_text = st.session_state.components['pdf_processor'].extract_text(uploaded_file)

                            # Evaluate with AI
                            evaluation = st.session_state.components['ai_evaluator'].evaluate_resume(
                                resume_text,
                                job['description'],
                                evaluation_criteria=criteria
                            )

                            # Save evaluation results
                            st.session_state.components['db'].save_evaluation(
                                job_id=job['id'],
                                resume_name=uploaded_file.name,
                                evaluation_result=evaluation,
                                resume_file=uploaded_file
                            )

                            # Display individual result
                            with results_container.expander(f"Results for {uploaded_file.name}"):
                                # Candidate Information
                                st.subheader("Candidate Information")
                                candidate_info = evaluation.get('candidate_info', {})
                                info_cols = st.columns(3)
                                with info_cols[0]:
                                    st.write("**Name:**", candidate_info.get('name', 'Not found'))
                                with info_cols[1]:
                                    st.write("**Email:**", candidate_info.get('email', 'Not found'))
                                with info_cols[2]:
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
                                exp_data = evaluation.get('years_of_experience', {})
                                cols = st.columns(3)
                                with cols[0]:
                                    st.metric("Total Experience", f"{exp_data.get('total', 0)} years")
                                with cols[1]:
                                    st.metric("Relevant Experience", f"{exp_data.get('relevant', 0)} years")
                                with cols[2]:
                                    st.metric("Required Experience", f"{exp_data.get('required', 0)} years")

                                # Download buttons
                                col1, col2 = st.columns(2)
                                with col1:
                                    evaluation_json = json.dumps(evaluation, indent=2)
                                    st.download_button(
                                        label="📄 Download Evaluation Report",
                                        data=evaluation_json,
                                        file_name=f"evaluation_{uploaded_file.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                        mime="application/json",
                                        key=f"download_eval_{index}"
                                    )
                                with col2:
                                    st.download_button(
                                        label="📥 Download Original Resume",
                                        data=uploaded_file.getvalue(),
                                        file_name=uploaded_file.name,
                                        mime=uploaded_file.type,
                                        key=f"download_resume_{index}"
                                    )

                    except Exception as e:
                        st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                        continue

                # Update final progress
                progress_bar.progress(1.0)
                status_text.text("All resumes processed!")
                st.success(f"Completed processing {len(uploaded_files)} resumes!")

    with tab2:
        st.subheader("Evaluations")

        # Period filter
        col1, col2 = st.columns([2, 3])
        with col1:
            period = st.selectbox(
                "Quick Filter",
                ["Past Week", "Past Month", "Past Quarter", "Custom Range"],
                key="eval_period"
            )

        # Custom date range
        if period == "Custom Range":
            with col2:
                col3, col4 = st.columns(2)
                with col3:
                    start_date = st.date_input(
                        "Start Date",
                        value=datetime.now() - timedelta(days=7),
                        max_value=datetime.now()
                    )
                with col4:
                    end_date = st.date_input(
                        "End Date",
                        value=datetime.now(),
                        max_value=datetime.now()
                    )
                if start_date > end_date:
                    st.error("Start date must be before end date")
                    return
            evaluations = st.session_state.components['db'].get_evaluations_by_date_range(start_date, end_date)
        else:
            # Convert period to database format
            period_map = {
                "Past Week": "week",
                "Past Month": "month",
                "Past Quarter": "quarter"
            }
            evaluations = st.session_state.components['db'].get_evaluations_by_period(period_map[period])

        if not evaluations:
            st.info("No evaluations found for the selected period.")
            return

        # Display evaluations as cards
        st.write("### Evaluation Results")

        # Add search/filter options
        search_term = st.text_input("Search by resume name or job title", "")

        # Process evaluations
        for eval_record in evaluations:
            try:
                # Extract evaluation data
                eval_data = {
                    'id': eval_record[0],
                    'job_id': eval_record[1],
                    'resume_name': eval_record[2],
                    'candidate_name': eval_record[3],
                    'candidate_email': eval_record[4],
                    'candidate_phone': eval_record[5],
                    'result': eval_record[6],
                    'match_score': float(eval_record[8]) if eval_record[8] is not None else 0.0,
                    'evaluation_date': eval_record[13],
                    'job_title': eval_record[15]
                }

                # Apply search filter
                if search_term.lower() not in eval_data['resume_name'].lower() and \
                   search_term.lower() not in eval_data['job_title'].lower() and \
                   search_term.lower() not in (eval_data['candidate_name'] or '').lower():
                    continue

                # Create card for each evaluation
                display_name = eval_data['candidate_name'] if eval_data['candidate_name'] else f"Resume: {eval_data['resume_name']}"
                decision = eval_data['result'].upper()
                decision_icon = "✅" if decision == "SHORTLIST" else "❌"
                with st.expander(f"{decision_icon} {display_name} - {decision} | {eval_data['job_title']} ({eval_data['evaluation_date'].strftime('%Y-%m-%d %H:%M')})"):
                    # Display candidate contact info if available
                    if eval_data['candidate_name'] or eval_data['candidate_email'] or eval_data['candidate_phone']:
                        st.write("#### Candidate Information")
                        info_cols = st.columns(3)
                        with info_cols[0]:
                            st.write("**Name:**", eval_data['candidate_name'] or "Not available")
                        with info_cols[1]:
                            st.write("**Email:**", eval_data['candidate_email'] or "Not available")
                        with info_cols[2]:
                            st.write("**Phone:**", eval_data['candidate_phone'] or "Not available")
                        st.markdown("---")  # Add a separator line

                    # Get detailed evaluation data
                    details = st.session_state.components['db'].get_evaluation_details(eval_data['id'])
                    if details:
                        # Download buttons section - Moved to top of card
                        st.write("#### Download Options")
                        dl_cols = st.columns(2)
                        with dl_cols[0]:
                            # Create downloadable JSON with full evaluation details
                            evaluation_json = json.dumps(details['evaluation_data'], indent=2)
                            st.download_button(
                                label="📄 Download Evaluation Report",
                                data=evaluation_json,
                                file_name=f"evaluation_{eval_data['id']}.json",
                                mime="application/json",
                                key=f"eval_download_{eval_data['id']}"  # Unique key for each button
                            )

                        with dl_cols[1]:
                            # Get resume file data
                            resume_file = st.session_state.components['db'].get_resume_file(eval_data['id'])
                            if resume_file and resume_file['file_data']:
                                st.download_button(
                                    label="📥 Download Original Resume",
                                    data=resume_file['file_data'],
                                    file_name=resume_file['file_name'],
                                    mime=resume_file['file_type'],
                                    key=f"resume_download_{eval_data['id']}"  # Unique key for each button
                                )
                            else:
                                st.write("Original resume file not available")

                        st.markdown("---")  # Add a separator line

                        # Experience Assessment Section
                        st.write("#### Experience Assessment")
                        exp_cols = st.columns(3)
                        exp_data = details['evaluation_data'].get('years_of_experience', {})

                        with exp_cols[0]:
                            st.metric("Total Experience", f"{details['years_experience_total']} years")
                        with exp_cols[1]:
                            st.metric("Relevant Experience", f"{details['years_experience_relevant']} years")
                        with exp_cols[2]:
                            st.metric("Required Experience", f"{details['years_experience_required']} years")

                        # Experience Analysis Section
                        st.write("#### Experience Analysis")
                        if exp_data.get('details'):
                            st.write(exp_data['details'])

                        # Relevant Projects
                        if details['key_matches'].get('projects'):
                            st.write("#### Relevant Projects")
                            for project in details['key_matches']['projects']:
                                st.write(f"• {project}")

                        # Evaluation Summary
                        st.write("#### Evaluation Summary")
                        st.write(details['justification'])


            except Exception as e:
                logger.error(f"Error displaying evaluation: {str(e)}")
                continue

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