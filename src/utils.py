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
    Extract text from an uploaded file (supports various file types).
    """
    try:
        # Get the file extension and mime type
        file_extension = os.path.splitext(uploaded_file.name)[1].lower() if uploaded_file.name else ""
        mime_type = uploaded_file.type if hasattr(uploaded_file, 'type') else ""
        
        # Try to process based on mime type first
        if mime_type == "application/pdf" or file_extension == ".pdf":
            # Save PDF temporarily and extract text
            file_path = save_uploaded_file(uploaded_file)
            try:
                text = parse_pdf(file_path)
            except Exception as e:
                # If parsing fails, return a placeholder
                text = f"[PDF Content - Unable to extract text: {str(e)}]"
            finally:
                os.remove(file_path)  # Clean up temporary file
            return text
            
        elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or file_extension == ".docx":
            # Save DOCX temporarily and extract text
            file_path = save_uploaded_file(uploaded_file)
            try:
                text = parse_docx(file_path)
            except Exception as e:
                # If parsing fails, return a placeholder
                text = f"[DOCX Content - Unable to extract text: {str(e)}]"
            finally:
                os.remove(file_path)  # Clean up temporary file
            return text
            
        elif mime_type == "text/plain" or file_extension in [".txt", ".csv", ".md", ".json"]:
            # Read text file directly
            try:
                return uploaded_file.getvalue().decode("utf-8")
            except UnicodeDecodeError:
                # Try with different encodings
                try:
                    return uploaded_file.getvalue().decode("latin-1")
                except:
                    return "[Text Content - Unable to decode with supported encodings]"
                    
        else:
            # For unsupported file types, save and try to extract anyway
            try:
                # First try as PDF
                file_path = save_uploaded_file(uploaded_file)
                try:
                    text = parse_pdf(file_path)
                    return text
                except:
                    # If not PDF, try as DOCX
                    try:
                        text = parse_docx(file_path)
                        return text
                    except:
                        # If both fail, return file info
                        return f"[Uploaded file: {uploaded_file.name} ({mime_type}) - Unable to extract text content]"
                finally:
                    os.remove(file_path)  # Clean up temporary file
            except:
                return f"[Uploaded file: {uploaded_file.name} - Unable to process]"
    except Exception as e:
        raise Exception(f"Failed to extract text from file: {e}")