import streamlit as st
import pandas as pd
from datetime import datetime
import os
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
        title = st.text_input("Job Title")
        uploaded_file = st.file_uploader(
            "Upload Job Description (PDF, DOCX, or TXT)",
            type=['pdf', 'docx', 'txt']
        )

        if uploaded_file is not None:
            try:
                if st.button("Save Uploaded Job Description"):
                    if not title:
                        st.error("Please provide a title for the job description.")
                        return

                    description = extract_text_from_upload(uploaded_file)
                    if description:
                        db.add_job_description(title, description)
                        st.success("Job description uploaded and saved successfully!")
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
                st.experimental_rerun()

def show_evaluation():
    st.title("Resume Evaluation")

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

                # Get job description
                job = next(job for job in jobs if job['title'] == selected_job)

                # Evaluate with AI
                evaluation = ai_evaluator.evaluate_resume(resume_text, job['description'])

                # Save evaluation
                db.save_evaluation(
                    job_id=job['id'],
                    resume_name=uploaded_file.name,
                    result=evaluation['decision'],
                    justification=evaluation['justification']
                )

                # Display results
                st.success("Evaluation Complete!")

                # Decision with color coding
                if evaluation['decision'] == 'shortlist':
                    st.success(f"Decision: {evaluation['decision'].upper()}")
                else:
                    st.error(f"Decision: {evaluation['decision'].upper()}")

                # SAP Experience Analysis
                st.subheader("SAP Implementation Experience")
                sap_exp = evaluation.get('sap_experience', {})
                if sap_exp.get('has_implementation'):
                    st.success("✓ Has SAP Implementation Experience")
                else:
                    st.error("✗ No SAP Implementation Experience")

                st.write("**Implementation Details:**", sap_exp.get('details', 'No details available'))

                if sap_exp.get('projects'):
                    st.write("**SAP Implementation Projects:**")
                    for project in sap_exp['projects']:
                        st.write("•", project)

                # Company Background Analysis
                st.subheader("Company Background")
                comp_bg = evaluation.get('company_background', {})
                if comp_bg.get('has_it_services'):
                    st.success("✓ Has IT Services Company Experience")
                else:
                    st.error("✗ No IT Services Company Experience")

                if comp_bg.get('companies'):
                    st.write("**Relevant Companies:**")
                    for company in comp_bg['companies']:
                        st.write("•", company)

                if comp_bg.get('roles'):
                    st.write("**Relevant Roles:**")
                    for role in comp_bg['roles']:
                        st.write("•", role)

                # Experience Analysis
                st.subheader("Experience Analysis")
                exp_data = evaluation.get('years_of_experience', {})
                cols = st.columns(4)
                with cols[0]:
                    st.metric("Total Experience", f"{exp_data.get('total', 0)} years")
                with cols[1]:
                    st.metric("Relevant Experience", f"{exp_data.get('relevant', 0)} years")
                with cols[2]:
                    st.metric("SAP Implementation", f"{exp_data.get('sap_implementation', 0)} years")
                with cols[3]:
                    st.metric("Required Experience", f"{exp_data.get('required', 0)} years")

                # Detailed justification
                st.subheader("Evaluation Details")
                st.write("**Justification:**", evaluation['justification'])

                if 'experience_analysis' in evaluation:
                    st.write("**Experience Relevance Analysis:**", evaluation['experience_analysis'])

                # Match score with progress bar
                st.subheader("Match Score")
                st.progress(float(evaluation['match_score']))
                st.write(f"Match Score: {evaluation['match_score']*100:.1f}%")

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