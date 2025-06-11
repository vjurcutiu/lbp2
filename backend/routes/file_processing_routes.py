import os
import json
from flask import Blueprint, request, jsonify, Response, stream_with_context
from pydantic import ValidationError
from utils.logging import logger, log_call
from schemas.file_processing import ProcessFolderSchema, CancelSchema
from services.session_store import SessionStore, ProcessingSession
from utils.event_formatting import format_sse
from services.mp_init import init_multiprocessing, get_pool, get_manager
from services.cleanup import SessionCleanup

# -----------------------------------------------------------------------------
# Blueprint & global state ----------------------------------------------------
# -----------------------------------------------------------------------------

file_bp = Blueprint("files", __name__, url_prefix="/files")
sessions = None

def set_session_store(sess_store):
    global sessions
    sessions = sess_store

def get_sessions():
    from flask import current_app
    # In real app, get from app context
    return sessions

# -----------------------------------------------------------------------------
# Routes ----------------------------------------------------------------------
# -----------------------------------------------------------------------------

@file_bp.route("/process_folder", methods=["POST"])
@log_call()
def start_process_folder():
    """
    Start a new processing session and queue a background processing job.
    """
    try:
        payload_dict = request.get_json() or {}
        logger.debug("Received payload: %s", payload_dict)
        payload = ProcessFolderSchema(**payload_dict)
    except ValidationError as ve:
        logger.warning("Validation error: %s", ve)
        return jsonify({"error": {"code": 400, "message": ve.errors()}}), 400

    session_store = get_sessions()
    if session_store is None:
        logger.error("SessionStore is not initialized.")
        return jsonify({"error": {"code": 500, "message": "Session store not initialized"}}), 500
    session = session_store.create()

    # Multiprocessing queues for SSE and websocket events
    session.sse_queue = get_manager().Queue()
    session.ws_queue = get_manager().Queue()

    # Example: Enqueue your processing task (replace this with your actual function!)
    from services.file_processing_service import process_folder_task

    # Provide app config as a dict for worker (adapt as needed)
    app_config = {
        "SQLALCHEMY_DATABASE_URI": os.getenv("DATABASE_URI", "sqlite:///rag_chat.db"),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    }

    def log_worker_error(e):
        logger.error("process_folder_task failed: %s", e, exc_info=True)

    get_pool().apply_async(
        process_folder_task,
        args=(
            payload.folder_paths,
            payload.extensions,
            session.session_id,
            session.sse_queue,
            session.ws_queue,
            app_config,
        ),
        error_callback=log_worker_error,
    )
    logger.info("Enqueued job for session %s", session.session_id)
    return jsonify({"sessionId": session.session_id}), 202

@file_bp.route("/process_folder", methods=["GET"])
@log_call()
def stream_process_folder():
    """
    SSE endpoint: streams processing progress and results to the client.
    """
    session_id = request.args.get("session_id")
    session_store = get_sessions()
    if session_store is None:
        logger.error("SessionStore is not initialized.")
        return Response(
            format_sse("error", {"error": "Session store not initialized"}),
            mimetype="text/event-stream",
        )
    session = session_store.get(session_id)
    if not session:
        logger.warning("Stream requested for invalid session_id %s", session_id)
        return Response(
            format_sse("error", {"error": "Invalid session_id"}),
            mimetype="text/event-stream",
        )

    import threading

    # Start websocket event listener thread if not already started
    if not hasattr(session, "ws_listener_thread") or not getattr(session, "ws_listener_thread", None) or not session.ws_listener_thread.is_alive():
        session.stop_ws_listener = threading.Event()
        from utils.websockets.upload_tracking import websocket_event_listener
        session.ws_listener_thread = threading.Thread(
            target=websocket_event_listener,
            args=(session.ws_queue, session_id, session.stop_ws_listener),
            daemon=True,
        )
        session.ws_listener_thread.start()

    def event_stream():
        logger.info("Client connected to stream for session %s", session_id)
        last_ping = 0
        import time
        import queue
        while True:
            try:
                msg = session.sse_queue.get(timeout=1)
                logger.debug("SSE message: %s", msg)
                if "progress" in msg:
                    yield format_sse("progress", {"value": msg["progress"]})
                elif "scan" in msg:
                    session.file_items = msg["scan"]
                    yield format_sse("scan", {"files": msg["scan"]})
                elif "complete" in msg:
                    session.final = msg.get("summary", {})
                    yield format_sse("complete", session.final or {})
                    if hasattr(session, "stop_ws_listener"):
                        session.stop_ws_listener.set()
                    sessions.delete(session_id)
                    logger.info("Session %s completed and removed", session_id)
                    break
            except queue.Empty:
                if time.time() - last_ping >= 10:
                    yield ": ping\n\n"
                    last_ping = time.time()
                continue
            except Exception:
                time.sleep(0.2)
                continue

    return Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )

@file_bp.route("/process_folder/cancel", methods=["POST"])
@log_call()
def cancel_process_folder():
    """
    Cancel an in-progress processing session and trigger cleanup.
    """
    try:
        payload_dict = request.get_json() or {}
        payload = CancelSchema(**payload_dict)
    except ValidationError as ve:
        logger.warning("Cancel validation error: %s", ve)
        return jsonify({"error": {"code": 400, "message": ve.errors()}}), 400

    session_store = get_sessions()
    if session_store is None:
        logger.error("SessionStore is not initialized.")
        return jsonify({"error": {"code": 500, "message": "Session store not initialized"}}), 500
    session = session_store.get(payload.session_id)
    if not session:
        logger.warning("Cancel requested for unknown session %s", payload.session_id)
        return jsonify({"error": {"code": 404, "message": "Session not found"}}), 404

    session.cancelled = True
    SessionCleanup(session).run()
    session.final = {"error": "Processing cancelled by user"}
    logger.info("Session %s marked as cancelled", payload.session_id)
    return jsonify({"status": "cancelled"}), 200
