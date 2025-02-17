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

    def extract_candidate_info(self, resume_text: str) -> Dict[str, Optional[str]]:
        """Extract candidate's personal information from resume using GPT-4."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
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
                temperature=0.1
            )

            try:
                content = response.choices[0].message.content.strip()
                result = json.loads(content)

                # Validate response format
                required_fields = ['name', 'email', 'phone', 'location', 'linkedin']
                if not all(field in result for field in required_fields):
                    logger.error(f"Invalid response format from OpenAI API: {content}")
                    return {field: None for field in required_fields}

                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse candidate info JSON: {str(e)}, Response: {content}")
                return {"name": None, "email": None, "phone": None, "location": None, "linkedin": None}

        except Exception as e:
            logger.error(f"Error extracting candidate info: {str(e)}")
            return {"name": None, "email": None, "phone": None, "location": None, "linkedin": None}

    def evaluate_resume(self, resume_text: str, job_description: str, evaluation_criteria: Optional[dict] = None) -> Dict[str, Union[str, float, List[str]]]:
        try:
            # Extract candidate information first
            candidate_info = self.extract_candidate_info(resume_text)

            # Build dynamic system message based on evaluation criteria
            system_message = """You are an expert technical recruiter for SAP and IT Services positions with these strict evaluation criteria:

            1. Experience Requirements:
               - Total experience must be within ±20% of the required years
               - Relevant SAP implementation experience is mandatory
               - IT services company experience is heavily weighted
               - SAP Public Cloud experience is a significant advantage

            2. Technical Experience Focus:
               - Direct hands-on SAP implementation experience
               - Project complexity and scale in IT services context
               - Experience with SAP Public Cloud solutions
               - Client-facing implementation roles

            3. Decision Criteria (ALL must be met for shortlisting):
               - Experience matches within ±20% of requirement
               - Has direct SAP implementation experience
               - Has worked in IT services company
               - Shows evidence of client-facing roles
               - Demonstrates project delivery experience

            4. Automatic Rejection Criteria:
               - Experience outside ±20% range
               - No SAP implementation experience
               - No IT services company experience
               - Lack of client-facing experience

            Analyze the resume against the job description and return your evaluation EXACTLY as a JSON object with this structure:
            {
                "decision": "shortlist" or "reject",
                "confidence_score": float between 0 and 1,
                "justification": "detailed explanation focusing on technical capabilities and experience match",
                "match_score": float between 0 and 1,
                "years_of_experience": {
                    "total": float,
                    "relevant": float,
                    "required": float,
                    "meets_requirement": boolean,
                    "quality_score": float between 0 and 1,
                    "details": "analysis focusing on quality and relevance of experience"
                },
                "sap_experience": {
                    "implementation_experience": boolean,
                    "public_cloud_experience": boolean,
                    "years_in_sap": float,
                    "expertise_areas": ["list of SAP expertise areas"]
                },
                "it_services_experience": {
                    "has_experience": boolean,
                    "years": float,
                    "companies": ["list of IT services companies"],
                    "client_facing_roles": boolean
                },
                "key_matches": {
                    "skills": ["relevant technical skills"],
                    "projects": ["relevant SAP implementation projects"],
                    "implementations": ["specific implementation examples"]
                },
                "missing_requirements": {
                    "critical": ["critical missing requirements"],
                    "preferred": ["preferred but missing requirements"]
                }
            }
            Only return the JSON object, nothing else."""

            if evaluation_criteria:
                system_message += "\n\nAdditional Evaluation Adjustments:"
                if evaluation_criteria.get('min_years_experience'):
                    required_years = evaluation_criteria['min_years_experience']
                    system_message += f"\n- Required Years: {required_years}"
                    system_message += f"\n- Acceptable Range: {required_years * 0.8} to {required_years * 1.2} years"

                if evaluation_criteria.get('required_skills'):
                    system_message += "\n- Required Technical Skills:"
                    for skill in evaluation_criteria['required_skills']:
                        system_message += f"\n  * {skill}"

            # Evaluation with GPT-4 Turbo
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

            try:
                content = response.choices[0].message.content.strip()
                result = json.loads(content)

                # Validate required fields
                required_fields = [
                    'decision', 'confidence_score', 'justification', 'match_score',
                    'years_of_experience', 'sap_experience', 'it_services_experience',
                    'key_matches', 'missing_requirements'
                ]

                if not all(field in result for field in required_fields):
                    logger.error(f"Invalid response format from OpenAI API: {content}")
                    raise ValueError("Response missing required fields")

                # Add candidate information to the result
                result['candidate_info'] = candidate_info

                return result

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse evaluation JSON: {str(e)}\nResponse content: {content}")
                raise ValueError(f"Failed to parse OpenAI API response: {str(e)}")
            except KeyError as e:
                logger.error(f"Missing required field in response: {str(e)}\nResponse content: {content}")
                raise ValueError(f"Invalid response format: missing field {str(e)}")
            except Exception as e:
                logger.error(f"Error processing evaluation response: {str(e)}\nResponse content: {content}")
                raise

        except Exception as e:
            logger.error(f"Failed to evaluate resume: {str(e)}")
            raise

    def get_improvement_suggestions(self, resume_text: str, job_description: str) -> Dict[str, List[str]]:
        """Get specific suggestions for improving the resume for the job."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": """As an expert HR consultant specializing in SAP and IT Services positions, 
                        analyze the resume against the job requirements and provide actionable improvement suggestions. 
                        Format your response EXACTLY as a JSON object with this structure:
                        {
                            "experience_gaps": {
                                "sap": ["specific SAP experience gaps"],
                                "it_services": ["IT services experience gaps"],
                                "implementation": ["implementation experience gaps"]
                            },
                            "skill_improvements": ["specific technical skills to develop"],
                            "certification_recommendations": ["relevant SAP certifications"],
                            "resume_presentation": {
                                "format": ["formatting improvements"],
                                "content": ["content enhancement suggestions"],
                                "keywords": ["important SAP and IT services keywords to include"]
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

            try:
                content = response.choices[0].message.content.strip()
                return json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse improvement suggestions JSON: {str(e)}\nResponse: {content}")
                raise ValueError(f"Failed to parse OpenAI API response for improvement suggestions: {str(e)}")

        except Exception as e:
            logger.error(f"Failed to get improvement suggestions: {str(e)}")
            raise