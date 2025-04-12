import os
from db.models import db, File
from utils.ai_apis import send_to_api, openai_api_logic  # You can swap out openai_api_logic with another API function as needed
from utils.vector_apis import send_to_vector_db, pinecone_vector_logic
from sqlalchemy import or_
from flask import current_app
import logging

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
                    metadata=None
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
                        metadata=None
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

# Modified helper to support list inputs
def scan_and_add_files_wrapper(paths, extension, conversation_id=None, progress_callback=None):
    """
    A wrapper to allow scan_and_add_files to accept either a single file/folder path or a list of paths.
    
    Args:
      paths (str or list[str]): A single path or a list of paths.
      extension (str): The file extension filter.
      conversation_id (optional): An optional conversation ID.
      progress_callback (optional): A callback function for progress updates.
    
    Returns:
      dict: A dictionary containing 'added' and 'skipped' files aggregated across all inputs.
    """
    # Check if paths is a list.
    if isinstance(paths, list):
        # Initialize aggregated result lists.
        aggregated_results = {
            'added': [],
            'skipped': []
        }
        for path in paths:
            # Process each file/folder separately.
            result = scan_and_add_files(path, extension, conversation_id, progress_callback)
            aggregated_results['added'].extend(result.get('added', []))
            aggregated_results['skipped'].extend(result.get('skipped', []))
        return aggregated_results
    else:
        # Single path provided, so process normally.
        return scan_and_add_files(paths, extension, conversation_id, progress_callback)

def extract_text_from_file(file_path):
    """
    Extracts text content from a file based on its file extension.
    
    Supported formats include:
      - Plain text files (.txt, .md, .csv)
      - PDF files (.pdf) using PyPDF2
      - Word documents (.docx, .doc) using python-docx
    
    For unsupported file types, an empty string is returned.
    
    Args:
        file_path (str): The path to the file.
    
    Returns:
        str: The extracted text content, or an empty string if extraction fails or if the format is unsupported.
    """
    # Get the file extension in lower case
    _, extension = os.path.splitext(file_path)
    extension = extension.lower()

    if extension in ['.txt', '.md', '.csv']:
        # For plain text, markdown, or CSV files, read the file as text.
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return ""
    
    elif extension == '.pdf':
        # For PDFs, use PyPDF2 to extract text.
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                # Some PDFs might have pages with no extractable text.
                page_text = page.extract_text() or ""
                text += page_text
            return text
        except Exception as e:
            print(f"Error extracting text from PDF {file_path}: {e}")
            return ""
    
    elif extension in ['.doc', '.docx']:
        # For Word documents, use python-docx.
        try:
            import docx
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        except Exception as e:
            print(f"Error extracting text from Word document {file_path}: {e}")
            return ""
    
    else:
        # If the file format is not supported, log a message and return an empty string.
        print(f"Unsupported file extension: {extension} for file {file_path}")
        return ""

def get_files_without_metadata_text():
    """
    Checks the database for files that have no metadata.
    For each such file, it extracts text from the file and returns a list of dictionaries,
    each containing the filename and its contents.
    
    Returns:
        list[dict]: A list of dictionaries where each dictionary has:
            - 'filename': The file's path.
            - 'contents': The text extracted from the file.
    """
    # Query for files that have no metadata.
    files_without_metadata = File.query.filter(
        or_(File.meta_data.is_(None), File.meta_data == {})
        ).all()
    
    results = []
    for file_entry in files_without_metadata:
        if os.path.exists(file_entry.file_path):
            file_text = extract_text_from_file(file_entry.file_path)
        else:
            file_text = ""
            print(f"File not found: {file_entry.file_path}")
        
        results.append({
            'filename': file_entry.file_path,
            'contents': file_text
        })
    
    return results

