import os
from db.models import db, File
from utils.pinecone_client import PineconeClient
from sqlalchemy import or_
from flask import current_app
import logging

# Use the new AI API manager wrapper
from utils.services.ai_api_manager import OpenAIService

# Instantiate service once for reuse
aii = OpenAIService()

def truncate_words(text: str, limit: int = 20) -> str:
    """
    Return at most the first `limit` words of `text`,
    joined by spaces, and append "..." if truncated.
    """
    words = text.split()
    if len(words) <= limit:
        return text
    return " ".join(words[:limit]) + "..."


def scan_and_add_files(path, extension, conversation_id=None, progress_callback=None):
    added_files = []
    skipped_files = []
    total_files = 0
    processed_files = 0

    # First pass to count files
    if os.path.isfile(path):
        total_files = 1
    elif os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            total_files += len([f for f in files if f.lower().endswith(extension.lower())])

    def update_progress():
        nonlocal processed_files
        processed_files += 1
        if progress_callback and total_files > 0:
            progress = int((processed_files / total_files) * 100)
            progress_callback(progress)

    if os.path.isfile(path):
        # Process a single file
        if path.lower().endswith(extension.lower()):
            full_path = os.path.abspath(path)
            existing_file = File.query.filter_by(file_path=full_path).first()
            if existing_file:
                skipped_files.append(full_path)
            else:
                _, file_ext = os.path.splitext(full_path)
                new_file = File(
                    file_path=full_path,
                    file_extension=file_ext,
                    conversation_id=conversation_id,
                    is_uploaded=False,
                    meta_data=None
                )
                db.session.add(new_file)
                added_files.append(full_path)
    elif os.path.isdir(path):
        # Process all files in the directory
        for root, dirs, files in os.walk(path):
            for filename in files:
                if filename.lower().endswith(extension.lower()):
                    full_path = os.path.join(root, filename)
                    existing_file = File.query.filter_by(file_path=full_path).first()
                    if existing_file:
                        skipped_files.append(full_path)
                        continue

                    _, file_ext = os.path.splitext(filename)
                    new_file = File(
                        file_path=full_path,
                        file_extension=file_ext,
                        conversation_id=conversation_id,
                        is_uploaded=False,
                        meta_data=None
                    )
                    db.session.add(new_file)
                    added_files.append(full_path)
    else:
        raise Exception("Invalid path provided.")

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Database error: {e}")

    return {
        'added': added_files,
        'skipped': skipped_files
    }


def scan_and_add_files_wrapper(paths, extension, conversation_id=None, progress_callback=None):
    """
    A wrapper to allow scan_and_add_files to accept either a single file/folder path or a list of paths.
    """
    if isinstance(paths, list):
        aggregated_results = {'added': [], 'skipped': []}
        for path in paths:
            result = scan_and_add_files(path, extension, conversation_id, progress_callback)
            aggregated_results['added'].extend(result.get('added', []))
            aggregated_results['skipped'].extend(result.get('skipped', []))
        return aggregated_results
    else:
        return scan_and_add_files(paths, extension, conversation_id, progress_callback)


def extract_text_from_file(file_path):
    _, extension = os.path.splitext(file_path)
    extension = extension.lower()

    if extension in ['.txt', '.md', '.csv']:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            current_app.logger.error(f"Error reading {file_path}: {e}")
            return ""
    elif extension == '.pdf':
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        except Exception as e:
            current_app.logger.error(f"Error extracting text from PDF {file_path}: {e}")
            return ""
    elif extension in ['.doc', '.docx']:
        try:
            import docx
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            current_app.logger.error(f"Error extracting text from Word document {file_path}: {e}")
            return ""
    else:
        current_app.logger.warning(f"Unsupported file extension: {extension} for file {file_path}")
        return ""


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


def process_files_for_metadata(type='keywords', progress_callback=None):
    meta_key = type
    current_app.logger.info(f"meta_key: {meta_key}")
    try:
        all_files = File.query.all()
        to_process = [f for f in all_files if f.meta_data is None or (isinstance(f.meta_data, dict) and meta_key not in f.meta_data)]
    except Exception as e:
        current_app.logger.error(f"Error querying files: {e}")
        raise

    results = []
    total = len(to_process)
    count = 0
    for f in to_process:
        if os.path.exists(f.file_path):
            text = extract_text_from_file(f.file_path)
            if text:
                try:
                    # Use manager wrapper for metadata
                    if type == 'keywords':
                        api_content = aii.keywords(text)
                    else:
                        # fallback to generic chat
                        api_content = aii.chat({
                            'messages': [
                                {'role': 'system', 'content': f'Generate {type} for this document.'},
                                {'role': 'user', 'content': text}
                            ]
                        })
                    f.meta_data = f.meta_data or {}
                    f.meta_data[meta_key] = api_content
                    results.append({'file_path': f.file_path, 'meta_data': api_content})
                except Exception as e:
                    current_app.logger.error(
                        "Error processing metadata for %s: %s. Text snippet: %s",
                        f.file_path,
                        e,
                        truncate_words(text, limit=20)
                    )
        else:
            current_app.logger.warning(f"File not found: {f.file_path}")
        count += 1
        if progress_callback:
            progress_callback(count, total)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error committing metadata: {e}")
    return results


def upsert_files_to_vector_db(progress_callback=None):
    """
    Upserts embeddings for files with metadata to Pinecone and marks them uploaded.
    """
    to_upsert = File.query.filter(File.meta_data.isnot(None), File.is_uploaded == False).all()
    current_app.logger.info(f"Files to upsert: {[f.file_path for f in to_upsert]}")
    results = []
    total = len(to_upsert)
    count = 0
    namespace = os.getenv('PINECONE_NAMESPACE')

    client = PineconeClient()

    for f in to_upsert:
        if os.path.exists(f.file_path):
            text = extract_text_from_file(f.file_path)
            if text:
                retrieval = f"Represent this document for searching relevant passages: {text}"
                try:
                    # Use manager for embeddings
                    embeddings = aii.embeddings(retrieval)
                    if embeddings:
                        record = {
                            'id': str(f.id),
                            'values': embeddings,
                            'metadata': {'source_text': text,
                                         'keywords': f.meta_data.get('keywords', [])}
                        }
                        vc_resp = client.upsert(vectors=[record], namespace=namespace)
                        f.is_uploaded = True
                        results.append({'file_path': f.file_path, 'vector_response': vc_resp})
                    else:
                        current_app.logger.error(f"No embeddings for {f.file_path}")
                except Exception as e:
                    current_app.logger.error(f"Error upserting {f.file_path}: {e}")
        else:
            current_app.logger.warning(f"File not found: {f.file_path}")
        count += 1
        if progress_callback:
            progress_callback(count, total)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error committing vector upload flags: {e}")

    return results
