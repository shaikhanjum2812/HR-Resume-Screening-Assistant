import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import Database

class Analytics:
    def __init__(self):
        self.db = Database()
    
    def get_evaluation_stats(self, period):
        evaluations = self.db.get_evaluations_by_period(period)
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
    
    def plot_evaluation_trend(self, period):
        evaluations = self.db.get_evaluations_by_period(period)
        df = pd.DataFrame(evaluations, columns=[
            'id', 'job_id', 'resume_name', 'result', 'justification', 
            'evaluation_date', 'job_title'
        ])
        
        df['evaluation_date'] = pd.to_datetime(df['evaluation_date'])
        daily_counts = df.groupby([df['evaluation_date'].dt.date, 'result']).size().unstack(fill_value=0)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_counts.index,
            y=daily_counts['shortlist'] if 'shortlist' in daily_counts.columns else 0,
            name='Shortlisted',
            line=dict(color='green')
        ))
        fig.add_trace(go.Scatter(
            x=daily_counts.index,
            y=daily_counts['reject'] if 'reject' in daily_counts.columns else 0,
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
    
    def plot_job_distribution(self):
        evaluations = self.db.get_evaluations_by_period('month')
        df = pd.DataFrame(evaluations, columns=[
            'id', 'job_id', 'resume_name', 'result', 'justification', 
            'evaluation_date', 'job_title'
        ])
        
        job_stats = df.groupby('job_title')['result'].value_counts().unstack(fill_value=0)
        
        fig = go.Figure(data=[
            go.Bar(name='Shortlisted', 
                  y=job_stats.index, 
                  x=job_stats['shortlist'] if 'shortlist' in job_stats.columns else 0,
                  orientation='h',
                  marker_color='green'),
            go.Bar(name='Rejected', 
                  y=job_stats.index, 
                  x=job_stats['reject'] if 'reject' in job_stats.columns else 0,
                  orientation='h',
                  marker_color='red')
        ])
        
        fig.update_layout(
            title='Evaluation Results by Job Position',
            barmode='stack',
            xaxis_title='Number of Candidates',
            yaxis_title='Job Position',
            height=400 + (len(job_stats) * 30)
        )
        
        return fig
