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
    with st.expander("Add New Job Description", expanded=True):
        # Method selection
        input_method = st.radio(
            "Choose input method",
            ["Manual Entry", "Upload File"],
            horizontal=True
        )

        if input_method == "Manual Entry":
            title = st.text_input("Job Title")
            description = st.text_area("Job Description")
            submit_button = st.button("Save Job Description")

            if submit_button and title and description:
                try:
                    db.add_job_description(title, description)
                    st.success("Job description added successfully!")
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
                        description = extract_text_from_upload(uploaded_file)
                        if title and description:
                            db.add_job_description(title, description)
                            st.success("Job description uploaded and saved successfully!")
                            # Preview the extracted text
                            with st.expander("Preview Extracted Text"):
                                st.text(description)
                        else:
                            st.error("Please provide both a title and upload a file.")
                except Exception as e:
                    st.error(f"Failed to process uploaded file: {str(e)}")

    # List existing job descriptions
    st.subheader("Existing Job Descriptions")
    jobs = db.get_all_jobs()
    for job in jobs:
        with st.expander(f"{job['title']} - {job['date_created']}"):
            st.write(job['description'])
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
                st.write("Decision:", evaluation['decision'])
                st.write("Justification:", evaluation['justification'])

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