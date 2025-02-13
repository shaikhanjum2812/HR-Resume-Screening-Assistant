import os
from openai import OpenAI
import json
from typing import Dict, Union, List

class AIEvaluator:
    def __init__(self):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
            )
        self.client = OpenAI(api_key=api_key)

    def extract_candidate_info(self, resume_text: str) -> Dict[str, str]:
        """Extract candidate's personal information from resume."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a precise information extractor. Extract the candidate's personal information from the resume and format your response EXACTLY as a JSON object with this structure:
                        {
                            "name": "full name of candidate",
                            "email": "email address",
                            "phone": "phone number"
                        }
                        If any field is not found, set it to null. Only return the JSON object, nothing else."""
                    },
                    {
                        "role": "user",
                        "content": resume_text
                    }
                ],
                temperature=0.3
            )

            content = response.choices[0].message.content.strip()
            return json.loads(content)
        except Exception as e:
            print(f"Error extracting candidate info: {str(e)}")
            return {"name": None, "email": None, "phone": None}

    def evaluate_resume(self, resume_text: str, job_description: str, evaluation_criteria: dict = None) -> Dict[str, Union[str, float, List[str]]]:
        try:
            # Extract candidate information first
            candidate_info = self.extract_candidate_info(resume_text)

            # Build dynamic system message based on evaluation criteria
            system_message = """You are an expert HR assistant with strict evaluation criteria. 
            Analyze the resume against the job description and return your evaluation EXACTLY as a JSON object with the following structure:
            {
                "decision": "shortlist" or "reject",
                "justification": "detailed explanation including specific gaps",
                "match_score": float between 0 and 1,
                "years_of_experience": {
                    "total": float,
                    "relevant": float,
                    "required": float,
                    "meets_requirement": boolean
                },
                "key_matches": ["list of matching skills/qualifications"],
                "missing_requirements": ["list of missing requirements"],
                "experience_analysis": "detailed analysis of experience relevance"
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

                if evaluation_criteria.get('additional_instructions'):
                    system_message += f"\n\nAdditional Instructions:\n{evaluation_criteria['additional_instructions']}"

            response = self.client.chat.completions.create(
                model="gpt-4",
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
                temperature=0.5
            )

            content = response.choices[0].message.content.strip()
            result = json.loads(content)

            # Add candidate information to the result
            result['candidate_info'] = candidate_info

            # Validate response format
            required_keys = ['decision', 'justification', 'match_score', 'key_matches', 
                           'missing_requirements', 'years_of_experience', 'experience_analysis']
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
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """Analyze the resume against the job requirements and provide
                        specific suggestions for improvement. Format your response EXACTLY as a JSON object with this structure:
                        {
                            "sap_implementation_gaps": [list of SAP implementation improvements needed],
                            "company_experience_suggestions": [suggestions for IT services experience],
                            "technical_skill_development": [list of technical skills to develop],
                            "domain_expertise_improvements": [list of domain expertise suggestions],
                            "project_experience_recommendations": [specific project experience needed]
                        }
                        Only return the JSON object, nothing else."""
                    },
                    {
                        "role": "user",
                        "content": f"""Job Description:\n{job_description}\n\n
                        Resume:\n{resume_text}"""
                    }
                ],
                temperature=0.5
            )

            content = response.choices[0].message.content.strip()
            return json.loads(content)

        except Exception as e:
            raise Exception(f"Failed to get improvement suggestions: {str(e)}")