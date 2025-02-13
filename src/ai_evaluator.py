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
                        "content": """You are an expert HR assistant with strict evaluation criteria. 
                        Carefully analyze the candidate's resume against the job description, paying special attention to:

                        1. SAP Implementation Experience:
                           - Must have hands-on SAP implementation experience
                           - Reject if only SAP end-user experience
                           - Check for specific SAP implementation projects
                           - Verify role in SAP implementations (developer/consultant vs user)

                        2. Company Background:
                           - Must have experience in IT services companies
                           - Reject if experience is only from manufacturing or non-IT organizations
                           - Look for consulting/services background
                           - Verify client-facing implementation roles

                        3. Years of Experience:
                           - Extract and compare exact years of experience
                           - Automatically reject if below minimum required experience
                           - Consider only relevant IT services experience
                           - Focus on SAP implementation duration

                        4. Domain Relevance:
                           - Verify if experience is in SAP implementation domain
                           - Check for specific technical skills mentioned in job description
                           - Evaluate depth of implementation experience

                        5. Skills Match:
                           - Compare required skills with candidate's skills
                           - Consider both technical and soft skills
                           - Note any missing critical skills

                        Evaluation Rules:
                        - Reject if no proven SAP implementation experience
                        - Reject if only end-user SAP experience
                        - Reject if no IT services company background
                        - Reject if years of experience don't meet minimum requirement
                        - Reject if missing critical required skills
                        - Provide detailed justification for rejection

                        Respond with JSON in this format:
                        {
                            "decision": "shortlist" or "reject",
                            "justification": "detailed explanation including specific gaps",
                            "match_score": float between 0 and 1,
                            "years_of_experience": {
                                "total": float,
                                "relevant": float,
                                "sap_implementation": float,
                                "required": float,
                                "meets_requirement": boolean
                            },
                            "sap_experience": {
                                "has_implementation": boolean,
                                "details": "description of SAP implementation experience",
                                "projects": ["list of SAP implementation projects"]
                            },
                            "company_background": {
                                "has_it_services": boolean,
                                "companies": ["list of relevant companies"],
                                "roles": ["list of relevant roles"]
                            },
                            "key_matches": ["list of matching skills/qualifications"],
                            "missing_requirements": ["list of missing requirements"],
                            "experience_analysis": "detailed analysis of experience relevance"
                        }"""
                    },
                    {
                        "role": "user",
                        "content": f"""Job Description:\n{job_description}\n\n
                        Resume:\n{resume_text}"""
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.5,  # Lower temperature for more consistent evaluation
                max_tokens=1500
            )

            result = json.loads(response.choices[0].message.content)

            # Validate response format
            required_keys = ['decision', 'justification', 'match_score', 'key_matches', 
                           'missing_requirements', 'years_of_experience', 'experience_analysis',
                           'sap_experience', 'company_background']
            if not all(key in result for key in required_keys):
                raise ValueError("Invalid response format from OpenAI API")

            return {
                'decision': result['decision'],
                'justification': result['justification'],
                'match_score': float(result['match_score']),
                'years_of_experience': result['years_of_experience'],
                'sap_experience': result['sap_experience'],
                'company_background': result['company_background'],
                'key_matches': result['key_matches'],
                'missing_requirements': result['missing_requirements'],
                'experience_analysis': result['experience_analysis']
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
                        specific suggestions for improvement. Focus on:
                        1. SAP implementation experience gaps
                        2. IT services company experience
                        3. Technical skills development
                        4. Domain expertise enhancement
                        5. Project experience recommendations

                        Respond with JSON in this format:
                        {
                            "sap_implementation_gaps": [list of SAP implementation improvements needed],
                            "company_experience_suggestions": [suggestions for IT services experience],
                            "technical_skill_development": [list of technical skills to develop],
                            "domain_expertise_improvements": [list of domain expertise suggestions],
                            "project_experience_recommendations": [specific project experience needed]
                        }"""
                    },
                    {
                        "role": "user",
                        "content": f"""Job Description:\n{job_description}\n\n
                        Resume:\n{resume_text}"""
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.5
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            raise Exception(f"Failed to get improvement suggestions: {str(e)}")