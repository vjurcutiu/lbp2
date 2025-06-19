import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
from flask import Flask
from db.models import File, db
from features.file_processing.file_pipeline import (
    scan_and_add_files_wrapper,
    process_file_for_metadata,
    upsert_file_to_vector_db,
)

logger = logging.getLogger("file_processing_service")

def process_folder_task(
    folder_paths: List[str],
    extensions: List[str],
    session_id: str,
    ws_queue,
    app_config: Dict[str, Any],
) -> None:
    """
    Worker process: scans folders, processes files in parallel, and puts websocket events on ws_queue.
    This version always queries model objects inside worker app contexts to avoid SQLAlchemy threading/session issues.
    """
    import os
    import logging
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    log_path = r"c:/code/lbp2/backend/instance/logs/app.log"
    log_dir = os.path.dirname(log_path)
    os.makedirs(log_dir, exist_ok=True)
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

    logger.info("file_processing_service.process_folder_task: Task started for session %s (folders=%s, exts=%s)", session_id, folder_paths, extensions)

    app = Flask(__name__)
    app.config.update(app_config)
    db.init_app(app)

    with app.app_context():
        # --- Scan Phase ---
        logger.info("file_processing_service.process_folder_task: Starting scan phase for folders: %s", folder_paths)
        all_added: List[Any] = []
        for folder in folder_paths:
            logger.info("file_processing_service.process_folder_task: Scanning folder: %s", folder)
            try:
                res = scan_and_add_files_wrapper(folder, extensions)
                logger.info("file_processing_service.process_folder_task: Scan result for folder %s: %s", folder, res)
                all_added.extend(res.get("added", []))
            except Exception as e:
                logger.error("file_processing_service.process_folder_task: Error scanning folder %s: %s", folder, e)
        logger.info("file_processing_service.process_folder_task: Scan phase complete. Files added: %d", len(all_added))

        ws_queue.put({"upload_started": len(all_added), "session_id": session_id})

        files = all_added
        total = max(len(files), 1)

        # --- Metadata Extraction Phase ---
        logger.info("file_processing_service.process_folder_task: Starting metadata extraction phase")
        meta_files = File.query.all()
        to_process = [f.id for f in meta_files if f.meta_data is None or (isinstance(f.meta_data, dict) and "keywords" not in f.meta_data)]
        logger.info("file_processing_service.process_folder_task: Files to process for metadata: %d", len(to_process))
        results = []
        app_ctx = Flask(__name__)
        app_ctx.config.update(app_config)
        db_ctx = db
        db_ctx.init_app(app_ctx)

        def process_file_with_context(file_id):
            with app_ctx.app_context():
                try:
                    f = File.query.get(file_id)
                    if f is None:
                        logger.warning("File with id %s not found for metadata processing", file_id)
                        return (str(file_id), False, "File not found")
                    logger.info("file_processing_service.process_folder_task: Processing file for metadata: %s", f.file_path)
                    result = process_file_for_metadata(f)
                    db_ctx.session.commit()  # Commit after processing metadata
                    logger.info("file_processing_service.process_folder_task: Successfully processed metadata for: %s", f.file_path)
                    return (f.file_path, True, None)
                except Exception as e:
                    db_ctx.session.rollback()
                    logger.error("file_processing_service.process_folder_task: Error processing file %s: %s", file_id, e)
                    return (str(file_id), False, str(e))

        with ThreadPoolExecutor(max_workers=10) as executor:
            for res in executor.map(process_file_with_context, to_process):
                results.append(res)

        # --- Vector Upsert Phase ---
        logger.info("file_processing_service.process_folder_task: Starting vector upsert phase")
        upsert_files = File.query.filter(File.meta_data.isnot(None), File.is_uploaded == False).all()
        upsert_file_ids = [f.id for f in upsert_files]
        logger.info("file_processing_service.process_folder_task: Files to upsert to vector DB: %d", len(upsert_file_ids))

        def upsert_file_with_context(file_id):
            with app_ctx.app_context():
                try:
                    f = File.query.get(file_id)
                    if f is None:
                        logger.warning("File with id %s not found for vector upsert", file_id)
                        return (str(file_id), False, "File not found")
                    logger.info("file_processing_service.process_folder_task: Upserting file to vector DB: %s", f.file_path)
                    result = upsert_file_to_vector_db(f)
                    db_ctx.session.commit()  # Commit after vector upsert
                    logger.info("file_processing_service.process_folder_task: Successfully upserted: %s", f.file_path)
                    return (f.file_path, True, None)
                except Exception as e:
                    db_ctx.session.rollback()
                    logger.error("file_processing_service.process_folder_task: Error upserting file %s: %s", file_id, e)
                    return (str(file_id), False, str(e))

        upsert_results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            for res in executor.map(upsert_file_with_context, upsert_file_ids):
                upsert_results.append(res)

        # --- Combine Results, WebSocket Events, and Summary ---
        logger.info("file_processing_service.process_folder_task: Combining results")
        combined_results = {}
        for file_path, success, error in results:
            combined_results[file_path] = (success, error)
        for file_path, success, error in upsert_results:
            combined_results[file_path] = (success, error)

        logger.info("file_processing_service.process_folder_task: Sending per-file websocket events")
        for file_path, (success, error) in combined_results.items():
            ws_queue.put({
                "file": file_path,
                "success": success,
                "error": error,
                "session_id": session_id,
            })

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
        ws_queue.put({"complete": True, "summary": summary, "session_id": session_id})
        logger.info(
            "file_processing_service.process_folder_task: Task complete for session %s (total_files=%d, uploaded_files=%d, failed_files=%d)",
            session_id, total_files, uploaded_files, len(failed_files)
        )
