# file_processing_routes.py

import os
import uuid
import json
import threading
import time
from flask import Blueprint, request, jsonify, Response, current_app, stream_with_context
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from db.models import File, db
from utils.file_processing import (
    scan_and_add_files_wrapper,
    process_files_for_metadata,
    upsert_files_to_vector_db
)
from utils.pinecone_client import PineconeClient

load_dotenv()  # for PINECONE_API_KEY, PINECONE_ENV, PINECONE_INDEX, PINECONE_NAMESPACE

file_bp = Blueprint('files', __name__, url_prefix='/files')

# In‑memory sessions:
#   progress: int, final: dict|None, cancelled: bool, file_items: list
processing_sessions = {}

class CancellationException(Exception):
    pass


def cleanup_session(session_id):
    func = "cleanup_session"
    current_app.logger.info(f"[{__file__}][{func}] Starting cleanup for session {session_id}")
    proc_sess = processing_sessions.get(session_id)
    if not proc_sess:
        current_app.logger.warning(f"[{__file__}][{func}] No session found for {session_id}")
        return

    items = proc_sess.get('file_items', [])
    if not items:
        current_app.logger.info(f"[{__file__}][{func}] No file items to clean for {session_id}")
        return

    ids, paths = [], []
    for x in items:
        if isinstance(x, int):
            ids.append(x)
        elif isinstance(x, dict) and 'id' in x:
            ids.append(x['id'])
        elif isinstance(x, str):
            paths.append(x)
    current_app.logger.debug(f"[{__file__}][{func}] Resolved ids={ids}, paths={paths}")

    SessionLocal = sessionmaker(bind=db.engine)
    cleanup_sess = SessionLocal()
    try:
        if not ids and paths:
            files = (
                cleanup_sess.query(File)
                .filter(File.file_path.in_(paths))
                .all()
            )
            ids = [f.id for f in files]
            current_app.logger.debug(f"[{__file__}][{func}] Looked up IDs from paths: {ids}")

        if ids:
            try:
                namespace = os.getenv("PINECONE_NAMESPACE", "default-namespace")
                client = PineconeClient()
                client.delete(ids=[str(i) for i in ids], namespace=namespace)
                current_app.logger.info(f"[{__file__}][{func}] Pinecone vectors deleted for IDs {ids}")
            except Exception as e:
                current_app.logger.error(f"[{__file__}][{func}] Pinecone delete error for {session_id}: {e}")

        if ids:
            cleanup_sess.query(File)\
                .filter(File.id.in_(ids))\
                .delete(synchronize_session=False)
            cleanup_sess.commit()
            current_app.logger.info(f"[{__file__}][{func}] DB rows deleted for IDs {ids}")

    except Exception as e:
        current_app.logger.error(f"[{__file__}][{func}] DB delete error for {session_id}: {e}")
        cleanup_sess.rollback()
    finally:
        cleanup_sess.close()
        current_app.logger.info(f"[{__file__}][{func}] Cleanup session closed for {session_id}")


@file_bp.route('/process_folder', methods=['POST'])
def start_process_folder():
    func = "start_process_folder"
    current_app.logger.info(f"[{__file__}][{func}] Received POST request")
    data = request.get_json() or {}
    folder_path = data.get("folder_path")
    extensions = data.get("extensions")
    current_app.logger.info(f"/process_folder - Scanning {folder_path} for *{extensions}* files")


    if not folder_path or not extensions:
        current_app.logger.error(f"[{__file__}][{func}] Missing folder_path or extension in payload")
        return jsonify({"error": "Both 'folder_path' and 'extension' are required."}), 400

    session_id = uuid.uuid4().hex
    processing_sessions[session_id] = {
        "progress": 0,
        "final": None,
        "cancelled": False,
        "file_items": []
    }
    current_app.logger.info(f"[{__file__}][{func}] Created session {session_id}")

    threading.Thread(
        target=process_folder_task,
        args=(folder_path, extensions, session_id, current_app._get_current_object())
    ).start()

    return jsonify({"sessionId": session_id})


@file_bp.route('/process_folder', methods=['GET'])
def stream_process_folder():
    
    func = "stream_process_folder"
    current_app.logger.info(f"[{__file__}][{func}] Received GET request for SSE")
    session_id = request.args.get("session_id")
    if session_id not in processing_sessions:
        current_app.logger.error(f"[{__file__}][{func}] Invalid session_id: {session_id}")
        return Response(
            "event: error\ndata: " + json.dumps({"error": "Invalid or missing session_id."}) + "\n\n",
            mimetype='text/event-stream'
        )

    def event_stream():
        while True:
            sess = processing_sessions.get(session_id)
            if sess is None:
                current_app.logger.info(f"[{__file__}][{func}] Session {session_id} removed, ending stream")
                break

            yield f"event: progress\ndata: " \
                  + json.dumps({'value': sess['progress']}) + "\n\n"

            if sess.get("final") is not None:
                yield f"event: complete\ndata: " \
                      + json.dumps(sess['final']) + "\n\n"
                del processing_sessions[session_id]
                current_app.logger.info(f"[{__file__}][{func}] Session {session_id} completed and deleted")
                break

            time.sleep(1)
    wrapped = stream_with_context(event_stream())
    return Response(
        wrapped,
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive'}
    )


