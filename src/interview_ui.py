"""
UI components for the new interview system
"""

import logging
import time
import streamlit as st
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

def add_accessibility_controls():
    """Add accessibility controls to the sidebar"""
    with st.sidebar.expander("Accessibility Options", expanded=False):
        # Font size controls
        st.write("**Font Size**")
        font_size = st.select_slider(
            "Adjust font size",
            options=["Small", "Medium", "Large", "X-Large"],
            value="Medium"
        )
        
        # Set font sizes based on selection
        font_sizes = {
            "Small": "0.9rem",
            "Medium": "1rem",
            "Large": "1.2rem",
            "X-Large": "1.4rem"
        }
        
        # High contrast mode
        high_contrast = st.checkbox("High Contrast Mode")
        
        # Voice-to-text option (simulated for now)
        voice_to_text = st.checkbox("Enable Voice-to-Text Input")
        
        # Apply accessibility settings
        bg_color = "#ffffff"
        text_color = "#000000"
        
        if high_contrast:
            bg_color = "#000000"
            text_color = "#ffffff"
        
        # Store accessibility preferences in session state
        st.session_state.accessibility = {
            "font_size": font_sizes[font_size],
            "high_contrast": high_contrast,
            "voice_to_text": voice_to_text,
            "bg_color": bg_color,
            "text_color": text_color
        }
        
        # Apply CSS for accessibility
        st.markdown(f"""
        <style>
        body {{
            font-size: {font_sizes[font_size]};
        }}
        
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
        }}
        
        .high-contrast {{
            background-color: {bg_color} !important;
            color: {text_color} !important;
        }}
        
        /* Make text areas and buttons more accessible */
        .stTextArea textarea {{
            font-size: {font_sizes[font_size]};
            padding: 10px;
            line-height: 1.5;
        }}
        </style>
        """, unsafe_allow_html=True)

