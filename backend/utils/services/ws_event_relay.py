import threading
import logging
import time
from utils.websockets.upload_tracking import (
    emit_upload_started,
    emit_file_uploaded,
    emit_file_failed,
    emit_upload_complete,
)

logger = logging.getLogger(__name__)

def ws_queue_relay(ws_queue, session_id, stop_event=None):
    """
    Relay events from ws_queue (multiprocessing.Queue) to websocket clients for a session.
    Launch as a thread in the main process.
    """
    logger.info(f"Starting WebSocket relay for session {session_id}")
    while stop_event is None or not stop_event.is_set():
        try:
            msg = ws_queue.get(timeout=1)
            logger.debug(f"Relaying ws_queue message for {session_id}: {msg}")
            if "upload_started" in msg:
                emit_upload_started(session_id, msg["upload_started"])
            elif "file" in msg:
                if msg.get("success", False):
                    emit_file_uploaded(session_id, msg["file"])
                else:
                    emit_file_failed(session_id, msg["file"], msg.get("error", "Unknown error"))
            elif "complete" in msg:
                emit_upload_complete(session_id, msg.get("summary", {}))
                logger.info(f"WebSocket relay: upload complete for {session_id}")
                break  # Stop relay after complete
        except Exception:
            time.sleep(0.1)
    logger.info(f"WebSocket relay stopped for session {session_id}")
