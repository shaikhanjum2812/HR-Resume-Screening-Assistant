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
            
            # SAP module-specific hint for question generation 
            module_specific_hints = {
                "FI": "Include questions about GL accounting, accounts payable, accounts receivable, asset accounting, financial statements, and integration with CO. Reference transactions like FB01, F-02, F-03, FBL1N, and tables like BKPF, BSEG.",
                "CO": "Include questions about cost center accounting, profit center accounting, product costing, profitability analysis, and CO-PA. Reference transactions like KE21N, KS01, CK11N, and tables like COEP, COSS.",
                "MM": "Include questions about procurement processes, inventory management, material master, vendor master, and purchasing. Reference transactions like ME21N, MIGO, MM01, XK01, and tables like EKKO, EKPO, MARA.",
                "SD": "Include questions about sales order processing, delivery, billing, pricing, customer master, and output determination. Reference transactions like VA01, VL01N, VF01, and tables like VBAK, VBAP, KNA1.",
                "PP": "Include questions about production planning, MRP, capacity planning, work centers, routing, and BOM management. Reference transactions like CS01, CS02, MD01, CO01, and tables like MAST, STKO, CRHD.",
                "HCM": "Include questions about personnel administration, time management, payroll, organizational management, and ESS/MSS. Reference infotypes, time evaluation schemas, and payroll clusters.",
                "PM": "Include questions about maintenance planning, work order management, equipment and functional location master data. Reference transactions like IW31, IW32, IE01, IL01, and tables like ILOA, EQUI.",
                "QM": "Include questions about quality planning, inspection processing, quality certificates, and defect recording. Reference transactions like QA01, QA02, QE51N, and quality-related tables.",
                "WM": "Include questions about warehouse structure, put-away strategies, picking strategies, and integration with MM and SD. Reference transactions like LT01, LT03, LS01, and tables like LQUA, LAGP.",
                "BW": "Include questions about data modeling, BW objects (InfoObjects, DSOs, MultiProviders), extraction, transformation, and reporting. Reference BW modeling and administration concepts.",
                "ABAP": "Include questions about programming concepts, ABAP Dictionary, performance optimization, ALV reporting, debugger, and enhancement techniques. Reference SE11, SE16, SE38, SE80 transactions."
            }
            
            # Get module-specific hints or use generic if module not in list
            module_hint = module_specific_hints.get(sap_module.upper(), 
                          f"Include questions specific to {sap_module} functionality, key transactions, tables, and integration points.")
            
            prompt = f"""
            You are an elite SAP {sap_module} interviewer with 15+ years of implementation experience and deep domain knowledge. Generate highly specialized interview questions for a candidate with the following resume, applying for a position with the following job description.
            
            The questions must be deeply technical and specifically tailored to evaluate SAP {sap_module} expertise. Focus on identifying both breadth and depth of knowledge. Assume the candidate claims expertise - your job is to verify real expertise vs. superficial knowledge.
            
            JOB DESCRIPTION:
            {job_description}
            
            CANDIDATE'S RESUME:
            {resume_text}
            
            SAP {sap_module} MODULE GUIDANCE:
            {module_hint}
            
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
            1. Extremely specific to the SAP {sap_module} module (always mention specific transactions, tables, configuration settings, BAPIs, etc.)
            2. Precisely tailored to the candidate's exact skills and experience from their resume
            3. Directly relevant to the job requirements mentioned in the description
            4. Uniquely crafted for this candidate (not generic)
            5. Detailed enough to assess true expertise (should challenge even experienced professionals)
            6. Include advanced SAP-specific terminology and concepts relevant to the {sap_module} module
            7. Include at least 2 questions about SAP S/4HANA-specific changes to the {sap_module} module (if applicable)
            8. Include at least 1 question about SAP Fiori apps relevant to the {sap_module} module
            
            For technical questions:
            - Ask about specific configuration settings, tables, BAPIs, reports, or transactions relevant to {sap_module}
            - Include questions about data structures, integration points, and authorization objects
            - Ask about specific customizing steps for complex {sap_module} processes
            
            For scenario questions:
            - Present complex real-world implementation challenges specific to {sap_module}
            - Include international/global scenarios with multiple legal entities if relevant
            - Reference actual business requirements that would require advanced configuration
            
            For behavioral questions:
            - Focus on SAP project experiences, specifically around {sap_module} implementations
            - Ask about challenging stakeholder situations related to {sap_module} requirements
            - Explore how they handled technical disagreements on configuration approaches
            
            For problem-solving:
            - Present complex technical issues that would arise in an SAP {sap_module} implementation
            - Include performance optimization scenarios
            - Include data migration or conversion challenges specific to {sap_module}
            - Include integration troubleshooting with other SAP modules
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
            
            # Create module and question type specific evaluation criteria
            sap_module = interview_context.get('sap_module', 'Unknown')
            
            # Define evaluation criteria weight based on question type
            weights = {
                "technical": {
                    "technical_accuracy": 40,
                    "sap_specific_knowledge": 30,
                    "experience_application": 20,
                    "clarity": 10
                },
                "scenario": {
                    "solution_approach": 30,
                    "sap_specific_knowledge": 30,
                    "business_understanding": 20,
                    "experience_application": 20
                },
                "behavioral": {
                    "relevant_experience": 40,
                    "teamwork_approach": 20,
                    "sap_context_understanding": 20,
                    "communication_clarity": 20
                },
                "problem_solving": {
                    "solution_approach": 30,
                    "technical_understanding": 30,
                    "experience_application": 20,
                    "systematic_thinking": 20
                }
            }
            
            # Get appropriate weights for this question type
            current_weights = weights.get(question_type, weights["technical"])
            weight_text = "\n".join([f"{k.replace('_', ' ').title()} ({v}%)" for k, v in current_weights.items()])
            
            prompt = f"""
            You are an experienced SAP {sap_module} technical interviewer with deep implementation expertise. Critically evaluate the candidate's response to the following {question_type} question with a focus on verifying genuine expertise.
            
            SAP MODULE: {sap_module}
            QUESTION TYPE: {question_type}
            
            QUESTION:
            {current_question}
            
            CANDIDATE'S RESPONSE:
            {candidate_response}
            
            Evaluate the response focusing on these weighted criteria:
            {weight_text}
            
            Provide an evaluation in the following JSON format:
            
            {{
                "score": /* Score between 0-10 based on the weighted criteria above */,
                "technical_assessment": /* Brief technical assessment of their SAP {sap_module} knowledge demonstrated */,
                "experience_evaluation": /* Brief assessment of their practical experience demonstrated in the answer */,
                "strengths": /* List of 2-3 specific strengths in the response, with focus on SAP {sap_module} technical accuracy */,
                "weaknesses": /* List of 2-3 specific weaknesses or areas for improvement, noting any technical inaccuracies */,
                "follow_up": /* Optional follow-up question to probe deeper where knowledge appears shallow */,
                "evaluation_notes": /* Detailed technical evaluation notes for the interviewer with specific SAP {sap_module} references */
            }}
            
            EVALUATION GUIDELINES:
            1. Be technically precise and critical while remaining fair
            2. Look specifically for SAP {sap_module} terminology, transaction codes, tables, and processes
            3. Verify if they demonstrate actual hands-on experience or just theoretical knowledge
            4. Check for depth of understanding rather than superficial answers
            5. Note if they mention relevant S/4HANA changes or Fiori apps when applicable
            6. Score of 7+ should only be given to answers that show clear expertise
            7. Distinguish between memorized facts vs. understanding of concepts
            8. Evaluate if their approach matches SAP best practices
            9. Note any inconsistencies between their claimed experience and demonstrated knowledge
            10. Be particularly attentive to accuracy regarding customizing, integration points, and authorization concepts
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            result = json.dumps(response.choices[0].message.content)
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
                              interview_transcript: List[Dict[str, Any]],
                              total_questions: int = None) -> Dict[str, Any]:
        """
        Generate a final comprehensive report after the interview.
        
        Args:
            sap_module: The specific SAP module for the position
            job_description: The full job description
            resume_text: The candidate's resume text
            interview_transcript: List of Q&A pairs with evaluations from the interview
            total_questions: Total number of questions in the interview plan
            
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
            
            # Calculate completion percentage
            answered_questions = len(interview_transcript)
            completion_percentage = 0
            
            if total_questions and total_questions > 0:
                completion_percentage = (answered_questions / total_questions) * 100
            else:
                # If total_questions is not provided, estimate based on standard interview format
                # Assuming a standard interview would have 10 questions
                estimated_total = 10
                completion_percentage = (answered_questions / estimated_total) * 100
            
            # Define module-specific evaluation criteria
            module_evaluation_guide = {
                "FI": "Focus on evaluating their knowledge of financial accounting, G/L, A/P, A/R, asset accounting, banking, and financial reporting. Assess their ability to handle complex financial scenarios, period-end closing activities, and financial process integration.",
                "CO": "Focus on evaluating their knowledge of cost center accounting, product costing, profit center accounting, internal orders, and profitability analysis. Assess their ability to handle management reporting, allocation methods, and integration with FI.",
                "MM": "Focus on evaluating their knowledge of purchasing, inventory management, master data, MRP, goods movements, and vendor management. Assess their understanding of procurement processes, source determination, and pricing conditions.",
                "SD": "Focus on evaluating their knowledge of sales order processing, delivery, billing, pricing, customer master data, and output determination. Assess their understanding of complex pricing scenarios and integration with logistics.",
                "PP": "Focus on evaluating their knowledge of production planning, MRP, capacity planning, shop floor control, and BOM/routing management. Assess their ability to handle complex manufacturing scenarios.",
                "HCM": "Focus on evaluating their knowledge of personnel administration, time management, payroll, organizational management, and benefits administration. Assess their understanding of complex payroll rules and legal requirements.",
                "PM": "Focus on evaluating their knowledge of maintenance planning, work order management, equipment and functional location master data, and integration with MM. Assess their understanding of maintenance strategies.",
                "QM": "Focus on evaluating their knowledge of quality planning, inspection processing, quality certificates, and integration with MM and PP. Assess their understanding of quality control processes.",
                "WM": "Focus on evaluating their knowledge of warehouse structure, storage bin determination, putaway strategies, picking strategies, and integration with MM and SD. Assess their understanding of warehouse optimization.",
                "ABAP": "Focus on evaluating their programming knowledge, ABAP Dictionary expertise, debugging skills, performance optimization knowledge, and experience with advanced ABAP concepts. Assess their understanding of BADI, User Exits, and enhancement frameworks."
            }
            
            eval_guide = module_evaluation_guide.get(sap_module.upper(), 
                         f"Focus on evaluating their knowledge of {sap_module} functionality, configuration, integration points, and business process understanding.")
            
            # Create a detailed prompt for final evaluation
            prompt = f"""
            You are an SAP {sap_module} Principal Consultant and technical hiring manager with 15+ years of implementation experience. Generate a comprehensive final evaluation report for a candidate after their SAP module-specific interview.
            
            IMPORTANT CONTEXT:
            - The candidate answered {answered_questions} questions out of {total_questions or 'the expected number of'} questions.
            - This represents approximately {completion_percentage:.1f}% completion of the full interview.
            - Take this completion rate into serious consideration when making your final recommendation.
            - If less than 70% of questions were answered, the candidate cannot receive a "Hire" recommendation.
            - If less than 50% of questions were answered, the candidate should receive a "Do Not Hire" recommendation unless their answers were truly exceptional.
            - If only 1-2 questions were answered, the assessment should clearly state that insufficient data was collected and recommend "Do Not Hire".
            
            JOB DESCRIPTION:
            {job_description}
            
            CANDIDATE'S RESUME:
            {resume_text}
            
            INTERVIEW TRANSCRIPT:
            {transcript_text}
            
            SAP {sap_module} EVALUATION GUIDANCE:
            {eval_guide}
            
            Evaluate the candidate across multiple dimensions with a significant focus on their SAP {sap_module} technical expertise and implementation experience.
            
            Provide a final evaluation report in the following JSON format:
            
            {{
                "interview_completion_rate": {completion_percentage:.1f},
                "data_sufficiency_assessment": /* Your assessment of whether enough data was collected to make a proper evaluation */,
                "overall_score": /* Overall score between 0-10, should reflect completion rate */,
                "technical_proficiency": {{
                    "score": /* Technical score between 0-10 */,
                    "assessment": /* Detailed assessment of technical skills in SAP {sap_module} */,
                    "sap_module_expertise": /* Specific evaluation of their {sap_module} knowledge including transactions, tables, and configuration expertise */,
                    "technical_gaps": /* Specific technical knowledge gaps identified in their {sap_module} expertise */
                }},
                "communication_skills": {{
                    "score": /* Communication score between 0-10 */,
                    "assessment": /* Assessment of their ability to explain complex SAP {sap_module} concepts clearly */,
                    "stakeholder_communication": /* Evaluation of how they would communicate with business stakeholders */
                }},
                "problem_solving_ability": {{
                    "score": /* Problem-solving score between 0-10 */,
                    "assessment": /* Assessment of their approach to {sap_module} implementation challenges */,
                    "methodology": /* Evaluation of their problem-solving methodology and structure */
                }},
                "experience_assessment": {{
                    "score": /* Experience score between 0-10 */,
                    "assessment": /* Detailed evaluation of the quality, depth and relevance of their SAP {sap_module} experience */,
                    "implementation_experience": /* Analysis of their SAP implementation experience including project phases, roles, and responsibilities */,
                    "s4hana_experience": /* Assessment of their SAP S/4HANA knowledge and experience if demonstrated */
                }},
                "strengths": [
                    /* List of 3-5 specific strengths, particularly noting SAP {sap_module} technical strengths with concrete examples from their responses */
                ],
                "areas_for_improvement": [
                    /* List of 3-5 specific areas for improvement with recommendations */
                ],
                "additional_observations": /* Any other important observations about the candidate including remarks about the incomplete interview if applicable */,
                "cultural_fit": /* Assessment of cultural fit and team collaboration potential based on behavioral responses */,
                "hiring_recommendation": /* "Hire", "Consider", or "Do Not Hire" */,
                "recommendation_reasoning": /* Detailed explanation for the hiring recommendation with specific reference to job requirements and interview completion rate */
            }}
            
            In your assessment:
            1. Be highly specific about their {sap_module} expertise level (beginner, intermediate, advanced, expert)
            2. Evaluate their knowledge of specific {sap_module} transactions, tables, and configuration settings mentioned in their responses
            3. Assess their understanding of SAP integration points with other modules
            4. Distinguish between theoretical knowledge and practical implementation experience
            5. Evaluate their experience with full-cycle SAP implementation projects
            6. Consider whether they meet the specific SAP {sap_module} requirements in the job description
            7. Assess their S/4HANA and Fiori knowledge if relevant to the position
            8. Evaluate their ability to bridge technical concepts with business requirements
            9. Consider their ability to handle complex {sap_module} scenarios typical in enterprise implementations
            10. Assess whether they understand SAP best practices and why they exist
            11. IMPORTANT: Factor in the interview completion rate in your final recommendation. If the interview was not fully completed, this should be noted as a significant limitation in your assessment.
            
            Be fair but critical in your final assessment, focusing on their demonstrated SAP {sap_module} expertise rather than general IT skills.
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            result = json.dumps(response.choices[0].message.content)
            logger.info("Successfully generated final interview report")
            
            return result
            
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating final report: {e}")
            raise
