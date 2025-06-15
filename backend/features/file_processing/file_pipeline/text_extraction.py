import os
from flask import current_app
from PyPDF2 import PdfReader
import docx

def extract_text_from_file(file_path):
    func = "extract_text_from_file"
    _, extension = os.path.splitext(file_path)
    extension = extension.lower()

    current_app.logger.debug(f"[{func}] starting. path={file_path}, ext={extension}")
    if extension in ['.txt', '.md', '.csv']:
        try:
            current_app.logger.debug(f"[{func}] Reading as plain text: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            current_app.logger.debug(f"[{func}] Read {len(text)} characters from text file")
            return text
        except Exception as e:
            current_app.logger.error(f"[{func}] Error reading {file_path}: {e}", exc_info=True)
            return ""

    elif extension == '.pdf':
        try:
            current_app.logger.debug(f"[{func}] Reading PDF: {file_path}")
            reader = PdfReader(file_path)
            text = ""
            current_app.logger.debug(f"[{func}] PDF has {len(reader.pages)} pages")
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text
                    current_app.logger.debug(f"[{func}] Extracted {len(page_text)} chars from page {i}")
                else:
                    current_app.logger.warning(f"[{func}] No text found on page {i} of {file_path}")
            current_app.logger.debug(f"[{func}] Total PDF text length: {len(text)} chars")
            return text
        except Exception as e:
            current_app.logger.error(f"[{func}] Error extracting text from PDF {file_path}: {e}", exc_info=True)
            return ""

    elif extension in ['.doc', '.docx']:
        try:
            current_app.logger.debug(f"[{func}] Reading Word doc: {file_path}")
            doc = docx.Document(file_path)
            full_text = "\n".join([para.text for para in doc.paragraphs])
            current_app.logger.debug(f"[{func}] Extracted {len(full_text)} characters from Word document")
            return full_text
        except Exception as e:
            current_app.logger.error(f"[{func}] Error extracting text from Word document {file_path}: {e}", exc_info=True)
            return ""

    else:
        current_app.logger.warning(f"[{func}] Unsupported file extension: {extension} for file {file_path}")
        return ""
