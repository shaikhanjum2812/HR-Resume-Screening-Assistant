"""
New implementation of the interview engine that is not specific to SAP modules
"""

import os
import logging
import json
import time
from typing import Dict, List, Any, Optional
from openai import OpenAI
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InterviewEngine:
    def __init__(self):
        """Initialize the Interview Engine with OpenAI client"""
        # Get API key from environment variables
        api_key = os.environ.get('OPENAI_API_KEY')
        
        if not api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables.")
            
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o"  # Use GPT-4o for best performance
        
    def generate_questions(self, 
                           job_title: str, 
                           job_description: str, 
                           resume_text: str,
                           num_questions: int = 20) -> Dict[str, List[Dict[str, str]]]:
        """
        Generate interview questions tailored to the candidate's resume and job description.
        
        Args:
            job_title: The position/role applied for
            job_description: The full job description
            resume_text: The candidate's resume text
            num_questions: Total number of questions to generate (default: 20)
            
        Returns:
            Dict containing categorized questions with their types
        """
        try:
            # Calculate questions per category
            technical_count = int(num_questions * 0.4)  # 40% technical questions
            scenario_count = int(num_questions * 0.3)   # 30% scenario questions
            behavioral_count = int(num_questions * 0.2) # 20% behavioral questions
            problem_solving_count = num_questions - technical_count - scenario_count - behavioral_count
            
            # Prepare prompt for question generation
            prompt = f"""
            You are an expert HR interviewer for the position of {job_title}. 
            
            Create a set of interview questions based on the following job description and candidate resume:
            
            JOB DESCRIPTION:
            {job_description}
            
            CANDIDATE RESUME:
            {resume_text}
            
            Please generate the following types of questions:
            
            1. {technical_count} TECHNICAL questions: These should assess the candidate's knowledge and expertise in specific skills required for the position. Each technical question should directly relate to a skill mentioned in either the job description or the candidate's resume.
            
            2. {scenario_count} SCENARIO-BASED questions: These should present realistic workplace scenarios the candidate might encounter in this role. Focus on situations that test their ability to apply knowledge in practical settings.
            
            3. {behavioral_count} BEHAVIORAL questions: These should assess how the candidate has dealt with situations in the past that demonstrate important soft skills for the role.
            
            4. {problem_solving_count} PROBLEM-SOLVING questions: These should test the candidate's analytical thinking and approach to solving complex problems relevant to the role.
            
            For each question, include:
            1. The question text
            2. The type of question (technical, scenario, behavioral, problem_solving)
            3. A brief context explaining why this question is relevant based on the job or resume
            
            Format your response as a JSON object with the following structure:
            {{
                "technical": [
                    {{"question": "Question text", "context": "Why this is relevant"}}
                ],
                "scenario": [
                    {{"question": "Question text", "context": "Why this is relevant"}}
                ],
                "behavioral": [
                    {{"question": "Question text", "context": "Why this is relevant"}}
                ],
                "problem_solving": [
                    {{"question": "Question text", "context": "Why this is relevant"}}
                ]
            }}
            
            Make sure questions are challenging but fair, and directly relevant to assessing the candidate's fit for this specific position.
            """
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are an expert HR interviewer who creates tailored interview questions based on job descriptions and candidate resumes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,  # Some creativity but mostly consistent
                max_tokens=4000
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            # Ensure all expected categories are present
            categories = ["technical", "scenario", "behavioral", "problem_solving"]
            for category in categories:
                if category not in result:
                    result[category] = []
                    
            # Log success
            total_generated = sum(len(result[cat]) for cat in categories)
            logger.info(f"Successfully generated {total_generated} interview questions")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating interview questions: {str(e)}")
            # Return empty structure in case of failure
            return {
                "technical": [],
                "scenario": [],
                "behavioral": [],
                "problem_solving": []
            }
    
    def evaluate_answer(self, 
                         question: str,
                         question_type: str,
                         answer: str,
                         job_title: str,
                         job_description: str) -> Dict[str, Any]:
        """
        Evaluate a candidate's answer to a specific interview question.
        
        Args:
            question: The interview question that was asked
            question_type: The type of question (technical, scenario, problem_solving, behavioral)
            answer: The candidate's response text
            job_title: The position/role applied for
            job_description: The full job description
            
        Returns:
            Dict containing evaluation of the response
        """
        try:
            # Prepare prompt for answer evaluation
            prompt = f"""
            You are an expert HR interviewer for the position of {job_title}. 
            
            You asked the following {question_type.upper()} question:
            "{question}"
            
            The candidate provided this answer:
            "{answer}"
            
            The job description is:
            {job_description}
            
            Please evaluate the candidate's response thoroughly and provide a detailed assessment with the following components:
            
            1. Overall score (0-10, where 10 is excellent)
            2. Technical accuracy (0-10)
            3. Clarity of communication (0-10)
            4. Relevance of the answer to the question (0-10)
            5. Demonstrated expertise (0-10)
            6. 2-4 specific strengths of the answer
            7. 2-4 specific weaknesses or areas for improvement
            8. Detailed feedback on the response
            
            Format your response as a JSON object with the following structure:
            {{
                "score": 7,
                "technical_accuracy": 8,
                "clarity_of_communication": 7,
                "relevance": 8,
                "demonstrated_expertise": 6,
                "strengths": ["Strength 1", "Strength 2"],
                "weaknesses": ["Weakness 1", "Weakness 2"],
                "feedback": "Detailed feedback..."
            }}
            
            Be fair but thorough in your assessment. For technical questions, focus more on accuracy and expertise. For behavioral questions, focus more on communication and relevance. For scenario questions, focus on problem-solving approach and practical application. For problem-solving questions, focus on analytical thinking and solution quality.
            """
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are an expert HR interviewer who evaluates interview answers professionally and fairly."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent evaluations
                max_tokens=2000
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            # Ensure all required fields are present and properly formatted
            required_fields = ["score", "technical_accuracy", "clarity_of_communication", 
                              "relevance", "demonstrated_expertise", "strengths", 
                              "weaknesses", "feedback"]
            
            for field in required_fields:
                if field not in result:
                    if field in ["strengths", "weaknesses"]:
                        result[field] = []
                    elif field == "feedback":
                        result[field] = "No detailed feedback provided."
                    else:
                        result[field] = 5  # Default middle score
            
            # Ensure scores are numerical and within range
            for score_field in ["score", "technical_accuracy", "clarity_of_communication", 
                              "relevance", "demonstrated_expertise"]:
                try:
                    result[score_field] = float(result[score_field])
                    result[score_field] = max(0, min(10, result[score_field]))  # Clamp between 0-10
                    result[score_field] = round(result[score_field], 1)  # Round to 1 decimal place
                except (ValueError, TypeError):
                    result[score_field] = 5.0
            
            logger.info(f"Successfully evaluated answer with score: {result['score']}")
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating answer: {str(e)}")
            # Return a basic structure in case of failure
            return {
                "score": 5.0,
                "technical_accuracy": 5.0,
                "clarity_of_communication": 5.0,
                "relevance": 5.0,
                "demonstrated_expertise": 5.0,
                "strengths": ["Unable to properly evaluate response"],
                "weaknesses": ["System could not analyze this response"],
                "feedback": f"Error during evaluation: {str(e)}"
            }
    
    def generate_final_report(self, 
                             job_title: str,
                             job_description: str,
                             resume_text: str,
                             interview_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a comprehensive final interview report based on all responses.
        
        Args:
            job_title: The position/role applied for
            job_description: The full job description
            resume_text: The candidate's resume text
            interview_results: List of all questions, answers and evaluations
            
        Returns:
            Dict containing the final assessment and scores
        """
        try:
            # Calculate completion rate
            total_questions = len(interview_results)
            answered_questions = sum(1 for q in interview_results if q.get('answer') is not None)
            completion_rate = answered_questions / total_questions if total_questions > 0 else 0
            
            # Prepare data for evaluation
            formatted_results = []
            scores_by_type = {
                "technical": [],
                "scenario": [],
                "behavioral": [],
                "problem_solving": []
            }
            
            for item in interview_results:
                question = item.get('question', '')
                q_type = item.get('type', '').lower()
                answer_data = item.get('answer')
                
                if not answer_data:
                    formatted_results.append({
                        "question": question,
                        "type": q_type,
                        "answered": False
                    })
                    continue
                    
                evaluation = answer_data.get('evaluation', {})
                score = evaluation.get('score', 0)
                
                # Track scores by question type
                if q_type in scores_by_type:
                    scores_by_type[q_type].append(score)
                
                formatted_results.append({
                    "question": question,
                    "type": q_type,
                    "answered": True,
                    "answer": answer_data.get('text', ''),
                    "score": score,
                    "strengths": evaluation.get('strengths', []),
                    "weaknesses": evaluation.get('weaknesses', [])
                })
            
            # Calculate average scores by type
            avg_scores = {}
            for q_type, scores in scores_by_type.items():
                if scores:
                    avg_scores[q_type] = sum(scores) / len(scores)
                else:
                    avg_scores[q_type] = 0
            
            # Calculate overall score (weighted)
            weights = {
                "technical": 0.4,
                "scenario": 0.3,
                "behavioral": 0.15,
                "problem_solving": 0.15
            }
            
            overall_score = 0
            total_weight = 0
            
            for q_type, score in avg_scores.items():
                if scores_by_type[q_type]:  # Only count types that have answers
                    weight = weights.get(q_type, 0)
                    overall_score += score * weight
                    total_weight += weight
            
            if total_weight > 0:
                overall_score = overall_score / total_weight
            else:
                overall_score = 0
                
            # Format results for sending to API
            formatted_data = {
                "job_title": job_title,
                "completion_rate": completion_rate,
                "question_results": formatted_results,
                "scores": {
                    "overall": round(overall_score, 1),
                    "technical": round(avg_scores.get("technical", 0), 1),
                    "scenario": round(avg_scores.get("scenario", 0), 1),
                    "behavioral": round(avg_scores.get("behavioral", 0), 1),
                    "problem_solving": round(avg_scores.get("problem_solving", 0), 1)
                }
            }
            
            # Prepare the prompt for the final assessment
            prompt = f"""
            You are an expert HR professional evaluating a candidate for the position of {job_title}.
            
            JOB DESCRIPTION:
            {job_description}
            
            CANDIDATE RESUME:
            {resume_text}
            
            INTERVIEW RESULTS:
            The candidate completed {answered_questions} out of {total_questions} questions ({int(completion_rate * 100)}% completion rate).
            
            Overall score: {formatted_data['scores']['overall']}/10
            Technical questions score: {formatted_data['scores']['technical']}/10
            Scenario questions score: {formatted_data['scores']['scenario']}/10
            Behavioral questions score: {formatted_data['scores']['behavioral']}/10
            Problem-solving questions score: {formatted_data['scores']['problem_solving']}/10
            
            Based on this information and the detailed question responses provided below, create a comprehensive final interview assessment report.
            
            DETAILED QUESTION RESPONSES:
            {json.dumps(formatted_results, indent=2)}
            
            Your report should include:
            
            1. Overall assessment of the candidate's performance and fit for the role
            2. Analysis of technical skills demonstrated during the interview
            3. Assessment of communication skills
            4. Assessment of problem-solving abilities 
            5. Key strengths identified during the interview (at least 3)
            6. Areas for improvement (at least 3)
            7. Key observations about the candidate's responses
            8. Assessment of the interview completion (whether the candidate answered enough questions to make a good evaluation)
            9. Final hiring recommendation (Hire, Consider with Reservations, or Do Not Hire)
            10. Reasoning behind your recommendation
            
            Format your response as a JSON object with the following structure:
            {{
                "overall_assessment": "Comprehensive assessment...",
                "technical_skills": {{
                    "assessment": "Technical skills assessment...",
                    "strengths": ["Strength 1", "Strength 2", "Strength 3"],
                    "weaknesses": ["Weakness 1", "Weakness 2"]
                }},
                "communication_skills": {{
                    "assessment": "Communication skills assessment..."
                }},
                "problem_solving": {{
                    "assessment": "Problem solving assessment..."
                }},
                "key_strengths": ["Major strength 1", "Major strength 2", "Major strength 3"],
                "areas_for_improvement": ["Area 1", "Area 2", "Area 3"],
                "key_observations": ["Observation 1", "Observation 2", "Observation 3"],
                "interview_completion": {{
                    "assessment": "Assessment of whether enough questions were answered..."
                }},
                "recommendation": "Hire / Consider with Reservations / Do Not Hire",
                "reasoning": "Detailed reasoning for the recommendation..."
            }}
            
            IMPORTANT: If the completion rate is less than 70%, the recommendation CANNOT be "Hire" as there is insufficient data for a full assessment.
            """
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are an expert HR professional who provides comprehensive interview assessments and hiring recommendations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=4000
            )
            
            # Parse response and combine with score data
            assessment = json.loads(response.choices[0].message.content)
            
            # Combine scores with assessment
            assessment["scores"] = formatted_data["scores"]
            assessment["completion_rate"] = completion_rate
            
            logger.info(f"Successfully generated final interview report with recommendation: {assessment.get('recommendation', 'Unknown')}")
            return assessment
            
        except Exception as e:
            logger.error(f"Error generating final report: {str(e)}")
            
            # Initialize default values before any error handling
            completion_rate = 0
            formatted_data = {
                "scores": {
                    "overall": 0,
                    "technical": 0,
                    "scenario": 0,
                    "behavioral": 0,
                    "problem_solving": 0
                }
            }
            
            # Calculate completion percentage
            try:
                # Use the completion_rate defined in the try block above
                completion_percentage = int(completion_rate * 100)
            except Exception:
                # Default to 0 if there was an error
                completion_percentage = 0
                
            # Use the scores from formatted_data
            scores = formatted_data["scores"]
            
            # Return a basic structure in case of failure
            return {
                "overall_assessment": "Could not generate a comprehensive assessment due to an error.",
                "technical_skills": {
                    "assessment": "Technical skills assessment could not be completed.",
                    "strengths": [],
                    "weaknesses": []
                },
                "communication_skills": {
                    "assessment": "Communication skills assessment could not be completed."
                },
                "problem_solving": {
                    "assessment": "Problem solving assessment could not be completed."
                },
                "key_strengths": ["Unable to determine key strengths"],
                "areas_for_improvement": ["Unable to determine areas for improvement"],
                "key_observations": ["System encountered an error during final assessment"],
                "interview_completion": {
                    "assessment": f"The candidate completed {completion_percentage}% of the interview questions."
                },
                "recommendation": "Unable to determine",
                "reasoning": f"An error occurred during the final assessment: {str(e)}",
                "scores": scores,
                "completion_rate": completion_rate
            }