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
from routes.file_processing_routes import file_bp  # *do not* eagerly start MP
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


# -----------------------------------------------------------------------------
# Logging ---------------------------------------------------------------------
# -----------------------------------------------------------------------------

def configure_logging(app: Flask):
    """Set up console & rotating-file logging with structlog JSON renderer."""

    LOG_DIR = os.path.join(app.instance_path, "logs")
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, "app.log")

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Console --------------------------------------------------------------
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    if hasattr(console_handler.stream, "reconfigure"):
        console_handler.stream.reconfigure(encoding="utf-8")
    else:
        console_handler.stream = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(console_handler)

    # Rotating file --------------------------------------------------------
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(file_handler)

    # structlog ------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# Utility helpers -------------------------------------------------------------
# -----------------------------------------------------------------------------

def get_free_port(start_port: int = 5000, max_port: int = 5100) -> int:
    """Return the first free localhost TCP port in *[start_port, max_port)*."""
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except socket.error:
                continue
    raise RuntimeError("No free port found in the specified range.")


# -----------------------------------------------------------------------------
# Blueprint + CLI registration ------------------------------------------------
# -----------------------------------------------------------------------------

def register_blueprints(app: Flask, conv_manager: ConversationManager):
    chat_bp = create_chat_blueprint(conv_manager)
    app.register_blueprint(chat_bp)

    app.register_blueprint(file_bp)
    app.register_blueprint(extra_bp, url_prefix="/extra")
    app.register_blueprint(info_bp,  url_prefix="/info")
    app.register_blueprint(api_vault_bp, url_prefix="/api-vault")


def register_cli_commands(app: Flask):
    @app.cli.command("prepare-reprocessing")
    def prepare_reprocessing():
        from db.models import File
        if input("Mark ALL documents for reprocessing? (y/n): ").lower() == "y":
            File.query.update({"is_uploaded": False}, synchronize_session='fetch')
            db.session.commit()
            print(f"Marked {File.query.count()} documents for reprocessing")
        else:
            print("Cancelled")

    @app.cli.command("reprocess-documents")
    def reprocess_documents():
        from utils.file_processing import upsert_files_to_vector_db
        print("Starting document reprocessing…")
        results = upsert_files_to_vector_db()
        print(f"Successfully processed {len(results)} documents")


# -----------------------------------------------------------------------------
# Application factory ---------------------------------------------------------
# -----------------------------------------------------------------------------

def create_app(config_object: str | None = None) -> Flask:  # noqa: D401
    """Flask application factory."""

    app = Flask(__name__, instance_relative_config=True)

    # ── SECRET_KEY — persisted in keyring ────────────────────────────────
    SERVICE_NAME = "LEXBOT_PRO"
    KR_USERNAME  = "flask-secret-key"
    secret = keyring.get_password(SERVICE_NAME, KR_USERNAME)
    if secret is None:
        secret = secrets.token_hex(32)
        keyring.set_password(SERVICE_NAME, KR_USERNAME, secret)
    app.config["SECRET_KEY"] = secret

    # ── Load env & configuration ─────────────────────────────────────────
    SecretsLoader().load_env()

    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URI", "sqlite:///rag_chat.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if config_object:
        app.config.from_object(config_object)
    else:
        app.config.from_pyfile("config.py", silent=True)

    os.makedirs(app.instance_path, exist_ok=True)  # ensure instance dir

    # ── Extensions --------------------------------------------------------
    db.init_app(app)
    Migrate(app, db)
    CORS(app)
    # Keep original SocketIO async mode (eventlet/gevent) — no explicit override
    socketio.init_app(app)
    emitters.init_app(app)

    # ── Logging ----------------------------------------------------------
    configure_logging(app)
    app.logger = structlog.get_logger(__name__).bind(component="app")

    # ── Services ---------------------------------------------------------
    notifier        = SocketNotifier(socketio, app)
    ai_service      = OpenAIService()
    api_key_manager = ApiKeyManager()
    app.api_key_manager = api_key_manager

    # ── Build RAG pipeline once -----------------------------------------
    with app.app_context():
        kw_logger = logging.getLogger("keyword_loader")
        app.logger.debug("keyword_loader handlers: %s", kw_logger.handlers)
        items  = load_keyword_items()
        topics = build_keyword_topics()

    keyword_search  = KeywordSearch(items)
    vector_search   = HybridSearch()
    qp              = QueryProcessor(ai_service, topics)
    search_router   = SearchRouter(qp, keyword_search, vector_search)
    conv_manager    = ConversationManager(db.session, ai_service, search_router, notifier)

    register_blueprints(app, conv_manager)
    register_cli_commands(app)
    # NOTE: *do not* call init_multiprocessing() here — each worker will do so lazily

    return app


# -----------------------------------------------------------------------------
# Local dev entry-point -------------------------------------------------------
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    # Required on Windows / macOS-spawn so that child processes can start cleanly
    from multiprocessing import freeze_support
    from multiprocessing import Manager, Pool
    from multiprocessing import freeze_support, Manager, Pool
    from services.mp_init import set_pool_and_manager
    from services.session_store import SessionStore
    from routes.file_processing_routes import set_session_store

    freeze_support()

    app = create_app()

    # --- Multiprocessing-safe initialization ---
    manager = Manager()
    pool = Pool()
    sessions = SessionStore()

    set_pool_and_manager(manager, pool)
    set_session_store(sessions)
    app.sessions = sessions

    port = get_free_port()
    app.logger.info("app starting", host="127.0.0.1", port=port, debug=app.debug)
    print(f"Starting Flask app on port {port}")
    socketio.run(app, debug=True, host="127.0.0.1", port=port)
