import PyPDF2
import io

class PDFProcessor:
    def extract_text(self, uploaded_file):
        try:
            # Create a file-like object from the uploaded file
            pdf_file = io.BytesIO(uploaded_file.read())
            
            # Create PDF reader object
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Extract text from all pages
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
        except Exception as e:
            raise Exception(f"Failed to process PDF: {e}")
