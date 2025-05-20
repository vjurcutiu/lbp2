import os
import uuid
import json
import logging
from multiprocessing import Pool, Manager, freeze_support, get_start_method
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any, Callable

from flask import (
    Blueprint,
    request,
    jsonify,
    Response,
    stream_with_context,
    Flask,
)
from pydantic import BaseModel, ValidationError, Field
from sqlalchemy.orm import sessionmaker

from db.models import File, db
from utils.file_processing import (
    scan_and_add_files_wrapper,
)
from utils.pinecone_client import PineconeClient
from functools import wraps

# -----------------------------------------------------------------------------
# Configuration ----------------------------------------------------------------
# -----------------------------------------------------------------------------

#: Cap the parallelism for per‑file work (metadata & vector phases).  
#: Clamp to available cores to avoid creating hundreds of threads when the
#: service runs on a beefy machine but the workload is mostly I/O bound.
MAX_PARALLEL_WORKERS: int = min(
    int(os.getenv("PARALLEL_WORKERS", "10")), os.cpu_count() or 4
)

# -----------------------------------------------------------------------------
# Logging configuration -------------------------------------------------------
# -----------------------------------------------------------------------------

logger = logging.getLogger(__name__)
if not logger.handlers:  # avoid duplicate handlers when re‑imported by workers
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "{"  # opening brace for JSON object
        "\"timestamp\": \"%(asctime)s\", "
        "\"level\": \"%(levelname)s\", "
        "\"module\": \"%(module)s\", "
        "\"funcName\": \"%(funcName)s\", "
        "\"lineno\": %(lineno)d, "
        "\"message\": \"%(message)s\""
        "}"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

# Convenience decorator to log function entry / exit -------------------------

def log_call(level: int = logging.DEBUG):
    """Decorator that logs the entry and exit of the wrapped function."""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.log(level, f"ENTER {func.__name__}")
            try:
                result = func(*args, **kwargs)
                logger.log(level, f"EXIT  {func.__name__}")
                return result
            except Exception as exc:
                logger.exception(f"{func.__name__} raised {exc}")
                raise

        return wrapper

    return decorator


# -----------------------------------------------------------------------------
# Blueprint & multiprocessing primitives -------------------------------------
# -----------------------------------------------------------------------------

file_bp = Blueprint("files", __name__, url_prefix="/files")

# Will initialise Pool and Manager lazily (used only to launch *tasks*, not per‑file work)
manager: Optional[Manager] = None
pool: Optional[Pool] = None
sessions: Optional["SessionStore"] = None

def set_multiprocessing_primitives(mgr, pl, sess_store):
    global manager, pool, sessions
    manager = mgr
    pool = pl
    sessions = sess_store

def get_sessions():
    from flask import current_app
    return getattr(current_app, "sessions", None)


@log_call()
def init_multiprocessing() -> None:
    """Initialise the task‑launcher Pool and Manager exactly once.

    WARNING: On Windows, multiprocessing.Manager and Pool must be created
    in the main process (inside if __name__ == "__main__") to avoid deadlocks.
    """

    import sys

    global manager, pool
    if manager is not None and pool is not None:
        logger.debug("Multiprocessing already initialised — skipping")
        return

    # On Windows, ensure we are in the main process
    if sys.platform == "win32" and __name__ != "__main__":
        logger.error(
            "Multiprocessing primitives must be created in the main process on Windows. "
            "Current __name__ is '%s'. This can cause deadlocks/hangs.",
            __name__,
        )
        raise RuntimeError(
            "Multiprocessing primitives must be created in the main process on Windows."
        )

    # Ensure safe start on Windows / macOS‑spawn
    if get_start_method(allow_none=True) != "fork":
        freeze_support()

    manager = Manager()
    pool = Pool(processes=os.cpu_count())
    logger.info("Initialised task‑pool (size=%s) and Manager", os.cpu_count())


# -----------------------------------------------------------------------------
# Session store ---------------------------------------------------------------
# -----------------------------------------------------------------------------

@dataclass
class ProcessingSession:
    session_id: str
    progress: int = 0
    final: Optional[Dict[str, Any]] = None
    cancelled: bool = False
    file_items: List[Any] = field(default_factory=list)
    queue: Any = None  # multiprocessing.Queue — but not type‑checked


