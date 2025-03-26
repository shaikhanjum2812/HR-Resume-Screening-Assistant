import os
import json
import logging
from datetime import datetime
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import DictCursor
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        """Initialize the Database with connection pool"""
        try:
            # Create a connection pool instead of a single connection
            self.pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=os.environ['DATABASE_URL']
            )
            self.create_tables()
            logger.info("Database connection and tables initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
            
    def _parse_json_safely(self, json_data):
        """Safely parse JSON data regardless of input type"""
        if json_data is None:
            return {}
            
        if isinstance(json_data, dict):
            return json_data
            
        try:
            if isinstance(json_data, str):
                return json.loads(json_data)
            else:
                # Handle PostgreSQL JSONB type
                return json_data
        except Exception as e:
            logger.error(f"JSON parsing error: {str(e)}")
            return {}

    @contextmanager
    def get_connection(self):
        """Context manager for database connections with improved error handling"""
        conn = None
        try:
            conn = self.pool.getconn()
            
            # Test if connection is alive
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
            except Exception as e:
                logger.warning(f"Connection test failed, reconnecting: {e}")
                # Close the bad connection if possible
                try:
                    conn.close()
                except:
                    pass
                
                # Try to reinitialize pool
                self.pool = SimpleConnectionPool(
                    minconn=1,
                    maxconn=10,
                    dsn=os.environ['DATABASE_URL']
                )
                conn = self.pool.getconn()
                
            yield conn
        except Exception as e:
            logger.error(f"Connection error in get_connection: {e}")
            raise
        finally:
            if conn is not None:
                try:
                    self.pool.putconn(conn)
                except Exception as e:
                    logger.warning(f"Error returning connection to pool: {e}")
                    # If we can't return it to the pool, try to close it
                    try:
                        conn.close()
                    except:
                        pass

    def create_tables(self):
        """Create necessary database tables if they don't exist"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    # Create tables with the updated schema
                    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS job_descriptions (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        active BOOLEAN DEFAULT TRUE
                    )
                    ''')

                    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS evaluation_criteria (
                        id SERIAL PRIMARY KEY,
                        job_id INTEGER REFERENCES job_descriptions(id),
                        min_years_experience INTEGER,
                        required_skills TEXT,
                        preferred_skills TEXT,
                        education_requirements TEXT,
                        company_background_requirements TEXT,
                        domain_experience_requirements TEXT,
                        additional_instructions TEXT
                    )
                    ''')

                    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS evaluations (
                        id SERIAL PRIMARY KEY,
                        job_id INTEGER REFERENCES job_descriptions(id),
                        resume_name TEXT NOT NULL,
                        candidate_name TEXT,
                        candidate_email TEXT,
                        candidate_phone TEXT,
                        candidate_location TEXT,
                        linkedin_profile TEXT,
                        result TEXT NOT NULL,
                        justification TEXT NOT NULL,
                        match_score FLOAT,
                        confidence_score FLOAT,
                        years_experience_total FLOAT,
                        years_experience_relevant FLOAT,
                        years_experience_required FLOAT,
                        meets_experience_requirement BOOLEAN,
                        key_matches TEXT,
                        missing_requirements TEXT,
                        experience_analysis TEXT,
                        evaluation_data JSONB,
                        evaluation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        resume_file_data BYTEA,
                        resume_file_type VARCHAR(255)
                    )
                    ''')
                    
                    # Create interview-related tables
                    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS interview_sessions (
                        id SERIAL PRIMARY KEY,
                        evaluation_id INTEGER REFERENCES evaluations(id),
                        sap_module VARCHAR(50) NOT NULL,
                        status VARCHAR(20) NOT NULL DEFAULT 'pending',
                        start_time TIMESTAMP,
                        end_time TIMESTAMP,
                        overall_score FLOAT,
                        technical_score FLOAT,
                        communication_score FLOAT,
                        problem_solving_score FLOAT,
                        experience_score FLOAT,
                        recommendation VARCHAR(50),
                        recommendation_reasoning TEXT,
                        interview_data JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    ''')
                    
                    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS interview_questions (
                        id SERIAL PRIMARY KEY,
                        session_id INTEGER REFERENCES interview_sessions(id),
                        question_type VARCHAR(20) NOT NULL,
                        question_text TEXT NOT NULL,
                        question_context TEXT,
                        display_order INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    ''')
                    
                    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS interview_responses (
                        id SERIAL PRIMARY KEY,
                        question_id INTEGER REFERENCES interview_questions(id),
                        response_text TEXT,
                        score FLOAT,
                        strengths TEXT,
                        weaknesses TEXT,
                        evaluation_notes TEXT,
                        follow_up TEXT,
                        response_time INTEGER, 
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    ''')

                    conn.commit()
                    logger.info("Database tables created successfully")
                except Exception as e:
                    logger.error(f"Error creating tables: {e}")
                    conn.rollback()
                    raise

    def execute_query(self, query, params=None, fetch=True, cursor_factory=None, max_retries=3):
        """Execute a query with proper connection handling and retry logic"""
        retries = 0
        last_error = None
        
        while retries < max_retries:
            try:
                with self.get_connection() as conn:
                    # Test if connection is still alive
                    if conn.closed:
                        logger.warning("Connection was closed, attempting to reconnect...")
                        # Clear the pool and reinitialize
                        self.pool = SimpleConnectionPool(
                            minconn=1,
                            maxconn=10,
                            dsn=os.environ['DATABASE_URL']
                        )
                        continue  # Retry with the new connection
                        
                    with conn.cursor(cursor_factory=cursor_factory) as cursor:
                        cursor.execute(query, params or ())
                        if fetch:
                            result = cursor.fetchall()
                            # Return empty list if no results instead of None
                            if result is None or len(result) == 0:
                                return []
                        else:
                            result = None
                        conn.commit()
                        return result
                        
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                # These are connection-related errors, so we should retry
                retries += 1
                last_error = e
                logger.warning(f"Database connection error (attempt {retries}/{max_retries}): {e}")
                
                # Try to reinitialize the connection pool
                try:
                    self.pool = SimpleConnectionPool(
                        minconn=1,
                        maxconn=10,
                        dsn=os.environ['DATABASE_URL']
                    )
                except Exception as pool_error:
                    logger.error(f"Failed to reinitialize connection pool: {pool_error}")
                
                # Wait a bit before retrying
                import time
                time.sleep(0.5 * retries)  # Exponential backoff
                
            except Exception as e:
                # For other errors, log and raise immediately
                logger.error(f"Query execution error: {e}")
                try:
                    # Only try to rollback if conn exists and is defined in this scope
                    if 'conn' in locals() and conn is not None:
                        conn.rollback()
                except Exception as rollback_error:
                    logger.warning(f"Failed to rollback transaction: {rollback_error}")
                raise
        
        # If we've exhausted all retries
        logger.error(f"Query failed after {max_retries} attempts. Last error: {last_error}")
        raise last_error or Exception("Failed to execute database query after multiple attempts")

    def get_evaluations_by_period(self, period):
        if period == 'week':
            time_filter = "INTERVAL '7 days'"
        elif period == 'month':
            time_filter = "INTERVAL '30 days'"
        elif period == 'quarter':
            time_filter = "INTERVAL '90 days'"
        else:  # year
            time_filter = "INTERVAL '365 days'"

        query = f'''
            SELECT 
                e.id, e.job_id, e.resume_name, 
                e.candidate_name, e.candidate_email, e.candidate_phone,
                e.result, e.justification, e.match_score, 
                e.years_experience_total, e.years_experience_relevant,
                e.years_experience_required, e.meets_experience_requirement,
                e.evaluation_date, e.evaluation_data,
                j.title as job_title
            FROM evaluations e
            JOIN job_descriptions j ON e.job_id = j.id
            WHERE e.evaluation_date >= NOW() - {time_filter}
            ORDER BY e.evaluation_date DESC
        '''

        return self.execute_query(query)

    def clear_evaluations(self):
        return self.execute_query('DELETE FROM evaluations', fetch=False)

    def add_job_description(self, title, description, evaluation_criteria=None):
        query = 'INSERT INTO job_descriptions (title, description) VALUES (%s, %s) RETURNING id'
        result = self.execute_query(query, (title, description))
        job_id = result[0][0] if result and len(result) > 0 else None

        if evaluation_criteria:
            query = '''
                INSERT INTO evaluation_criteria (
                    job_id, min_years_experience, required_skills,
                    preferred_skills, education_requirements,
                    company_background_requirements, domain_experience_requirements,
                    additional_instructions
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            '''
            params = (
                job_id,
                evaluation_criteria.get('min_years_experience', 0),
                json.dumps(evaluation_criteria.get('required_skills', [])),
                json.dumps(evaluation_criteria.get('preferred_skills', [])),
                evaluation_criteria.get('education_requirements', ''),
                evaluation_criteria.get('company_background_requirements', ''),
                evaluation_criteria.get('domain_experience_requirements', ''),
                evaluation_criteria.get('additional_instructions', '')
            )
            self.execute_query(query, params, fetch=False)

        return job_id

    def get_all_jobs(self):
        """Get all active jobs"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT j.id, j.title, j.description, j.date_created, 
                           EXISTS(SELECT 1 FROM evaluation_criteria e WHERE e.job_id = j.id) as has_criteria
                    FROM job_descriptions j
                    WHERE j.active = true
                ''')
                jobs = cursor.fetchall()
                return [
                    {
                        'id': job[0],
                        'title': job[1],
                        'description': job[2],
                        'date_created': job[3],
                        'has_criteria': job[4]
                    }
                    for job in jobs
                ]

    def delete_job(self, job_id):
        query = 'UPDATE job_descriptions SET active = false WHERE id = %s'
        self.execute_query(query, (job_id,), fetch=False)

    def save_evaluation(self, job_id, resume_name, evaluation_result, resume_file=None):
        """Save evaluation results along with the resume file if provided"""
        query = '''
            INSERT INTO evaluations (
                job_id, resume_name, 
                candidate_name, candidate_email, candidate_phone, candidate_location, linkedin_profile,
                result, justification, match_score, confidence_score,
                years_experience_total, years_experience_relevant, years_experience_required,
                meets_experience_requirement, key_matches, missing_requirements,
                experience_analysis, evaluation_data,
                resume_file_data, resume_file_type
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        '''

        candidate_info = evaluation_result.get('candidate_info', {})

        # Prepare resume file data if provided
        resume_file_data = None
        resume_file_type = None
        if resume_file:
            resume_file_data = resume_file.getvalue()
            resume_file_type = resume_file.type

        params = (
            job_id,
            resume_name,
            candidate_info.get('name', ''),
            candidate_info.get('email', ''),
            candidate_info.get('phone', ''),
            candidate_info.get('location', ''),
            candidate_info.get('linkedin', ''),
            evaluation_result['decision'],
            evaluation_result['justification'],
            evaluation_result['match_score'],
            evaluation_result.get('confidence_score', 0.0),
            evaluation_result['years_of_experience']['total'],
            evaluation_result['years_of_experience']['relevant'],
            evaluation_result['years_of_experience']['required'],
            evaluation_result['years_of_experience']['meets_requirement'],
            json.dumps(evaluation_result['key_matches']),
            json.dumps(evaluation_result['missing_requirements']),
            evaluation_result['years_of_experience'].get('details', ''),
            json.dumps(evaluation_result),
            resume_file_data,
            resume_file_type
        )

        self.execute_query(query, params, fetch=False)

    def get_resume_file(self, evaluation_id):
        """Retrieve resume file data for a specific evaluation"""
        query = '''
            SELECT resume_file_data, resume_file_type, resume_name 
            FROM evaluations 
            WHERE id = %s
        '''
        result = self.execute_query(query, (evaluation_id,))
        if result and result[0][0]:
            # Convert memoryview to bytes for proper handling
            file_data = bytes(result[0][0]) if isinstance(result[0][0], memoryview) else result[0][0]
            return {
                'file_data': file_data,
                'file_type': result[0][1],
                'file_name': result[0][2]
            }
        return None

    def get_evaluations_by_date_range(self, start_date, end_date):
        query = '''
            SELECT 
                e.id, e.job_id, e.resume_name, e.result, e.justification,
                e.match_score, e.years_experience_total, e.years_experience_relevant,
                e.years_experience_required, e.meets_experience_requirement,
                e.key_matches, e.missing_requirements, e.experience_analysis,
                e.evaluation_date, e.evaluation_data,
                j.title as job_title
            FROM evaluations e
            JOIN job_descriptions j ON e.job_id = j.id
            WHERE DATE(e.evaluation_date) BETWEEN %s AND %s
            ORDER BY e.evaluation_date DESC
        '''
        return self.execute_query(query,(start_date, end_date))

    def get_active_jobs_count(self):
        query = 'SELECT COUNT(*) FROM job_descriptions WHERE active = true'
        result = self.execute_query(query)
        return result[0][0] if result and len(result) > 0 else 0

    def get_today_evaluations_count(self):
        query = '''
                SELECT COUNT(*) FROM evaluations 
                WHERE DATE(evaluation_date) = CURRENT_DATE
            '''
        result = self.execute_query(query)
        return result[0][0] if result and len(result) > 0 else 0

    def get_total_evaluations_count(self):
        """Get the total number of evaluations"""
        query = 'SELECT COUNT(*) FROM evaluations'
        result = self.execute_query(query)
        return result[0][0] if result and len(result) > 0 else 0

    def get_shortlisted_count(self):
        """Get the total number of shortlisted resumes"""
        query = "SELECT COUNT(*) FROM evaluations WHERE LOWER(result) = 'shortlist'"
        result = self.execute_query(query)
        return result[0][0] if result and len(result) > 0 else 0

    def get_rejected_count(self):
        """Get the total number of rejected resumes"""
        query = "SELECT COUNT(*) FROM evaluations WHERE LOWER(result) = 'reject'"
        result = self.execute_query(query)
        return result[0][0] if result and len(result) > 0 else 0

    def get_evaluation_criteria(self, job_id):
        query = 'SELECT * FROM evaluation_criteria WHERE job_id = %s'
        criteria = self.execute_query(query, (job_id,))
        if criteria and len(criteria) > 0:
            return {
                'min_years_experience': criteria[0][2],
                'required_skills': self._parse_json_safely(criteria[0][3]),
                'preferred_skills': self._parse_json_safely(criteria[0][4]),
                'education_requirements': criteria[0][5],
                'company_background_requirements': criteria[0][6],
                'domain_experience_requirements': criteria[0][7],
                'additional_instructions': criteria[0][8]
            }
        return None

    def get_evaluation_details(self, evaluation_id):
        """Retrieve detailed evaluation data by ID"""
        query = '''
            SELECT * FROM evaluations WHERE id = %s
        '''
        eval_data = self.execute_query(query, (evaluation_id,), cursor_factory=psycopg2.extras.DictCursor)
        if eval_data and len(eval_data) > 0:
            row = eval_data[0]  # Get the first row since we're querying by ID
            return {
                'id': row['id'],
                'job_id': row['job_id'],
                'resume_name': row['resume_name'],
                'result': row['result'],
                'justification': row['justification'],
                'match_score': row['match_score'],
                'years_experience_total': row['years_experience_total'],
                'years_experience_relevant': row['years_experience_relevant'],
                'years_experience_required': row['years_experience_required'],
                'meets_experience_requirement': row['meets_experience_requirement'],
                'key_matches': self._parse_json_safely(row['key_matches']),
                'missing_requirements': self._parse_json_safely(row['missing_requirements']),
                'experience_analysis': row['experience_analysis'],
                'evaluation_date': row['evaluation_date'],
                'evaluation_data': self._parse_json_safely(row['evaluation_data'])
            }
        return None
        
    # Interview-related methods
    def create_interview_session(self, evaluation_id, sap_module):
        """Create a new interview session for an evaluated candidate"""
        query = '''
            INSERT INTO interview_sessions 
            (evaluation_id, sap_module, status)
            VALUES (%s, %s, 'pending')
            RETURNING id
        '''
        result = self.execute_query(query, (evaluation_id, sap_module))
        if result and len(result) > 0:
            return result[0][0]
        return None
        
    def save_interview_questions(self, session_id, questions):
        """Save a set of generated interview questions"""
        for question_type, questions_list in questions.items():
            for i, question in enumerate(questions_list):
                query = '''
                    INSERT INTO interview_questions
                    (session_id, question_type, question_text, question_context, display_order)
                    VALUES (%s, %s, %s, %s, %s)
                '''
                self.execute_query(
                    query, 
                    (session_id, question_type, question['question'], question.get('context', ''), i),
                    fetch=False
                )
                
    def get_interview_questions(self, session_id):
        """Get all questions for an interview session, grouped by type"""
        query = '''
            SELECT id, question_type, question_text, question_context, display_order
            FROM interview_questions
            WHERE session_id = %s
            ORDER BY question_type, display_order
        '''
        result = self.execute_query(query, (session_id,), cursor_factory=psycopg2.extras.DictCursor)
        
        # Group questions by type
        questions = {
            'technical': [],
            'scenario': [],
            'behavioral': [],
            'problem_solving': []
        }
        
        if result and len(result) > 0:
            for row in result:
                questions[row['question_type']].append({
                    'id': row['id'],
                    'question': row['question_text'],
                    'context': row['question_context'],
                    'order': row['display_order']
                })
            
        return questions
        
    def save_interview_response(self, question_id, response_data):
        """Save a candidate's response and its evaluation"""
        query = '''
            INSERT INTO interview_responses
            (question_id, response_text, score, strengths, weaknesses, 
             evaluation_notes, follow_up, response_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        '''
        # Convert strengths and weaknesses to JSON if they are lists or dicts
        strengths = response_data.get('strengths', '')
        if isinstance(strengths, (list, dict)):
            strengths = json.dumps(strengths)
        
        weaknesses = response_data.get('weaknesses', '')
        if isinstance(weaknesses, (list, dict)):
            weaknesses = json.dumps(weaknesses)
            
        params = (
            question_id,
            response_data.get('response_text', ''),
            response_data.get('score', 0),
            strengths,
            weaknesses,
            response_data.get('evaluation_notes', ''),
            response_data.get('follow_up', ''),
            response_data.get('response_time', 0)
        )
        
        result = self.execute_query(query, params)
        if result and len(result) > 0:
            return result[0][0]
        return None
        
    def update_interview_session(self, session_id, session_data):
        """Update an interview session with final results"""
        query = '''
            UPDATE interview_sessions
            SET status = %s,
                end_time = %s,
                overall_score = %s,
                technical_score = %s,
                communication_score = %s,
                problem_solving_score = %s,
                experience_score = %s,
                recommendation = %s,
                recommendation_reasoning = %s,
                interview_data = %s
            WHERE id = %s
        '''
        
        # Handle interview_data
        interview_data = session_data.get('interview_data', {})
        if isinstance(interview_data, dict):
            # Convert dictionary to JSON string
            interview_data_json = json.dumps(interview_data)
        elif isinstance(interview_data, str):
            # Already a JSON string
            interview_data_json = interview_data
        else:
            # Default to empty object
            interview_data_json = '{}'
            
        params = (
            session_data.get('status', 'completed'),
            datetime.now(),
            session_data.get('overall_score', 0),
            session_data.get('technical_score', 0),
            session_data.get('communication_score', 0),
            session_data.get('problem_solving_score', 0),
            session_data.get('experience_score', 0),
            session_data.get('recommendation', ''),
            session_data.get('recommendation_reasoning', ''),
            interview_data_json,
            session_id
        )
        
        self.execute_query(query, params, fetch=False)
        
    def get_interview_session(self, session_id):
        """Get details of an interview session"""
        query = '''
            SELECT 
                sess.id, sess.evaluation_id, sess.sap_module, sess.status,
                sess.start_time, sess.end_time, sess.overall_score, 
                sess.technical_score, sess.communication_score, sess.problem_solving_score, sess.experience_score,
                sess.recommendation, sess.recommendation_reasoning, sess.interview_data,
                ev.candidate_name, ev.resume_name, ev.job_id,
                jd.title as job_title, jd.description as job_description
            FROM interview_sessions sess
            JOIN evaluations ev ON sess.evaluation_id = ev.id
            JOIN job_descriptions jd ON ev.job_id = jd.id
            WHERE sess.id = %s
        '''
        
        result = self.execute_query(query, (session_id,), cursor_factory=psycopg2.extras.DictCursor)
        if result and len(result) > 0:
            row = result[0]
            return {
                'id': row['id'],
                'evaluation_id': row['evaluation_id'],
                'sap_module': row['sap_module'],
                'status': row['status'],
                'start_time': row['start_time'],
                'end_time': row['end_time'],
                'overall_score': row['overall_score'],
                'technical_score': row['technical_score'],
                'communication_score': row['communication_score'],
                'problem_solving_score': row['problem_solving_score'],
                'experience_score': row['experience_score'],
                'recommendation': row['recommendation'],
                'recommendation_reasoning': row['recommendation_reasoning'],
                'interview_data': self._parse_json_safely(row['interview_data']),
                'candidate_name': row['candidate_name'],
                'resume_name': row['resume_name'],
                'job_id': row['job_id'],
                'job_title': row['job_title'],
                'job_description': row['job_description']
            }
        return None
        
    def get_interview_transcript(self, session_id):
        """Get the full transcript of an interview session with questions and responses"""
        query = '''
            SELECT 
                q.id as question_id, q.question_type, q.question_text, q.display_order,
                r.id as response_id, r.response_text, r.score, r.strengths, 
                r.weaknesses, r.evaluation_notes, r.follow_up, r.response_time, r.created_at
            FROM interview_questions q
            LEFT JOIN interview_responses r ON q.id = r.question_id
            WHERE q.session_id = %s
            ORDER BY q.question_type, q.display_order
        '''
        
        result = self.execute_query(query, (session_id,), cursor_factory=psycopg2.extras.DictCursor)
        transcript = []
        
        if result and len(result) > 0:
            for row in result:
                transcript.append({
                    'question_id': row['question_id'],
                    'question_type': row['question_type'],
                    'question': row['question_text'],
                    'order': row['display_order'],
                    'response_id': row['response_id'],
                    'response': row['response_text'],
                    'score': row['score'],
                    'strengths': self._parse_json_safely(row['strengths']),
                    'weaknesses': self._parse_json_safely(row['weaknesses']),
                    'evaluation_notes': row['evaluation_notes'],
                    'follow_up': row['follow_up'],
                    'response_time': row['response_time'],
                    'response_time_formatted': f"{row['response_time'] // 60}m {row['response_time'] % 60}s" if row['response_time'] else "",
                    'timestamp': row['created_at']
                })
            
        return transcript
        
    def get_pending_interviews(self):
        """Get all pending interview sessions"""
        query = '''
            SELECT 
                sess.id, sess.evaluation_id, sess.sap_module, sess.status,
                sess.created_at, ev.candidate_name, jd.title as job_title
            FROM interview_sessions sess
            JOIN evaluations ev ON sess.evaluation_id = ev.id
            JOIN job_descriptions jd ON ev.job_id = jd.id
            WHERE sess.status = 'pending'
            ORDER BY sess.created_at DESC
        '''
        
        result = self.execute_query(query, cursor_factory=psycopg2.extras.DictCursor)
        if result and len(result) > 0:
            return [dict(row) for row in result]
        return []
        
    # Import the new interview system methods
    from database_methods import create_new_interview, save_interview_questions_new, get_interview_questions_new
    from database_methods import save_interview_answer, get_interview_answers, complete_interview
    from database_methods import get_interview_details, get_completed_interviews_new, get_in_progress_interviews
    
    # Add methods to the class
    create_new_interview = create_new_interview
    save_interview_questions_new = save_interview_questions_new
    get_interview_questions_new = get_interview_questions_new
    save_interview_answer = save_interview_answer
    get_interview_answers = get_interview_answers
    complete_interview = complete_interview
    get_interview_details = get_interview_details
    get_completed_interviews_new = get_completed_interviews_new
    get_in_progress_interviews = get_in_progress_interviews
        
    def get_completed_interviews(self):
        """Get all completed interview sessions"""
        query = '''
            SELECT 
                sess.id, sess.evaluation_id, sess.sap_module, sess.status,
                sess.start_time, sess.end_time, sess.overall_score, 
                sess.technical_score, sess.communication_score, sess.problem_solving_score, sess.experience_score, 
                sess.recommendation,
                ev.candidate_name, jd.title as job_title
            FROM interview_sessions sess
            JOIN evaluations ev ON sess.evaluation_id = ev.id
            JOIN job_descriptions jd ON ev.job_id = jd.id
            WHERE sess.status = 'completed'
            ORDER BY sess.end_time DESC
        '''
        
        result = self.execute_query(query, cursor_factory=psycopg2.extras.DictCursor)
        if result and len(result) > 0:
            return [dict(row) for row in result]
        return []