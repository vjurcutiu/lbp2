from flask_socketio import SocketIO, emit
import eventlet
from engineio.async_drivers import gevent
from flask import request


# Create a SocketIO instance with CORS allowed (modify cors_allowed_origins as needed)
socketio = SocketIO(cors_allowed_origins="*", async_mode='gevent')

from utils.websockets.upload_tracking import join_upload_room

@socketio.on('connect', namespace='/upload')
def handle_connect(auth = None):
    print('Request args:', dict(request.args))
    session_id = auth.get('session_id') if auth else None
    if session_id:
        join_upload_room(session_id)
        # Send a test message to client after joining room
        emit('test_message', {'message': 'Test message from server'}, room=session_id, namespace='/upload')
    print(f"Client connected to upload namespace with session_id={session_id}")
    emit('server_response', {'data': 'Connected to Flask WebSocket server!'}, namespace='/upload')

@socketio.on('disconnect', namespace='/upload')
def handle_disconnect():
    print("Client disconnected from upload namespace")


@socketio.on('client_message', namespace='/upload')
def handle_message(data):
    print(f"Received message: {data}")
    # Process the incoming message conditionally
    if data.get('type') == 'greeting':
        response = {'data': 'Hello from Flask!'}
    elif data.get('type') == 'farewell':
        response = {'data': 'Goodbye from Flask!'}
    else:
        response = {'data': 'Message received'}
    # Emit the response back to the client
    emit('server_response', response, namespace='/upload')

@socketio.on('heartbeat', namespace='/upload')
def handle_heartbeat(data):
    print(f"Received heartbeat ping: {data}")
    # Optionally, send a pong or acknowledgment back
    emit('heartbeat_ack', {'timestamp': data.get('timestamp')}, namespace='/upload')
