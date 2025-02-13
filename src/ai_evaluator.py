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

    def evaluate_resume(self, resume_text: str, job_description: str) -> Dict[str, Union[str, float, List[str]]]:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert HR assistant. Evaluate the candidate's 
                        resume against the job description and provide a detailed assessment. 
                        Consider technical skills, experience, education, and overall fit.
                        Respond with JSON in this format:
                        {
                            "decision": "shortlist" or "reject",
                            "justification": "detailed explanation",
                            "match_score": float between 0 and 1,
                            "key_matches": [list of matching skills/qualifications],
                            "missing_requirements": [list of missing requirements]
                        }"""
                    },
                    {
                        "role": "user",
                        "content": f"""Job Description:\n{job_description}\n\n
                        Resume:\n{resume_text}"""
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=1000
            )

            result = json.loads(response.choices[0].message.content)

            # Validate response format
            required_keys = ['decision', 'justification', 'match_score', 'key_matches', 'missing_requirements']
            if not all(key in result for key in required_keys):
                raise ValueError("Invalid response format from OpenAI API")

            return {
                'decision': result['decision'],
                'justification': result['justification'],
                'match_score': float(result['match_score']),
                'key_matches': result['key_matches'],
                'missing_requirements': result['missing_requirements']
            }

        except json.JSONDecodeError:
            raise Exception("Failed to parse OpenAI API response")
        except Exception as e:
            raise Exception(f"Failed to evaluate resume: {str(e)}")

    def get_improvement_suggestions(self, resume_text: str, job_description: str) -> Dict[str, List[str]]:
        """Get specific suggestions for improving the resume for the job."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """Analyze the resume against the job requirements and provide
                        specific suggestions for improvement. Focus on content, format, and missing skills.
                        Respond with JSON in this format:
                        {
                            "content_suggestions": [list of content improvements],
                            "format_suggestions": [list of format improvements],
                            "skill_development": [list of skills to develop]
                        }"""
                    },
                    {
                        "role": "user",
                        "content": f"""Job Description:\n{job_description}\n\n
                        Resume:\n{resume_text}"""
                    }
                ],
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            raise Exception(f"Failed to get improvement suggestions: {str(e)}")