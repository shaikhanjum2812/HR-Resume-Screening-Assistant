import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from openai import OpenAI, APIError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIEvaluator:
    def __init__(self):
        """Initialize the AI Evaluator with OpenAI client"""
        try:
            self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            self.model = "gpt-4o"
            logger.info("AIEvaluator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AIEvaluator: {e}")
            raise

    def _extract_candidate_info(self, resume_text: str) -> Dict[str, Any]:
        """Extract candidate information from resume text"""
        try:
            logger.info("Extracting candidate information")
            prompt = """
            Extract the following information from the resume text. Respond in JSON format:
            {
                "name": "candidate full name",
                "email": "email address",
                "phone": "phone number",
                "location": "location if available",
                "linkedin": "LinkedIn profile URL if available"
            }
            If any field is not found, use null as the value.

            Resume text:
            {resume_text}
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a resume parser expert."},
                    {"role": "user", "content": prompt.format(resume_text=resume_text)}
                ],
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            logger.info("Successfully extracted candidate information")
            return result
        except Exception as e:
            logger.error(f"Failed to extract candidate information: {e}")
            return {
                "name": None,
                "email": None,
                "phone": None,
                "location": None,
                "linkedin": None
            }

    def _analyze_experience(self, resume_text: str, job_description: str, min_years: int = 0) -> Dict[str, Any]:
        """Analyze candidate's experience"""
        try:
            logger.info("Analyzing candidate experience")
            prompt = f"""
            Analyze the candidate's experience based on their resume and the job requirements.
            Required minimum years: {min_years}

            Job Description:
            {job_description}

            Resume:
            {resume_text}

            Provide a detailed analysis in JSON format:
            {{
                "total": "total years of experience",
                "relevant": "years of relevant experience",
                "required": {min_years},
                "meets_requirement": true/false,
                "details": "detailed analysis of experience",
                "quality_score": "score between 0 and 1"
            }}
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Failed to analyze experience: {e}")
            return {
                "total": 0,
                "relevant": 0,
                "required": min_years,
                "meets_requirement": False,
                "details": "Failed to analyze experience",
                "quality_score": 0
            }

    def evaluate_resume(self, resume_text: str, job_description: str, evaluation_criteria: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Evaluate a single resume against the job description and criteria
        Returns a structured evaluation result
        """
        try:
            logger.info("Starting resume evaluation")

            # Extract candidate information
            candidate_info = self._extract_candidate_info(resume_text)

            # Get experience requirements
            min_years = evaluation_criteria.get('min_years_experience', 0) if evaluation_criteria else 0

            # Analyze experience
            experience_analysis = self._analyze_experience(resume_text, job_description, min_years)

            # Evaluate against job requirements
            evaluation_prompt = f"""
            Evaluate the candidate's resume against the job requirements.
            Provide a detailed evaluation in JSON format:
            {{
                "decision": "SHORTLIST or REJECT",
                "justification": "detailed explanation",
                "match_score": "score between 0 and 1",
                "confidence_score": "score between 0 and 1",
                "key_matches": {{
                    "skills": ["matching skills"],
                    "projects": ["relevant projects"]
                }},
                "missing_requirements": ["list of missing requirements"],
                "evaluation_metrics": {{
                    "technical_skills": "score between 0 and 1",
                    "experience_relevance": "score between 0 and 1",
                    "education_match": "score between 0 and 1",
                    "overall_fit": "score between 0 and 1"
                }},
                "recommendations": {{
                    "interview_focus": ["areas to focus on in interview"],
                    "skill_gaps": ["identified skill gaps"]
                }}
            }}

            Job Description:
            {job_description}

            Resume:
            {resume_text}
            """

            if evaluation_criteria:
                evaluation_prompt += f"""
                Additional Criteria:
                Required Skills: {evaluation_criteria.get('required_skills', [])}
                Preferred Skills: {evaluation_criteria.get('preferred_skills', [])}
                Education Requirements: {evaluation_criteria.get('education_requirements', '')}
                Domain Experience: {evaluation_criteria.get('domain_experience_requirements', '')}
                Additional Instructions: {evaluation_criteria.get('additional_instructions', '')}
                """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": evaluation_prompt}],
                response_format={"type": "json_object"}
            )

            evaluation_result = json.loads(response.choices[0].message.content)

            # Combine all results
            final_result = {
                **evaluation_result,
                "candidate_info": candidate_info,
                "years_of_experience": experience_analysis,
                "evaluation_date": datetime.now().isoformat()
            }

            logger.info("Resume evaluation completed successfully")
            return final_result

        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error evaluating resume: {e}")
            raise