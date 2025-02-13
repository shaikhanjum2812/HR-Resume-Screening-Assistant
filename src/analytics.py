import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import Database
import logging

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
                    'rejection_rate': 0
                }

            df = pd.DataFrame(evaluations, columns=[
                'id', 'job_id', 'resume_name', 'result', 'justification', 
                'evaluation_date', 'job_title'
            ])

            total = len(df)
            shortlisted = len(df[df['result'] == 'shortlist'])
            rejection_rate = (total - shortlisted) / total * 100 if total > 0 else 0

            return {
                'total_evaluations': total,
                'shortlisted': shortlisted,
                'rejection_rate': rejection_rate
            }
        except Exception as e:
            logger.error(f"Failed to get evaluation stats: {e}")
            return {
                'total_evaluations': 0,
                'shortlisted': 0,
                'rejection_rate': 0
            }

    def plot_evaluation_trend(self, period):
        try:
            evaluations = self.db.get_evaluations_by_period(period)
            if not evaluations:
                # Return empty figure if no data
                fig = go.Figure()
                fig.update_layout(
                    title='Daily Evaluation Trends (No Data)',
                    xaxis_title='Date',
                    yaxis_title='Number of Evaluations'
                )
                return fig

            df = pd.DataFrame(evaluations, columns=[
                'id', 'job_id', 'resume_name', 'result', 'justification', 
                'evaluation_date', 'job_title'
            ])

            df['evaluation_date'] = pd.to_datetime(df['evaluation_date'])
            daily_counts = df.groupby([df['evaluation_date'].dt.date, 'result']).size().unstack(fill_value=0)

            fig = go.Figure()
            if 'shortlist' in daily_counts.columns:
                fig.add_trace(go.Scatter(
                    x=daily_counts.index,
                    y=daily_counts['shortlist'],
                    name='Shortlisted',
                    line=dict(color='green')
                ))

            if 'reject' in daily_counts.columns:
                fig.add_trace(go.Scatter(
                    x=daily_counts.index,
                    y=daily_counts['reject'],
                    name='Rejected',
                    line=dict(color='red')
                ))

            fig.update_layout(
                title='Daily Evaluation Trends',
                xaxis_title='Date',
                yaxis_title='Number of Evaluations',
                hovermode='x unified'
            )

            return fig
        except Exception as e:
            logger.error(f"Failed to plot evaluation trend: {e}")
            fig = go.Figure()
            fig.update_layout(
                title='Error Loading Evaluation Trends',
                xaxis_title='Date',
                yaxis_title='Number of Evaluations'
            )
            return fig

    def plot_job_distribution(self):
        try:
            evaluations = self.db.get_evaluations_by_period('month')
            if not evaluations:
                # Return empty figure if no data
                fig = go.Figure()
                fig.update_layout(
                    title='Evaluation Results by Job Position (No Data)',
                    xaxis_title='Number of Candidates',
                    yaxis_title='Job Position'
                )
                return fig

            df = pd.DataFrame(evaluations, columns=[
                'id', 'job_id', 'resume_name', 'result', 'justification', 
                'evaluation_date', 'job_title'
            ])

            job_stats = df.groupby('job_title')['result'].value_counts().unstack(fill_value=0)

            fig = go.Figure(data=[
                go.Bar(name='Shortlisted', 
                      y=job_stats.index, 
                      x=job_stats['shortlist'] if 'shortlist' in job_stats.columns else [0] * len(job_stats),
                      orientation='h',
                      marker_color='green'),
                go.Bar(name='Rejected', 
                      y=job_stats.index, 
                      x=job_stats['reject'] if 'reject' in job_stats.columns else [0] * len(job_stats),
                      orientation='h',
                      marker_color='red')
            ])

            fig.update_layout(
                title='Evaluation Results by Job Position',
                barmode='stack',
                xaxis_title='Number of Candidates',
                yaxis_title='Job Position',
                height=max(400, len(job_stats) * 30)
            )

            return fig
        except Exception as e:
            logger.error(f"Failed to plot job distribution: {e}")
            fig = go.Figure()
            fig.update_layout(
                title='Error Loading Job Distribution',
                xaxis_title='Number of Candidates',
                yaxis_title='Job Position'
            )
            return fig