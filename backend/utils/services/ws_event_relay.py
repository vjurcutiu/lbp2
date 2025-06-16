import threading
import logging
import time
from utils.websockets.upload_tracking import (
    emit_upload_started,
    emit_file_uploaded,
    emit_file_failed,
    emit_upload_complete,
)
import queue

logger = logging.getLogger(__name__)

def ws_queue_relay(ws_queue, session_id, stop_event=None):
    logger.info(f"Starting WebSocket relay for session {session_id}")
    while stop_event is None or not stop_event.is_set():
        try:
            msg = ws_queue.get(timeout=1)
            logger.info(f"[WS RELAY] Got message for session {session_id}: {msg!r}")
            if "upload_started" in msg:
                logger.info(f"[WS RELAY] Calling emit_upload_started for {session_id}")
                emit_upload_started(session_id, msg["upload_started"])
            elif "file" in msg:
                if msg.get("success", False):
                    logger.info(f"[WS RELAY] Calling emit_file_uploaded for {session_id}, file: {msg['file']}")
                    emit_file_uploaded(session_id, msg["file"])
                else:
                    logger.info(f"[WS RELAY] Calling emit_file_failed for {session_id}, file: {msg['file']}, error: {msg.get('error')}")
                    emit_file_failed(session_id, msg["file"], msg.get("error", "Unknown error"))
            elif "complete" in msg:
                logger.info(f"[WS RELAY] Calling emit_upload_complete for {session_id}")
                emit_upload_complete(session_id, msg.get("summary", {}))
                logger.info(f"[WS RELAY] upload complete for {session_id}")
                break  # Stop relay after complete
        except Exception as e:
            logger.error(f"[WS RELAY] Exception in relay for {session_id}: {e}", exc_info=True)
            time.sleep(0.1)
        except queue.Empty:
            logger.info(f"[WS RELAY] No messages in queue for session {session_id}")
    logger.info(f"WebSocket relay stopped for session {session_id}")