def process_files_for_metadata(type='keywords', progress_callback=None):
    """
    Processes files one-by-one for metadata generation. For each file that either has
    no metadata or is missing the metadata key (specified by 'type'), this function:
      - Extracts text from the file.
      - Sends the text to an API (using the provided AI API logic).
      - Stores the API response under the metadata key.
    
    After processing each file, if a progress_callback is provided, it is called with:
         progress_callback(processed_files, total_files)
    so that the caller can update overall progress accordingly.
    
    Returns:
        list[dict]: Results for each processed file.
    """
    # Use the 'type' parameter as the metadata key.
    meta_key = type
    current_app.logger.info(f"meta_key: {meta_key}")
    
    try:
        all_files = File.query.all()
        current_app.logger.info(f"Total files retrieved: {len(all_files)}")
        # Filter out files that already have metadata for this key.
        files_to_process = [
            file_entry for file_entry in all_files
            if (file_entry.meta_data is None) or 
               (isinstance(file_entry.meta_data, dict) and meta_key not in file_entry.meta_data)
        ]
        current_app.logger.info(f"Files to process for metadata: {[f.file_path for f in files_to_process]}")
    except Exception as e:
        current_app.logger.error("Error during query: %s", e)
        raise

    results = []
    total_files = len(files_to_process)
    processed_count = 0

    for file_entry in files_to_process:
        if os.path.exists(file_entry.file_path):
            file_text = extract_text_from_file(file_entry.file_path)
            if file_text:
                try:
                    # Send file text to API to get metadata (using the AI API logic)
                    api_response = send_to_api(file_text, openai_api_logic, purpose=type)
                    if api_response is not None:
                        # Initialize metadata field if necessary.
                        if file_entry.meta_data is None:
                            file_entry.meta_data = {}
                        file_entry.meta_data[meta_key] = api_response.content
                        results.append({
                            "file_path": file_entry.file_path,
                            "meta_data": api_response.content
                        })
                except Exception as e:
                    current_app.logger.error(f"Error processing metadata for {file_entry.file_path}: {e}")
        else:
            current_app.logger.warning(f"File not found: {file_entry.file_path}")

        processed_count += 1
        # Call the progress callback with the current count and total files for this phase.
        if progress_callback:
            progress_callback(processed_count, total_files)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating database: {e}")

    return results


def upsert_files_to_vector_db(progress_callback=None):
    """
    Processes files one-by-one for vector upsert. For every file that has metadata but has not
    been uploaded to the vector database (is_uploaded == False), this function:
      - Extracts the file text.
      - Generates embeddings (via an AI API using retrieval-optimized formatting).
      - Upserts the embeddings to the vector database.
      - Marks the file as uploaded.
    
    After processing each file, if a progress_callback is provided, it is called with:
         progress_callback(processed_files, total_files)
    so that the calling route can update overall progress accordingly.
    
    Returns:
        list[dict]: Results for each successfully processed file.
    """
    files_to_upsert = File.query.filter(File.meta_data.isnot(None), File.is_uploaded == False).all()
    current_app.logger.info('Files to upsert: ' + str([f.file_path for f in files_to_upsert]))
    results = []
    total_files = len(files_to_upsert)
    processed_count = 0

    for file_entry in files_to_upsert:
        if os.path.exists(file_entry.file_path):
            file_text = extract_text_from_file(file_entry.file_path)
            if file_text:
                # Prepare the text in a retrieval-friendly format.
                retrieval_text = f"Represent this document for searching relevant passages: {file_text}"
                try:
                    api_response = send_to_api(retrieval_text, openai_api_logic, purpose='embeddings')
                    if api_response is not None:
                        embeddings = api_response
                        if embeddings:
                            # Upsert the embeddings to the vector database.
                            vector_response = send_to_vector_db(embeddings, pinecone_vector_logic, filetext=file_text)
                            if vector_response is not None:
                                # Mark the file as uploaded so it won't be reprocessed.
                                file_entry.is_uploaded = True
                                results.append({
                                    "file_path": file_entry.file_path,
                                    "vector_response": str(vector_response)
                                })
                            else:
                                current_app.logger.error(f"Failed to upsert embeddings for {file_entry.file_path}")
                        else:
                            current_app.logger.error(f"No embeddings returned for {file_entry.file_path}")
                except Exception as e:
                    current_app.logger.error(f"Error during vector upsert for {file_entry.file_path}: {e}")
            else:
                current_app.logger.error(f"No usable text for embeddings for {file_entry.file_path}")
        else:
            current_app.logger.error(f"File not found: {file_entry.file_path}")

        processed_count += 1
        # Call the progress callback for each processed file in this phase.
        if progress_callback:
            progress_callback(processed_count, total_files)
            
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating database: {e}")

    return results
