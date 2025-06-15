from flask_socketio import join_room
from flask import current_app
import logging
import threading
import time

from utils.websockets.sockets import socketio


logger = logging.getLogger(__name__)

# Dictionary to track if client has joined room: {session_id: bool}
client_joined_rooms = {}

def emit_upload_started(session_id, total_files):
    if not client_joined_rooms.get(session_id, False):
        logger.info(f"Buffering upload_started event for session {session_id} until client joins room")
        buffer_event(session_id, ('upload_started', {'total_files': total_files}))
        return
    room = session_id
    logger.info(f"Emitting upload_started to session {session_id} with total_files={total_files}")
    socketio.emit('upload_started', {'total_files': total_files}, room=room, namespace='/upload', broadcast=True)

def emit_file_uploaded(session_id, file_name):
    if not client_joined_rooms.get(session_id, False):
        logger.info(f"Buffering file_uploaded event for session {session_id} until client joins room")
        buffer_event(session_id, ('file_uploaded', {'file_name': file_name}))
        return
    room = session_id
    logger.info(f"Emitting file_uploaded to session {session_id} for file {file_name}")
    socketio.emit('file_uploaded', {'file_name': file_name}, room=room, namespace='/upload', broadcast=True)

def emit_file_failed(session_id, file_name, error_message):
    if not client_joined_rooms.get(session_id, False):
        logger.info(f"Buffering file_failed event for session {session_id} until client joins room")
        buffer_event(session_id, ('file_failed', {'file_name': file_name, 'error': error_message}))
        return
    room = session_id
    logger.info(f"Emitting file_failed to session {session_id} for file {file_name} with error {error_message}")
    socketio.emit('file_failed', {'file_name': file_name, 'error': error_message}, room=room, namespace='/upload', broadcast=True)

def emit_upload_complete(session_id, summary):
    if not client_joined_rooms.get(session_id, False):
        logger.info(f"Buffering upload_complete event for session {session_id} until client joins room")
        buffer_event(session_id, ('upload_complete', summary))
        return
    room = session_id
    logger.info(f"Emitting upload_complete to session {session_id} with summary")
    socketio.emit('upload_complete', summary, room=room, namespace='/upload', broadcast=True)

# Buffer to hold events until client joins room: {session_id: [ (event_name, data), ... ]}
event_buffer = {}

def buffer_event(session_id, event):
    if session_id not in event_buffer:
        event_buffer[session_id] = []
    event_buffer[session_id].append(event)

def flush_buffered_events(session_id):
    if session_id in event_buffer:
        logger.info(f"Flushing buffered events for session {session_id}")
        for event_name, data in event_buffer[session_id]:
            socketio.emit(event_name, data, room=session_id, namespace='/upload', broadcast=True)
        event_buffer[session_id] = []

def join_upload_room(session_id):
    join_room(session_id, namespace='/upload')
    client_joined_rooms[session_id] = True
    logger.info(f"Client joined room {session_id} for upload tracking")
    print(f"Client joined room {session_id} for upload tracking")
    flush_buffered_events(session_id)

def websocket_event_listener(ws_queue, session_id, stop_event):
    """Background thread to listen on ws_queue and emit websocket events."""
    logger.info(f"Starting websocket event listener for session {session_id}")
    while not stop_event.is_set():
        try:
            msg = ws_queue.get(timeout=1)
            logger.info(f"Dequeued websocket message for session {session_id}: {msg}")
            if "upload_started" in msg:
                logger.info(f"Emitting upload_started event with count: {msg['upload_started']}")
                emit_upload_started(session_id, msg["upload_started"])
            elif "file" in msg:
                if msg.get("success", False):
                    emit_file_uploaded(session_id, msg["file"])
                else:
                    emit_file_failed(session_id, msg["file"], msg.get("error", "Unknown error"))
            elif "complete" in msg:
                emit_upload_complete(session_id, msg.get("summary", {}))
                logger.info(f"Upload complete event emitted for session {session_id}")
                break
        except Exception:
            time.sleep(0.1)
    logger.info(f"Websocket event listener stopped for session {session_id}")

