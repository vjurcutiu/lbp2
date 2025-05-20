import os
import uuid
import json
import logging
import threading
import time
import queue
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from flask import Blueprint, request, jsonify, Response, stream_with_context, current_app
from pydantic import BaseModel, ValidationError, Field
from sqlalchemy.orm import sessionmaker

from db.models import File, db
from utils.file_processing import scan_and_add_files_wrapper, process_files_for_metadata, upsert_files_to_vector_db
from utils.pinecone_client import PineconeClient

# Configure structured logger
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": "%(message)s"}'
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

file_bp = Blueprint('files', __name__, url_prefix='/files')

# In-memory session store and dataclass
@dataclass
class ProcessingSession:
    session_id: str
    progress: int = 0
    final: Optional[Dict] = None
    cancelled: bool = False
    file_items: List = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

class SessionStore:
    def __init__(self):
        self._store: Dict[str, ProcessingSession] = {}

    def create(self) -> ProcessingSession:
        session_id = uuid.uuid4().hex
        sess = ProcessingSession(session_id=session_id)
        self._store[session_id] = sess
        return sess

    def get(self, session_id: str) -> Optional[ProcessingSession]:
        return self._store.get(session_id)

    def delete(self, session_id: str) -> None:
        self._store.pop(session_id, None)

sessions = SessionStore()

# Job queue and worker
job_queue: queue.Queue[Tuple[str, List[str], str]] = queue.Queue()

_app = None
_thread = None

def init_worker(app) -> None:
    import os
    from dotenv import load_dotenv
    global _app, _thread
    _app = app
    # Load environment variables from .env file explicitly here for the worker thread
    load_dotenv(dotenv_path=".env", override=True)
    def _worker() -> None:
        logger.info("Background worker thread started")
        while True:
            logger.info("Worker waiting for job...")
            folder_path, extensions, session_id = job_queue.get()
            logger.info(f"Worker dequeued job for session {session_id}")
            try:
                with _app.app_context():
                    process_folder_task(folder_path, extensions, session_id)
            except Exception as e:
                logger.error(f"Background job error for session {session_id}: {e}")
                session = sessions.get(session_id)
                if session:
                    session.final = {"error": str(e)}
            finally:
                job_queue.task_done()

    _thread = threading.Thread(target=_worker, daemon=True)
    _thread.start()

# Input schemas
class ProcessFolderSchema(BaseModel):
    folder_path: str = Field(..., min_length=1)
    extensions: List[str] = Field(..., min_items=1)

class CancelSchema(BaseModel):
    session_id: str = Field(..., min_length=1)

# SSE payload helper
def format_sse(event: str, data: dict) -> str:
    payload = {
        "event": event,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data
    }
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"

# Cleanup logic encapsulated
class SessionCleanup:
    def __init__(self, session: ProcessingSession):
        self.session = session
        self.SessionLocal = sessionmaker(bind=db.engine)

    def run(self) -> None:
        logger.info(f"Starting cleanup for session {self.session.session_id}")
        items = self.session.file_items
        if not items:
            logger.info("No file items to clean")
            return

        ids, paths = [], []
        for x in items:
            if isinstance(x, int): ids.append(x)
            elif isinstance(x, dict) and 'id' in x: ids.append(x['id'])
            elif isinstance(x, str): paths.append(x)

        if paths and not ids:
            db_sess = self.SessionLocal()
            files = db_sess.query(File).filter(File.file_path.in_(paths)).all()
            ids = [f.id for f in files]
            db_sess.close()

        if ids:
            try:
                namespace = os.getenv("PINECONE_NAMESPACE", "default-namespace")
                PineconeClient().delete(ids=[str(i) for i in ids], namespace=namespace)
                logger.info(f"Pinecone vectors deleted for IDs {ids}")
            except Exception as e:
                logger.error(f"Pinecone deletion error: {e}")

            db_sess = self.SessionLocal()
            try:
                db_sess.query(File).filter(File.id.in_(ids)).delete(synchronize_session=False)
                db_sess.commit()
                logger.info(f"DB rows deleted for IDs {ids}")
            except Exception as e:
                db_sess.rollback()
                logger.error(f"DB deletion error: {e}")
            finally:
                db_sess.close()

