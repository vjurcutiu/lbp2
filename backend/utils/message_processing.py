from db.models import db, Conversation, ConversationMessage
from utils.ai_apis import send_to_api, openai_api_logic
from flask import current_app
from utils.websockets.sockets import socketio
from utils.comms import summarize_conversation, get_all_messages_for_conversation

import datetime
import pendulum
from utils.search import search

def conversation_to_dict(conversation):
    return {
        'id': conversation.id,
        'title': conversation.title,
        'meta_data': conversation.meta_data,
        'created_at': conversation.created_at.isoformat() if conversation.created_at else None,
        'updated_at': conversation.updated_at.isoformat() if conversation.updated_at else None,
    }

def ensure_conversation(conversation_id):
    """Ensure the conversation exists; create if not.
    
    Returns a tuple of (conversation, is_new)
    """
    if conversation_id:
        conversation = Conversation.query.get(conversation_id)
        if conversation:
            # Consider the conversation new if it has fewer than two messages.
            is_new = len(conversation.messages) < 2
            return conversation, is_new
    # Create a new conversation if not found or conversation_id is None.
    conversation = Conversation()
    db.session.add(conversation)
    db.session.flush()  # Flush so that conversation.id is assigned.
    return conversation, True


def emit_new_conversation(conversation_id):
    """Emit an event to notify the frontend of a new conversation."""
    with current_app.app_context():
        socketio.emit('new_conversation', {'id': conversation_id})

def store_message(conversation, sender, message, metadata=None):
    """Store a message in the conversation."""
    msg = ConversationMessage(
        conversation_id=conversation.id,
        sender=sender,
        message=message,
        meta_data=metadata or {}
    )
    db.session.add(msg)
    return msg

def emit_updated_conversation_title(conversation):
    """Emit an event to update the conversation title on the frontend."""
    with current_app.app_context():
        socketio.emit('updated_conversation_title', {
            'id': conversation.id,
            'title': conversation.title
        })

def update_conversation_title_if_new(conversation, frontend_message, is_new):
    """Generate and update conversation title if the conversation is new.
    
    Returns the generated title.
    """
    if is_new:
        title_response = send_to_api(frontend_message, openai_api_logic, purpose='convo-name')
        generated_title = (title_response.content.strip() 
                           if title_response and hasattr(title_response, 'content') 
                           else "No Title")
        conversation.title = generated_title
        return generated_title
    return conversation.title

def enrich_context(frontend_message, conversation_id, additional_params):
    """Enrich the context by summarizing and retrieving documents."""
    # Assume summarize_conversation and get_all_messages_for_conversation are already defined.
    updated_summary = summarize_conversation(conversation_id, frontend_message, additional_params)
    conversation_context = get_all_messages_for_conversation(conversation_id, 'user')
    search_results = search(frontend_message, additional_params={
        "index_name": "test",
        "namespace": "default-namespace",
        "top_k": 3
    })
    
    retrieved_docs = "\n".join(match.get("text", "") for match in search_results.get("results", []))
    combined_context = f"{conversation_context}\nRetrieved Documents:\n{retrieved_docs}"
    return {"context": combined_context}

def process_chat_message(frontend_message, conversation_id=None, additional_params=None):
    """
    Processes a chat message by:
      1. Ensuring the conversation exists.
      2. Storing the user's message.
      3. Updating the conversation title for new conversations.
      4. Enriching the context (via summarization and document retrieval).
      5. Sending the message to the AI API.
      6. Storing the AI's response.
      7. Emitting conversation updates if a new conversation was created.
      
    Returns a dictionary with conversation details.
    """
    with current_app.app_context():
        try:
            # Start a single transaction
            with db.session.begin():
                # Step 1: Ensure a valid conversation exists.
                conversation, is_new = ensure_conversation(conversation_id)
                # Capture the conversation ID (guaranteed to be assigned because of flush)
                conv_id = conversation.id

                # Step 2: Store the user's message.
                store_message(conversation, 'user', frontend_message)

                # Step 3: For new conversations, update the title.
                new_title = update_conversation_title_if_new(conversation, frontend_message, is_new)

                # Step 4: Enrich context.
                messages_context = enrich_context(frontend_message, conversation.id, additional_params)

                # Step 5: Get AI response.
                ai_api_response = send_to_api(frontend_message, openai_api_logic, messages_context)
                ai_reply_text = (ai_api_response.content 
                                 if ai_api_response and hasattr(ai_api_response, 'content') 
                                 else "No response")

                # Step 6: Store the AI's response.
                store_message(conversation, 'ai', ai_reply_text)
            # End transaction – all operations committed at once.

            # Step 7: If a new conversation was created, emit the updates.
            if is_new:
                conversation_list = [conversation_to_dict(c) for c in Conversation.query.all()]
                socketio.emit('conversation_list', conversation_list)
                socketio.emit('new_conversation', {'id': conv_id})

            # Return the processed results.
            return {
                "conversation_id": conversation.id,
                "conversation_title": conversation.title,
                "user_message": frontend_message,
                "ai_response": ai_reply_text,
                "context": messages_context,
                "new_conversation_id": conversation.id if is_new else None
            }
        except Exception as e:
            db.session.rollback()
            print(f"Error processing chat message: {e}")
            raise

