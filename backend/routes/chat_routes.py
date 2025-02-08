# chat_routes.py
from flask import Blueprint, request, jsonify, current_app
from utils.comms import process_chat_message, get_all_conversation_ids, get_all_messages_for_conversation

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