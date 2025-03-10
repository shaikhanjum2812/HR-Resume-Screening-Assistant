import PyPDF2
import os
from datetime import datetime
import tempfile
from docx import Document

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

def parse_docx(file_path):
    """
    Extract text content from a DOCX file.
    """
    try:
        doc = Document(file_path)
        text = []
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        return '\n'.join(text)
    except Exception as e:
        raise Exception(f"Failed to parse DOCX: {e}")

def save_uploaded_file(uploaded_file):
    """
    Save an uploaded file to a temporary location and return the file path.
    """
    try:
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, f"jd_{datetime.now().strftime('%Y%m%d_%H%M%S')}{os.path.splitext(uploaded_file.name)[1]}")
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    except Exception as e:
        raise Exception(f"Failed to save uploaded file: {e}")

def extract_text_from_upload(uploaded_file):
    """
    Extract text from an uploaded file (supports PDF, DOCX, and text files).
    """
    try:
        if uploaded_file.type == "application/pdf":
            # Save PDF temporarily and extract text
            file_path = save_uploaded_file(uploaded_file)
            text = parse_pdf(file_path)
            os.remove(file_path)  # Clean up temporary file
            return text
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            # Save DOCX temporarily and extract text
            file_path = save_uploaded_file(uploaded_file)
            text = parse_docx(file_path)
            os.remove(file_path)  # Clean up temporary file
            return text
        elif uploaded_file.type == "text/plain":
            # Read text file directly
            return uploaded_file.getvalue().decode("utf-8")
        else:
            raise ValueError("Unsupported file type. Please upload a PDF, DOCX, or text file.")
    except Exception as e:
        raise Exception(f"Failed to extract text from file: {e}")