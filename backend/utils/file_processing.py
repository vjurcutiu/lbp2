import os
from db.models import db, File
from utils.pinecone_client import PineconeClient
from sqlalchemy import or_
from flask import current_app
import logging
from PyPDF2 import PdfReader
import docx

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


def scan_and_add_files(path, extensions, conversation_id=None, progress_callback=None):
    added_files = []
    skipped_files = []
    total_files = 0
    processed_files = 0

    # Normalize extensions to a list of lowercase strings
    if isinstance(extensions, str):
        extensions = [extensions]
    exts = [ext.lower() for ext in extensions]

    # First pass to count files matching any of the exts
    if os.path.isfile(path):
        total_files = 1 if any(path.lower().endswith(ext) for ext in exts) else 0
    elif os.path.isdir(path):
        for _, _, files in os.walk(path):
            total_files += sum(1 for f in files if any(f.lower().endswith(ext) for ext in exts))


    def update_progress():
        nonlocal processed_files
        processed_files += 1
        if progress_callback and total_files > 0:
            progress = int((processed_files / total_files) * 100)
            progress_callback(progress)

    if os.path.isfile(path) and any(path.lower().endswith(ext) for ext in exts):
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
        # Process all files in the directory matching any ext
        for root, dirs, files in os.walk(path):
            for filename in files:
                if not any(filename.lower().endswith(ext) for ext in exts):
                    continue
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
    func = "process_files_for_metadata"
    current_app.logger.info(f"[{func}] meta_key: {meta_key}")
    try:
        all_files = File.query.all()
        to_process = [f for f in all_files if f.meta_data is None or (isinstance(f.meta_data, dict) and meta_key not in f.meta_data)]
        current_app.logger.info(f"[{func}] Found {len(to_process)} files to process")
    except Exception as e:
        current_app.logger.error(f"[{func}] Error querying files: {e}")
        raise

    results = []
    total = len(to_process)
    count = 0
    for f in to_process:
        if os.path.exists(f.file_path):
            text = extract_text_from_file(f.file_path)
            current_app.logger.info(f"[{func}] Processing file: {f.file_path} with text length: {len(text)}")
            if text:
                try:
                    if type == 'keywords':
                        api_content = aii.keywords(text)
                        current_app.logger.info(f"[{func}] Raw keywords output for {f.file_path}: {api_content}")
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
                    results.append({'file_path': f.file_path, 'meta_data': api_content})
                    current_app.logger.info(f"[{func}] Metadata saved for {f.file_path}")
                except Exception as e:
                    current_app.logger.error(
                        f"[{func}] Error processing metadata for {f.file_path}: {e}. Text snippet: {truncate_words(text, limit=20)}",
                        exc_info=True
                    )
            else:
                current_app.logger.warning(f"[{func}] Empty text extracted from {f.file_path}")
        else:
            current_app.logger.warning(f"[{func}] File not found: {f.file_path}")
        count += 1
        if progress_callback:
            progress_callback(count, total)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[{func}] Error committing metadata: {e}")
    return results

def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 400) -> list[str]:
    """
    Splits `text` into chunks of up to `chunk_size` characters with `overlap` characters between chunks.
    Returns a list of text chunks.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and less than chunk_size")

    chunks = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunks.append(text[start:end])
        # advance start by chunk_size minus overlap
        start += chunk_size - overlap
    return chunks


import json

def flatten_values(data):
    """
    Recursively extract all values from nested dicts and lists into a flat list.
    """
    values = []
    if isinstance(data, dict):
        for v in data.values():
            values.extend(flatten_values(v))
    elif isinstance(data, list):
        for item in data:
            values.extend(flatten_values(item))
    else:
        values.append(data)
    return values

def upsert_files_to_vector_db(chunk_size: int = 1500,
                              overlap: int = 200,
                              progress_callback=None):
    """
    Upserts embeddings for files with metadata to Pinecone in text chunks and marks them uploaded.

    Each file is split into overlapping chunks by character count, then each chunk is embedded and upserted.
    """
    to_upsert = File.query.filter(File.meta_data.isnot(None), File.is_uploaded == False).all()
    current_app.logger.info(f"Files to upsert: {[f.file_path for f in to_upsert]}")
    results = []
    total = len(to_upsert)
    count = 0
    namespace = os.getenv('PINECONE_NAMESPACE')

    client = PineconeClient()

    for f in to_upsert:
        if not os.path.exists(f.file_path):
            current_app.logger.warning(f"File not found: {f.file_path}")
            count += 1
            if progress_callback:
                progress_callback(count, total)
            continue

        text = extract_text_from_file(f.file_path)
        if not text:
            current_app.logger.error(f"No text extracted from {f.file_path}")
            count += 1
            if progress_callback:
                progress_callback(count, total)
            continue

        chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        current_app.logger.info(f"Split {f.file_path} into {len(chunks)} chunks")

        # Prepare metadata to include keywords and other file metadata if available
        file_metadata = f.meta_data if isinstance(f.meta_data, dict) else {}

        # Flatten all relevant metadata values into keywords list
        raw_keywords = []

        # Keys to extract values from, excluding 'cuvinte_cheie'
        keys_to_extract = ['locatie', 'data', 'domeniu', 'hotarare', 'keywords']

        for key in keys_to_extract:
            val = file_metadata.get(key)
            current_app.logger.info(f"[file_processing.upsert_files_to_vector_db] Processing metadata key '{key}': {val}")
            if val:
                # If val is a string that looks like JSON, parse it
                if isinstance(val, str):
                    try:
                        parsed_val = json.loads(val)
                        current_app.logger.info(f"[file_processing.upsert_files_to_vector_db] Parsed JSON string for key '{key}': {parsed_val}")
                        val = parsed_val
                    except Exception:
                        # Not a JSON string, keep as is
                        pass
                # Flatten values recursively
                flattened = flatten_values(val)
                current_app.logger.info(f"[file_processing.upsert_files_to_vector_db] Flattened values for key '{key}': {flattened}")
                raw_keywords.extend(flattened)

        # Deduplicate and normalize keywords
        unique_keywords = list({str(k).lower() for k in raw_keywords if k})

        for idx, chunk in enumerate(chunks):
            prompt = f"Represent this document chunk for searching relevant passages: {chunk}"
            try:
                # Use public embeddings method
                embeddings = aii.embeddings(prompt)
                record = {
                    'id': f"{f.id}_chunk_{idx}",
                    'values': embeddings,
                    'metadata': {
                        'source_text': chunk,
                        'source_file': f.file_path,
                        'chunk_index': idx,
                        'text_snippet': chunk[:100],
                        'keywords': unique_keywords
                    }
                }
                current_app.logger.info(f"[file_processing.upsert_files_to_vector_db] Upserting chunk {idx} of file {f.file_path} with metadata keywords: {unique_keywords}")
                vc_resp = client.upsert([record], namespace)
                results.append({'file_path': f.file_path, 'chunk': idx, 'vector_response': vc_resp})
            except Exception as e:
                current_app.logger.error(f"Error upserting chunk {idx} of {f.file_path}: {e}", exc_info=True)

        # After all chunks upserted, mark file as uploaded
        f.is_uploaded = True
        count += 1
        if progress_callback:
            progress_callback(count, total)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error committing vector upload flags: {e}")

    return results
