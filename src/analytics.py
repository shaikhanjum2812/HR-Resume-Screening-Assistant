import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import Database
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class Analytics:
    def __init__(self):
        try:
            self.db = Database()
            logger.info("Analytics: Database connection initialized")
        except Exception as e:
            logger.error(f"Analytics: Failed to initialize database connection: {e}")
            raise

    def get_evaluation_stats(self, period):
        try:
            evaluations = self.db.get_evaluations_by_period(period)
            if not evaluations:
                logger.info(f"No evaluations found for period: {period}")
                return {
                    'total_evaluations': 0,
                    'shortlisted': 0,
                    'rejection_rate': 0,
                    'avg_experience': 0,
                    'top_skills': [],
                    'education_levels': {}
                }

            # Create DataFrame with all columns from evaluations
            df = pd.DataFrame(evaluations, columns=[
                'id', 'job_id', 'resume_name', 'candidate_name', 'candidate_email',
                'candidate_phone', 'result', 'justification', 'match_score',
                'years_experience_total', 'years_experience_relevant',
                'years_experience_required', 'meets_experience_requirement',
                'evaluation_date', 'evaluation_data', 'job_title'
            ])

            total = len(df)
            shortlisted = len(df[df['result'].str.lower() == 'shortlist'])
            rejection_rate = (total - shortlisted) / total * 100 if total > 0 else 0
            avg_experience = df['years_experience_total'].mean() if not df['years_experience_total'].empty else 0

            return {
                'total_evaluations': total,
                'shortlisted': shortlisted,
                'rejection_rate': rejection_rate,
                'avg_experience': round(avg_experience, 1),
                'top_skills': self._extract_top_skills(df),
                'education_levels': self._extract_education_levels(df)
            }
        except Exception as e:
            logger.error(f"Failed to get evaluation stats: {e}")
            return {
                'total_evaluations': 0,
                'shortlisted': 0,
                'rejection_rate': 0,
                'avg_experience': 0,
                'top_skills': [],
                'education_levels': {}
            }

    def plot_evaluation_trend(self, period):
        try:
            evaluations = self.db.get_evaluations_by_period(period)
            if not evaluations:
                return self._create_empty_figure("Daily Evaluation Trends", 
                                              "Date", "Number of Evaluations")

            # Create DataFrame with all columns
            df = pd.DataFrame(evaluations, columns=[
                'id', 'job_id', 'resume_name', 'candidate_name', 'candidate_email',
                'candidate_phone', 'result', 'justification', 'match_score',
                'years_experience_total', 'years_experience_relevant',
                'years_experience_required', 'meets_experience_requirement',
                'evaluation_date', 'evaluation_data', 'job_title'
            ])

            df['evaluation_date'] = pd.to_datetime(df['evaluation_date'])
            daily_counts = df.groupby([df['evaluation_date'].dt.date, 'result']).size().unstack(fill_value=0)

            fig = go.Figure()

            # Add traces for each status
            for status in daily_counts.columns:
                color = 'green' if status.lower() == 'shortlist' else 'red'
                fig.add_trace(go.Scatter(
                    x=daily_counts.index,
                    y=daily_counts[status],
                    name=status.capitalize(),
                    line=dict(color=color)
                ))

            fig.update_layout(
                title='Daily Evaluation Trends',
                xaxis_title='Date',
                yaxis_title='Number of Evaluations',
                hovermode='x unified',
                showlegend=True,
                template='plotly_dark'
            )

            return fig
        except Exception as e:
            logger.error(f"Failed to plot evaluation trend: {e}")
            return self._create_empty_figure("Error Loading Evaluation Trends", 
                                          "Date", "Number of Evaluations")

    def plot_job_distribution(self):
        try:
            evaluations = self.db.get_evaluations_by_period('month')
            if not evaluations:
                return self._create_empty_figure("Evaluation Results by Job Position",
                                              "Number of Candidates", "Job Position")

            # Create DataFrame with all columns
            df = pd.DataFrame(evaluations, columns=[
                'id', 'job_id', 'resume_name', 'candidate_name', 'candidate_email',
                'candidate_phone', 'result', 'justification', 'match_score',
                'years_experience_total', 'years_experience_relevant',
                'years_experience_required', 'meets_experience_requirement',
                'evaluation_date', 'evaluation_data', 'job_title'
            ])

            job_stats = df.groupby(['job_title', 'result']).size().unstack(fill_value=0)

            fig = go.Figure()

            # Add bars for each status
            for status in job_stats.columns:
                color = 'green' if status.lower() == 'shortlist' else 'red'
                fig.add_trace(go.Bar(
                    name=status.capitalize(),
                    y=job_stats.index,
                    x=job_stats[status],
                    orientation='h',
                    marker_color=color
                ))

            fig.update_layout(
                title='Evaluation Results by Job Position',
                barmode='stack',
                xaxis_title='Number of Candidates',
                yaxis_title='Job Position',
                height=max(400, len(job_stats) * 50),
                template='plotly_dark',
                showlegend=True
            )

            return fig
        except Exception as e:
            logger.error(f"Failed to plot job distribution: {e}")
            return self._create_empty_figure("Error Loading Job Distribution",
                                          "Number of Candidates", "Job Position")

    def plot_experience_distribution(self):
        try:
            evaluations = self.db.get_evaluations_by_period('month')
            if not evaluations:
                return self._create_empty_figure("Experience Distribution",
                                              "Years of Experience", "Number of Candidates")

            df = pd.DataFrame(evaluations, columns=[
                'id', 'job_id', 'resume_name', 'candidate_name', 'candidate_email',
                'candidate_phone', 'result', 'justification', 'match_score',
                'years_experience_total', 'years_experience_relevant',
                'years_experience_required', 'meets_experience_requirement',
                'evaluation_date', 'evaluation_data', 'job_title'
            ])

            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=df['years_experience_total'],
                nbinsx=20,
                name='Total Experience',
                marker_color='lightblue'
            ))

            fig.update_layout(
                title='Experience Distribution of Candidates',
                xaxis_title='Years of Experience',
                yaxis_title='Number of Candidates',
                template='plotly_dark',
                showlegend=True
            )

            return fig
        except Exception as e:
            logger.error(f"Failed to plot experience distribution: {e}")
            return self._create_empty_figure("Error Loading Experience Distribution",
                                          "Years of Experience", "Number of Candidates")

    def _create_empty_figure(self, title, xaxis_title, yaxis_title):
        """Helper method to create empty figures with consistent styling"""
        fig = go.Figure()
        fig.update_layout(
            title=f"{title} (No Data)",
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title,
            template='plotly_dark'
        )
        return fig

    def _extract_top_skills(self, df):
        """Extract top skills from evaluation data"""
        skills = []
        for eval_data in df['evaluation_data']:
            if isinstance(eval_data, str):
                try:
                    data = eval_data.get('key_matches', {}).get('skills', [])
                    if isinstance(data, list):
                        skills.extend(data)
                except:
                    continue

        if not skills:
            return []

        skill_counts = pd.Series(skills).value_counts()
        return skill_counts.head(10).to_dict()

    def _extract_education_levels(self, df):
        """Extract education levels from evaluation data"""
        education_levels = []
        for eval_data in df['evaluation_data']:
            if isinstance(eval_data, str):
                try:
                    data = eval_data.get('candidate_info', {}).get('education', '')
                    if data:
                        education_levels.append(data)
                except:
                    continue

        if not education_levels:
            return {}

        edu_counts = pd.Series(education_levels).value_counts()
        return edu_counts.to_dict()