from flask_socketio import SocketIO, emit
import eventlet
from engineio.async_drivers import gevent

# Create a SocketIO instance with CORS allowed (modify cors_allowed_origins as needed)
socketio = SocketIO(cors_allowed_origins="*", async_mode='gevent')

@socketio.on('connect')
def handle_connect():
    print("Client connected")
    # Send a welcome message to the client upon connection
    emit('server_response', {'data': 'Connected to Flask WebSocket server!'})

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

@socketio.on('client_message')
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
    emit('server_response', response)
