"""
This script updates the database structure to support the new interview engine
"""

import os
import logging
import psycopg2
from psycopg2 import sql
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@contextmanager
def get_connection():
    """Context manager for database connections"""
    conn = None
    try:
        # Get database URL from environment
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
            
        # Connect to the database
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        yield conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def check_table_exists(conn, table_name):
    """Check if a table exists in the database"""
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name = %s
            )
        """, (table_name,))
        result = cursor.fetchone()
        if result and len(result) > 0:
            return result[0]
        return False

def update_database_schema():
    """Update database schema to support the new interview system"""
    try:
        with get_connection() as conn:
            # Check if the new interview tables already exist
            logger.info("Checking if new interview tables exist...")
            if check_table_exists(conn, 'interviews_new'):
                logger.info("New interview tables already exist, skipping creation")
                conn.commit()
                return True
                
            # Create new interview tables
            logger.info("Creating new interview tables...")
            
            with conn.cursor() as cursor:
                # Create interviews_new table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS interviews_new (
                        id SERIAL PRIMARY KEY,
                        job_title VARCHAR(255) NOT NULL,
                        job_description TEXT NOT NULL,
                        resume_text TEXT NOT NULL,
                        status VARCHAR(50) NOT NULL DEFAULT 'in_progress',
                        start_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        end_time TIMESTAMP,
                        completion_rate FLOAT DEFAULT 0,
                        overall_score FLOAT DEFAULT 0,
                        technical_score FLOAT DEFAULT 0,
                        problem_solving_score FLOAT DEFAULT 0,
                        communication_score FLOAT DEFAULT 0,
                        recommendation VARCHAR(100),
                        report_data JSONB
                    )
                """)
                
                # Create interview_questions_new table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS interview_questions_new (
                        id SERIAL PRIMARY KEY,
                        interview_id INTEGER NOT NULL REFERENCES interviews_new(id) ON DELETE CASCADE,
                        question_text TEXT NOT NULL,
                        question_type VARCHAR(50) NOT NULL,
                        display_order INTEGER NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create interview_answers table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS interview_answers (
                        id SERIAL PRIMARY KEY,
                        question_id INTEGER NOT NULL REFERENCES interview_questions_new(id) ON DELETE CASCADE,
                        answer_text TEXT NOT NULL,
                        score FLOAT DEFAULT 0,
                        technical_accuracy FLOAT DEFAULT 0,
                        clarity_of_communication FLOAT DEFAULT 0,
                        relevance FLOAT DEFAULT 0,
                        demonstrated_expertise FLOAT DEFAULT 0,
                        strengths JSONB DEFAULT '[]'::jsonb,
                        weaknesses JSONB DEFAULT '[]'::jsonb,
                        feedback TEXT,
                        response_time INTEGER DEFAULT 0,
                        answered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indices for better performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_interviews_status ON interviews_new(status);
                    CREATE INDEX IF NOT EXISTS idx_interviews_start_time ON interviews_new(start_time);
                    CREATE INDEX IF NOT EXISTS idx_question_order ON interview_questions_new(interview_id, display_order);
                """)
            
            # Commit the transaction
            conn.commit()
            logger.info("New interview tables created successfully")
            return True
            
    except Exception as e:
        logger.error(f"Error updating database schema: {str(e)}")
        return False

if __name__ == "__main__":
    # Run the database update when script is executed directly
    success = update_database_schema()
    if success:
        print("Database schema updated successfully")
    else:
        print("Failed to update database schema")
        exit(1)