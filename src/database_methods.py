"""
Methods to be added to the Database class to support the new interview system
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

def create_new_interview(self, job_title, job_description, resume_text):
    """Create a new interview session for the new interview system
    
    Args:
        job_title: The title of the job position
        job_description: The full job description text
        resume_text: The candidate's resume text
        
    Returns:
        The ID of the created interview
    """
    try:
        query = """
            INSERT INTO interviews_new (
                job_title, 
                job_description, 
                resume_text, 
                status, 
                start_time
            ) VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        
        result = self.execute_query(
            query,
            (job_title, job_description, resume_text, 'in_progress', datetime.now())
        )
        
        if result and len(result) > 0:
            interview_id = result[0][0]
            logger.info(f"Created new interview with ID: {interview_id}")
            return interview_id
        else:
            logger.error("Failed to create new interview, no ID returned")
            return None
            
    except Exception as e:
        logger.error(f"Error creating new interview: {str(e)}")
        return None

def save_interview_questions_new(self, interview_id, questions_data):
    """Save generated interview questions for the new interview system
    
    Args:
        interview_id: ID of the interview session
        questions_data: Dictionary containing the questions data
        
    Returns:
        Boolean indicating success
    """
    try:
        questions = questions_data.get('questions', [])
        
        if not questions:
            logger.error("No questions provided to save")
            return False
            
        # Insert each question with its order
        for i, question in enumerate(questions):
            query = """
                INSERT INTO interview_questions_new (
                    interview_id,
                    question_text,
                    question_type,
                    display_order
                ) VALUES (%s, %s, %s, %s)
            """
            
            self.execute_query(
                query,
                (
                    interview_id,
                    question.get('question', ''),
                    question.get('type', 'technical'),
                    i + 1
                ),
                fetch=False
            )
            
        logger.info(f"Saved {len(questions)} questions for interview {interview_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving interview questions: {str(e)}")
        return False

def get_interview_questions_new(self, interview_id):
    """Get all interview questions for an interview session in the new system
    
    Args:
        interview_id: ID of the interview session
        
    Returns:
        List of questions with their details
    """
    try:
        query = """
            SELECT id, question_text, question_type, display_order
            FROM interview_questions_new
            WHERE interview_id = %s
            ORDER BY display_order
        """
        
        results = self.execute_query(query, (interview_id,))
        
        if not results:
            logger.warning(f"No questions found for interview {interview_id}")
            return []
            
        questions = []
        for row in results:
            questions.append({
                'id': row[0],
                'question': row[1],
                'type': row[2],
                'order': row[3]
            })
            
        logger.info(f"Retrieved {len(questions)} questions for interview {interview_id}")
        return questions
        
    except Exception as e:
        logger.error(f"Error retrieving interview questions: {str(e)}")
        return []

