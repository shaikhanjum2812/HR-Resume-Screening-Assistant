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
            You are an expert SAP {sap_module} interviewer with deep domain knowledge. Generate highly specialized interview questions for a candidate with the following resume, applying for a position with the following job description.
            
            The questions must be deeply technical and specifically tailored to evaluate SAP {sap_module} expertise. Focus on identifying both breadth and depth of knowledge.
            
            JOB DESCRIPTION:
            {job_description}
            
            CANDIDATE'S RESUME:
            {resume_text}
            
            Please generate unique interview questions in the following JSON format:
            
            {{
                "technical": [
                    {{"question": "detailed technical question about specific SAP {sap_module} concepts, configurations, or tables", "context": "why this question is relevant to the candidate's background or job"}}
                    // Generate {tech_count} technical questions about SAP {sap_module}
                ],
                "scenario": [
                    {{"question": "detailed scenario question involving real-world SAP {sap_module} implementation challenges", "context": "why this scenario is relevant to the candidate's background or job"}}
                    // Generate {scenario_count} scenario-based questions related to SAP {sap_module}
                ],
                "behavioral": [
                    {{"question": "detailed behavioral question focused on SAP project experiences", "context": "why this behavioral question is relevant to the candidate's background or job"}}
                    // Generate {behavioral_count} behavioral questions
                ],
                "problem_solving": [
                    {{"question": "detailed problem-solving question involving SAP {sap_module} troubleshooting or optimization", "context": "why this problem is relevant to the candidate's background or job"}}
                    // Generate {problem_count} problem-solving questions related to SAP {sap_module}
                ]
            }}
            
            The questions MUST adhere to these requirements:
            1. Highly specific to the SAP {sap_module} module (mention specific transactions, tables, configuration settings)
            2. Based on the candidate's exact skills and experience from their resume
            3. Directly relevant to the job requirements
            4. Different for each candidate (not generic)
            5. Detailed enough to assess true expertise (should challenge even experienced professionals)
            6. Include SAP-specific terminology and concepts relevant to the {sap_module} module
            
            For technical questions, ask about specific configuration settings, tables, BAPIs, reports, or transactions relevant to {sap_module}.
            For scenario questions, present real-world implementation challenges specific to {sap_module}.
            For behavioral questions, focus on SAP project experiences, team dynamics, and stakeholder management.
            For problem-solving, present complex technical issues that would arise in an SAP {sap_module} implementation.
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
            You are an expert SAP {question_type} interviewer with deep technical knowledge. Critically evaluate the candidate's response to the following question:
            
            QUESTION TYPE: {question_type}
            
            QUESTION:
            {current_question}
            
            CANDIDATE'S RESPONSE:
            {candidate_response}
            
            Evaluate the response focusing on:
            1. Technical accuracy and depth (60%)
            2. Demonstration of SAP-specific knowledge (20%) 
            3. Clarity and structure of response (10%)
            4. Application of experience to the answer (10%)
            
            Provide an evaluation in the following JSON format:
            
            {{
                "score": /* Score between 0-10 based on above criteria */,
                "strengths": /* List of specific strengths in the response, particularly noting correct SAP technical details */,
                "weaknesses": /* List of specific weaknesses or areas for improvement, noting any technical inaccuracies */,
                "follow_up": /* Optional follow-up question if needed for clarification or to probe deeper */,
                "evaluation_notes": /* Detailed technical evaluation notes for the interviewer */
            }}
            
            Be critical but fair in your evaluation. For technical questions especially, verify if the candidate demonstrates actual SAP module expertise or just generic knowledge. Look for specific SAP terminology, transaction codes, tables, and processes in their answer. If they provide vague or generic answers to specific technical questions, this should be reflected in the score.
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
            You are an expert SAP {sap_module} interviewer and technical hiring manager. Generate a comprehensive final evaluation report for a candidate after their SAP module-specific interview.
            
            JOB DESCRIPTION:
            {job_description}
            
            CANDIDATE'S RESUME:
            {resume_text}
            
            INTERVIEW TRANSCRIPT:
            {transcript_text}
            
            Evaluate the candidate across multiple dimensions with a significant focus on their SAP {sap_module} technical expertise.
            
            Provide a final evaluation report in the following JSON format:
            
            {{
                "overall_score": /* Overall score between 0-10 */,
                "technical_proficiency": {{
                    "score": /* Technical score between 0-10 */,
                    "assessment": /* Detailed assessment of technical skills in SAP {sap_module} */,
                    "sap_module_expertise": /* Specific evaluation of their {sap_module} knowledge */,
                    "technical_gaps": /* Specific technical knowledge gaps identified */
                }},
                "communication_skills": {{
                    "score": /* Communication score between 0-10 */,
                    "assessment": /* Assessment of their ability to explain complex SAP concepts */
                }},
                "problem_solving_ability": {{
                    "score": /* Problem-solving score between 0-10 */,
                    "assessment": /* Assessment of their approach to SAP implementation challenges */
                }},
                "experience_assessment": {{
                    "score": /* Experience score between 0-10 */,
                    "assessment": /* Evaluation of the quality and relevance of their SAP experience */,
                    "implementation_experience": /* Analysis of their SAP implementation experience */
                }},
                "strengths": /* List of key strengths, particularly noting SAP technical strengths */,
                "areas_for_improvement": /* List of specific areas for improvement */,
                "cultural_fit": /* Assessment of cultural fit and team collaboration potential */,
                "hiring_recommendation": /* "Hire", "Reject", or "Consider for another position" */,
                "recommendation_reasoning": /* Detailed explanation for the hiring recommendation */
            }}
            
            In your assessment:
            1. Be specific about their {sap_module} expertise level (beginner, intermediate, advanced, expert)
            2. Evaluate their knowledge of specific {sap_module} transactions, tables, and configuration settings
            3. Assess their understanding of SAP integration points with other modules
            4. Consider both theoretical knowledge and practical application expertise
            5. Evaluate their experience with SAP implementation, support, and enhancement projects
            6. Consider whether they meet the specific requirements in the job description
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