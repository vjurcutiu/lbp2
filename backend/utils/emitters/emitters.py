from flask import current_app
from sqlalchemy import event
from db.models import Conversation
from utils.websockets.sockets import socketio
from db.models import db  # Adjust the import to match your project structure

def conversation_to_dict(conversation):
    return {
        'id': conversation.id,
        'title': conversation.title,
        'meta_data': conversation.meta_data,
        'created_at': conversation.created_at.isoformat() if conversation.created_at else None,
        'updated_at': conversation.updated_at.isoformat() if conversation.updated_at else None,
    }

@event.listens_for(db.session, "after_commit")
def after_commit(session):
    return