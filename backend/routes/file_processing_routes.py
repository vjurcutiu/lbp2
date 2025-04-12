from flask import Blueprint, request, jsonify, Response, current_app
import uuid
import json
import threading
import time

# Import the updated processing functions.
from utils.file_processing import (
    scan_and_add_files_wrapper,
    process_files_for_metadata,
    upsert_files_to_vector_db
)

file_bp = Blueprint('files', __name__, url_prefix='/files')

# Global in-memory store for processing sessions.
processing_sessions = {}

@file_bp.route('/process_folder', methods=['POST'])
def start_process_folder():
    data = request.get_json()
    folder_path = data.get("folder_path")
    extension = data.get("extension") or ".txt"

    if not folder_path or not extension:
        error_msg = "Both 'folder_path' and 'extension' are required."
        return jsonify({"error": error_msg}), 400

    session_id = uuid.uuid4().hex
    processing_sessions[session_id] = {"progress": 0, "final": None}

    my_app = current_app._get_current_object()

    # Start background processing in a separate thread.
    threading.Thread(target=process_folder_task, args=(folder_path, extension, session_id, my_app)).start()

    return jsonify({"sessionId": session_id})

@file_bp.route('/process_folder', methods=['GET'])
def stream_process_folder():
    session_id = request.args.get("session_id")
    if not session_id or session_id not in processing_sessions:
        error_msg = "Invalid or missing session_id."
        return Response(f"event: error\ndata: {json.dumps({'error': error_msg})}\n\n", mimetype='text/event-stream')

    def event_stream():
        while True:
            session = processing_sessions.get(session_id)
            if session is None:
                break

            yield f"event: progress\ndata: {json.dumps({'value': session['progress']})}\n\n"

            if session.get("final") is not None:
                yield f"event: complete\ndata: {json.dumps(session['final'])}\n\n"
                del processing_sessions[session_id]
                break

            time.sleep(1)

    return Response(
        event_stream(),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive'}
    )

def process_folder_task(folder_path, extension, session_id, app):
    """
    This function runs in a background thread. It processes files in three phases:
      1. File Scan and Add – scanning is done without tracking progress.
      2. Metadata Generation – this phase is tracked from 0% to 50%.
      3. Vector Upsert – this phase is tracked from 50% to 100%.
    """
    with app.app_context():
        results = {}

        # -------------------------------
        # PHASE 1: File Scan and Add
        # -------------------------------
        try:
            app.logger.info(f"Session {session_id}: Starting folder scan...")
            scan_results = scan_and_add_files_wrapper(folder_path, extension)
            results["scan"] = scan_results
            app.logger.info(f"Session {session_id}: Scan complete.")
        except Exception as e:
            processing_sessions[session_id]["final"] = {"error": f"Error during file scan: {str(e)}"}
            return

        # Reset progress to 0% once scanning is done.
        processing_sessions[session_id]["progress"] = 0

        # -------------------------------
        # PHASE 2: Metadata Generation
        # (Progress from 0% up to 50%)
        # -------------------------------
        try:
            # Base progress for metadata phase is 0%.
            base_progress = 0

            def metadata_progress_callback(processed, total):
                # Scale each file processed in this phase into a 50% range.
                new_progress = base_progress + (processed / total) * 50
                processing_sessions[session_id]["progress"] = int(new_progress)

            metadata_results = process_files_for_metadata(type="keywords", progress_callback=metadata_progress_callback)
            results["metadata_generation"] = metadata_results
            # Ensure that if the phase completes, progress is exactly 50%.
            processing_sessions[session_id]["progress"] = 50
            app.logger.info(f"Session {session_id}: Metadata generation complete.")
        except Exception as e:
            processing_sessions[session_id]["final"] = {"error": f"Error during metadata generation: {str(e)}"}
            return

        # -------------------------------
        # PHASE 3: Vector Upsert
        # (Progress from 50% up to 100%)
        # -------------------------------
        try:
            base_progress = 50

            def vector_progress_callback(processed, total):
                new_progress = base_progress + (processed / total) * 50
                processing_sessions[session_id]["progress"] = int(new_progress)

            vector_results = upsert_files_to_vector_db(progress_callback=vector_progress_callback)
            results["vector_upsert"] = vector_results
            # Ensure final progress is 100%.
            processing_sessions[session_id]["progress"] = 100
            app.logger.info(f"Session {session_id}: Vector upsert complete.")
        except Exception as e:
            processing_sessions[session_id]["final"] = {"error": f"Error during vector upsert: {str(e)}"}
            return

        processing_sessions[session_id]["final"] = results
