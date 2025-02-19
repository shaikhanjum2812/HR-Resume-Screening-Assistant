import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

def generate_evaluation_report(evaluation_data, resume_name):
    """Generate a PDF report from evaluation data"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    # Collect the elements that will make up our document
    elements = []
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    
    section_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        spaceBefore=20
    )
    
    # Add title
    elements.append(Paragraph("Resume Evaluation Report", title_style))
    elements.append(Paragraph(f"Resume: {resume_name}", styles["Heading2"]))
    elements.append(Spacer(1, 20))

    # Add evaluation date
    elements.append(Paragraph(
        f"Evaluation Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 20))

    # Candidate Information Section
    elements.append(Paragraph("Candidate Information", section_style))
    candidate_info = evaluation_data.get('candidate_info', {})
    candidate_data = [
        ["Name:", candidate_info.get('name', 'Not provided')],
        ["Email:", candidate_info.get('email', 'Not provided')],
        ["Phone:", candidate_info.get('phone', 'Not provided')],
        ["Location:", candidate_info.get('location', 'Not provided')],
        ["LinkedIn:", candidate_info.get('linkedin', 'Not provided')]
    ]
    
    candidate_table = Table(candidate_data, colWidths=[1.5*inch, 4*inch])
    candidate_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(candidate_table)
    elements.append(Spacer(1, 20))

    # Evaluation Results Section
    elements.append(Paragraph("Evaluation Results", section_style))
    decision = evaluation_data.get('decision', 'NOT PROVIDED')
    elements.append(Paragraph(f"Decision: {decision}", styles["Heading3"]))
    elements.append(Paragraph(
        f"Match Score: {float(evaluation_data.get('match_score', 0))*100:.1f}%",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 10))
    
    # Justification
    elements.append(Paragraph("Justification:", styles["Heading3"]))
    elements.append(Paragraph(
        evaluation_data.get('justification', 'No justification provided'),
        styles["Normal"]
    ))
    elements.append(Spacer(1, 20))

    # Experience Analysis Section
    elements.append(Paragraph("Experience Analysis", section_style))
    exp_data = evaluation_data.get('years_of_experience', {})
    experience_data = [
        ["Total Experience:", f"{exp_data.get('total', 0)} years"],
        ["Relevant Experience:", f"{exp_data.get('relevant', 0)} years"],
        ["Required Experience:", f"{exp_data.get('required', 0)} years"],
        ["Meets Requirement:", "Yes" if exp_data.get('meets_requirement', False) else "No"]
    ]
    
    exp_table = Table(experience_data, colWidths=[2*inch, 3.5*inch])
    exp_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(exp_table)
    elements.append(Spacer(1, 10))

    # Key Matches Section
    elements.append(Paragraph("Key Matches & Missing Requirements", section_style))
    key_matches = evaluation_data.get('key_matches', {})
    if isinstance(key_matches, dict) and 'skills' in key_matches:
        elements.append(Paragraph("Matching Skills:", styles["Heading3"]))
        for skill in key_matches['skills']:
            elements.append(Paragraph(f"• {skill}", styles["Normal"]))
    
    elements.append(Spacer(1, 10))
    missing_reqs = evaluation_data.get('missing_requirements', [])
    if missing_reqs:
        elements.append(Paragraph("Missing Requirements:", styles["Heading3"]))
        for req in missing_reqs:
            elements.append(Paragraph(f"• {req}", styles["Normal"]))

    # Build the PDF document
    doc.build(elements)
    buffer.seek(0)
    return buffer
