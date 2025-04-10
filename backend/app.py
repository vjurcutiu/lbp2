from gevent import monkey
monkey.patch_all()
import socket
from flask import Flask
from db.models import db
from routes.chat_routes import chat_bp
from routes.file_processing_routes import file_bp
from routes.extra_routes import extra_bp
from flask_migrate import Migrate
from flask_cors import CORS
from utils.websockets.sockets import socketio  # Import the Socket.IO instance
from utils.emitters import emitters
from routes.info_routes import info_bp

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rag_chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)
CORS(app)  # Enable CORS for all routes

# Register blueprints
app.register_blueprint(chat_bp, url_prefix='/conversation')
app.register_blueprint(file_bp, url_prefix='/files')
app.register_blueprint(extra_bp, url_prefix='/extra')
app.register_blueprint(info_bp, url_prefix='/info')

# Initialize SocketIO with the Flask app
socketio.init_app(app)
print(f"Using async mode in app.py: {socketio.server.async_mode}")


def get_free_port(start_port=5000, max_port=5100):
    """Find a free port between start_port and max_port on localhost."""
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                # Binding to localhost ensures the application is only available locally
                sock.bind(("127.0.0.1", port))
                return port
            except socket.error:
                continue
    raise RuntimeError("No free port found in the specified range.")

@app.cli.command("prepare-reprocessing")
def prepare_reprocessing():
    """Mark all documents for reprocessing"""
    from db.models import File
    
    with app.app_context():
        if input("Mark ALL documents for reprocessing? (y/n): ").lower() == 'y':
            # Reset upload status and clear existing embeddings
            File.query.update({'is_uploaded': False})
            db.session.commit()
            print(f"Marked {File.query.count()} documents for reprocessing")
        else:
            print("Cancelled")

@app.cli.command("reprocess-documents")
def reprocess_documents():
    """Custom Flask command to reprocess all documents"""
    from utils.file_processing import upsert_files_to_vector_db
    
    with app.app_context():
        print("Starting document reprocessing...")
        results = upsert_files_to_vector_db()
        print(f"Successfully processed {len(results)} documents")

if __name__ == '__main__':
    port = get_free_port()
    print(f"Starting Flask app on port {port}")
    # Ensure we're binding to localhost (127.0.0.1)
    socketio.run(app, debug=True, host="127.0.0.1", port=port)
