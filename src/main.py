import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import json # added for json download
from database import Database
from ai_evaluator import AIEvaluator
from pdf_processor import PDFProcessor
from analytics import Analytics
from utils import extract_text_from_upload

# Initialize components
db = Database()
ai_evaluator = AIEvaluator()
pdf_processor = PDFProcessor()
analytics = Analytics()

def init_session_state():
    if 'page' not in st.session_state:
        st.session_state.page = 'home'

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

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Active Job Descriptions", db.get_active_jobs_count())
    with col2:
        st.metric("Evaluations Today", db.get_today_evaluations_count())

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

                    db.add_job_description(title, description, evaluation_criteria)
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

                        db.add_job_description(title, description, evaluation_criteria)
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
    jobs = db.get_all_jobs()
    for job in jobs:
        with st.expander(f"{job['title']} - {job['date_created']}"):
            st.write(job['description'])

            # Show evaluation criteria if exists
            if job['has_criteria']:
                criteria = db.get_evaluation_criteria(job['id'])
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
                db.delete_job(job['id'])
                st.rerun()

def show_evaluation():
    st.title("Resume Evaluation")

    # Create tabs for new evaluation and evaluations list
    tab1, tab2 = st.tabs(["New Evaluation", "Evaluations"])

    with tab1:
        # Job selection
        jobs = db.get_all_jobs()
        job_titles = [job['title'] for job in jobs]
        selected_job = st.selectbox("Select Job Description", job_titles)

        # Resume upload
        uploaded_file = st.file_uploader("Upload Resume (PDF)", type=['pdf'])

        if uploaded_file and selected_job:
            if st.button("Evaluate Resume"):
                with st.spinner("Processing resume..."):
                    # Extract text from PDF
                    resume_text = pdf_processor.extract_text(uploaded_file)

                    # Get job description and criteria
                    job = next(job for job in jobs if job['title'] == selected_job)
                    criteria = db.get_evaluation_criteria(job['id']) if job['has_criteria'] else None

                    # Evaluate with AI
                    evaluation = ai_evaluator.evaluate_resume(
                        resume_text,
                        job['description'],
                        evaluation_criteria=criteria
                    )

                    # Save complete evaluation results
                    db.save_evaluation(
                        job_id=job['id'],
                        resume_name=uploaded_file.name,
                        evaluation_result=evaluation
                    )

                    # Display results
                    st.success("Evaluation Complete!")

                    # Decision with color coding
                    if evaluation['decision'] == 'shortlist':
                        st.success(f"Decision: {evaluation['decision'].upper()}")
                    else:
                        st.error(f"Decision: {evaluation['decision'].upper()}")

                    # Match score with progress bar
                    st.subheader("Match Score")
                    st.progress(float(evaluation['match_score']))
                    st.write(f"Match Score: {evaluation['match_score']*100:.1f}%")

                    # Experience Analysis
                    st.subheader("Experience Analysis")
                    exp_data = evaluation['years_of_experience']
                    cols = st.columns(3)
                    with cols[0]:
                        st.metric("Total Experience", f"{exp_data['total']} years")
                    with cols[1]:
                        st.metric("Relevant Experience", f"{exp_data['relevant']} years")
                    with cols[2]:
                        st.metric("Required Experience", f"{exp_data['required']} years")

                    # Detailed justification
                    st.subheader("Evaluation Details")
                    st.write("**Justification:**", evaluation['justification'])

                    if 'experience_analysis' in evaluation:
                        st.write("**Experience Analysis:**", evaluation['experience_analysis'])

                    # Skills and Requirements
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Matching Skills/Qualifications:**")
                        for skill in evaluation['key_matches']:
                            st.write("✓", skill)

                    with col2:
                        st.write("**Missing Requirements:**")
                        for req in evaluation['missing_requirements']:
                            st.write("✗", req)
                    st.session_state.evaluation_complete = True

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
            evaluations = db.get_evaluations_by_date_range(start_date, end_date)
        else:
            # Convert period to database format
            period_map = {
                "Past Week": "week",
                "Past Month": "month",
                "Past Quarter": "quarter"
            }
            evaluations = db.get_evaluations_by_period(period_map[period])

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
                    'resume_name': eval_record[2],
                    'job_title': eval_record[15],
                    'result': eval_record[3],
                    'match_score': eval_record[5],
                    'evaluation_date': eval_record[13]
                }

                # Apply search filter
                if search_term.lower() not in eval_data['resume_name'].lower() and \
                   search_term.lower() not in eval_data['job_title'].lower():
                    continue

                # Create card for each evaluation
                with st.expander(f"📄 {eval_data['resume_name']} - {eval_data['job_title']} ({eval_data['evaluation_date'].strftime('%Y-%m-%d %H:%M')})"):
                    cols = st.columns([2, 1, 1])

                    with cols[0]:
                        if eval_data['result'] == 'shortlist':
                            st.success(f"Decision: {eval_data['result'].upper()}")
                        else:
                            st.error(f"Decision: {eval_data['result'].upper()}")

                    with cols[1]:
                        st.metric("Match Score", f"{float(eval_data['match_score'])*100:.1f}%")

                    # Get detailed evaluation data
                    details = db.get_evaluation_details(eval_data['id'])
                    if details:
                        st.write("#### Key Information")
                        exp_cols = st.columns(3)
                        with exp_cols[0]:
                            st.metric("Total Experience", f"{details['years_experience_total']} years")
                        with exp_cols[1]:
                            st.metric("Relevant Experience", f"{details['years_experience_relevant']} years")
                        with exp_cols[2]:
                            st.metric("Required Experience", f"{details['years_experience_required']} years")

                        st.write("#### Evaluation Summary")
                        st.write(details['justification'])

                        # Skills and Requirements in columns
                        sk_cols = st.columns(2)
                        with sk_cols[0]:
                            st.write("**Key Matches:**")
                            for skill in details['key_matches']:
                                st.write(f"✓ {skill}")

                        with sk_cols[1]:
                            st.write("**Missing Requirements:**")
                            for req in details['missing_requirements']:
                                st.write(f"✗ {req}")

                        # Download buttons
                        dl_cols = st.columns(2)
                        with dl_cols[0]:
                            # Create downloadable JSON with full evaluation details
                            evaluation_json = json.dumps(details['evaluation_data'], indent=2)
                            st.download_button(
                                label="📥 Download Detailed Report",
                                data=evaluation_json,
                                file_name=f"evaluation_{eval_data['id']}.json",
                                mime="application/json"
                            )

                        with dl_cols[1]:
                            st.write("Resume download option will be added here")

            except Exception as e:
                st.error(f"Error displaying evaluation: {str(e)}")
                continue

        # Handle row selection (removed, replaced by card system)

        # Show modal with justification (removed, integrated into cards)


def show_analytics():
    st.title("Analytics Dashboard")

    # Time period selection
    period = st.selectbox("Select Time Period", ["Week", "Month", "Year"])

    # Get analytics data
    data = analytics.get_evaluation_stats(period.lower())

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
    st.plotly_chart(analytics.plot_evaluation_trend(period.lower()))

    st.subheader("Job-wise Distribution")
    st.plotly_chart(analytics.plot_job_distribution())

def main():
    init_session_state()
    sidebar()

    if st.session_state.page == 'home':
        show_home()
    elif st.session_state.page == 'jobs':
        show_jobs()
    elif st.session_state.page == 'evaluation':
        show_evaluation()
    elif st.session_state.page == 'analytics':
        show_analytics()

if __name__ == "__main__":
    main()