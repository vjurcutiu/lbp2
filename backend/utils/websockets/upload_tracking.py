from flask_socketio import emit, join_room
from flask import current_app
import logging

logger = logging.getLogger(__name__)

def emit_upload_started(session_id, total_files):
    room = session_id
    logger.info(f"Emitting upload_started to session {session_id} with total_files={total_files}")
    emit('upload_started', {'total_files': total_files}, room=room, namespace='/upload')

def emit_file_uploaded(session_id, file_name):
    room = session_id
    logger.info(f"Emitting file_uploaded to session {session_id} for file {file_name}")
    emit('file_uploaded', {'file_name': file_name}, room=room, namespace='/upload')

def emit_file_failed(session_id, file_name, error_message):
    room = session_id
    logger.info(f"Emitting file_failed to session {session_id} for file {file_name} with error {error_message}")
    emit('file_failed', {'file_name': file_name, 'error': error_message}, room=room, namespace='/upload')

def emit_upload_complete(session_id, summary):
    room = session_id
    logger.info(f"Emitting upload_complete to session {session_id} with summary")
    emit('upload_complete', summary, room=room, namespace='/upload')

def join_upload_room(session_id):
    join_room(session_id, namespace='/upload')
    logger.info(f"Client joined room {session_id} for upload tracking")
