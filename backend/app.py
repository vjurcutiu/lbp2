from gevent import monkey
monkey.patch_all()
import os
import socket
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from flask import Flask
from db.models import db
from routes.chat_routes import chat_bp
from routes.file_processing_routes import file_bp
from routes.extra_routes import extra_bp
from routes.info_routes import info_bp
from flask_migrate import Migrate
from flask_cors import CORS
from utils.websockets.sockets import socketio  # Import the Socket.IO instance
from utils.emitters import emitters
import structlog

app = Flask(__name__)
# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rag_chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
CORS(app)

# Register blueprints
app.register_blueprint(chat_bp, url_prefix='/conversation')
app.register_blueprint(file_bp)
app.register_blueprint(extra_bp, url_prefix='/extra')
app.register_blueprint(info_bp, url_prefix='/info')

# Initialize SocketIO with the Flask app
socketio.init_app(app)

# Logging configuration
LOG_DIR = os.path.join(app.instance_path, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, 'app.log')

# Configure root logger
root = logging.getLogger()
root.setLevel(logging.DEBUG)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter("%(message)s"))
root.addHandler(console_handler)

# File handler (size-based rotation)
file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter("%(message)s"))
root.addHandler(file_handler)

# Optional: daily rotation instead of size
# time_handler = TimedRotatingFileHandler(log_file, when='midnight', backupCount=7)
# time_handler.setLevel(logging.DEBUG)
# time_handler.setFormatter(logging.Formatter("%(message)s"))
# root.addHandler(time_handler)

# Structlog integration
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__).bind(component="app")


def get_free_port(start_port=5000, max_port=5100):
    """Find a free port between start_port and max_port on localhost."""
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
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
    logger.info("app starting", host="127.0.0.1", port=port, debug=app.debug)
    socketio.run(app, debug=True, host="127.0.0.1", port=port)
