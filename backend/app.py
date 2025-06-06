import os
import socket
import sys
import io
import keyring
import secrets
import logging
from logging.handlers import RotatingFileHandler
import structlog

from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS

from db.models import db
from utils.websockets.sockets import socketio
from utils.emitters.emitters import emitters
from utils.services.ai_api_manager import OpenAIService
from utils.services.conversation_manager import SocketNotifier, ConversationManager

from routes.chat_routes import create_chat_blueprint
from routes.file_processing_routes import file_bp
from routes.extra_routes import extra_bp
from routes.info_routes import info_bp
from routes.api_vault_routes import api_vault_bp

# ───> RAG integration imports
from utils.services.agentic.query_processor import QueryProcessor
from utils.services.agentic.search_router    import SearchRouter
from utils.search     import KeywordSearch, VectorSearch, HybridSearch
from utils.keyword_loader import load_keyword_items, build_keyword_topics

from utils.services.api_vault.secrets import ApiKeyManager
from utils.services.api_vault.secrets_loader import SecretsLoader




def configure_logging(app: Flask):
    """Set up Console, File and structlog logging with UTF-8 encoding."""
    LOG_DIR = os.path.join(app.instance_path, 'logs')
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, 'app.log')

    # Base logger
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Force UTF-8 encoding on Windows consoles (or any stream)
    if hasattr(console_handler.stream, 'reconfigure'):
        # Python 3.7+ supports reconfigure
        console_handler.stream.reconfigure(encoding='utf-8')
    else:
        # Wrap fallback
        console_handler.stream = io.TextIOWrapper(
            sys.stdout.buffer, encoding='utf-8', errors='replace'
        )

    console_handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(console_handler)

    # Rotating File handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'            # <-- ensure file is UTF-8
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(file_handler)

    # structlog configuration
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


def get_free_port(start_port=5000, max_port=5100) -> int:
    """Find a free port between start_port and max_port on localhost."""
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except socket.error:
                continue
    raise RuntimeError("No free port found in the specified range.")


def register_blueprints(app: Flask, conv_manager: ConversationManager):
    # Chat endpoints under /conversation/*
    chat_bp = create_chat_blueprint(conv_manager)
    app.register_blueprint(chat_bp)

    # Other feature blueprints
    app.register_blueprint(file_bp)
    app.register_blueprint(extra_bp, url_prefix='/extra')
    app.register_blueprint(info_bp, url_prefix='/info')
    app.register_blueprint(api_vault_bp, url_prefix='/api-vault')


def register_cli_commands(app: Flask):
    @app.cli.command("prepare-reprocessing")
    def prepare_reprocessing():
        """Mark all documents for reprocessing"""
        from db.models import File

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

        print("Starting document reprocessing...")
        results = upsert_files_to_vector_db()
        print(f"Successfully processed {len(results)} documents")


def create_app(config_object: str = None) -> Flask:
    print("💥 create_app() entered")
    """Application factory: creates and configures the Flask app."""
    app = Flask(__name__, instance_relative_config=True)

    # ── Bootstrap SECRET_KEY via keyring ──
    SERVICE_NAME = "LEXBOT_PRO"              # pick a sensible name
    KR_USERNAME  = "flask-secret-key"       # a fixed “username” for this secret

    secret = keyring.get_password(SERVICE_NAME, KR_USERNAME)
    if secret is None:
        # first run: generate and persist a new one
        secret = secrets.token_hex(32)      # 64 hex chars
        keyring.set_password(SERVICE_NAME, KR_USERNAME, secret)

    app.config['SECRET_KEY'] = secret

    SecretsLoader().load_env()

    key = os.environ.get("OPENAI_API_KEY")
    if key:
        print(f"OPENAI_API_KEY is set and begins with: {key[:8]}…")
    else:
        print("OPENAI_API_KEY is not set in the environment")

    # Load default & override config
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URI', 'sqlite:///rag_chat.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if config_object:
        app.config.from_object(config_object)
    else:
        # Load any instance config, if present
        app.config.from_pyfile('config.py', silent=True)

    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)
    CORS(app)
    socketio.init_app(app)
    emitters.init_app(app)

    # Setup services
    notifier     = SocketNotifier(socketio, app)
    ai_service   = OpenAIService()
    api_key_manager = ApiKeyManager()
    app.api_key_manager = api_key_manager

    # Configure logging (now with UTF-8)
    configure_logging(app)
    app.logger = structlog.get_logger(__name__).bind(component="app")

    # ───> Build RAG pipeline in one place
    with app.app_context():
        import logging
        kw_logger = logging.getLogger("keyword_loader")
        print("keyword_loader handlers:", kw_logger.handlers)
        items  = load_keyword_items()
        topics = build_keyword_topics()

    keyword_search  = KeywordSearch(items)
    vector_search   = HybridSearch()
    qp              = QueryProcessor(ai_service, topics)
    search_router   = SearchRouter(qp, keyword_search, vector_search)
    conv_manager    = ConversationManager(
        db.session,
        ai_service,
        search_router,
        notifier
    )

    # Register blueprints and CLI
    register_blueprints(app, conv_manager)
    register_cli_commands(app)

    return app


if __name__ == '__main__':
    app  = create_app()
    port = get_free_port()
    app.logger.info("app starting", host="127.0.0.1", port=port, debug=app.debug)
    print(f"Starting Flask app on port {port}")
    socketio.run(app, debug=True, host="127.0.0.1", port=port)
