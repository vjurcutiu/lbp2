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

def process_files_for_metadata(type='keywords'):
    """
    Retrieves files from the database that need metadata generation,
    extracts text from them, and sends them to an API for metadata generation.
    
    For each file, if its meta_data does not have a key equal to the passed `type`
    value (or if meta_data is None), it processes the file and stores the API response 
    under that key.
    
    Returns:
        list[dict]: A list of results from the API for each processed file.
    """
    # Use the 'type' parameter as the metadata key.
    meta_key = type  # You can also map values if needed.
    current_app.logger.info(f"meta_key: {meta_key}")

    try:
        # Retrieve all files from the database.
        all_files = File.query.all()
        current_app.logger.info(f"Total files retrieved: {len(all_files)}")
        
        # Filter in Python for files where meta_data is None or does not contain meta_key.
        files_to_process = [
            file_entry for file_entry in all_files
            if (file_entry.meta_data is None) or 
               (isinstance(file_entry.meta_data, dict) and meta_key not in file_entry.meta_data)
        ]
        current_app.logger.info(f"Files to process: {files_to_process}")
    except Exception as e:
        current_app.logger.error("Error during query: %s", e)
        raise

    results = []
    for file_entry in files_to_process:
        if os.path.exists(file_entry.file_path):
            file_text = extract_text_from_file(file_entry.file_path)
            if file_text:
                # Send file_text to the API using the interface layer, using type as the purpose.
                api_response = send_to_api(file_text, openai_api_logic, purpose=type)
                if api_response is not None:
                    # Ensure meta_data is initialized as a dict before updating.
                    if file_entry.meta_data is None:
                        file_entry.meta_data = {}
                    
                    # Update the file metadata with the API response.
                    file_entry.meta_data[meta_key] = api_response.content
                    results.append({
                        "file_path": file_entry.file_path,
                        "meta_data": api_response.content
                    })
        else:
            current_app.logger.warning(f"File not found: {file_entry.file_path}")

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating database: {e}")


def upsert_files_to_vector_db():
    """
    Retrieves files from the database that have metadata and have not yet been upserted
    (is_uploaded == False), generates embeddings for them using an AI API, and then upserts
    them to a vector database. After a successful upsert, marks the file as uploaded.
    
    Returns:
        list[dict]: A list of results for each processed file containing the file_path and
                    the response from the vector API.
    """
    # Query for files that have metadata and have not been uploaded to the vector database.
    files_to_upsert = File.query.filter(File.meta_data.isnot(None), File.is_uploaded == False).all()
    print('files to upsert:' + str(files_to_upsert))
    
    results = []
    for file_entry in files_to_upsert:
        if os.path.exists(file_entry.file_path):
            # Here you can choose to use metadata or re-extract text for embeddings.
            # For this example, we use file metadata as the source text.
            file_text = extract_text_from_file(file_entry.file_path)
            
            if file_text:
                
                # Generate embeddings with retrieval-optimized formatting
                retrieval_text = f"Represent this document for searching relevant passages: {file_text}"
                api_response = send_to_api(retrieval_text, openai_api_logic, purpose='embeddings')
                
                if api_response is not None:
                    # Extract embeddings from the API response.
                    # The structure of api_response depends on your AI API.
                    embeddings = api_response
                    
                    if embeddings:                                            
                        # Upsert the embeddings to the vector database.
                        vector_response = send_to_vector_db(embeddings, pinecone_vector_logic, filetext=file_text)

                    
                        
                        
                        if vector_response is not None:
                            # Mark file as uploaded to avoid reprocessing.
                            file_entry.is_uploaded = True
                            results.append({
                                "file_path": file_entry.file_path,
                                "vector_response": str(vector_response)
                            })
                            print(results)
                        else:
                            print(f"Failed to upsert embeddings for {file_entry.file_path}")
                    else:
                        print(f"No embeddings returned for {file_entry.file_path}")
            else:
                print(f"No usable text for embeddings for {file_entry.file_path}")
        else:
            print(f"File not found: {file_entry.file_path}")
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error updating database: {e}")
    
    return results
