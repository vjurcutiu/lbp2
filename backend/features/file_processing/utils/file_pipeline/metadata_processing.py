import os
from flask import current_app
from sqlalchemy import or_
from db.models import File
from text_extraction import extract_text_from_file
from utils.services.ai_api_manager import OpenAIService

aii = OpenAIService()

def truncate_words(text: str, limit: int = 20) -> str:
    words = text.split()
    if len(words) <= limit:
        return text
    return " ".join(words[:limit]) + "..."

def get_files_without_metadata_text():
    files = File.query.filter(or_(File.meta_data.is_(None), File.meta_data == {})).all()
    results = []
    for f in files:
        if os.path.exists(f.file_path):
            contents = extract_text_from_file(f.file_path)
            current_app.logger.debug(
                "Loaded contents for %s: %s",
                f.file_path,
                truncate_words(contents, limit=20)
            )
        else:
            contents = ""
            current_app.logger.warning(f"File not found: {f.file_path}")
        results.append({'filename': f.file_path, 'contents': contents})
    return results

def process_file_for_metadata(f, type='keywords'):
    """
    Process a single file for metadata (keywords or other type).
    """
    meta_key = type
    func = "process_file_for_metadata"
    if os.path.exists(f.file_path):
        text = extract_text_from_file(f.file_path)
        current_app.logger.info(f"[{func}] Processing file: {f.file_path} with text length: {len(text)}")
        if text:
            try:
                if type == 'keywords':
                    api_content = aii.keywords(text)
                else:
                    api_content = aii.chat({
                        'messages': [
                            {'role': 'system', 'content': f'Generate {type} for this document.'},
                            {'role': 'user', 'content': text}
                        ]
                    })
                    current_app.logger.info(f"[{func}] Raw metadata output for {f.file_path}: {api_content}")
                f.meta_data = f.meta_data or {}
                f.meta_data[meta_key] = api_content
                current_app.logger.info(f"[{func}] Metadata saved for {f.file_path}")
                return {'file_path': f.file_path, 'meta_data': api_content}
            except Exception as e:
                current_app.logger.error(
                    f"[{func}] Error processing metadata for {f.file_path}: {e}. Text snippet: {truncate_words(text, limit=20)}",
                    exc_info=True
                )
        else:
            current_app.logger.warning(f"[{func}] Empty text extracted from {f.file_path}")
    else:
        current_app.logger.warning(f"[{func}] File not found: {f.file_path}")
    return None
