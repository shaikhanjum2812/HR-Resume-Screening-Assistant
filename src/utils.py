import PyPDF2
import os
from datetime import datetime
import tempfile

def parse_pdf(file_path):
    """
    Extract text content from a PDF file.
    """
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        raise Exception(f"Failed to parse PDF: {e}")

def save_uploaded_file(uploaded_file):
    """
    Save an uploaded file to a temporary location and return the file path.
    """
    try:
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, f"resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    except Exception as e:
        raise Exception(f"Failed to save uploaded file: {e}")