class SessionStore:
    """In‑memory store of active ProcessingSession objects."""

    def __init__(self) -> None:
        self._store: Dict[str, ProcessingSession] = {}

    @log_call()
    def create(self) -> ProcessingSession:
        session_id = uuid.uuid4().hex
        sess = ProcessingSession(session_id=session_id)
        init_multiprocessing()
        sess.queue = manager.Queue()
        self._store[session_id] = sess
        logger.info("Created new session %s", session_id)
        return sess

    @log_call()
    def get(self, session_id: str) -> Optional[ProcessingSession]:
        return self._store.get(session_id)

    @log_call()
    def delete(self, session_id: str) -> None:
        self._store.pop(session_id, None)
        logger.info("Deleted session %s", session_id)


# sessions = SessionStore()  # REMOVED: will be set by main app

# -----------------------------------------------------------------------------
# Schemas ---------------------------------------------------------------------
# -----------------------------------------------------------------------------


class ProcessFolderSchema(BaseModel):
    folder_paths: List[str] = Field(..., min_items=1)
    extensions: List[str] = Field(..., min_items=1)


class CancelSchema(BaseModel):
    session_id: str = Field(..., min_length=1)


# -----------------------------------------------------------------------------
# Helper functions ------------------------------------------------------------
# -----------------------------------------------------------------------------


@log_call()
def format_sse(event: str, data: dict) -> str:
    payload = {"event": event, "timestamp": datetime.utcnow().isoformat(), "data": data}
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


# -----------------------------------------------------------------------------
# Cleanup logic ---------------------------------------------------------------
# -----------------------------------------------------------------------------


class SessionCleanup:
    """Cleanup helper — deletes DB rows and Pinecone vectors for a session."""

    def __init__(self, session: ProcessingSession):
        self.session = session
        self.SessionLocal = sessionmaker(bind=db.engine)

    @log_call(logging.INFO)
    def run(self) -> None:
        logger.info("Starting cleanup for session %s", self.session.session_id)
        items = self.session.file_items
        if not items:
            logger.info("No file items to clean for session %s", self.session.session_id)
            return

        ids: List[int] = []
        paths: List[str] = []
        for x in items:
            if isinstance(x, int):
                ids.append(x)
            elif isinstance(x, dict) and "id" in x:
                ids.append(x["id"])
            elif isinstance(x, str):
                paths.append(x)

        if paths and not ids:
            db_sess = self.SessionLocal()
            files = db_sess.query(File).filter(File.file_path.in_(paths)).all()
            ids = [f.id for f in files]
            db_sess.close()
            logger.debug("Resolved %d DB IDs from file paths", len(ids))

        if not ids:
            logger.warning(
                "Nothing to delete from Pinecone / DB for session %s",
                self.session.session_id,
            )
            return

        # Delete vectors from Pinecone
        try:
            namespace = os.getenv("PINECONE_NAMESPACE", "default-namespace")
            PineconeClient().delete(ids=[str(i) for i in ids], namespace=namespace)
            logger.info(
                "Deleted %d vectors from Pinecone (namespace=%s)", len(ids), namespace
            )
        except Exception as e:
            logger.exception("Pinecone deletion error: %s", e)

        # Delete rows from DB
        db_sess = self.SessionLocal()
        try:
            db_sess.query(File).filter(File.id.in_(ids)).delete(synchronize_session=False)
            db_sess.commit()
            logger.info("Deleted %d rows from DB", len(ids))
        except Exception as e:
            db_sess.rollback()
            logger.exception("DB deletion error: %s", e)
        finally:
            db_sess.close()


# -----------------------------------------------------------------------------
# Background task -------------------------------------------------------------
# -----------------------------------------------------------------------------


