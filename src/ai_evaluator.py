import os
import json
import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional
from openai import OpenAI, APIError
from anthropic import Anthropic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIEvaluator:
    def __init__(self):
        """Initialize the AI Evaluator with OpenAI and Anthropic clients"""
        try:
            self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            self.anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
            self.openai_model = "gpt-4o"
            self.anthropic_model = "claude-3-5-sonnet-20241022"
            logger.info("AIEvaluator initialized successfully with both OpenAI and Anthropic")
        except Exception as e:
            logger.error(f"Failed to initialize AIEvaluator: {str(e)}")
            raise

    def _extract_candidate_info(self, resume_text: str) -> Dict[str, Any]:
        """Extract candidate information from resume text using Anthropic's Claude"""
        try:
            logger.info("Extracting candidate information using Claude")
            prompt = f"""
            You are a professional resume parser. Analyze this resume very carefully and extract key information.
            Focus on accuracy and completeness. Use exact matches from the text, don't paraphrase.

            Required Information to Extract:
            1. Full Name: Must be the candidate's complete name as written
            2. Email: Must be a valid email format (e.g., name@domain.com)
            3. Phone: Extract complete number, maintain original format
            4. Location: Current location including city/state/country
            5. LinkedIn: Complete LinkedIn profile URL if present
            6. Education: Highest degree and field of study
            7. Total Years of Experience: Calculate from work history
            8. Key Skills: List of primary technical and professional skills

            Resume text to analyze:
            {resume_text}

            Return the information in this exact JSON format:
            {{
                "name": "extracted full name",
                "email": "extracted email",
                "phone": "extracted phone",
                "location": "extracted location",
                "linkedin": "extracted linkedin url",
                "education": "extracted education details",
                "total_experience": "calculated years",
                "key_skills": ["skill1", "skill2", "skill3"]
            }}

            Rules:
            - Extract EXACT text from resume, don't modify or standardize
            - If information isn't found, use "Not provided"
            - For experience, calculate total years from work history
            - Include ALL skills mentioned in technical skills or core competencies sections
            """

            # First try with Anthropic
            try:
                response = self.anthropic_client.messages.create(
                    model=self.anthropic_model,
                    max_tokens=1000,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                result = json.loads(response.content)
                logger.info("Successfully parsed resume with Anthropic")
            except Exception as e:
                logger.warning(f"Anthropic extraction failed, falling back to OpenAI: {e}")
                # Fallback to OpenAI
                response = self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=[
                        {"role": "system", "content": "You are a resume parsing expert focused on accurate information extraction."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                result = json.loads(response.choices[0].message.content)
                logger.info("Successfully parsed resume with OpenAI fallback")

            # Validate and clean results
            for key in ['name', 'email', 'phone', 'location', 'linkedin', 'education', 'total_experience']:
                if key not in result or not result[key] or result[key].lower() in ['none', 'null', '']:
                    result[key] = "Not provided"

            if 'key_skills' not in result or not isinstance(result['key_skills'], list):
                result['key_skills'] = []

            # Log the extracted information for debugging
            logger.info(f"Extracted candidate information: {json.dumps(result, indent=2)}")

            return result
        except Exception as e:
            logger.error(f"Failed to extract candidate information: {e}")
            return {
                "name": "Not provided",
                "email": "Not provided",
                "phone": "Not provided",
                "location": "Not provided",
                "linkedin": "Not provided",
                "education": "Not provided",
                "total_experience": "Not provided",
                "key_skills": []
            }

    def _extract_years_from_text(self, text: str) -> float:
        """Extract numerical years from text description"""
        try:
            # Try to find a number followed by "years" or "year"
            years_pattern = r'(\d+(?:\.\d+)?)\s*(?:years?|yrs?)'
            match = re.search(years_pattern, text.lower())
            if match:
                return float(match.group(1))

            # If no direct year mention, try to extract just the number
            number_pattern = r'(\d+(?:\.\d+)?)'
            match = re.search(number_pattern, text)
            if match:
                return float(match.group(1))

            return 0.0
        except Exception as e:
            logger.error(f"Error extracting years from text: {e}")
            return 0.0

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
                "total_years": "Numeric value only (e.g., 5.5)",
                "relevant_years": "Numeric value only (e.g., 3.0)",
                "experience_details": "detailed analysis of experience",
                "quality_score": "score between 0 and 1"
            }}

            Important: For total_years and relevant_years, provide ONLY the numeric value, no text description.
            Example: "total_years": "5.5" (not "5.5 years" or "5 years and 6 months")
            """

            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            # Convert experience values to float and ensure they're numeric
            total_years = self._extract_years_from_text(str(result.get('total_years', '0')))
            relevant_years = self._extract_years_from_text(str(result.get('relevant_years', '0')))

            # Ensure quality score is a float between 0 and 1
            quality_score = float(result.get('quality_score', 0))
            quality_score = max(0.0, min(1.0, quality_score))

            return {
                "total": total_years,
                "relevant": relevant_years,
                "required": float(min_years),
                "meets_requirement": relevant_years >= float(min_years),
                "details": result.get('experience_details', 'No details provided'),
                "quality_score": quality_score
            }
        except Exception as e:
            logger.error(f"Failed to analyze experience: {e}")
            return {
                "total": 0.0,
                "relevant": 0.0,
                "required": float(min_years),
                "meets_requirement": False,
                "details": "Failed to analyze experience",
                "quality_score": 0.0
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

            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
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