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
    logger.info("file_processing_routes.set_session_store: Session store initialized: %s", str(sess_store))

def get_sessions():
    logger.debug("file_processing_routes.get_sessions: Returning sessions store")
    return sessions

@file_bp.route("/process_folder", methods=["POST"])
@log_call()
def start_process_folder():
    """
    Start a new processing session and queue a background processing job.
    """
    logger.info("file_processing_routes.start_process_folder: Received request")
    try:
        print("Headers:", request.headers)
        print("Data:", request.data)
        print("is_json:", request.is_json)
        payload_dict = request.get_json() or {}
        print(payload_dict)
        logger.debug("file_processing_routes.start_process_folder: Received payload: %s", payload_dict)
        payload = ProcessFolderSchema(**payload_dict)
        logger.info("file_processing_routes.start_process_folder: Payload validated")
    except ValidationError as ve:
        logger.warning("file_processing_routes.start_process_folder: Validation error: %s", ve)
        return jsonify({"error": {"code": 400, "message": ve.errors()}}), 400

    session_store = get_sessions()
    if session_store is None:
        logger.error("file_processing_routes.start_process_folder: SessionStore is not initialized.")
        return jsonify({"error": {"code": 500, "message": "Session store not initialized"}}), 500
    session = session_store.create()
    logger.info("file_processing_routes.start_process_folder: Created session with ID: %s", session.session_id)

    # Only WebSocket queue for events
    session.ws_queue = get_manager().Queue()
    logger.info("file_processing_routes.start_process_folder: WebSocket queue created for session %s", session.session_id)

    stop_event = threading.Event()
    relay_thread = threading.Thread(
        target=ws_queue_relay,
        args=(session.ws_queue, session.session_id, stop_event),
        daemon=True,
    )
    relay_thread.start()
    logger.info("file_processing_routes.start_process_folder: WebSocket relay thread started for session %s", session.session_id)
    session.ws_relay_thread = relay_thread
    session.ws_stop_event = stop_event

    from features.file_processing.file_processing_service import process_folder_task

    app_config = {
        "SQLALCHEMY_DATABASE_URI": os.getenv("DATABASE_URI", "sqlite:///rag_chat.db"),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    }

    def log_worker_error(e):
        logger.error("file_processing_routes.start_process_folder: process_folder_task failed: %s", e, exc_info=True)

    logger.info("file_processing_routes.start_process_folder: Getting multiprocessing pool")
    pool = get_pool()
    logger.info("file_processing_routes.start_process_folder: Pool object created: %s", str(pool))

    logger.info("file_processing_routes.start_process_folder: Enqueuing background job for session %s", session.session_id)
    pool.apply_async(
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
    logger.info("file_processing_routes.start_process_folder: Job enqueued for session %s", session.session_id)
    return jsonify({"sessionId": session.session_id}), 202

@file_bp.route("/process_folder/cancel", methods=["POST"])
@log_call()
def cancel_process_folder():
    """
    Cancel an in-progress processing session and trigger cleanup.
    """
    logger.info("file_processing_routes.cancel_process_folder: Received cancel request")
    try:
        payload_dict = request.get_json() or {}
        payload = CancelSchema(**payload_dict)
        logger.info("file_processing_routes.cancel_process_folder: Payload validated for session: %s", payload.session_id)
    except ValidationError as ve:
        logger.warning("file_processing_routes.cancel_process_folder: Cancel validation error: %s", ve)
        return jsonify({"error": {"code": 400, "message": ve.errors()}}), 400

    session_store = get_sessions()
    if session_store is None:
        logger.error("file_processing_routes.cancel_process_folder: SessionStore is not initialized.")
        return jsonify({"error": {"code": 500, "message": "Session store not initialized"}}), 500
    session = session_store.get(payload.session_id)
    if not session:
        logger.warning("file_processing_routes.cancel_process_folder: Cancel requested for unknown session %s", payload.session_id)
        return jsonify({"error": {"code": 404, "message": "Session not found"}}), 404

    session.cancelled = True
    logger.info("file_processing_routes.cancel_process_folder: Session %s marked as cancelled, starting cleanup", payload.session_id)
    SessionCleanup(session).run()
    session.ws_stop_event.set()
    session.final = {"error": "Processing cancelled by user"}
    logger.info("file_processing_routes.cancel_process_folder: Cleanup complete for session %s", payload.session_id)
    return jsonify({"status": "cancelled"}), 200
