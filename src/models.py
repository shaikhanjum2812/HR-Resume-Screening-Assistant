from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base, SessionLocal
from datetime import datetime

class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    department = Column(String)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    resumes = relationship("Resume", back_populates="job")

    @classmethod
    def create(cls, title, department, description):
        db = SessionLocal()
        db_job = cls(title=title, department=department, description=description)
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        db.close()
        return db_job

    @classmethod
    def get_all(cls):
        db = SessionLocal()
        jobs = db.query(cls).all()
        db.close()
        return jobs

    @classmethod
    def get_by_id(cls, job_id):
        db = SessionLocal()
        job = db.query(cls).filter(cls.id == job_id).first()
        db.close()
        return job

    @classmethod
    def delete(cls, job_id):
        db = SessionLocal()
        job = db.query(cls).filter(cls.id == job_id).first()
        if job:
            db.delete(job)
            db.commit()
        db.close()

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    candidate_name = Column(String)
    job_id = Column(Integer, ForeignKey("job_descriptions.id"))
    resume_text = Column(Text)
    evaluation_result = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("JobDescription", back_populates="resumes")

    @classmethod
    def create(cls, candidate_name, job_id, resume_text, evaluation_result):
        db = SessionLocal()
        db_resume = cls(
            candidate_name=candidate_name,
            job_id=job_id,
            resume_text=resume_text,
            evaluation_result=evaluation_result
        )
        db.add(db_resume)
        db.commit()
        db.refresh(db_resume)
        db.close()
        return db_resume

    @classmethod
    def get_evaluation_summary(cls):
        db = SessionLocal()
        resumes = db.query(cls).all()
        summary = []
        for resume in resumes:
            summary.append({
                'candidate': resume.candidate_name,
                'job': resume.job.title,
                'decision': resume.evaluation_result.get('decision'),
                'score': resume.evaluation_result.get('score'),
                'date': resume.created_at
            })
        db.close()
        return summary

    @classmethod
    def get_department_analysis(cls):
        db = SessionLocal()
        results = db.query(
            JobDescription.department,
            func.count(Resume.id).label('total_resumes'),
            func.sum(case(
                [(Resume.evaluation_result['decision'].astext == 'shortlisted', 1)],
                else_=0
            )).label('shortlisted')
        ).join(Resume).group_by(JobDescription.department).all()
        db.close()
        return results
