import os
import json
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from utils.logging import logger, log_call
from schemas.file_processing import ProcessFolderSchema, CancelSchema
from services.session_store import SessionStore, ProcessingSession
from services.mp_init import get_pool, get_manager
from services.cleanup import SessionCleanup
import threading
from utils.services.ws_event_relay import ws_queue_relay

file_bp = Blueprint("files", __name__, url_prefix="/files")
sessions = None

def set_session_store(sess_store):
    global sessions
    sessions = sess_store

def get_sessions():
    return sessions

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

    # Only WebSocket queue for events
    session.ws_queue = get_manager().Queue()

    stop_event = threading.Event()
    relay_thread = threading.Thread(
        target=ws_queue_relay,
        args=(session.ws_queue, session.session_id, stop_event),
        daemon=True,
    )
    relay_thread.start()
    session.ws_relay_thread = relay_thread
    session.ws_stop_event = stop_event

    from features.file_processing.services.file_processing_service import process_folder_task

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
            session.ws_queue,
            app_config,
        ),
        error_callback=log_worker_error,
    )
    logger.info("Enqueued job for session %s", session.session_id)
    return jsonify({"sessionId": session.session_id}), 202

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
    session.ws_stop_event.set()
    session.final = {"error": "Processing cancelled by user"}
    logger.info("Session %s marked as cancelled", payload.session_id)
    return jsonify({"status": "cancelled"}), 200
