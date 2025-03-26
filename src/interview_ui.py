"""
UI components for the new interview system
"""

import logging
import time
import streamlit as st
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

def setup_interview_page():
    """Display the initial setup page for interviews"""
    st.title("AI-Powered Interview System")
    st.markdown("### Comprehensive skills assessment platform for technical hiring")
    
    # Create a container with a light background and padding
    setup_container = st.container()
    with setup_container:
        st.markdown("---")
        
        # Layout for job description and resume
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Job Position")
            
            # Define tech roles for dropdown
            tech_roles = [
                "Frontend Developer", 
                "Backend Developer", 
                "Full Stack Developer",
                "Data Scientist", 
                "Machine Learning Engineer",
                "DevOps Engineer", 
                "Site Reliability Engineer",
                "Mobile Developer",
                "UI/UX Designer",
                "QA Engineer",
                "Software Architect",
                "Product Manager",
                "Technical Project Manager",
                "Data Engineer",
                "Cloud Engineer",
                "Blockchain Developer",
                "Security Engineer",
                "Database Administrator",
                "Network Engineer",
                "Other (specify below)"
            ]
            
            # Role selection with dropdown
            selected_role = st.selectbox(
                "Select Role/Position", 
                options=tech_roles,
                help="Choose the technical role for this interview"
            )
            
            # If "Other" is selected, allow custom entry
            if selected_role == "Other (specify below)":
                custom_role = st.text_input("Specify Role", key="custom_role_input")
                job_title = custom_role if custom_role else "Custom Role"
            else:
                job_title = selected_role
                
            # Job Description file upload
            st.subheader("Job Description")
            jd_file = st.file_uploader(
                "Upload Job Description (Any file type)",
                type=None,
                help="Upload a detailed job description document",
                key="jd_file_input"
            )
            
            # File validation info
            if jd_file is not None:
                col_size, col_type = st.columns(2)
                with col_size:
                    file_size_mb = jd_file.size / (1024 * 1024)
                    if file_size_mb > 5:
                        st.error(f"File size: {file_size_mb:.2f}MB (exceeds 5MB limit)")
                    else:
                        st.success(f"File size: {file_size_mb:.2f}MB")
                
                with col_type:
                    st.success(f"File type: {jd_file.type}")
                
                # Process job description file
                try:
                    with st.spinner("Extracting job description..."):
                        if st.session_state.components.get('utils'):
                            jd_text = st.session_state.components['utils'].extract_text_from_upload(jd_file)
                            st.session_state.jd_text = jd_text
                            
                            # Parse key information from JD
                            with st.expander("Extracted Job Information (Verify)", expanded=True):
                                st.write(f"**Job Title:** {job_title}")
                                if len(jd_text) > 500:
                                    st.write("**Summary:**")
                                    st.write(jd_text[:500] + "...")
                                else:
                                    st.write(jd_text)
                                st.success("✓ Job description processed successfully")
                        else:
                            st.error("Utils component not initialized")
                except Exception as e:
                    logger.error(f"Error processing job description file: {str(e)}")
                    st.error(f"Error processing job description file: {str(e)}")
            
            # Or enter job description manually
            jd_placeholder = (
                "Paste the detailed job description here, including:\n"
                "- Required skills and qualifications\n"
                "- Responsibilities and duties\n"
                "- Technical requirements\n"
                "- Experience level needed"
            )
            
            st.write("Or enter job description manually")
            job_description = st.text_area(
                "Job Description Details",
                height=250,
                placeholder=jd_placeholder,
                help="Enter the complete job description with all requirements",
                key="job_description_input"
            )
            
            # Use processed text if available
            if jd_file is not None and not job_description.strip() and 'jd_text' in st.session_state:
                job_description = st.session_state.jd_text
        
        with col2:
            st.subheader("Candidate Resume/CV")
            
            # Resume file upload with drag-and-drop
            resume_file = st.file_uploader(
                "Upload Resume (Any file type)",
                type=None,
                help="Upload the candidate's resume or CV",
                key="resume_file_input"
            )
            
            # File validation info
            if resume_file is not None:
                col_size, col_type = st.columns(2)
                with col_size:
                    file_size_mb = resume_file.size / (1024 * 1024)
                    if file_size_mb > 5:
                        st.error(f"File size: {file_size_mb:.2f}MB (exceeds 5MB limit)")
                    else:
                        st.success(f"File size: {file_size_mb:.2f}MB")
                
                with col_type:
                    st.success(f"File type: {resume_file.type}")
                
                # Process resume file
                try:
                    with st.spinner("Processing resume..."):
                        if st.session_state.components.get('utils'):
                            resume_text = st.session_state.components['utils'].extract_text_from_upload(resume_file)
                            st.session_state.resume_text = resume_text
                            
                            # Parse key information from resume
                            with st.expander("Extracted Resume Information (Verify)", expanded=True):
                                if len(resume_text) > 500:
                                    st.write("**Summary:**")
                                    st.write(resume_text[:500] + "...")
                                else:
                                    st.write(resume_text)
                                st.success("✓ Resume processed successfully")
                        else:
                            st.error("Utils component not initialized")
                except Exception as e:
                    logger.error(f"Error processing resume file: {str(e)}")
                    st.error(f"Error processing resume file: {str(e)}")
            
            # Or enter resume text manually
            resume_placeholder = (
                "Paste the candidate's resume here, including:\n"
                "- Work experience\n"
                "- Education\n"
                "- Technical skills\n"
                "- Projects and accomplishments\n"
                "- Certifications"
            )
            
            st.write("Or enter resume text manually")
            resume_text = st.text_area(
                "Resume Content",
                height=250,
                placeholder=resume_placeholder,
                help="Enter the complete resume content",
                key="resume_text_input"
            )
            
            # Use processed text if available
            if resume_file is not None and not resume_text.strip() and 'resume_text' in st.session_state:
                resume_text = st.session_state.resume_text
    
    st.subheader("Interview Configuration")
    num_questions = st.slider(
        "Number of Questions", 
        min_value=5, 
        max_value=40,
        value=20, 
        step=5,
        help="Total number of questions for the interview"
    )
    
    # Start interview button
    if st.button("Generate Interview Questions"):
        if not job_title.strip():
            st.error("Job title is required")
            return
            
        if not job_description.strip():
            st.error("Job description is required")
            return
            
        if not resume_text.strip() and resume_file is None:
            st.error("Please either upload a resume or enter resume text")
            return
            
        # If we have file but not text, ensure text is extracted
        if resume_file is not None and not resume_text.strip():
            if 'resume_text' in st.session_state:
                resume_text = st.session_state.resume_text
            else:
                st.error("Failed to process resume. Please enter resume text manually.")
                return
            
        # Create new interview in the database
        try:
            with st.spinner("Setting up interview..."):
                # Save to database
                interview_id = st.session_state.components['db'].create_new_interview(
                    job_title=job_title,
                    job_description=job_description,
                    resume_text=resume_text
                )
                
                if not interview_id:
                    st.error("Failed to create interview session")
                    return
                    
                # Generate questions
                questions_by_type = st.session_state.components['interview_engine'].generate_questions(
                    job_title=job_title,
                    job_description=job_description,
                    resume_text=resume_text,
                    num_questions=num_questions
                )
                
                # Prepare questions for saving to database
                all_questions = []
                for q_type, questions in questions_by_type.items():
                    for question in questions:
                        all_questions.append({
                            "question": question.get("question", ""),
                            "type": q_type
                        })
                
                # Save questions
                success = st.session_state.components['db'].save_interview_questions_new(
                    interview_id=interview_id,
                    questions_data={"questions": all_questions}
                )
                
                if not success:
                    st.error("Failed to save interview questions")
                    return
                
                # Store ID in session state and move to interview interface
                st.session_state.current_interview_id = interview_id
                st.session_state.interview_setup_complete = True
                
                st.success("Interview setup complete! Click below to start the interview.")
                
                # Button to proceed to interview
                if st.button("Start Interview"):
                    st.rerun()
                
        except Exception as e:
            logger.error(f"Error setting up interview: {str(e)}")
            st.error(f"Error setting up interview: {str(e)}")

