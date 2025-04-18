# file_processing_routes.py

from flask import Blueprint, request, jsonify, Response, current_app
import uuid, json, threading, time, os
from dotenv import load_dotenv

from sqlalchemy.orm import Session

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
    """
    Remove any files added in this session from SQL and Pinecone.
    Handles file IDs (int), file_paths (str), or dicts with 'id' keys.
    """
    session = processing_sessions.get(session_id)
    if not session:
        return

    items = session.get('file_items', [])
    if not items:
        return

    # 1) Normalize to DB IDs and file_paths
    ids, paths = [], []
    for x in items:
        if isinstance(x, int):
            ids.append(x)
        elif isinstance(x, dict) and 'id' in x:
            ids.append(x['id'])
        elif isinstance(x, str):
            paths.append(x)

    # 2) If we only got paths, look up their IDs
    if not ids and paths:
        files = File.query.filter(File.file_path.in_(paths)).all()
        ids = [f.id for f in files]

    # 3) Delete vectors in Pinecone using client
    if ids:
        try:
            namespace = os.getenv("PINECONE_NAMESPACE")
            PineconeClient.delete(ids=ids, namespace=namespace)
        except Exception as e:
            current_app.logger.error(f"[cleanup] Pinecone delete error for {session_id}: {e}")

    # 4) Delete rows in SQL
    if ids:
        try:
            File.query.filter(File.id.in_(ids)).delete(synchronize_session=False)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"[cleanup] DB delete error for {session_id}: {e}")


@file_bp.route('/process_folder', methods=['POST'])
def start_process_folder():
    data = request.get_json() or {}
    folder_path = data.get("folder_path")
    extension = data.get("extension", ".txt")

    if not folder_path or not extension:
        return jsonify({"error": "Both 'folder_path' and 'extension' are required."}), 400

    session_id = uuid.uuid4().hex
    processing_sessions[session_id] = {
        "progress": 0,
        "final": None,
        "cancelled": False,
        "file_items": []
    }

    threading.Thread(
        target=process_folder_task,
        args=(folder_path, extension, session_id, current_app._get_current_object())
    ).start()

    return jsonify({"sessionId": session_id})


@file_bp.route('/process_folder', methods=['GET'])
def stream_process_folder():
    session_id = request.args.get("session_id")
    if session_id not in processing_sessions:
        return Response(
            "event: error\ndata: " + json.dumps({"error": "Invalid or missing session_id."}) + "\n\n",
            mimetype='text/event-stream'
        )

    def event_stream():
        while True:
            sess = processing_sessions.get(session_id)
            if sess is None:
                break

            yield f"event: progress\ndata: {json.dumps({'value': sess['progress']})}\n\n"

            if sess.get("final") is not None:
                yield f"event: complete\ndata: {json.dumps(sess['final'])}\n\n"
                del processing_sessions[session_id]
                break

            time.sleep(1)

    return Response(
        event_stream(),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive'}
    )


@file_bp.route('/process_folder/cancel', methods=['POST'])
def cancel_process_folder():
    data = request.get_json() or {}
    session_id = data.get("session_id")
    if session_id in processing_sessions:
        sess = processing_sessions[session_id]
        sess["cancelled"] = True

        # Immediately clean up DB & Pinecone
        cleanup_session(session_id)

        # Mark final so SSE client sees cancellation
        sess["final"] = {"error": "Processing cancelled by user"}
        return jsonify({"status": "cancelled"}), 200

    return jsonify({"error": "Invalid or missing session_id."}), 400


def process_folder_task(folder_path, extension, session_id, app):
    with app.app_context():
        results = {}
        sess = processing_sessions[session_id]

        # PHASE 1: Scan & add
        try:
            if sess["cancelled"]:
                raise CancellationException()

            scan_res = scan_and_add_files_wrapper(folder_path, extension)
            results["scan"] = scan_res
            sess["file_items"] = scan_res.get("added", [])

        except CancellationException:
            cleanup_session(session_id)
            sess["final"] = {"error": "Processing cancelled by user"}
            return
        except Exception as e:
            sess["final"] = {"error": f"Error during file scan: {e}"}
            return

        # PHASE 2: Metadata (0→50%)
        sess["progress"] = 0
        try:
            def meta_cb(done, total):
                if sess["cancelled"]:
                    raise CancellationException()
                sess["progress"] = int(done/total*50)

            meta_res = process_files_for_metadata(
                type="keywords",
                progress_callback=meta_cb
            )
            results["metadata_generation"] = meta_res
            sess["progress"] = 50

        except CancellationException:
            cleanup_session(session_id)
            sess["final"] = {"error": "Processing cancelled by user"}
            return
        except Exception as e:
            sess["final"] = {"error": f"Error during metadata generation: {e}"}
            return

        # PHASE 3: Vector upsert (50→100%)
        try:
            def vec_cb(done, total):
                if sess["cancelled"]:
                    raise CancellationException()
                sess["progress"] = 50 + int(done/total*50)

            vec_res = upsert_files_to_vector_db(progress_callback=vec_cb)
            results["vector_upsert"] = vec_res
            sess["progress"] = 100

        except CancellationException:
            cleanup_session(session_id)
            sess["final"] = {"error": "Processing cancelled by user"}
            return
        except Exception as e:
            sess["final"] = {"error": f"Error during vector upsert: {e}"}
            return

        # All done successfully
        sess["final"] = results