# Background task function
from flask import Flask

def process_folder_task(folder_path: str, extensions: List[str], session_id: str) -> None:
    # Ensure application context for DB
    app = current_app._get_current_object()
    with app.app_context():
        logger.info(f"Entered process_folder_task for session {session_id} with folder {folder_path} and extensions {extensions}")
        session = sessions.get(session_id)
        try:
            if not session:
                logger.error(f"Session {session_id} not found at task start")
                return
            if session.cancelled:
                logger.info(f"Session {session_id} is cancelled before start")
                return
            results = {}

            # PHASE 1: Scan
            session.progress = 1
            logger.info(f"Session {session_id}: starting scan")
            scan_res = scan_and_add_files_wrapper(folder_path, extensions)
            session.file_items = scan_res.get('added', [])
            results['scan'] = scan_res
            logger.info(f"Scan completed: {len(session.file_items)} items for session {session_id}")

            # PHASE 2: Metadata
            def meta_cb(done, total):
                if session.cancelled:
                    raise Exception("Cancelled")
                session.progress = int(done / total * 50)
            meta_res = process_files_for_metadata(type="keywords", progress_callback=meta_cb)
            session.progress = 50
            results['metadata'] = meta_res
            logger.info(f"Metadata generation completed for session {session_id}")

            # PHASE 3: Vector Upsert
            def vec_cb(done, total):
                if session.cancelled:
                    raise Exception("Cancelled")
                session.progress = 50 + int(done / total * 50)
            vec_res = upsert_files_to_vector_db(progress_callback=vec_cb)
            session.progress = 100
            results['vector'] = vec_res
            logger.info(f"Vector upsert completed for session {session_id}")

            session.final = results
            logger.info(f"Task complete for session {session_id}")
        except Exception as e:
            logger.exception(f"Error in processing task for session {session_id}")
            if session:
                session.final = {"error": str(e)}

# Routes
@file_bp.route('/process_folder', methods=['POST'])
def start_process_folder() -> Response:
    """Validate input and enqueue folder processing."""
    try:
        payload = ProcessFolderSchema(**request.get_json() or {})
    except ValidationError as ve:
        return jsonify({"error": {"code": 400, "message": ve.errors()}}), 400

    session = sessions.create()
    job_queue.put((payload.folder_path, payload.extensions, session.session_id))
    logger.info(f"Enqueued job for session {session.session_id}")
    return jsonify({"sessionId": session.session_id}), 202

@file_bp.route('/process_folder', methods=['GET'])
def stream_process_folder() -> Response:
    """Stream SSE events for progress, file items, and completion."""
    session_id = request.args.get('session_id')
    session = sessions.get(session_id)
    if not session:
        return Response(format_sse('error', {"error": "Invalid session_id"}), mimetype='text/event-stream')

    sent_scan_items = False
    last_progress = session.progress

    def event_stream():
        nonlocal sent_scan_items, last_progress
        # initial progress
        yield format_sse('progress', {'value': last_progress})
        while True:
            sess = sessions.get(session_id)
            if not sess:
                break
            if sess.file_items and not sent_scan_items:
                yield format_sse('scan', {'files': sess.file_items})
                sent_scan_items = True
            if sess.progress != last_progress:
                yield format_sse('progress', {'value': sess.progress})
                last_progress = sess.progress
            if sess.final is not None:
                yield format_sse('complete', sess.final)
                sessions.delete(session_id)
                break
            time.sleep(0.5)

    return Response(
        stream_with_context(event_stream()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive'}
    )

@file_bp.route('/process_folder/cancel', methods=['POST'])
def cancel_process_folder() -> Response:
    """Mark a session cancelled and trigger cleanup."""
    try:
        payload = CancelSchema(**request.get_json() or {})
    except ValidationError as ve:
        return jsonify({"error": {"code": 400, "message": ve.errors()}}), 400

    session = sessions.get(payload.session_id)
    if not session:
        return jsonify({"error": {"code": 404, "message": "Session not found"}}), 404

    session.cancelled = True
    SessionCleanup(session).run()
    session.final = {"error": "Processing cancelled by user"}
    return jsonify({"status": "cancelled"}), 200
