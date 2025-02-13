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
        
        # Evaluations table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            resume_name TEXT NOT NULL,
            result TEXT NOT NULL,
            justification TEXT NOT NULL,
            evaluation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES job_descriptions (id)
        )
        ''')
        
        self.conn.commit()
    
    def add_job_description(self, title, description):
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO job_descriptions (title, description) VALUES (?, ?)',
            (title, description)
        )
        self.conn.commit()
    
    def get_all_jobs(self):
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT id, title, description, date_created FROM job_descriptions WHERE active = 1'
        )
        jobs = cursor.fetchall()
        return [
            {
                'id': job[0],
                'title': job[1],
                'description': job[2],
                'date_created': job[3]
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
    
    def save_evaluation(self, job_id, resume_name, result, justification):
        cursor = self.conn.cursor()
        cursor.execute(
            '''INSERT INTO evaluations 
            (job_id, resume_name, result, justification) 
            VALUES (?, ?, ?, ?)''',
            (job_id, resume_name, result, justification)
        )
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
            SELECT e.*, j.title 
            FROM evaluations e
            JOIN job_descriptions j ON e.job_id = j.id
            WHERE e.evaluation_date >= {time_filter}
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