def save_interview_answer(self, question_id, answer_data):
    """Save a candidate's answer and its evaluation in the new system
    
    Args:
        question_id: ID of the question being answered
        answer_data: Dictionary containing answer text and evaluation data
        
    Returns:
        ID of the saved answer
    """
    try:
        evaluation = answer_data.get('evaluation', {})
        is_skipped = answer_data.get('skipped', False)
        
        # Extract data from the evaluation
        query = """
            INSERT INTO interview_answers (
                question_id,
                answer_text,
                score,
                technical_accuracy,
                clarity_of_communication,
                relevance,
                demonstrated_expertise,
                strengths,
                weaknesses,
                feedback,
                response_time,
                is_skipped
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        # Convert lists to JSONB format
        strengths = json.dumps(evaluation.get('strengths', []))
        weaknesses = json.dumps(evaluation.get('weaknesses', []))
        
        result = self.execute_query(
            query,
            (
                question_id,
                answer_data.get('answer_text', ''),
                evaluation.get('score', 0),
                evaluation.get('technical_accuracy', 0),
                evaluation.get('clarity_of_communication', 0),
                evaluation.get('relevance', 0),
                evaluation.get('demonstrated_expertise', 0),
                strengths,
                weaknesses,
                evaluation.get('feedback', ''),
                answer_data.get('response_time', 0),
                is_skipped
            )
        )
        
        if result and len(result) > 0:
            answer_id = result[0][0]
            logger.info(f"Saved answer for question {question_id} with ID: {answer_id}")
            return answer_id
        else:
            logger.error("Failed to save answer, no ID returned")
            return None
            
    except Exception as e:
        logger.error(f"Error saving interview answer: {str(e)}")
        return None

def get_interview_answers(self, interview_id):
    """Get all answers for an interview in the new system
    
    Args:
        interview_id: ID of the interview session
        
    Returns:
        List of questions with answers and evaluations
    """
    try:
        query = """
            SELECT 
                q.id, 
                q.question_text, 
                q.question_type, 
                q.display_order,
                a.id as answer_id,
                a.answer_text,
                a.score,
                a.technical_accuracy,
                a.clarity_of_communication,
                a.relevance,
                a.demonstrated_expertise,
                a.strengths,
                a.weaknesses,
                a.feedback,
                a.response_time,
                a.answered_at,
                a.is_skipped
            FROM interview_questions_new q
            LEFT JOIN interview_answers a ON q.id = a.question_id
            WHERE q.interview_id = %s
            ORDER BY q.display_order
        """
        
        results = self.execute_query(query, (interview_id,))
        
        if not results:
            logger.warning(f"No questions/answers found for interview {interview_id}")
            return []
            
        questions_with_answers = []
        for row in results:
            # Parse strengths and weaknesses from JSONB
            strengths = []
            weaknesses = []
            
            if row[11]:  # strengths
                try:
                    strengths = json.loads(row[11])
                except:
                    pass
                    
            if row[12]:  # weaknesses
                try:
                    weaknesses = json.loads(row[12])
                except:
                    pass
            
            # Construct response
            answer_data = None
            if row[5]:  # answer_text exists
                # Check if the answer was skipped (will be at index 16 after our change)
                is_skipped = row[16] if len(row) > 16 else False
                
                answer_data = {
                    'id': row[4],  # answer_id
                    'text': row[5],  # answer_text
                    'evaluation': {
                        'score': row[6],
                        'technical_accuracy': row[7],
                        'clarity_of_communication': row[8],
                        'relevance': row[9],
                        'demonstrated_expertise': row[10],
                        'strengths': strengths,
                        'weaknesses': weaknesses,
                        'feedback': row[13]
                    },
                    'response_time': row[14],
                    'timestamp': row[15],
                    'skipped': is_skipped
                }
            
            questions_with_answers.append({
                'id': row[0],
                'question': row[1],
                'type': row[2],
                'order': row[3],
                'answer': answer_data
            })
            
        logger.info(f"Retrieved {len(questions_with_answers)} questions/answers for interview {interview_id}")
        return questions_with_answers
        
    except Exception as e:
        logger.error(f"Error retrieving interview answers: {str(e)}")
        return []

def complete_interview(self, interview_id, report_data):
    """Complete an interview and save the final report in the new system
    
    Args:
        interview_id: ID of the interview session
        report_data: Dictionary containing the final evaluation report
        
    Returns:
        Boolean indicating success
    """
    try:
        # Extract scores from the report data
        scores = report_data.get('scores', {})
        
        # First, get the interview start time to calculate duration
        start_time_query = """
            SELECT start_time FROM interviews_new WHERE id = %s
        """
        start_time_result = self.execute_query(start_time_query, (interview_id,))
        
        end_time = datetime.now()
        
        # Calculate interview duration if start time exists
        if start_time_result and len(start_time_result) > 0 and start_time_result[0][0]:
            start_time = start_time_result[0][0]
            duration_seconds = (end_time - start_time).total_seconds()
            
            # Format duration as readable string (e.g., "45 minutes 20 seconds")
            minutes, seconds = divmod(int(duration_seconds), 60)
            hours, minutes = divmod(minutes, 60)
            
            if hours > 0:
                duration_str = f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"
            else:
                duration_str = f"{minutes} minute{'s' if minutes != 1 else ''} {seconds} second{'s' if seconds != 1 else ''}"
            
            # Add duration to report data
            report_data['interview_duration'] = duration_str
        else:
            # Default duration if start time is not available
            report_data['interview_duration'] = "Unknown"
        
        query = """
            UPDATE interviews_new
            SET 
                status = 'completed',
                end_time = %s,
                overall_score = %s,
                technical_score = %s,
                problem_solving_score = %s,
                communication_score = %s,
                completion_rate = %s,
                recommendation = %s,
                report_data = %s
            WHERE id = %s
        """
        
        # Convert report data to JSONB
        report_json = json.dumps(report_data)
        
        self.execute_query(
            query,
            (
                end_time,
                scores.get('overall', 0),
                scores.get('technical', 0),
                scores.get('problem_solving', 0),
                scores.get('behavioral', 0),  # Using behavioral for communication score
                report_data.get('completion_rate', 0),
                report_data.get('recommendation', 'No recommendation'),
                report_json,
                interview_id
            ),
            fetch=False
        )
        
        logger.info(f"Completed interview {interview_id} with recommendation: {report_data.get('recommendation', 'No recommendation')}")
        return True
        
    except Exception as e:
        logger.error(f"Error completing interview: {str(e)}")
        return False

def get_interview_details(self, interview_id):
    """Get full details of an interview session in the new system
    
    Args:
        interview_id: ID of the interview session
        
    Returns:
        Dictionary containing interview details
    """
    try:
        query = """
            SELECT 
                id,
                job_title,
                job_description,
                resume_text,
                status,
                start_time,
                end_time,
                completion_rate,
                overall_score,
                technical_score,
                problem_solving_score,
                communication_score,
                recommendation,
                report_data
            FROM interviews_new
            WHERE id = %s
        """
        
        result = self.execute_query(query, (interview_id,))
        
        if not result or len(result) == 0:
            logger.warning(f"No interview found with ID {interview_id}")
            return None
            
        row = result[0]
        
        # Parse report data from JSONB if it exists
        report_data = None
        if row[13]:  # report_data
            try:
                report_data = json.loads(row[13])
            except:
                pass
        
        interview_details = {
            'id': row[0],
            'job_title': row[1],
            'job_description': row[2],
            'resume_text': row[3],
            'status': row[4],
            'start_time': row[5],
            'end_time': row[6],
            'completion_rate': row[7],
            'overall_score': row[8],
            'technical_score': row[9],
            'problem_solving_score': row[10],
            'communication_score': row[11],
            'recommendation': row[12],
            'report_data': report_data
        }
        
        logger.info(f"Retrieved details for interview {interview_id}")
        return interview_details
        
    except Exception as e:
        logger.error(f"Error retrieving interview details: {str(e)}")
        return None

def get_completed_interviews_new(self):
    """Get all completed interviews in the new system
    
    Returns:
        List of completed interviews with basic details
    """
    try:
        query = """
            SELECT 
                id,
                job_title,
                status,
                start_time,
                end_time,
                completion_rate,
                overall_score,
                recommendation
            FROM interviews_new
            WHERE status = 'completed'
            ORDER BY end_time DESC
        """
        
        results = self.execute_query(query)
        
        if not results:
            logger.info("No completed interviews found")
            return []
            
        completed_interviews = []
        for row in results:
            completed_interviews.append({
                'id': row[0],
                'job_title': row[1],
                'status': row[2],
                'start_time': row[3],
                'end_time': row[4],
                'completion_rate': row[5],
                'overall_score': row[6],
                'recommendation': row[7]
            })
            
        logger.info(f"Retrieved {len(completed_interviews)} completed interviews")
        return completed_interviews
        
    except Exception as e:
        logger.error(f"Error retrieving completed interviews: {str(e)}")
        return []

def get_in_progress_interviews(self):
    """Get all in-progress interviews in the new system
    
    Returns:
        List of in-progress interviews with basic details
    """
    try:
        query = """
            SELECT 
                id,
                job_title,
                status,
                start_time
            FROM interviews_new
            WHERE status = 'in_progress'
            ORDER BY start_time DESC
        """
        
        results = self.execute_query(query)
        
        if not results:
            logger.info("No in-progress interviews found")
            return []
            
        in_progress_interviews = []
        for row in results:
            in_progress_interviews.append({
                'id': row[0],
                'job_title': row[1],
                'status': row[2],
                'start_time': row[3]
            })
            
        logger.info(f"Retrieved {len(in_progress_interviews)} in-progress interviews")
        return in_progress_interviews
        
    except Exception as e:
        logger.error(f"Error retrieving in-progress interviews: {str(e)}")
        return []