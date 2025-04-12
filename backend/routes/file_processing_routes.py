from flask import Blueprint, request, jsonify, Response, current_app
import uuid
import json
import threading
import time

# Import your processing functions; adjust these imports to your actual modules.
from utils.file_processing import scan_and_add_files, process_files_for_metadata, upsert_files_to_vector_db

file_bp = Blueprint('files', __name__, url_prefix='/files')

# A simple global in-memory store for processing sessions.
processing_sessions = {}

@file_bp.route('/process_folder', methods=['POST'])
def start_process_folder():
    """
    This endpoint starts the folder processing. It requires a JSON payload with:
      - folder_path: path to the folder to process
      - extension: file extension filter (defaults to ".txt")
    It creates a session and kicks off a background thread to process the folder.
    Returns a sessionId for tracking.
    """
    data = request.get_json()
    folder_path = data.get("folder_path")
    extension = data.get("extension") or ".txt"

    if not folder_path or not extension:
        error_msg = "Both 'folder_path' and 'extension' are required."
        return jsonify({"error": error_msg}), 400

    session_id = uuid.uuid4().hex
    processing_sessions[session_id] = {"progress": 0, "final": None}

    # Capture the real app instance from the current context.
    my_app = current_app._get_current_object()

    # Start background processing and pass the app instance.
    threading.Thread(target=process_folder_task, args=(folder_path, extension, session_id, my_app)).start()

    return jsonify({"sessionId": session_id})

@file_bp.route('/process_folder', methods=['GET'])
def stream_process_folder():
    """
    This endpoint uses Server-Sent Events (SSE) to stream progress updates and the final result.
    It expects a query parameter "session_id" to know which session to stream.
    """
    session_id = request.args.get("session_id")
    if not session_id or session_id not in processing_sessions:
        error_msg = "Invalid or missing session_id."
        return Response(f"event: error\ndata: {json.dumps({'error': error_msg})}\n\n", mimetype='text/event-stream')

    def event_stream():
        while True:
            session = processing_sessions.get(session_id)
            if session is None:
                break

            progress_payload = json.dumps({'progress': session['progress']})
            yield f"data: {progress_payload}\n\n"

            if session.get("final") is not None:
                final_payload = json.dumps(session["final"])
                yield f"event: complete\ndata: {final_payload}\n\n"
                del processing_sessions[session_id]
                break

            time.sleep(1)

    return Response(event_stream(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive'})

def process_folder_task(folder_path, extension, session_id, app):
    """
    This function runs in a background thread and performs the folder processing.
    It updates the global processing_sessions dictionary with progress and final results.
    The app instance is passed to establish the proper application context.
    """
    with app.app_context():
        results = {}
        try:
            app.logger.info(f"Session {session_id}: starting file scan...")
            scan_results = scan_and_add_files(folder_path, extension)
            results["scan"] = scan_results
            processing_sessions[session_id]["progress"] = 33
            app.logger.info(f"Session {session_id}: file scan complete. Progress 33%.")
        except Exception as e:
            processing_sessions[session_id]["final"] = {"error": f"Error during file scan: {str(e)}"}
            return

        try:
            app.logger.info(f"Session {session_id}: starting metadata generation...")
            metadata_results = process_files_for_metadata()
            results["metadata_generation"] = metadata_results
            processing_sessions[session_id]["progress"] = 66
            app.logger.info(f"Session {session_id}: metadata generation complete. Progress 66%.")
        except Exception as e:
            processing_sessions[session_id]["final"] = {"error": f"Error during metadata generation: {str(e)}"}
            return

        try:
            app.logger.info(f"Session {session_id}: starting vector upsert...")
            vector_results = upsert_files_to_vector_db()
            results["vector_upsert"] = vector_results
            processing_sessions[session_id]["progress"] = 100
            app.logger.info(f"Session {session_id}: vector upsert complete. Progress 100%.")
        except Exception as e:
            processing_sessions[session_id]["final"] = {"error": f"Error during vector upsert: {str(e)}"}
            return

        processing_sessions[session_id]["final"] = results
