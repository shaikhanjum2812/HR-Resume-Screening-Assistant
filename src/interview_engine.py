import os
import json
import logging
from typing import Dict, List, Any, Optional
try:
    from openai import OpenAI, APIError
except ImportError:
    from openai import OpenAI, OpenAIError as APIError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InterviewEngine:
    def __init__(self):
        """Initialize the Interview Engine with OpenAI client"""
        try:
            self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            self.openai_model = "gpt-4o"  # Using the latest model for best performance
            logger.info("Interview Engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Interview Engine: {str(e)}")
            raise

    def generate_questions(self, 
                           sap_module: str, 
                           job_description: str, 
                           resume_text: str, 
                           num_questions: int = 10) -> Dict[str, List[Dict[str, str]]]:
        """
        Generate interview questions tailored to the candidate's resume and job description.
        
        Args:
            sap_module: The specific SAP module for the position (FI/CO/MM/SD/PP/etc.)
            job_description: The full job description
            resume_text: The candidate's resume text
            num_questions: Number of questions to generate
            
        Returns:
            Dict containing categorized questions:
            {
                "technical": [{"question": "...", "context": "..."}],
                "scenario": [{"question": "...", "context": "..."}],
                "behavioral": [{"question": "...", "context": "..."}],
                "problem_solving": [{"question": "...", "context": "..."}]
            }
        """
        try:
            logger.info(f"Generating questions for SAP module: {sap_module}")
            
            # Calculate how many questions per category based on percentages
            tech_count = int(num_questions * 0.4)  # 40% technical
            scenario_count = int(num_questions * 0.3)  # 30% scenario
            behavioral_count = int(num_questions * 0.2)  # 20% behavioral
            problem_count = num_questions - tech_count - scenario_count - behavioral_count  # Remainder for problem-solving
            
            prompt = f"""
            You are an expert SAP {sap_module} interviewer. Generate personalized interview questions for a candidate with the following resume, applying for a position with the following job description.
            
            The questions should be specifically tailored to the candidate's experiences and skills, and relevant to the job requirements.
            
            JOB DESCRIPTION:
            {job_description}
            
            CANDIDATE'S RESUME:
            {resume_text}
            
            Please generate unique interview questions in the following JSON format:
            
            {{
                "technical": [
                    {{"question": "detailed technical question", "context": "why this question is relevant to the candidate's background or job"}}
                    // Generate {tech_count} technical questions about SAP {sap_module}
                ],
                "scenario": [
                    {{"question": "detailed scenario question", "context": "why this question is relevant to the candidate's background or job"}}
                    // Generate {scenario_count} scenario-based questions related to SAP {sap_module}
                ],
                "behavioral": [
                    {{"question": "detailed behavioral question", "context": "why this question is relevant to the candidate's background or job"}}
                    // Generate {behavioral_count} behavioral questions
                ],
                "problem_solving": [
                    {{"question": "detailed problem-solving question", "context": "why this question is relevant to the candidate's background or job"}}
                    // Generate {problem_count} problem-solving questions related to SAP {sap_module}
                ]
            }}
            
            The questions must be:
            1. Highly specific to the SAP {sap_module} module
            2. Based on the candidate's exact skills and experience
            3. Directly relevant to the job requirements
            4. Different for each candidate (not generic)
            5. Detailed enough to assess true expertise
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info("Successfully generated interview questions")
            
            return result
            
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating interview questions: {e}")
            raise
    
    def conduct_interview(self, 
                          questions: Dict[str, List[Dict[str, str]]], 
                          candidate_response: str, 
                          interview_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a candidate's response during the interview.
        
        Args:
            questions: The categorized questions generated earlier
            candidate_response: The candidate's response text to a specific question
            interview_context: Context of the current interview including which question is being asked
            
        Returns:
            Dict containing evaluation of the response and next steps
        """
        try:
            question_number = interview_context.get('current_question', 0)
            question_type = interview_context.get('current_question_type', 'technical')
            
            # Get the current question being asked
            current_question = ""
            if question_type in questions and len(questions[question_type]) > 0:
                question_index = min(question_number, len(questions[question_type])-1)
                current_question = questions[question_type][question_index]['question']
            
            prompt = f"""
            You are an expert SAP interviewer. Evaluate the candidate's response to the following question:
            
            QUESTION:
            {current_question}
            
            CANDIDATE'S RESPONSE:
            {candidate_response}
            
            Provide an evaluation in the following JSON format:
            
            {{
                "score": /* Score between 0-10 based on accuracy, depth, and relevance */,
                "strengths": /* List of strengths in the response */,
                "weaknesses": /* List of weaknesses or areas for improvement */,
                "follow_up": /* Optional follow-up question if needed for clarification */,
                "evaluation_notes": /* Detailed evaluation notes for the interviewer */
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info("Successfully evaluated candidate response")
            
            return result
            
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error evaluating candidate response: {e}")
            raise
    
    def generate_final_report(self, 
                              sap_module: str,
                              job_description: str,
                              resume_text: str,
                              interview_transcript: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a final comprehensive report after the interview.
        
        Args:
            sap_module: The specific SAP module for the position
            job_description: The full job description
            resume_text: The candidate's resume text
            interview_transcript: List of Q&A pairs with evaluations from the interview
            
        Returns:
            Dict containing the final comprehensive evaluation
        """
        try:
            # Prepare the interview transcript for the prompt
            transcript_text = ""
            for i, qa in enumerate(interview_transcript):
                transcript_text += f"Q{i+1}: {qa.get('question', '')}\n"
                transcript_text += f"A{i+1}: {qa.get('answer', '')}\n"
                transcript_text += f"Evaluation: Score {qa.get('evaluation', {}).get('score', 'N/A')}/10\n\n"
            
            prompt = f"""
            You are an expert SAP {sap_module} interviewer. Generate a comprehensive final report for a candidate after their interview.
            
            JOB DESCRIPTION:
            {job_description}
            
            CANDIDATE'S RESUME:
            {resume_text}
            
            INTERVIEW TRANSCRIPT:
            {transcript_text}
            
            Provide a final evaluation report in the following JSON format:
            
            {{
                "overall_score": /* Overall score between 0-10 */,
                "technical_proficiency": /* Detailed assessment of technical skills in SAP {sap_module} */,
                "communication_skills": /* Assessment of communication skills */,
                "problem_solving_ability": /* Assessment of problem-solving abilities */,
                "strengths": /* List of key strengths */,
                "areas_for_improvement": /* List of areas for improvement */,
                "cultural_fit": /* Assessment of cultural fit */,
                "hiring_recommendation": /* "Hire", "Reject", or "Consider for another position" */,
                "recommendation_reasoning": /* Detailed explanation for the recommendation */
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info("Successfully generated final interview report")
            
            return result
            
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating final report: {e}")
            raise