@file_bp.route('/process_folder/cancel', methods=['POST'])
def cancel_process_folder():
    func = "cancel_process_folder"
    current_app.logger.info(f"[{__file__}][{func}] Received cancel request")
    data = request.get_json() or {}
    session_id = data.get("session_id")
    if session_id in processing_sessions:
        sess = processing_sessions[session_id]
        sess["cancelled"] = True
        current_app.logger.info(f"[{__file__}][{func}] Marked session {session_id} as cancelled")

        cleanup_session(session_id)

        sess["final"] = {"error": "Processing cancelled by user"}
        current_app.logger.info(f"[{__file__}][{func}] Sent cancellation complete event for {session_id}")
        return jsonify({"status": "cancelled"}), 200

    current_app.logger.error(f"[{__file__}][{func}] Invalid or missing session_id: {session_id}")
    return jsonify({"error": "Invalid or missing session_id."}), 400


def process_folder_task(folder_path, extension, session_id, app):
    func = "process_folder_task"
    with app.app_context():
        current_app.logger.info(f"[{__file__}][{func}] Starting task for session {session_id}, folder={folder_path}, ext={extension}")
        results = {}
        sess = processing_sessions[session_id]

        # PHASE 1: Scan & add
        try:
            if sess["cancelled"]:
                raise CancellationException()

            scan_res = scan_and_add_files_wrapper(folder_path, extension)
            results["scan"] = scan_res
            sess["file_items"] = scan_res.get("added", [])
            current_app.logger.info(f"[{__file__}][{func}] Scan completed, added items: {sess['file_items']}")

        except CancellationException:
            current_app.logger.warning(f"[{__file__}][{func}] Cancelled during scan phase for {session_id}")
            cleanup_session(session_id)
            sess["final"] = {"error": "Processing cancelled by user"}
            return
        except Exception as e:
            current_app.logger.error(f"[{__file__}][{func}] Error during file scan: {e}")
            sess["final"] = {"error": f"Error during file scan: {e}"}
            return

        # PHASE 2: Metadata (0→50%)
        sess["progress"] = 0
        try:
            def meta_cb(done, total):
                if sess["cancelled"]:
                    raise CancellationException()
                sess["progress"] = int(done / total * 50)

            current_app.logger.info(f"[{__file__}][{func}] Starting metadata generation")
            meta_res = process_files_for_metadata(
                type="keywords",
                progress_callback=meta_cb
            )
            results["metadata_generation"] = meta_res
            sess["progress"] = 50
            current_app.logger.info(f"[{__file__}][{func}] Metadata generation completed")

        except CancellationException:
            current_app.logger.warning(f"[{__file__}][{func}] Cancelled during metadata phase for {session_id}")
            cleanup_session(session_id)
            sess["final"] = {"error": "Processing cancelled by user"}
            return
        except Exception as e:
            current_app.logger.error(f"[{__file__}][{func}] Error during metadata generation: {e}")
            sess["final"] = {"error": f"Error during metadata generation: {e}"}
            return

        # PHASE 3: Vector upsert (50→100%)
        try:
            def vec_cb(done, total):
                if sess["cancelled"]:
                    raise CancellationException()
                sess["progress"] = 50 + int(done / total * 50)

            current_app.logger.info(f"[{__file__}][{func}] Starting vector upsert")
            vec_res = upsert_files_to_vector_db(progress_callback=vec_cb)
            results["vector_upsert"] = vec_res
            sess["progress"] = 100
            current_app.logger.info(f"[{__file__}][{func}] Vector upsert completed")

        except CancellationException:
            current_app.logger.warning(f"[{__file__}][{func}] Cancelled during vector upsert for {session_id}")
            cleanup_session(session_id)
            sess["final"] = {"error": "Processing cancelled by user"}
            return
        except Exception as e:
            current_app.logger.error(f"[{__file__}][{func}] Error during vector upsert: {e}")
            sess["final"] = {"error": f"Error during vector upsert: {e}"}
            return

        # All done successfully
        sess["final"] = results
        current_app.logger.info(f"[{__file__}][{func}] Processing complete for session {session_id}")
