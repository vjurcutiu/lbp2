from flask import current_app
from sqlalchemy import event
from db.models import Conversation
from utils.websockets.sockets import socketio

def conversation_to_dict(conversation):
    return {
        'id': conversation.id,
        'title': conversation.title,
        'meta_data': conversation.meta_data,
        'created_at': conversation.created_at.isoformat() if conversation.created_at else None,
        'updated_at': conversation.updated_at.isoformat() if conversation.updated_at else None,
    }

@event.listens_for(Conversation, 'after_insert')
def after_insert_conversation(mapper, connection, target):
    # Use the current app context to perform a query
    with current_app.app_context():
        conversations = Conversation.query.all()
        conversation_list = [conversation_to_dict(conv) for conv in conversations]
        # Emit the full list of conversations to all connected clients
        socketio.emit('conversation_list', conversation_list)
        # Emit the new conversation id to all connected clients
        socketio.emit('new_conversation', {'id': target.id})