def process_folder_task(
    folder_paths: List[str],
    extensions: List[str],
    session_id: str,
    queue,
    app_config: Dict[str, Any],
) -> None:
    """Runs in a worker process — scans folders, then handles per‑file work in a
    *thread* pool (max ``MAX_PARALLEL_WORKERS`` threads) to avoid nesting process
    pools. Progress updates are pushed to the SSE queue.
    
    **NOTE:** We *do not* pass the Flask ``app`` object itself – only its *config*
    (a plain ``dict``) because the app instance is not picklable on Windows /
    macOS‑spawn. A lightweight ad‑hoc ``Flask`` object is created inside the
    worker so that any code that needs ``current_app`` continues to work.
    """

    # --- Ensure logging in worker writes to the main log file ---
    log_path = os.path.join(os.path.dirname(__file__), "..", "instance", "logs", "app.log")
    log_path = os.path.abspath(log_path)
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(logging.Formatter(
        "{"  # opening brace for JSON object
        "\"timestamp\": \"%(asctime)s\", "
        "\"level\": \"%(levelname)s\", "
        "\"module\": \"%(module)s\", "
        "\"funcName\": \"%(funcName)s\", "
        "\"lineno\": %(lineno)d, "
        "\"message\": \"%(message)s\""
        "}"
    ))
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    # Avoid duplicate handlers
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == file_handler.baseFilename for h in root_logger.handlers):
        root_logger.addHandler(file_handler)
    logger.addHandler(file_handler)

    logger.info(
        "Task started for session %s (folders=%s, exts=%s, workers=%s)",
        session_id,
        folder_paths,
        extensions,
        MAX_PARALLEL_WORKERS,
    )

    # Re‑hydrate a minimal Flask app in this process
    app = Flask(__name__)
    app.config.update(app_config)
    from db.models import db
    db.init_app(app)

    with app.app_context():
        # ------------------------------------------------------------------
        # Phase 1: Scan folders --------------------------------------------
        # ------------------------------------------------------------------

        def scan_cb(progress: int) -> None:
            queue.put({"progress": progress // 2})  # first 0‑50 %

        queue.put({"progress": 0})
        all_added: List[Any] = []
        for folder in folder_paths:
            logger.debug("Scanning folder %s", folder)
            res = scan_and_add_files_wrapper(
                folder, extensions, progress_callback=scan_cb
            )
            all_added.extend(res.get("added", []))

        # Let the client know what we found straight away
        queue.put({"scan": all_added})
        logger.info("Scan phase complete — %d files added", len(all_added))

        files = all_added
        total = max(len(files), 1)

        # Helper to send mid‑phase progress --------------------------------
        def _progress(phase_base: int, idx: int) -> int:
            return phase_base + (50 * idx) // total  # each phase is 0‑50 or 50‑100

        # ------------------------------------------------------------------
        # Phase 2: Metadata extraction -------------------------------------
        # ------------------------------------------------------------------
        from utils.file_processing import process_file_for_metadata
        from db.models import File, db

        meta_files = File.query.all()
        to_process = [f for f in meta_files if f.meta_data is None or (isinstance(f.meta_data, dict) and "keywords" not in f.meta_data)]
        logger.info(f"[process_folder_task] Found {len(to_process)} files to process for metadata")

        results = []
        app_ctx = Flask(__name__)
        app_ctx.config.update(app_config)
        from db.models import db as db_ctx
        db_ctx.init_app(app_ctx)

        def process_file_with_context(f):
            with app_ctx.app_context():
                return process_file_for_metadata(f)

        with ThreadPoolExecutor(max_workers=10) as executor:
            for res in executor.map(process_file_with_context, to_process):
                results.append(res)
        with app_ctx.app_context():
            try:
                db_ctx.session.commit()
            except Exception as e:
                db_ctx.session.rollback()
                logger.error(f"[process_folder_task] Error committing metadata: {e}")

        queue.put({"progress": 50})
        logger.info(
            "Metadata phase complete — processed all files in parallel"
        )

        # ------------------------------------------------------------------
        # Phase 3: Vector upsert -------------------------------------------
        # ------------------------------------------------------------------
        from utils.file_processing import upsert_file_to_vector_db

        upsert_files = File.query.filter(File.meta_data.isnot(None), File.is_uploaded == False).all()
        logger.info(f"[process_folder_task] Found {len(upsert_files)} files to upsert to vector DB")

        def upsert_file_with_context(f):
            with app_ctx.app_context():
                return upsert_file_to_vector_db(f)

        with ThreadPoolExecutor(max_workers=10) as executor:
            for _ in executor.map(upsert_file_with_context, upsert_files):
                pass
        with app_ctx.app_context():
            try:
                db_ctx.session.commit()
            except Exception as e:
                db_ctx.session.rollback()
                logger.error(f"[process_folder_task] Error committing vector upload flags: {e}")

        queue.put({"progress": 100})
        logger.info(
            "Vector upsert phase complete — processed all files in parallel"
        )

        # ------------------------------------------------------------------
        # Done -------------------------------------------------------------
        # ------------------------------------------------------------------
        queue.put({"complete": True})
        logger.info("Task complete for session %s", session_id)


# -----------------------------------------------------------------------------
# Module‑level helpers for the pool  ------------------------------------------
# -----------------------------------------------------------------------------


def _square(x):  # noqa: D401  — simple helper for /test_pool
    """Return *x* squared (used only by the test endpoint)."""

    return x * x


# -----------------------------------------------------------------------------
# Routes ----------------------------------------------------------------------
# -----------------------------------------------------------------------------


@file_bp.route("/process_folder", methods=["POST"])
@log_call(logging.INFO)
def start_process_folder() -> Response:
    try:
        payload_dict = request.get_json() or {}
        logger.debug("Received payload: %s", payload_dict)
        payload = ProcessFolderSchema(**payload_dict)
    except ValidationError as ve:
        logger.warning("Validation error: %s", ve)
        return jsonify({"error": {"code": 400, "message": ve.errors()}}), 400

    session_store = get_sessions()
    if session_store is None:
        logger.error("SessionStore is not initialized. Did you forget to set it in the main app?")
        return jsonify({"error": {"code": 500, "message": "Session store not initialized"}}), 500
    session = session_store.create()

    # Pass only the *picklable* config dict to the worker
    # Ensure SQLALCHEMY_DATABASE_URI is always present
    from flask import current_app
    app_config = dict(current_app.config)
    if "SQLALCHEMY_DATABASE_URI" not in app_config:
        import os
        app_config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI", "sqlite:///rag_chat.db")
    app_config["SQLALCHEMY_TRACK_MODIFICATIONS"] = app_config.get("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    logger.debug(
        "Pool is %s before apply_async", "initialised" if pool else "not initialised"
    )
    def log_worker_error(e):
        logger.error("process_folder_task failed: %s", e, exc_info=True)

    pool.apply_async(
        process_folder_task,
        args=(
            payload.folder_paths,
            payload.extensions,
            session.session_id,
            session.queue,
            app_config,
        ),
        error_callback=log_worker_error,
    )
    logger.info(
        "Enqueued multiprocessing job for session %s", session.session_id
    )
    return jsonify({"sessionId": session.session_id}), 202


@file_bp.route("/test_pool", methods=["GET"])
@log_call(logging.INFO)
def test_pool() -> Response:
    init_multiprocessing()

    def log_result(result):
        logger.info("Pool test result: %s", result)

    pool.apply_async(_square, args=(5,), callback=log_result)
    return jsonify({"status": "Pool test task submitted"}), 200


@file_bp.route("/process_folder", methods=["GET"])
@log_call(logging.INFO)
def stream_process_folder() -> Response:
    session_id = request.args.get("session_id")
    session_store = get_sessions()
    if session_store is None:
        logger.error("SessionStore is not initialized. Did you forget to set it in the main app?")
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

    def event_stream():
        logger.info("Client connected to stream for session %s", session_id)
        while True:
            try:
                msg = session.queue.get(timeout=1)
                logger.debug("SSE message: %s", msg)
                if "progress" in msg:
                    yield format_sse("progress", {"value": msg["progress"]})
                elif "scan" in msg:
                    # Cache files on the session so cleanup can work later
                    session.file_items = msg["scan"]
                    yield format_sse("scan", {"files": msg["scan"]})
                elif "complete" in msg:
                    yield format_sse("complete", session.final or {})
                    sessions.delete(session_id)
                    logger.info(
                        "Session %s completed and removed", session_id
                    )
                    break
            except Exception:
                # queue.Empty or others — keep connection alive without burning CPU
                import time

                time.sleep(0.2)
                continue

    return Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@file_bp.route("/process_folder/cancel", methods=["POST"])
@log_call(logging.INFO)
def cancel_process_folder() -> Response:
    try:
        payload_dict = request.get_json() or {}
        payload = CancelSchema(**payload_dict)
    except ValidationError as ve:
        logger.warning("Cancel validation error: %s", ve)
        return jsonify({"error": {"code": 400, "message": ve.errors()}}), 400

    session_store = get_sessions()
    if session_store is None:
        logger.error("SessionStore is not initialized. Did you forget to set it in the main app?")
        return jsonify({"error": {"code": 500, "message": "Session store not initialized"}}), 500
    session = session_store.get(payload.session_id)
    if not session:
        logger.warning(
            "Cancel requested for unknown session %s", payload.session_id
        )
        return jsonify({"error": {"code": 404, "message": "Session not found"}}), 404

    session.cancelled = True
    SessionCleanup(session).run()
    session.final = {"error": "Processing cancelled by user"}
    logger.info("Session %s marked as cancelled", payload.session_id)
    return jsonify({"status": "cancelled"}), 200
