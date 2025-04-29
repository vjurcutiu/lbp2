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

class Emitter:
    @staticmethod
    def emit(event_name, data, broadcast=True):
        """Emit an event with a given name and data.

        Parameters:
          event_name (str): The name of the event (e.g., "conversation_update" or "new_message").
          data (dict): The payload to send to the frontend.
          broadcast (bool): Whether to broadcast to all connected clients.
        """
        logging.info(f"Emitting event '{event_name}' with data: {data}")
        socketio.emit(event_name, data)

# Optionally, you could add more helper methods or parameter validations here.

def emit_conversation_update(conversation_id, broadcast=True):
    conversation = Conversation.query.get(conversation_id)
    if conversation:
        conversation_data = conversation_to_dict(conversation)
        logging.info(f"Emitting update for Conversation ID {conversation_id}")
        Emitter.emit("conversation_update", conversation_data, broadcast=broadcast)
    else:
        logging.error(f"Conversation with ID {conversation_id} not found.")

def emit_all_conversations(broadcast=True):
    conversations = Conversation.query.all()
    conversation_list = [conversation_to_dict(conv) for conv in conversations]
    logging.info("Emitting list of all conversations")
    Emitter.emit("conversation_list", conversation_list, broadcast=broadcast)