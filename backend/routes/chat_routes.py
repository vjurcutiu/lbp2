# chat_routes.py
from flask import Blueprint, request, jsonify, current_app
from utils.comms import get_all_conversation_ids, get_all_messages_for_conversation, delete_conversation, rename_conversation
from utils.comms import process_chat_message
from db.models import Conversation
from utils.comms import model_to_dict
from utils.emitters.emitters import emit_conversation_update

# Create a blueprint for chat routes.
chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint to process chat messages from the frontend.
    
    Expected JSON payload:
        {
            "message": "User message text",
            "conversation_id": <optional conversation id>,
            "additional_params": <optional dict with extra parameters>
        }
    
    Returns a JSON response with the updated conversation details,
    including the AI's response and the updated conversation context (summary).
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request, JSON required."}), 400

    # Retrieve required and optional parameters from the payload.
    frontend_message = data.get("message")
    if not frontend_message:
        return jsonify({"error": "No message provided."}), 400

    conversation_id = data.get("conversation_id")
    additional_params = data.get("additional_params", {})

    try:
        # Process the incoming chat message using our chat logic.
        result = process_chat_message(frontend_message, conversation_id, additional_params)
        return result, 200
    except Exception as e:
        # Log the exception with a traceback for debugging
        current_app.logger.error("Error processing chat message", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@chat_bp.route('/conversation_ids', methods=['GET'])
def conversation_ids_route():
    """
    Route that returns all conversation IDs as JSON.
    Example response:
      { "conversation_ids": [1, 2, 3, ...] }
    """
    try:
        conversation_ids = get_all_conversation_ids()
        return jsonify({"conversation_ids": conversation_ids}), 200
    except Exception as e:
        current_app.logger.error("Error fetching conversation ids", exc_info=True)
        return jsonify({"error": "Failed to fetch conversation ids"}), 500
    
@chat_bp.route('/<int:conversation_id>/messages', methods=['GET'])
def get_conversation_messages(conversation_id):
    """
    Retrieve all messages for the conversation with the given ID.
    
    Returns a JSON response in the following format:
      { "messages": [ { ... }, { ... }, ... ] }
    """
    try:
        messages = get_all_messages_for_conversation(conversation_id)
        return jsonify({"messages": messages}), 200
    except Exception as e:
        current_app.logger.error("Error fetching messages for conversation %s: %s", conversation_id, e, exc_info=True)
        return jsonify({"error": "Failed to retrieve messages for conversation."}), 500
    
@chat_bp.route('/delete', methods=['POST'])
def delete_conversation_route():
    """
    Endpoint to delete a conversation along with its associated messages and files.
    
    Expected JSON payload:
      {
          "conversation_id": <conversation id>
      }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request, JSON required."}), 400

    conversation_id = data.get("conversation_id")
    if not conversation_id:
        return jsonify({"error": "Conversation ID is required."}), 400

    try:
        result = delete_conversation(conversation_id)
        # Return 200 if deletion was successful, else 400.
        status_code = 200 if "message" in result else 400
        return jsonify(result), status_code
    except Exception as e:
        current_app.logger.error("Error deleting conversation", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@chat_bp.route('/rename', methods=['POST'])
def rename_conversation_route():
    """
    Endpoint to rename a conversation.
    
    Expected JSON payload:
      {
          "conversation_id": <conversation id>,
          "new_title": "New Conversation Title"
      }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request, JSON required."}), 400

    conversation_id = data.get("conversation_id")
    new_title = data.get("new_title")
    if not conversation_id or not new_title:
        return jsonify({"error": "Both conversation_id and new_title are required."}), 400

    try:
        result = rename_conversation(conversation_id, new_title)
        status_code = 200 if "message" in result else 400
        return jsonify(result), status_code
    except Exception as e:
        current_app.logger.error("Error renaming conversation", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
    
@chat_bp.route('/list', methods=['GET'])
def list_conversations():
    """
    Endpoint to retrieve all conversations with their metadata.
    Returns a JSON object like:
      { "conversations": [ { id, title, meta_data, created_at, ... }, ... ] }
    """
    try:
        conversations = Conversation.query.all()
        conv_list = [model_to_dict(conv) for conv in conversations]
        return jsonify({"conversations": conv_list}), 200
    except Exception as e:
        current_app.logger.error("Error fetching conversations", exc_info=True)
        return jsonify({"error": "Failed to fetch conversations"}), 500
    