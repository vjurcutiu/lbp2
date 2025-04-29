from flask import current_app
from sqlalchemy import event
from db.models import Conversation
from utils.websockets.sockets import socketio
from db.models import db  # Adjust the import to match your project structure
import logging

def conversation_to_dict(conversation):
    return {
        'id': conversation.id,
        'title': conversation.title,
        'meta_data': conversation.meta_data,
        'created_at': conversation.created_at.isoformat() if conversation.created_at else None,
        'updated_at': conversation.updated_at.isoformat() if conversation.updated_at else None,
    }

class EmitterManager:
    def __init__(self):
        self.app = None

    def init_app(self, app):
        """
        Initialize emitter manager with Flask app context.
        Registers SQLAlchemy event listeners if needed.
        """
        self.app = app
        # Example: emit full list when a conversation is inserted or updated
        @event.listens_for(Conversation, 'after_insert')
        @event.listens_for(Conversation, 'after_update')
        def _emit_conversation(mapper, connection, target):
            self.emit_conversation_update(target.id)

    def emit(self, event_name, data, broadcast=True):
        """Emit an event via Socket.IO."""
        logging.info(f"Emitting event '{event_name}' with data: {data}")
        socketio.emit(event_name, data, broadcast=broadcast)

    def emit_conversation_update(self, conversation_id, broadcast=True):
        """Emit update for a single conversation."""
        with self.app.app_context():
            conversation = Conversation.query.get(conversation_id)
            if conversation:
                data = conversation_to_dict(conversation)
                self.emit("conversation_update", data, broadcast=broadcast)
            else:
                logging.error(f"Conversation with ID {conversation_id} not found.")

    def emit_all_conversations(self, broadcast=True):
        """Emit list of all conversations."""
        with self.app.app_context():
            conversations = Conversation.query.all()
            data = [conversation_to_dict(conv) for conv in conversations]
            self.emit("conversation_list", data, broadcast=broadcast)

# Singleton instance for application use
emitters = EmitterManager()
