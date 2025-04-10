from flask import Blueprint, request, jsonify, Response, current_app
import uuid
from utils.file_processing import scan_and_add_files, process_files_for_metadata, upsert_files_to_vector_db
import json

file_bp = Blueprint('files', __name__, url_prefix='/files')

@file_bp.route('/process_folder', methods=['GET', 'POST'])
def process_folder():
    # Determine input source (JSON or form/query parameters)
    if request.is_json:
        data = request.get_json()
        folder_path = data.get("folder_path")
        extension = data.get("extension") or ".txt"
        conversation_id = data.get("conversation_id")
    else:
        folder_path = request.values.get("folder_path")
        extension = request.values.get("extension") or ".txt"
        conversation_id = request.values.get("conversation_id")

    # Enforce required parameters for POST requests
    if request.method == 'POST':
        if not folder_path or not extension:
            print("Error: Missing folder_path or extension")
            return jsonify({"error": "Both 'folder_path' and 'extension' are required."}), 400

    # Capture the actual app instance before leaving the request context.
    app_instance = current_app._get_current_object()

    # Generate a unique session ID
    session_id = uuid.uuid4().hex
    print(f"Starting folder processing session: {session_id}")
    print(f"Folder path: {folder_path}, Extension: {extension}, Conversation ID: {conversation_id}")

    def inner_generator():
        results = {'sessionId': session_id}
        # Validate essential parameter early.
        if not folder_path:
            error_msg = "Invalid input: folder_path is required."
            print(f"Error: {error_msg}")
            yield f"event: error\ndata: {json.dumps({'error': error_msg})}\n\n"            # Terminate generator immediately
            return

        try:
            # Send session ID event
            session_payload = json.dumps({'sessionId': session_id})
            print(f"Sending session event with sessionId: {session_id}")
            yield f"event: session\ndata: {session_payload}\n\n"

            # Step 1: Scan with progress
            print("Starting file scan...")
            def progress_callback(progress):
                progress_payload = json.dumps({'progress': progress})
                print(f"Progress update: {progress}")
                return f"data: {progress_payload}\n\n"

            try:
                scan_results = scan_and_add_files(folder_path, extension, conversation_id, progress_callback)
                results["scan"] = scan_results
                print("File scan complete.")
            except Exception as e:
                error_msg = f"Error during file scan: {str(e)}"
                print(error_msg)
                yield f"event: error\ndata: {json.dumps({'error': error_msg})}\n\n"                # Exit the generator immediately on critical error.
                return

            yield f"data: {json.dumps({'progress': 33})}\n\n"

            # Step 2: Generate metadata
            print("Starting metadata generation...")
            try:
                metadata_results = process_files_for_metadata()
                results["metadata_generation"] = metadata_results
                print("Metadata generation complete.")
            except Exception as e:
                error_msg = f"Error during metadata generation: {str(e)}"
                print(error_msg)
                yield f"event: error\ndata: {json.dumps({'error': error_msg})}\n\n"
                return

            yield f"data: {json.dumps({'progress': 66})}\n\n"

            # Step 3: Upsert vectors
            print("Starting vector upsert...")
            try:
                vector_results = upsert_files_to_vector_db()
                results["vector_upsert"] = vector_results
                print("Vector upsert complete.")
            except Exception as e:
                error_msg = f"Error during vector upsert: {str(e)}"
                print(error_msg)
                yield f"event: error\ndata: {json.dumps({'error': error_msg})}\n\n"
                return

            yield f"data: {json.dumps({'progress': 100})}\n\n"

        except Exception as e:
            error_msg = f"Unexpected error in inner_generator: {str(e)}"
            print(error_msg)
            yield f"event: error\ndata: {json.dumps({'error': error_msg})}\n\n"
            return

        # Send final data and complete event
        final_payload = json.dumps(results)
        print("Sending final data and complete event.")
        yield f"data: {final_payload}\n\n"
        yield f"event: complete\ndata: {final_payload}\n\n"
        return  # End the generator

    def generate():
        with app_instance.app_context():
            yield from inner_generator()

    return Response(generate(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
    })
