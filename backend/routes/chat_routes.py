from flask import Blueprint, request, jsonify, current_app
from utils.services.conversation_manager import handle_frontend_message
from utils.comms import get_all_conversation_ids, get_all_messages_for_conversation, delete_conversation, rename_conversation
from utils.emitters.emitters import emit_conversation_update, emit_all_conversations

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    message = data.get('message')
    if not message:
        return jsonify({'error': 'No message provided.'}), 400
    conversation_id = data.get('conversation_id')
    additional_params = data.get('additional_params', {})
    try:
        result = handle_frontend_message(
            text=message,
            conversation_id=conversation_id,
            additional_params=additional_params
        )
        return jsonify(result), 200
    except Exception as e:
        current_app.logger.error('Error processing chat message', exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@chat_bp.route('/conversation_ids', methods=['GET'])
def conversation_ids_route():
    try:
        ids = get_all_conversation_ids()
        return jsonify({'conversation_ids': ids}), 200
    except Exception:
        current_app.logger.error('Error fetching conversation ids', exc_info=True)
        return jsonify({'error': 'Failed to fetch conversation ids.'}), 500

@chat_bp.route('/<int:conversation_id>/messages', methods=['GET'])
def get_conversation_messages(conversation_id):
    try:
        msgs = get_all_messages_for_conversation(conversation_id)
        return jsonify({'messages': msgs}), 200
    except Exception:
        current_app.logger.error(f'Error fetching messages for {conversation_id}', exc_info=True)
        return jsonify({'error': 'Failed to retrieve messages.'}), 500

@chat_bp.route('/delete', methods=['POST'])
def delete_conversation_route():
    data = request.get_json() or {}
    convo_id = data.get('conversation_id')
    if not convo_id:
        return jsonify({'error': 'Conversation ID is required.'}), 400
    try:
        res = delete_conversation(convo_id)
        emit_all_conversations()
        status = 200 if 'message' in res else 400
        return jsonify(res), status
    except Exception:
        current_app.logger.error('Error deleting conversation', exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@chat_bp.route('/rename', methods=['POST'])
def rename_conversation_route():
    data = request.get_json() or {}
    convo_id = data.get('conversation_id')
    new_title = data.get('new_title')
    if not (convo_id and new_title):
        return jsonify({'error': 'conversation_id and new_title required.'}), 400
    try:
        res = rename_conversation(convo_id, new_title)
        if 'message' in res:
            emit_conversation_update(convo_id)
            return jsonify(res), 200
        return jsonify(res), 400
    except Exception:
        current_app.logger.error('Error renaming conversation', exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@chat_bp.route('/list', methods=['GET'])
def list_conversations():
    try:
        from db.models import Conversation  # lazy import if needed
        convos = Conversation.query.all()
        conv_list = [c.to_dict() for c in convos]
        return jsonify({'conversations': conv_list}), 200
    except Exception:
        current_app.logger.error('Error fetching conversations', exc_info=True)
        return jsonify({'error': 'Failed to fetch conversations.'}), 500
