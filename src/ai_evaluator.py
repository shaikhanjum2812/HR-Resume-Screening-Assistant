import os
from openai import OpenAI
import json
from typing import Dict, Union, List, Optional
import logging

logger = logging.getLogger(__name__)

class AIEvaluator:
    def __init__(self):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
            )
        self.client = OpenAI(api_key=api_key)

    def extract_candidate_info(self, resume_text: str) -> Dict[str, str]:
        """Extract candidate's personal information from resume using GPT-4."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",  # Using GPT-4 Turbo for better extraction
                messages=[
                    {
                        "role": "system",
                        "content": """You are a precise information extractor specialized in HR documents. 
                        Extract the candidate's personal information from the resume and format your response 
                        EXACTLY as a JSON object with this structure:
                        {
                            "name": "full name of candidate",
                            "email": "email address",
                            "phone": "phone number",
                            "location": "candidate location",
                            "linkedin": "linkedin profile URL if available"
                        }
                        If any field is not found, set it to null. Only return the JSON object, nothing else."""
                    },
                    {
                        "role": "user",
                        "content": resume_text
                    }
                ],
                temperature=0.1  # Lower temperature for more consistent extraction
            )

            content = response.choices[0].message.content.strip()
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error extracting candidate info: {str(e)}")
            return {"name": None, "email": None, "phone": None, "location": None, "linkedin": None}

    def evaluate_resume(self, resume_text: str, job_description: str, evaluation_criteria: dict = None) -> Dict[str, Union[str, float, List[str]]]:
        try:
            # Extract candidate information first
            candidate_info = self.extract_candidate_info(resume_text)

            # Build dynamic system message based on evaluation criteria
            system_message = """You are an expert HR evaluator with the following capabilities:
            1. Deep understanding of industry-specific requirements
            2. Ability to assess both technical and soft skills
            3. Experience evaluation across different seniority levels

            Analyze the resume against the job description and return your evaluation EXACTLY as a JSON object 
            with the following structure:
            {
                "decision": "shortlist" or "reject",
                "confidence_score": float between 0 and 1,
                "justification": "detailed explanation including specific gaps",
                "match_score": float between 0 and 1,
                "years_of_experience": {
                    "total": float,
                    "relevant": float,
                    "required": float,
                    "meets_requirement": boolean,
                    "details": "breakdown of experience by relevance"
                },
                "key_matches": {
                    "skills": ["list of matching technical skills"],
                    "experience": ["list of relevant experience matches"],
                    "certifications": ["list of relevant certifications"]
                },
                "missing_requirements": {
                    "critical": ["list of critical missing requirements"],
                    "preferred": ["list of preferred but missing requirements"]
                },
                "recommendations": {
                    "interview_focus": ["specific areas to focus on during interview"],
                    "skill_gaps": ["recommended areas for skill development"]
                },
                "evaluation_metrics": {
                    "technical_skills": float between 0 and 1,
                    "experience_relevance": float between 0 and 1,
                    "education_match": float between 0 and 1,
                    "overall_fit": float between 0 and 1
                }
            }
            Only return the JSON object, nothing else."""

            if evaluation_criteria:
                system_message += "\n\nSpecific Evaluation Criteria:"

                if evaluation_criteria.get('min_years_experience'):
                    system_message += f"\n- Minimum {evaluation_criteria['min_years_experience']} years of experience required"

                if evaluation_criteria.get('required_skills'):
                    system_message += "\n- Required Skills:"
                    for skill in evaluation_criteria['required_skills']:
                        system_message += f"\n  * {skill}"

                if evaluation_criteria.get('preferred_skills'):
                    system_message += "\n- Preferred Skills:"
                    for skill in evaluation_criteria['preferred_skills']:
                        system_message += f"\n  * {skill}"

                if evaluation_criteria.get('education_requirements'):
                    system_message += f"\n- Education Requirements:\n  {evaluation_criteria['education_requirements']}"

                if evaluation_criteria.get('company_background_requirements'):
                    system_message += f"\n- Company Background Requirements:\n  {evaluation_criteria['company_background_requirements']}"

                if evaluation_criteria.get('domain_experience_requirements'):
                    system_message += f"\n- Domain Experience Requirements:\n  {evaluation_criteria['domain_experience_requirements']}"

            # First evaluation with GPT-4 Turbo
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": system_message
                    },
                    {
                        "role": "user",
                        "content": f"""Job Description:\n{job_description}\n\nResume:\n{resume_text}"""
                    }
                ],
                temperature=0.4,
                max_tokens=2000
            )

            result = json.loads(response.choices[0].message.content.strip())

            # Add candidate information to the result
            result['candidate_info'] = candidate_info

            # Validate response format
            required_keys = [
                'decision', 'justification', 'match_score', 'key_matches', 
                'missing_requirements', 'years_of_experience', 'evaluation_metrics'
            ]
            if not all(key in result for key in required_keys):
                raise ValueError("Invalid response format from OpenAI API")

            return result

        except json.JSONDecodeError:
            raise Exception("Failed to parse OpenAI API response")
        except Exception as e:
            raise Exception(f"Failed to evaluate resume: {str(e)}")

    def get_improvement_suggestions(self, resume_text: str, job_description: str) -> Dict[str, List[str]]:
        """Get specific suggestions for improving the resume for the job."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": """As an expert HR consultant, analyze the resume against the job requirements 
                        and provide actionable improvement suggestions. Format your response EXACTLY as a JSON object 
                        with this structure:
                        {
                            "skill_improvements": {
                                "technical": ["specific technical skills to develop"],
                                "soft": ["specific soft skills to enhance"]
                            },
                            "experience_suggestions": {
                                "roles": ["specific roles or positions to target"],
                                "projects": ["types of projects to undertake"]
                            },
                            "certification_recommendations": ["specific certifications that would add value"],
                            "resume_presentation": {
                                "format": ["formatting improvements"],
                                "content": ["content enhancement suggestions"],
                                "keywords": ["important keywords to include"]
                            }
                        }
                        Only return the JSON object, nothing else."""
                    },
                    {
                        "role": "user",
                        "content": f"""Job Description:\n{job_description}\n\nResume:\n{resume_text}"""
                    }
                ],
                temperature=0.4
            )

            return json.loads(response.choices[0].message.content.strip())

        except Exception as e:
            raise Exception(f"Failed to get improvement suggestions: {str(e)}")