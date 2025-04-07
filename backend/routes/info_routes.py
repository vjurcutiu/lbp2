from flask import Blueprint, jsonify, abort
from db.models import Conversation

# Create a blueprint for conversation-related routes with a URL prefix.
info_bp = Blueprint('info', __name__)

@info_bp.route('/<int:conversation_id>/title', methods=['GET'])
def get_conversation_title(conversation_id):
    # Query the database for the conversation by ID.
    conversation = Conversation.query.get(conversation_id)
    if conversation is None:
        abort(404, description="Conversation not found")
    # Return the conversation title as JSON.
    return jsonify({'title': conversation.title})
