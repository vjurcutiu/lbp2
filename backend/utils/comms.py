# comms.py
from db.models import db, Conversation, ConversationMessage
from utils.ai_apis import send_to_api, openai_api_logic

def process_chat_message(frontend_message, conversation_id=None, additional_params=None):
    """
    Processes a chat message received from the frontend by:
      1. Ensuring the conversation exists.
      2. Storing the user's message.
      3. Auto-generating an updated conversation summary context.
      4. Sending the user message along with the updated context to the AI API.
      5. Storing the AI's response in the conversation.
    
    Args:
        frontend_message (str): The message received from the frontend.
        conversation_id (int, optional): The conversation to which this message belongs.
                                         If not provided, a new conversation is created.
        additional_params (dict, optional): Additional parameters for the AI API call.
    
    Returns:
        dict: A dictionary containing:
            - conversation_id: The conversation's ID.
            - user_message: The user's message.
            - ai_response: The AI's API response.
            - context: The updated conversation summary used as context.
    """
    
    # Step 1: Ensure a valid conversation exists.
    if conversation_id:
        conversation = Conversation.query.get(conversation_id)
        if not conversation:
            # If provided conversation_id doesn't exist, create a new conversation.
            conversation = Conversation()
            db.session.add(conversation)
            db.session.commit()
            conversation_id = conversation.id
    else:
        # No conversation provided; create a new one.
        conversation = Conversation()
        db.session.add(conversation)
        db.session.commit()
        conversation_id = conversation.id

    # Step 2: Store the user's message in the database.
    user_message = ConversationMessage(
        conversation_id=conversation_id,
        sender='user',
        message=frontend_message,
        metadata={}
    )
    db.session.add(user_message)
    db.session.commit()
    
    # Step 3: Update the conversation summary context.
    # This function appends the new message to any existing summary (if present) and returns an updated summary.
    # You can pass extra parameters to control summarization behavior if needed.
    updated_summary = summarize_conversation(conversation_id, frontend_message, additional_params)

    # Prepare additional parameters for the chat response that includes the updated summary.
    # Here, we add a "context" field to additional_params to supply the conversation summary to the AI API.
    chat_params = additional_params.copy() if additional_params else {}
    
    # Step 4: Process the chat message via the AI API, using the updated context.
    ai_api_response = send_to_api(frontend_message, openai_api_logic, chat_params)
    
    # Extract the AI reply text. (Adjust the key as per your API response structure.)
    ai_reply_text = ai_api_response if ai_api_response else "No response"
    
    # Step 5: Store the AI's response in the conversation.
    ai_message = ConversationMessage(
        conversation_id=conversation_id,
        sender='ai',
        message=ai_reply_text.content
    )
    db.session.add(ai_message)
    db.session.commit()
    
    return {
        "conversation_id": conversation_id,
        "user_message": frontend_message,
        "ai_response": ai_api_response,
        "context": updated_summary
    }

def summarize_conversation(conversation_id, new_message, additional_params=None):
    """
    Summarizes the conversation history for a given conversation, taking into account
    any previously stored summary in the conversation's metadata. The new message from the
    frontend is appended to the existing context (if available) and then re-summarized.

    Args:
        conversation_id (int): The ID of the conversation to summarize.
        new_message (str): The new message from the frontend to incorporate into the summary.
        additional_params (dict, optional): Additional parameters for the AI API call.
            For example, you can override the summarization endpoint or include extra context.

    Returns:
        str: A new summary of the conversation.
    """
    # Retrieve the conversation from the database.
    conversation = Conversation.query.get(conversation_id)
    if not conversation:
        return "Conversation not found."

    # Prepare the base context.
    # If a summary already exists in metadata, use it. Otherwise, build context from all messages.
    if conversation.meta_data and conversation.meta_data.get("summary"):
        base_context = conversation.meta_data.get("summary")
    else:
        # Build context from all messages if no summary exists.
        # (For brevity, we assume a method exists to get a full conversation context.
        #  Alternatively, you could loop through conversation.messages similar to the previous example.)
        messages = conversation.messages  # Assuming this relationship is defined
        context_lines = []
        for msg in messages:
            line = f"{msg.sender.capitalize()}: {msg.message}"
            context_lines.append(line)
        base_context = "\n".join(context_lines)

    # Append the new message from the frontend.
    updated_context = f"{base_context}\nUser (new): {new_message}"

    # Set up parameters for the summarization API call.
    params = additional_params.copy() if additional_params else {}
    # Set the endpoint if not provided. Adjust this endpoint for summarization as needed.
    params.setdefault("endpoint", "https://api.openai.com/v1/engines/davinci-codex/completions")
    # Construct a prompt instructing the API to summarize the updated conversation.
    params.setdefault("prompt", f"Summarize the following conversation:\n\n{updated_context}\n\nSummary:")
    params.setdefault("max_tokens", 100)

    # Send the updated context to the AI API for summarization.
    api_response = send_to_api(updated_context, openai_api_logic, params)

    # Extract the summary text from the API response.
    # Adjust the extraction logic based on your API's response structure.
    new_summary = api_response.content if api_response else "No summary generated."
    print(new_summary)

    # Update the conversation's metadata with the new summary.
    conversation.meta_data = conversation.meta_data or {}
    conversation.meta_data["summary"] = new_summary

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error updating conversation metadata: {e}")

    return new_summary

