# file_processing_routes.py
from flask import Blueprint, request, jsonify
from utils.file_processing import scan_and_add_files, process_files_for_metadata, upsert_files_to_vector_db

file_bp = Blueprint('file', __name__)

@file_bp.route('/process_folder', methods=['POST'])
def process_folder():
    """
    Endpoint to process a folder selected by the user.

    Expected JSON payload:
    {
        "folder_path": "path/to/the/folder",
        "extension": ".txt",
        "conversation_id": <optional integer>
    }

    Workflow:
      1. Scan the folder and add matching files to the database.
      2. Process files to generate metadata for those missing it.
      3. Upsert the processed files (with metadata) into the vector database.

    Returns:
      A JSON response with the results from scanning, metadata generation, and vector upsert.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON payload required."}), 400

    folder_path = data.get("folder_path")
    extension = data.get("extension")
    conversation_id = data.get("conversation_id")  # Optional

    if not folder_path or not extension:
        return jsonify({"error": "Both 'folder_path' and 'extension' are required."}), 400

    results = {}

    try:
        # Step 1: Scan the folder and add files to the database.
        scan_results = scan_and_add_files(folder_path, extension, conversation_id)
        results["scan"] = scan_results
    except Exception as e:
        results["scan"] = {"error": f"Error scanning folder: {str(e)}"}

    try:
        # Step 2: Process files to generate metadata.
        metadata_results = process_files_for_metadata()
        results["metadata_generation"] = metadata_results
    except Exception as e:
        results["metadata_generation"] = {"error": f"Error generating metadata: {str(e)}"}

    try:
        # Step 3: Upsert files (with metadata) to the vector database.
        vector_results = upsert_files_to_vector_db()
        results["vector_upsert"] = vector_results
    except Exception as e:
        results["vector_upsert"] = {"error": f"Error upserting files to vector database: {str(e)}"}

    return jsonify(results), 200
