import os
from datetime import datetime
import json
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import DictCursor
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        try:
            # Create a connection pool instead of a single connection
            self.pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=os.environ['DATABASE_URL'],
                connect_timeout=3
            )
            self.create_tables()
            logger.info("Database connection and tables initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = self.pool.getconn()
            yield conn
        except Exception as e:
            logger.error(f"Error with database connection: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self.pool.putconn(conn)

    def execute_query(self, query, params=None, fetch=True, cursor_factory=None):
        """Execute a query with proper connection handling"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=cursor_factory) as cursor:
                try:
                    cursor.execute(query, params or ())
                    if fetch:
                        result = cursor.fetchall()
                    else:
                        result = None
                    conn.commit()
                    return result
                except Exception as e:
                    logger.error(f"Query execution error: {e}")
                    conn.rollback()
                    raise

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
                        technical_skills_score FLOAT,
                        experience_relevance_score FLOAT,
                        education_match_score FLOAT,
                        overall_fit_score FLOAT,
                        interview_focus TEXT,
                        skill_gaps TEXT,
                        technical_depth FLOAT,
                        problem_solving_score FLOAT,
                        project_complexity_score FLOAT,
                        implementation_experience_score FLOAT,
                        project_expertise_score FLOAT,
                        experience_quality_score FLOAT,
                        evaluation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        evaluation_data TEXT,
                        resume_file_data BYTEA,
                        resume_file_type VARCHAR(255)
                    )
                    ''')

                    conn.commit()
                    logger.info("Database tables created successfully")
                except Exception as e:
                    logger.error(f"Error creating tables: {e}")
                    conn.rollback()
                    raise

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
        job_id = self.execute_query(query, (title, description))[0][0]

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
        query = '''
            SELECT j.id, j.title, j.description, j.date_created, e.id
            FROM job_descriptions j
            LEFT JOIN evaluation_criteria e ON j.id = e.job_id
            WHERE j.active = true
        '''
        jobs = self.execute_query(query)
        return [
            {
                'id': job[0],
                'title': job[1],
                'description': job[2],
                'date_created': job[3],
                'has_criteria': job[4] is not None
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
                experience_analysis, technical_skills_score, experience_relevance_score,
                education_match_score, overall_fit_score, interview_focus, skill_gaps,
                technical_depth, problem_solving_score, project_complexity_score,
                implementation_experience_score, project_expertise_score,
                experience_quality_score,
                evaluation_data,
                resume_file_data, resume_file_type
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        '''

        candidate_info = evaluation_result.get('candidate_info', {})
        evaluation_metrics = evaluation_result.get('evaluation_metrics', {})
        recommendations = evaluation_result.get('recommendations', {})
        technical_assessment = evaluation_result.get('technical_assessment', {})

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
            evaluation_metrics.get('technical_skills', 0.0),
            evaluation_metrics.get('experience_relevance', 0.0),
            evaluation_metrics.get('education_match', 0.0),
            evaluation_metrics.get('overall_fit', 0.0),
            json.dumps(recommendations.get('interview_focus', [])),
            json.dumps(recommendations.get('skill_gaps', [])),
            technical_assessment.get('technical_depth', 0.0),
            technical_assessment.get('problem_solving', 0.0),
            technical_assessment.get('project_complexity', 0.0),
            evaluation_metrics.get('implementation_experience', 0.0),
            evaluation_metrics.get('project_expertise', 0.0),
            evaluation_result['years_of_experience'].get('quality_score', 0.0),
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
        return self.execute_query('SELECT COUNT(*) FROM job_descriptions WHERE active = true')[0][0]

    def get_today_evaluations_count(self):
        query = '''
                SELECT COUNT(*) FROM evaluations 
                WHERE DATE(evaluation_date) = CURRENT_DATE
            '''
        return self.execute_query(query)[0][0]

    def get_evaluation_criteria(self, job_id):
        query = 'SELECT * FROM evaluation_criteria WHERE job_id = %s'
        criteria = self.execute_query(query, (job_id,))
        if criteria:
            return {
                'min_years_experience': criteria[0][2],
                'required_skills': json.loads(criteria[0][3]),
                'preferred_skills': json.loads(criteria[0][4]),
                'education_requirements': criteria[0][5],
                'company_background_requirements': criteria[0][6],
                'domain_experience_requirements': criteria[0][7],
                'additional_instructions': criteria[0][8]
            }
        return None

    def get_evaluation_details(self, evaluation_id):
        query = '''
            SELECT * FROM evaluations WHERE id = %s
        '''
        eval_data = self.execute_query(query, (evaluation_id,),cursor_factory=psycopg2.extras.DictCursor)
        if eval_data:
            return {
                'id': eval_data[0]['id'],
                'job_id': eval_data[0]['job_id'],
                'resume_name': eval_data[0]['resume_name'],
                'result': eval_data[0]['result'],
                'justification': eval_data[0]['justification'],
                'match_score': eval_data[0]['match_score'],
                'years_experience_total': eval_data[0]['years_experience_total'],
                'years_experience_relevant': eval_data[0]['years_experience_relevant'],
                'years_experience_required': eval_data[0]['years_experience_required'],
                'meets_experience_requirement': eval_data[0]['meets_experience_requirement'],
                'key_matches': json.loads(eval_data[0]['key_matches']),
                'missing_requirements': json.loads(eval_data[0]['missing_requirements']),
                'experience_analysis': eval_data[0]['experience_analysis'],
                'evaluation_date': eval_data[0]['evaluation_date'],
                'evaluation_data': json.loads(eval_data[0]['evaluation_data'])
            }
        return None