def interview_interface():
    """Display the main interview interface"""
    # Get the current interview
    interview_id = st.session_state.current_interview_id
    
    # Variables to store interview data
    interview = None
    questions = None
    
    try:
        # Get interview details
        interview = st.session_state.components['db'].get_interview_details(interview_id)
        
        if not interview:
            st.error("Interview session not found")
            if st.button("Return to Setup"):
                st.session_state.interview_setup_complete = False
                st.rerun()
            return
        
        # Get all questions and answers
        questions = st.session_state.components['db'].get_interview_answers(interview_id)
        
        if not questions:
            st.error("No questions found for this interview")
            if st.button("Return to Setup"):
                st.session_state.interview_setup_complete = False
                st.rerun()
            return
            
    except Exception as e:
        logger.error(f"Error loading interview: {str(e)}")
        st.error(f"Error loading interview: {str(e)}")
        if st.button("Return to Setup"):
            st.session_state.interview_setup_complete = False
            st.rerun()
        return
    
    # Display interview header
    st.title(f"Interview: {interview['job_title']}")
    
    # Calculate progress
    total_questions = len(questions)
    answered_questions = sum(1 for q in questions if q.get('answer') is not None)
    progress = answered_questions / total_questions if total_questions > 0 else 0
    
    # Display progress
    st.progress(progress)
    st.write(f"Question {answered_questions + 1} of {total_questions} ({int(progress * 100)}% complete)")
    
    # Find the current question (first unanswered)
    current_question = None
    for q in questions:
        if not q.get('answer'):
            current_question = q
            break
    
    if not current_question:
        # All questions answered, show completion button
        st.success("All questions have been answered!")
        if st.button("Complete Interview & Generate Report"):
            st.session_state.interview_complete = True
            st.rerun()
        return
    
    # Display question type
    question_type = current_question.get('type', 'technical')
    type_labels = {
        'technical': '💻 Technical Question',
        'scenario': '🔄 Scenario-Based Question',
        'behavioral': '👥 Behavioral Question',
        'problem_solving': '🧩 Problem-Solving Question'
    }
    
    st.subheader(type_labels.get(question_type, question_type.capitalize()))
    
    # Display the current question
    st.write(f"### Q: {current_question['question']}")
    
    # Response input
    if 'response_start_time' not in st.session_state:
        st.session_state.response_start_time = time.time()
    
    # Add custom HTML/CSS to disable copy/paste on the text area
    st.markdown("""
    <style>
    .no-copy-paste textarea {
        user-select: none; /* Standard */
        -webkit-user-select: none; /* Safari */
        -ms-user-select: none; /* IE 10+ */
    }
    </style>
    """, unsafe_allow_html=True)

    # Create a container with the class for the no-copy-paste styling
    with st.container():
        st.markdown('<div class="no-copy-paste">', unsafe_allow_html=True)
        answer_text = st.text_area(
            "Enter your response (copy/paste disabled for authentic assessment)",
            height=200,
            key=f"response_{current_question['id']}"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
    # Add a note about the copy/paste restriction
    st.info("📝 **Note:** Copy/paste functionality is disabled to ensure authentic skill assessment.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("Submit Response"):
            if not answer_text.strip():
                st.error("Please enter a response before submitting")
            else:
                # Calculate response time
                response_time = int(time.time() - st.session_state.response_start_time)
                
                with st.spinner("Evaluating response..."):
                    try:
                        # Get job information for context
                        job_title = interview['job_title']
                        job_description = interview['job_description']
                        
                        # Evaluate response
                        evaluation = st.session_state.components['interview_engine'].evaluate_answer(
                            question=current_question['question'],
                            question_type=question_type,
                            answer=answer_text,
                            job_title=job_title,
                            job_description=job_description
                        )
                        
                        # Save response
                        answer_data = {
                            'answer_text': answer_text,
                            'evaluation': evaluation,
                            'response_time': response_time
                        }
                        
                        st.session_state.components['db'].save_interview_answer(
                            question_id=current_question['id'],
                            answer_data=answer_data
                        )
                        
                        # Reset timer and refresh
                        if 'response_start_time' in st.session_state:
                            del st.session_state.response_start_time
                            
                        st.success("Response recorded!")
                        time.sleep(1)  # Brief pause to show success message
                        st.rerun()
                        
                    except Exception as e:
                        logger.error(f"Error processing response: {str(e)}")
                        st.error(f"Error processing response: {str(e)}")
    
    with col2:
        if st.button("End Interview Early"):
            if answered_questions > 0:
                if st.button("Confirm End Interview", key="confirm_end"):
                    st.session_state.interview_complete = True
                    st.rerun()
            else:
                st.error("Please answer at least one question before ending the interview")

def complete_interview():
    """Display the interview completion page and generate final report"""
    interview_id = st.session_state.current_interview_id
    
    try:
        # Get interview details
        interview = st.session_state.components['db'].get_interview_details(interview_id)
        
        if not interview:
            st.error("Interview session not found")
            if st.button("Return to Home"):
                # Clear interview state
                for key in ['current_interview_id', 'interview_setup_complete', 'interview_complete']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
            return
        
        # If already completed, just show the report
        if interview['status'] == 'completed' and interview['report_data']:
            display_interview_report(interview)
            return
        
        # Get all questions and answers
        questions_with_answers = st.session_state.components['db'].get_interview_answers(interview_id)
        
        # Generate final report
        with st.spinner("Generating final interview report..."):
            # Format data for the report generator
            interview_results = []
            for q in questions_with_answers:
                if q.get('answer'):
                    result = {
                        'question': q['question'],
                        'type': q['type'],
                        'answer': q['answer']
                    }
                    interview_results.append(result)
            
            # Calculate completion rate
            completion_rate = len(interview_results) / len(questions_with_answers) if questions_with_answers else 0
            
            # Generate report
            final_report = st.session_state.components['interview_engine'].generate_final_report(
                job_title=interview['job_title'],
                job_description=interview['job_description'],
                resume_text=interview['resume_text'],
                interview_results=interview_results
            )
            
            # Add completion rate to report
            final_report['completion_rate'] = completion_rate
            
            # Save report to database
            success = st.session_state.components['db'].complete_interview(
                interview_id=interview_id,
                report_data=final_report
            )
            
            if not success:
                st.error("Failed to save interview report")
                return
            
            # Get updated interview data
            interview = st.session_state.components['db'].get_interview_details(interview_id)
            
            # Display the report
            display_interview_report(interview)
            
    except Exception as e:
        logger.error(f"Error generating final report: {str(e)}")
        st.error(f"Error generating final report: {str(e)}")
        
        if st.button("Return to Home"):
            # Clear interview state
            for key in ['current_interview_id', 'interview_setup_complete', 'interview_complete']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

def display_interview_report(interview):
    """Helper function to display the interview report"""
    report_data = interview.get('report_data', {})
    
    st.title("Interview Assessment Report")
    st.subheader(f"Position: {interview['job_title']}")
    
    # Show completion rate
    completion_rate = interview.get('completion_rate', 0) * 100
    if completion_rate < 50:
        st.error(f"Interview Completion Rate: {completion_rate:.1f}%")
    elif completion_rate < 80:
        st.warning(f"Interview Completion Rate: {completion_rate:.1f}%")
    else:
        st.success(f"Interview Completion Rate: {completion_rate:.1f}%")
    
    # Overall assessment
    st.subheader("Overall Assessment")
    st.write(report_data.get('overall_assessment', 'No assessment available'))
    
    # Overall scores
    scores = report_data.get('scores', {})
    
    st.subheader("Evaluation Scores")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Overall", f"{scores.get('overall', 0)}/10")
    with col2:
        st.metric("Technical", f"{scores.get('technical', 0)}/10")
    with col3:
        st.metric("Scenario", f"{scores.get('scenario', 0)}/10")
    with col4:
        st.metric("Behavioral", f"{scores.get('behavioral', 0)}/10")
    with col5:
        st.metric("Problem Solving", f"{scores.get('problem_solving', 0)}/10")
    
    # Final recommendation
    recommendation = report_data.get('recommendation', 'No recommendation')
    st.subheader("Final Recommendation")
    
    if recommendation.lower() == 'hire':
        st.success(f"Recommendation: {recommendation}")
    elif recommendation.lower() == 'do not hire':
        st.error(f"Recommendation: {recommendation}")
    else:
        st.info(f"Recommendation: {recommendation}")
    
    st.write(report_data.get('reasoning', 'No reasoning provided'))
    
    # Strengths and weaknesses
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Key Strengths")
        strengths = report_data.get('key_strengths', [])
        for strength in strengths:
            st.write(f"- {strength}")
    
    with col2:
        st.subheader("Areas for Improvement")
        weaknesses = report_data.get('areas_for_improvement', [])
        for weakness in weaknesses:
            st.write(f"- {weakness}")
    
    # Detailed assessments
    with st.expander("Technical Skills Assessment"):
        tech_skills = report_data.get('technical_skills', {})
        st.write(tech_skills.get('assessment', 'No assessment available'))
        
        st.write("**Strengths:**")
        for strength in tech_skills.get('strengths', []):
            st.write(f"- {strength}")
            
        st.write("**Weaknesses:**")
        for weakness in tech_skills.get('weaknesses', []):
            st.write(f"- {weakness}")
    
    with st.expander("Communication Skills Assessment"):
        comm_skills = report_data.get('communication_skills', {})
        st.write(comm_skills.get('assessment', 'No assessment available'))
    
    with st.expander("Problem Solving Assessment"):
        problem_solving = report_data.get('problem_solving', {})
        st.write(problem_solving.get('assessment', 'No assessment available'))
        
    # Key observations
    with st.expander("Key Observations"):
        observations = report_data.get('key_observations', [])
        for observation in observations:
            st.write(f"- {observation}")
    
    # Interview answers
    with st.expander("Interview Transcript"):
        try:
            # Get all questions and answers
            questions_with_answers = st.session_state.components['db'].get_interview_answers(interview['id'])
            
            for i, qa in enumerate(questions_with_answers):
                if not qa.get('answer'):
                    continue  # Skip unanswered questions
                    
                with st.expander(f"Q{i+1}: {qa['question'][:80]}..."):
                    st.write(f"**Question:** {qa['question']}")
                    st.write(f"**Type:** {qa['type'].capitalize()}")
                    
                    answer = qa['answer']
                    st.write(f"**Response:** {answer['text']}")
                    
                    evaluation = answer.get('evaluation', {})
                    st.write(f"**Score:** {evaluation.get('score', 0)}/10")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Strengths:**")
                        for strength in evaluation.get('strengths', []):
                            st.write(f"- {strength}")
                            
                    with col2:
                        st.write("**Areas for Improvement:**")
                        for weakness in evaluation.get('weaknesses', []):
                            st.write(f"- {weakness}")
                            
                    st.write(f"**Feedback:** {evaluation.get('feedback', 'No feedback provided')}")
                    
                    if 'response_time' in answer:
                        response_time = answer['response_time']
                        st.write(f"**Response Time:** {response_time} seconds")
        except Exception as e:
            logger.error(f"Error displaying interview transcript: {str(e)}")
            st.error("Could not load interview transcript")
    
    # Actions
    st.subheader("Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export PDF Report"):
            try:
                from report_generator import generate_evaluation_report
                
                # Format data for report
                formatted_data = {
                    'candidate_name': 'Candidate',  # We don't have candidate name in new system
                    'job_title': interview['job_title'],
                    'interview_date': interview['end_time'].strftime("%Y-%m-%d") if interview['end_time'] else datetime.now().strftime("%Y-%m-%d"),
                    'overall_score': scores.get('overall', 0),
                    'technical_score': scores.get('technical', 0),
                    'communication_score': scores.get('behavioral', 0),  # Using behavioral for communication
                    'problem_solving_score': scores.get('problem_solving', 0),
                    'experience_score': 0,  # Not available in new system
                    'recommendation': report_data.get('recommendation', 'No recommendation'),
                    'reasoning': report_data.get('reasoning', 'No reasoning provided'),
                    'strengths': report_data.get('key_strengths', []),
                    'weaknesses': report_data.get('areas_for_improvement', []),
                    'technical_assessment': report_data.get('technical_skills', {}).get('assessment', '')
                }
                
                pdf_bytes = generate_evaluation_report(formatted_data, f"Candidate-{interview['id']}")
                
                # Provide download link
                st.download_button(
                    label="Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"interview_report_{interview['job_title'].replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                logger.error(f"Error generating PDF report: {str(e)}")
                st.error(f"Error generating PDF report: {str(e)}")
    
    with col2:
        if st.button("Back to Dashboard"):
            # Clear interview state
            for key in ['current_interview_id', 'interview_setup_complete', 'interview_complete']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

def show_interview_history():
    """Display the interview history page"""
    st.title("Interview History")
    
    try:
        # Tabs for completed and in-progress interviews
        tab1, tab2 = st.tabs(["Completed Interviews", "In-Progress Interviews"])
        
        with tab1:
            # Get completed interviews
            completed_interviews = st.session_state.components['db'].get_completed_interviews_new()
            
            if not completed_interviews:
                st.info("No completed interviews found")
            else:
                # Create a dataframe for better display
                df_data = []
                for interview in completed_interviews:
                    df_data.append({
                        'ID': interview['id'],
                        'Position': interview['job_title'],
                        'Date': interview['end_time'].strftime("%Y-%m-%d %H:%M") if interview['end_time'] else 'Unknown',
                        'Score': f"{interview['overall_score']}/10",
                        'Completion': f"{interview['completion_rate'] * 100:.1f}%",
                        'Recommendation': interview['recommendation']
                    })
                
                if df_data:
                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True)
                    
                    # Allow selecting interview to view
                    selected_id = st.selectbox(
                        "Select interview to view details",
                        options=[interview['id'] for interview in completed_interviews],
                        format_func=lambda x: f"ID: {x} - {next((i['job_title'] for i in completed_interviews if i['id'] == x), 'Unknown')}"
                    )
                    
                    if st.button("View Selected Interview"):
                        st.session_state.current_interview_id = selected_id
                        st.session_state.interview_setup_complete = True
                        st.session_state.interview_complete = True
                        st.rerun()
        
        with tab2:
            # Get in-progress interviews
            try:
                in_progress_interviews = st.session_state.components['db'].get_in_progress_interviews()
                
                if not in_progress_interviews:
                    st.info("No in-progress interviews found")
                else:
                    # Create a dataframe for better display
                    df_data = []
                    for interview in in_progress_interviews:
                        df_data.append({
                            'ID': interview['id'],
                            'Position': interview['job_title'],
                            'Started': interview['start_time'].strftime("%Y-%m-%d %H:%M") if interview['start_time'] else 'Unknown'
                        })
                    
                    if df_data:
                        df = pd.DataFrame(df_data)
                        st.dataframe(df, use_container_width=True)
                        
                        # Allow selecting interview to continue
                        selected_id = st.selectbox(
                            "Select interview to continue",
                            options=[interview['id'] for interview in in_progress_interviews],
                            format_func=lambda x: f"ID: {x} - {next((i['job_title'] for i in in_progress_interviews if i['id'] == x), 'Unknown')}"
                        )
                        
                        if st.button("Continue Selected Interview"):
                            st.session_state.current_interview_id = selected_id
                            st.session_state.interview_setup_complete = True
                            st.session_state.interview_complete = False
                            st.rerun()
            except Exception as e:
                logger.error(f"Error loading in-progress interviews: {str(e)}")
                st.error("Could not load in-progress interviews")
    
    except Exception as e:
        logger.error(f"Error displaying interview history: {str(e)}")
        st.error(f"Error displaying interview history: {str(e)}")
    
    # Button to start new interview
    if st.button("Start New Interview"):
        # Clear interview state to start fresh
        for key in ['current_interview_id', 'interview_setup_complete', 'interview_complete']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

def show_interviews():
    """Main interview system page"""
    # Initialize session state if needed
    if 'interview_setup_complete' not in st.session_state:
        st.session_state.interview_setup_complete = False
    
    if 'interview_complete' not in st.session_state:
        st.session_state.interview_complete = False
    
    if 'view_history' not in st.session_state:
        st.session_state.view_history = False
    
    # Custom styling for the UI
    st.markdown("""
    <style>
    .main-header {
        color: #3366ff;
        text-align: center;
        margin-bottom: 20px;
    }
    .system-description {
        text-align: center;
        color: #666;
        margin-bottom: 30px;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Determine which view to show
    if st.session_state.view_history:
        show_interview_history()
    elif st.session_state.interview_complete:
        complete_interview()
    elif st.session_state.interview_setup_complete:
        interview_interface()
    else:
        # Display a welcome header before the setup page
        st.markdown("<h1 class='main-header'>AI-Powered Interview System</h1>", unsafe_allow_html=True)
        st.markdown("<p class='system-description'>Comprehensive skills assessment platform for technical hiring</p>", unsafe_allow_html=True)
        
        # Information box with instructions
        st.info("""
        ### How to use this system:
        1. Select a technical role and provide a job description
        2. Upload a candidate's resume or paste the text
        3. Generate tailored technical interview questions
        4. Conduct the interview with AI-powered evaluation
        5. Receive a detailed assessment report with hiring recommendations
        """)
        
        # Create two columns for actions
        col1, col2 = st.columns(2)
        
        # Button to view history in the first column
        with col1:
            if st.button("📋 View Interview History", key="view_history_btn"):
                st.session_state.view_history = True
                st.rerun()
        
        # Button to create new interview in the second column
        with col2:
            if st.button("🚀 Start New Interview", key="start_new_btn"):
                # This will show the setup page below
                pass
        
        # Show the setup page regardless
        setup_interview_page()