def setup_interview_page():
    """Display the initial setup page for interviews"""
    # Add accessibility controls
    add_accessibility_controls()
    
    # Create a container with a light background and padding
    setup_container = st.container()
    with setup_container:
        st.markdown("---")
        
        # First: Job Position
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
        
        # Second: Candidate Resume/CV 
        st.markdown("---")
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
        
        # Use processed text if available
        if resume_file is not None and 'resume_text' in st.session_state:
            resume_text = st.session_state.resume_text
        else:
            # Initialize resume_text as empty string if no file is uploaded
            resume_text = ""
        
        # Third: Job Description
        st.markdown("---")
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
        
        st.markdown("---")
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
                
            if resume_file is None:
                st.error("Please upload a candidate resume/CV")
                return
                
            # If we have file but text extraction failed
            if resume_file is not None and not resume_text.strip():
                if 'resume_text' in st.session_state:
                    resume_text = st.session_state.resume_text
                else:
                    st.error("Failed to process resume. Please try uploading the file again or try a different file format.")
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
    
    # Initialize interview timer if not present
    if 'interview_start_time' not in st.session_state:
        st.session_state.interview_start_time = time.time()
    
    # Function to format elapsed time
    def format_elapsed_time(seconds):
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        else:
            return f"{minutes}m {seconds}s"
    
    try:
        # Get interview details
        interview = st.session_state.components['db'].get_interview_details(interview_id)
        
        if not interview:
            st.error("Interview session not found")
            if st.button("Return to Setup"):
                st.session_state.interview_setup_complete = False
                if 'interview_start_time' in st.session_state:
                    del st.session_state.interview_start_time
                st.rerun()
            return
        
        # Get all questions and answers
        questions = st.session_state.components['db'].get_interview_answers(interview_id)
        
        if not questions:
            st.error("No questions found for this interview")
            if st.button("Return to Setup"):
                st.session_state.interview_setup_complete = False
                if 'interview_start_time' in st.session_state:
                    del st.session_state.interview_start_time
                st.rerun()
            return
            
    except Exception as e:
        logger.error(f"Error loading interview: {str(e)}")
        st.error(f"Error loading interview: {str(e)}")
        if st.button("Return to Setup"):
            st.session_state.interview_setup_complete = False
            if 'interview_start_time' in st.session_state:
                del st.session_state.interview_start_time
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

    # Get accessibility settings if available
    voice_to_text_enabled = False
    if 'accessibility' in st.session_state:
        voice_to_text_enabled = st.session_state.accessibility.get('voice_to_text', False)
    
    # Show voice-to-text option if enabled
    if voice_to_text_enabled:
        st.info("🎤 **Voice-to-Text is enabled**. Click the button below to start recording.")
        
        # Voice input button (simulated functionality)
        voice_col1, voice_col2 = st.columns([1, 3])
        with voice_col1:
            if st.button("🎤 Record", key="voice_record"):
                with st.spinner("Recording... (simulated)"):
                    # Simulate recording for 3 seconds
                    time.sleep(2)
                    # In a real implementation, this would capture audio and convert to text
                    if 'voice_text' not in st.session_state:
                        st.session_state.voice_text = "Voice input would be transcribed and appear here."
                    else:
                        st.session_state.voice_text += " Additional voice input would be added here."
        
        with voice_col2:
            if st.button("❌ Clear", key="voice_clear"):
                if 'voice_text' in st.session_state:
                    del st.session_state.voice_text
    
    # Create a container with the class for the no-copy-paste styling
    with st.container():
        st.markdown('<div class="no-copy-paste">', unsafe_allow_html=True)
        
        # Pre-fill with voice text if available
        initial_value = ""
        if voice_to_text_enabled and 'voice_text' in st.session_state:
            initial_value = st.session_state.voice_text
            
        answer_text = st.text_area(
            "Enter your response (copy/paste disabled for authentic assessment)",
            value=initial_value,
            height=200,
            key=f"response_{current_question['id']}"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Character counter
        char_count = len(answer_text)
        max_chars = 3000
        char_percentage = min(100, (char_count / max_chars) * 100)
        
        # Show character counter with warning colors when approaching limit
        counter_color = "green"
        if char_percentage > 80:
            counter_color = "orange"
        if char_percentage > 95:
            counter_color = "red"
            
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: -15px;">
            <span style="color: {counter_color}; font-size: 0.8rem;">
                {char_count}/{max_chars} characters
            </span>
        </div>
        """, unsafe_allow_html=True)
        
    # Add a note about the copy/paste restriction
    st.info("📝 **Note:** Copy/paste functionality is disabled to ensure authentic skill assessment.")
    
    # Timer displays - both question timer and total interview timer
    current_time = time.time()
    
    # Question timer (current question response time)
    question_elapsed_seconds = int(current_time - st.session_state.response_start_time)
    q_minutes, q_seconds = divmod(question_elapsed_seconds, 60)
    question_time_display = f"{q_minutes:02d}:{q_seconds:02d}"
    
    # Total interview timer
    total_elapsed_seconds = int(current_time - st.session_state.interview_start_time)
    total_time = format_elapsed_time(total_elapsed_seconds)
    
    # Display both timers
    st.markdown(f"""
    <div style="position: absolute; top: 70px; right: 30px; background-color: #f0f2f6; padding: 8px 12px; 
         border-radius: 4px; font-size: 1.1rem; font-weight: bold;">
        ⏱️ Question: {question_time_display}
    </div>
    
    <div style="position: absolute; top: 130px; right: 30px; background-color: #e9ecef; padding: 8px 12px; 
         border-radius: 4px; font-size: 0.9rem;">
        Total interview time: {total_time}
    </div>
    """, unsafe_allow_html=True)
    
    # Create three columns for the action buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("Submit Response", use_container_width=True):
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
        if st.button("Next Question ➡️", use_container_width=True):
            # Mark the question as skipped with a minimal evaluation
            with st.spinner("Skipping to next question..."):
                try:
                    # Save a minimal response indicating question was skipped
                    answer_data = {
                        'answer_text': "[Question skipped by interviewer]",
                        'evaluation': {
                            'score': 0,
                            'feedback': "This question was skipped.",
                            'improvement_suggestions': "",
                            'strengths': "",
                            'weaknesses': "Question was not attempted."
                        },
                        'response_time': 0,
                        'skipped': True
                    }
                    
                    st.session_state.components['db'].save_interview_answer(
                        question_id=current_question['id'],
                        answer_data=answer_data
                    )
                    
                    # Reset timer and refresh
                    if 'response_start_time' in st.session_state:
                        del st.session_state.response_start_time
                        
                    st.success("Question skipped!")
                    time.sleep(1)  # Brief pause to show success message
                    st.rerun()
                    
                except Exception as e:
                    logger.error(f"Error skipping question: {str(e)}")
                    st.error(f"Error skipping question: {str(e)}")
    
    with col3:
        if st.button("End Interview", use_container_width=True):
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
    """Helper function to display the modern, minimalistic post-interview UI dashboard"""
    report_data = interview.get('report_data', {})
    completion_rate = report_data.get('completion_rate', 0)
    scores = report_data.get('scores', {})
    
    # Custom CSS for modern UI
    st.markdown("""
    <style>
    .success-header {
        color: #0DB16E;
        font-size: 36px;
        font-weight: 700;
        text-align: center;
        margin-bottom: 10px;
        padding: 20px 0;
    }
    .interview-summary {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 30px;
    }
    .section-header {
        font-size: 24px;
        font-weight: 600;
        margin-bottom: 15px;
        border-bottom: 1px solid #eee;
        padding-bottom: 10px;
    }
    .rating-container {
        margin-top: 5px;
        margin-bottom: 15px;
    }
    .star-rating {
        font-size: 24px;
        color: #FFC107;
    }
    .rating-empty {
        color: #E0E0E0;
    }
    .progress-label {
        display: flex;
        justify-content: space-between;
        margin-bottom: 5px;
    }
    .progress-container {
        margin-bottom: 20px;
    }
    .recommendation-box {
        padding: 20px;
        border-radius: 8px;
        margin-top: 20px;
        font-weight: 600;
        text-align: center;
    }
    .hire-recommendation {
        background-color: #d4edda;
        color: #155724;
    }
    .consider-recommendation {
        background-color: #fff3cd;
        color: #856404;
    }
    .no-hire-recommendation {
        background-color: #f8d7da;
        color: #721c24;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Interview Completed Successfully Header
    st.markdown('<div class="success-header">Interview Completed Successfully</div>', unsafe_allow_html=True)
    
    # Summary Section
    st.markdown('<div class="interview-summary">', unsafe_allow_html=True)
    
    # Extract candidate name or use placeholder
    candidate_name = "Candidate"
    if "candidate_info" in report_data:
        candidate_name = report_data.get("candidate_info", {}).get("name", "Candidate")
    
    # Calculate interview duration from report or use placeholder
    interview_duration = report_data.get("interview_duration", "30 minutes")
    
    # Create two columns for candidate info and completion rate
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div style="margin-bottom: 10px;">
            <strong>Candidate:</strong> {candidate_name}<br>
            <strong>Position:</strong> {interview['job_title']}<br>
            <strong>Duration:</strong> {interview_duration}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Display completion rate with progress bar
        completion_percentage = int(completion_rate * 100)
        st.markdown(f"""
        <div style="margin-bottom: 10px;">
            <strong>Interview Completion Rate:</strong> {completion_percentage}%
        </div>
        """, unsafe_allow_html=True)
        st.progress(completion_rate)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Performance Breakdown Section
    st.markdown('<div class="section-header">Performance Breakdown</div>', unsafe_allow_html=True)
    
    # Create scoring function for stars and percentage bars
    def display_rating(category, score, max_score=10):
        # Normalize score to 0-5 stars
        star_score = min(5, max(0, round(score * 5 / max_score)))
        percentage = int(score * 100 / max_score)
        
        # Create progress bar with percentage
        st.markdown(f"""
        <div class="progress-container">
            <div class="progress-label">
                <span><strong>{category}</strong></span>
                <span>{percentage}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(score/max_score)
        
        # Create star rating
        stars_html = ""
        for i in range(5):
            if i < star_score:
                stars_html += '★'
            else:
                stars_html += '☆'
        
        st.markdown(f"""
        <div class="rating-container">
            <span class="star-rating">{stars_html}</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Display each category
    col1, col2 = st.columns(2)
    
    with col1:
        display_rating("Technical Skills", scores.get('technical', 0))
        display_rating("Communication", scores.get('behavioral', 0))
    
    with col2:
        display_rating("Problem-Solving", scores.get('problem_solving', 0))
        display_rating("Overall Performance", scores.get('overall', 0))
    
    # Recommendation Section
    recommendation = report_data.get('recommendation', 'No recommendation')
    recommendation_class = "consider-recommendation"
    
    if recommendation.lower() == 'hire':
        recommendation_class = "hire-recommendation"
    elif recommendation.lower() == 'do not hire':
        recommendation_class = "no-hire-recommendation"
    
    st.markdown(f"""
    <div class="recommendation-box {recommendation_class}">
        Final Recommendation: {recommendation.upper()}
    </div>
    """, unsafe_allow_html=True)
    
    # Reasoning
    st.markdown('<div class="section-header">Assessment Summary</div>', unsafe_allow_html=True)
    st.write(report_data.get('reasoning', 'No reasoning provided'))
    
    # Strengths and areas for improvement
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Key Strengths")
        strengths = report_data.get('key_strengths', [])
        for strength in strengths:
            st.markdown(f"✓ {strength}")
    
    with col2:
        st.subheader("Areas for Improvement")
        weaknesses = report_data.get('areas_for_improvement', [])
        for weakness in weaknesses:
            st.markdown(f"→ {weakness}")
    
    # Detailed assessments in expandable sections
    with st.expander("Detailed Technical Skills Assessment"):
        tech_skills = report_data.get('technical_skills', {})
        st.write(tech_skills.get('assessment', 'No assessment available'))
        
        st.write("**Strengths:**")
        for strength in tech_skills.get('strengths', []):
            st.markdown(f"✓ {strength}")
            
        st.write("**Areas to Improve:**")
        for weakness in tech_skills.get('weaknesses', []):
            st.markdown(f"→ {weakness}")
    
    with st.expander("Detailed Communication Skills Assessment"):
        comm_skills = report_data.get('communication_skills', {})
        st.write(comm_skills.get('assessment', 'No assessment available'))
    
    with st.expander("Detailed Problem Solving Assessment"):
        problem_solving = report_data.get('problem_solving', {})
        st.write(problem_solving.get('assessment', 'No assessment available'))
        
    # Export and actions section
    st.markdown('<div class="section-header">Report Actions</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1,1])
    
    with col1:
        st.button("📄 Export Report (PDF)", key="export_pdf")
    
    with col2:
        st.button("📧 Share Report", key="share_report")
    
    with col3:
        if st.button("🏠 Return to Home"):
            # Clear interview state
            for key in ['current_interview_id', 'interview_setup_complete', 'interview_complete']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
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
                    
                # Check if the question was skipped
                answer = qa['answer']
                is_skipped = answer.get('skipped', False)
                
                # Add visual indicator for skipped questions
                question_prefix = f"Q{i+1}: "
                if is_skipped:
                    question_prefix = f"Q{i+1} [SKIPPED]: "
                
                with st.expander(f"{question_prefix}{qa['question'][:80]}..."):
                    st.write(f"**Question:** {qa['question']}")
                    st.write(f"**Type:** {qa['type'].capitalize()}")
                    
                    if is_skipped:
                        st.warning("This question was skipped during the interview.")
                        st.write(f"**Response:** {answer['text']}")
                        st.write("**Score:** 0/10 (skipped questions do not contribute to final score)")
                    else:
                        st.write(f"**Response:** {answer['text']}")
                        evaluation = answer.get('evaluation', {})
                        st.write(f"**Score:** {evaluation.get('score', 0)}/10")
                    
                    evaluation = answer.get('evaluation', {})
                    
                    # Don't show detailed feedback for skipped questions
                    if not is_skipped:
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
    
    # Add a container with custom styling for the buttons
    st.markdown("""
    <style>
    .history-button {
        width: 100%;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    
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
                    
                    st.subheader("View Completed Interview Report")
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Allow selecting interview to view
                        selected_id = st.selectbox(
                            "Select interview to view details",
                            options=[interview['id'] for interview in completed_interviews],
                            format_func=lambda x: f"ID: {x} - {next((i['job_title'] for i in completed_interviews if i['id'] == x), 'Unknown')}",
                            key="completed_select"
                        )
                    
                    with col2:
                        # Ensure button is prominently displayed
                        if st.button("📋 View Report", key="view_completed", use_container_width=True):
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
                        
                        st.subheader("Continue In-Progress Interview")
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            # Allow selecting interview to continue
                            selected_id = st.selectbox(
                                "Select interview to continue",
                                options=[interview['id'] for interview in in_progress_interviews],
                                format_func=lambda x: f"ID: {x} - {next((i['job_title'] for i in in_progress_interviews if i['id'] == x), 'Unknown')}",
                                key="in_progress_select"
                            )
                        
                        with col2:
                            # Ensure button is prominently displayed
                            if st.button("▶️ Continue", key="continue_interview", use_container_width=True):
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
    
    # Create a visual separator
    st.markdown("---")
    
    # Add navigation buttons
    col1, col2 = st.columns(2)
    
    with col1:
        # Return to Home button
        if st.button("🏠 Return to Home", key="return_home", use_container_width=True):
            # Clear all interview state
            for key in ['current_interview_id', 'interview_setup_complete', 'interview_complete', 'view_history', 'interview_start_time', 'response_start_time']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    with col2:
        # Add a more prominent "Start New Interview" button
        if st.button("🆕 Start New Interview", key="start_new", use_container_width=True):
            # Clear interview state to start fresh
            for key in ['current_interview_id', 'interview_setup_complete', 'interview_complete', 'view_history', 'interview_start_time', 'response_start_time']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # No subtitle needed

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
        st.markdown("<h1 class='main-header'>Candidate Assessment</h1>", unsafe_allow_html=True)
        
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
                # Clear existing interview state but keep view_history
                for key in ['current_interview_id', 'interview_setup_complete', 'interview_complete', 'interview_start_time', 'response_start_time']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.session_state.view_history = True
                st.rerun()
        
        # Button to create new interview in the second column
        with col2:
            if st.button("🚀 Start New Interview", key="start_new_btn"):
                # This will show the setup page below
                pass
        
        # Show the setup page regardless
        setup_interview_page()