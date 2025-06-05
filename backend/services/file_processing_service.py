import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

from flask import Flask
from db.models import File, db
from utils.file_processing import scan_and_add_files_wrapper, process_file_for_metadata, upsert_file_to_vector_db

logger = logging.getLogger(__name__)

def process_folder_task(
    folder_paths: List[str],
    extensions: List[str],
    session_id: str,
    queue,
    app_config: Dict[str, Any],
) -> None:
    """Runs in a worker process — scans folders, then handles per-file work in a
    thread pool (max workers) to avoid nesting process pools. Emits WebSocket events
    for upload progress and results."""

    # --- Setup logging to main log file ---
    import os
    import logging
    log_path = os.path.join(os.path.dirname(__file__), "..", "instance", "logs", "app.log")
    log_path = os.path.abspath(log_path)
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(logging.Formatter(
        "{"
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
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == file_handler.baseFilename for h in root_logger.handlers):
        root_logger.addHandler(file_handler)
    logger.addHandler(file_handler)

    logger.info(
        "Task started for session %s (folders=%s, exts=%s)",
        session_id,
        folder_paths,
        extensions,
    )

    # Rehydrate minimal Flask app context
    app = Flask(__name__)
    app.config.update(app_config)
    db.init_app(app)

    with app.app_context():
        # Phase 1: Scan folders
        def scan_cb(progress: int) -> None:
            queue.put({"progress": progress // 2})  # first 0-50%

        queue.put({"progress": 0})
        all_added: List[Any] = []
        for folder in folder_paths:
            logger.debug("Scanning folder %s", folder)
            res = scan_and_add_files_wrapper(folder, extensions, progress_callback=scan_cb)
            all_added.extend(res.get("added", []))

        queue.put({"scan": all_added})
        logger.info("Scan phase complete — %d files added", len(all_added))

        # Notify frontend about upload start
        queue.put({"upload_started": len(all_added), "session_id": session_id})

        files = all_added
        total = max(len(files), 1)

        # Phase 2: Metadata extraction
        meta_files = File.query.all()
        to_process = [f for f in meta_files if f.meta_data is None or (isinstance(f.meta_data, dict) and "keywords" not in f.meta_data)]
        logger.info(f"Found {len(to_process)} files to process for metadata")

        results = []
        app_ctx = Flask(__name__)
        app_ctx.config.update(app_config)
        db_ctx = db
        db_ctx.init_app(app_ctx)

        def process_file_with_context(f):
            with app_ctx.app_context():
                try:
                    result = process_file_for_metadata(f)
                    return (f, True, None)
                except Exception as e:
                    logger.error(f"Error processing file {f.file_path}: {e}")
                    return (f, False, str(e))

        with ThreadPoolExecutor(max_workers=10) as executor:
            for res in executor.map(process_file_with_context, to_process):
                results.append(res)
        with app_ctx.app_context():
            try:
                db_ctx.session.commit()
            except Exception as e:
                db_ctx.session.rollback()
                logger.error(f"Error committing metadata: {e}")

        # Phase 3: Vector upsert
        upsert_files = File.query.filter(File.meta_data.isnot(None), File.is_uploaded == False).all()
        logger.info(f"Found {len(upsert_files)} files to upsert to vector DB")

        def upsert_file_with_context(f):
            with app_ctx.app_context():
                try:
                    result = upsert_file_to_vector_db(f)
                    return (f, True, None)
                except Exception as e:
                    logger.error(f"Error upserting file {f.file_path}: {e}")
                    return (f, False, str(e))

        upsert_results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            for res in executor.map(upsert_file_with_context, upsert_files):
                upsert_results.append(res)
        with app_ctx.app_context():
            try:
                db_ctx.session.commit()
            except Exception as e:
                db_ctx.session.rollback()
                logger.error(f"Error committing vector upload flags: {e}")

        # Combine results
        combined_results = {}
        for f, success, error in results:
            combined_results[f.file_path] = (success, error)
        for f, success, error in upsert_results:
            combined_results[f.file_path] = (success, error)

        # Enqueue per-file events for SSE/WebSocket bridge
        for file_path, (success, error) in combined_results.items():
            queue.put({
                "file": file_path,
                "success": success,
                "error": error,
                "session_id": session_id,
            })

        # Emit upload complete summary
        total_files = len(combined_results)
        uploaded_files = sum(1 for success, _ in combined_results.values() if success)
        failed_files = [
            {"file_name": file_path, "error": error}
            for file_path, (success, error) in combined_results.items()
            if not success
        ]
        summary = {
            "total_files": total_files,
            "uploaded_files": uploaded_files,
            "failed_files": failed_files,
        }
        # Final summary
        queue.put({"complete": True, "summary": summary, "session_id": session_id})

        logger.info("Task complete for session %s", session_id)
