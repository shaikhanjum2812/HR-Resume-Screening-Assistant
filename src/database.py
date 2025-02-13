import sqlite3
from datetime import datetime
import json

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('hr_assistant.db', check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        # Job Descriptions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_descriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            active BOOLEAN DEFAULT 1
        )
        ''')

        # Evaluation Criteria table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS evaluation_criteria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            min_years_experience INTEGER,
            required_skills TEXT,
            preferred_skills TEXT,
            education_requirements TEXT,
            company_background_requirements TEXT,
            domain_experience_requirements TEXT,
            additional_instructions TEXT,
            FOREIGN KEY (job_id) REFERENCES job_descriptions (id)
        )
        ''')

        # Enhanced Evaluations table with additional fields
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            resume_name TEXT NOT NULL,
            result TEXT NOT NULL,
            justification TEXT NOT NULL,
            match_score REAL,
            years_experience_total REAL,
            years_experience_relevant REAL,
            years_experience_required REAL,
            meets_experience_requirement BOOLEAN,
            key_matches TEXT,
            missing_requirements TEXT,
            experience_analysis TEXT,
            evaluation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            evaluation_data TEXT,
            FOREIGN KEY (job_id) REFERENCES job_descriptions (id)
        )
        ''')

        self.conn.commit()

    def add_job_description(self, title, description, evaluation_criteria=None):
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO job_descriptions (title, description) VALUES (?, ?)',
            (title, description)
        )
        job_id = cursor.lastrowid

        if evaluation_criteria:
            cursor.execute('''
                INSERT INTO evaluation_criteria (
                    job_id, min_years_experience, required_skills,
                    preferred_skills, education_requirements,
                    company_background_requirements, domain_experience_requirements,
                    additional_instructions
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_id,
                evaluation_criteria.get('min_years_experience', 0),
                json.dumps(evaluation_criteria.get('required_skills', [])),
                json.dumps(evaluation_criteria.get('preferred_skills', [])),
                evaluation_criteria.get('education_requirements', ''),
                evaluation_criteria.get('company_background_requirements', ''),
                evaluation_criteria.get('domain_experience_requirements', ''),
                evaluation_criteria.get('additional_instructions', '')
            ))

        self.conn.commit()
        return job_id

    def get_all_jobs(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT j.id, j.title, j.description, j.date_created, e.id
            FROM job_descriptions j
            LEFT JOIN evaluation_criteria e ON j.id = e.job_id
            WHERE j.active = 1
        ''')
        jobs = cursor.fetchall()
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
        cursor = self.conn.cursor()
        cursor.execute(
            'UPDATE job_descriptions SET active = 0 WHERE id = ?',
            (job_id,)
        )
        self.conn.commit()

    def save_evaluation(self, job_id, resume_name, evaluation_result):
        """
        Save the complete evaluation results to the database
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO evaluations (
                job_id, resume_name, result, justification,
                match_score, years_experience_total, years_experience_relevant,
                years_experience_required, meets_experience_requirement,
                key_matches, missing_requirements, experience_analysis,
                evaluation_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            job_id,
            resume_name,
            evaluation_result['decision'],
            evaluation_result['justification'],
            evaluation_result['match_score'],
            evaluation_result['years_of_experience']['total'],
            evaluation_result['years_of_experience']['relevant'],
            evaluation_result['years_of_experience']['required'],
            evaluation_result['years_of_experience']['meets_requirement'],
            json.dumps(evaluation_result['key_matches']),
            json.dumps(evaluation_result['missing_requirements']),
            evaluation_result['experience_analysis'],
            json.dumps(evaluation_result)  # Store complete evaluation data as JSON
        ))
        self.conn.commit()

    def get_evaluations_by_period(self, period):
        cursor = self.conn.cursor()
        if period == 'week':
            time_filter = "datetime('now', '-7 days')"
        elif period == 'month':
            time_filter = "datetime('now', '-30 days')"
        else:  # year
            time_filter = "datetime('now', '-365 days')"

        cursor.execute(f'''
            SELECT 
                e.id, e.job_id, e.resume_name, e.result, e.justification,
                e.match_score, e.years_experience_total, e.years_experience_relevant,
                e.years_experience_required, e.meets_experience_requirement,
                e.key_matches, e.missing_requirements, e.experience_analysis,
                e.evaluation_date, e.evaluation_data,
                j.title as job_title
            FROM evaluations e
            JOIN job_descriptions j ON e.job_id = j.id
            WHERE e.evaluation_date >= {time_filter}
            ORDER BY e.evaluation_date DESC
        ''')
        return cursor.fetchall()

    def get_active_jobs_count(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM job_descriptions WHERE active = 1')
        return cursor.fetchone()[0]

    def get_today_evaluations_count(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM evaluations 
            WHERE date(evaluation_date) = date('now')
        ''')
        return cursor.fetchone()[0]

    def get_evaluation_criteria(self, job_id):
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT * FROM evaluation_criteria WHERE job_id = ?',
            (job_id,)
        )
        criteria = cursor.fetchone()

        if criteria:
            return {
                'min_years_experience': criteria[2],
                'required_skills': json.loads(criteria[3]),
                'preferred_skills': json.loads(criteria[4]),
                'education_requirements': criteria[5],
                'company_background_requirements': criteria[6],
                'domain_experience_requirements': criteria[7],
                'additional_instructions': criteria[8]
            }
        return None

    def get_evaluation_details(self, evaluation_id):
        """
        Retrieve detailed evaluation results
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM evaluations WHERE id = ?
        ''', (evaluation_id,))
        eval_data = cursor.fetchone()
        if eval_data:
            return {
                'id': eval_data[0],
                'job_id': eval_data[1],
                'resume_name': eval_data[2],
                'result': eval_data[3],
                'justification': eval_data[4],
                'match_score': eval_data[5],
                'years_experience_total': eval_data[6],
                'years_experience_relevant': eval_data[7],
                'years_experience_required': eval_data[8],
                'meets_experience_requirement': bool(eval_data[9]),
                'key_matches': json.loads(eval_data[10]),
                'missing_requirements': json.loads(eval_data[11]),
                'experience_analysis': eval_data[12],
                'evaluation_date': eval_data[13],
                'evaluation_data': json.loads(eval_data[14])
            }
        return None