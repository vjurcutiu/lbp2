import os
from db.models import db, File
from ai_apis import send_to_api, openai_api_logic  # You can swap out openai_api_logic with another API function as needed
from vector_apis import send_to_vector_db, pinecone_vector_logic


def scan_and_add_files(folder_path, extension, conversation_id=None):
    """
    Scans the given folder for files with the specified extension and adds them to the database.
    
    Args:
        folder_path (str): The directory to scan for files.
        extension (str): The file extension to filter by (e.g., '.txt').
        conversation_id (int, optional): If provided, associates each file with a conversation.
        
    Returns:
        dict: A summary containing two keys:
            - 'added': list of file paths that were added to the database.
            - 'skipped': list of file paths that were skipped (already exist in the database).
    """
    added_files = []
    skipped_files = []
    
    # Walk the directory tree (including subdirectories)
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            # Check if the file has the specified extension (case-insensitive)
            if filename.lower().endswith(extension.lower()):
                full_path = os.path.join(root, filename)
                
                # Check if the file already exists in the database
                existing_file = File.query.filter_by(file_path=full_path).first()
                if existing_file:
                    skipped_files.append(full_path)
                    continue
                
                # Extract the file extension from the filename
                _, file_ext = os.path.splitext(filename)

                # Create a new File record.
                # Here, is_uploaded is set to True because the file exists on disk.
                new_file = File(
                    file_path=full_path,
                    file_extension=file_ext,
                    conversation_id=conversation_id,
                    is_uploaded=False,
                    metadata=None  # You could add logic to generate metadata if needed.
                )
                db.session.add(new_file)
                added_files.append(full_path)
    
    # Commit the session to save the new records
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Database error: {e}")
    
    return {
        'added': added_files,
        'skipped': skipped_files
    }

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
    files_without_metadata = File.query.filter(File.metadata.is_(None)).all()
    
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

def process_files_for_metadata():
    """
    Retrieves files from the database that need metadata generation,
    extracts text from them, and sends them to an API for metadata generation.
    
    Returns:
        list[dict]: A list of results from the API for each processed file.
    """
    # Query for files that need metadata generation (e.g., metadata field is None)
    files_to_process = File.query.filter(File.metadata.is_(None)).all()
    
    results = []
    for file_entry in files_to_process:
        if os.path.exists(file_entry.file_path):          
            file_text = extract_text_from_file(file_entry.file_path)
            
            if file_text:
                # Send file_text to the API using the interface layer
                api_response = send_to_api(file_text, openai_api_logic)
                
                if api_response is not None:
                    # Update the file metadata in the database based on the API response.
                    file_entry.metadata = api_response
                    results.append({
                        "file_path": file_entry.file_path,
                        "api_response": api_response
                    })
        else:
            print(f"File not found: {file_entry.file_path}")
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error updating database: {e}")
    
    return results

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
    files_to_upsert = File.query.filter(File.metadata.isnot(None), File.is_uploaded == False).all()
    
    results = []
    for file_entry in files_to_upsert:
        if os.path.exists(file_entry.file_path):
            # Here you can choose to use metadata or re-extract text for embeddings.
            # For this example, we use file metadata as the source text.
            file_text = file_entry.metadata.get("summary", "") if isinstance(file_entry.metadata, dict) else ""
            
            if file_text:
                # Set additional parameters, including an endpoint for embeddings generation.
                additional_params = {
                    "endpoint": "https://api.openai.com/v1/embeddings",  # Example endpoint for embeddings
                    "max_tokens": 100  # Example parameter; adjust as needed.
                }
                
                # Generate embeddings using the AI API.
                api_response = send_to_api(file_text, openai_api_logic, additional_params)
                
                if api_response is not None:
                    # Extract embeddings from the API response.
                    # The structure of api_response depends on your AI API.
                    embeddings = api_response.get("data") or api_response.get("embeddings")
                    
                    if embeddings:
                        # Set the vector database endpoint and additional parameters if needed.
                        vector_endpoint = "https://your-vector-db.com/upsert"  # Example endpoint
                        vector_additional_params = {"namespace": "your_namespace"}
                        
                        # Upsert the embeddings to the vector database.
                        vector_response = send_to_vector_db(embeddings, vector_endpoint, pinecone_vector_logic, vector_additional_params)
                        
                        if vector_response is not None:
                            # Mark file as uploaded to avoid reprocessing.
                            file_entry.is_uploaded = True
                            results.append({
                                "file_path": file_entry.file_path,
                                "vector_response": vector_response
                            })
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