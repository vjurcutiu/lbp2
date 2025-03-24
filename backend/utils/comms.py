# comms.py
from db.models import db, Conversation, ConversationMessage
from utils.ai_apis import send_to_api, openai_api_logic
import datetime
import pendulum
from utils.search import search

def process_chat_message(frontend_message, conversation_id=None, additional_params=None):
    """
    Processes a chat message received from the frontend by:
      1. Ensuring the conversation exists.
      2. Storing the user's message.
      3. Auto-generating an updated conversation summary context.
      4. Searching the vector database to retrieve relevant documents.
      5. Sending the user message along with the enriched context to the AI API.
      6. Storing the AI's response in the conversation.
      
    Returns a dictionary with conversation details, including a new_conversation_id
    if a new conversation was created.
    """
    # Step 1: Ensure a valid conversation exists.
    if conversation_id:
        conversation = Conversation.query.get(conversation_id)
        if not conversation:
            conversation = Conversation()
            db.session.add(conversation)
            db.session.commit()
            conversation_id = conversation.id
        is_new = False
    else:
        conversation = Conversation()
        db.session.add(conversation)
        db.session.commit()
        conversation_id = conversation.id
        is_new = True

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
    updated_summary = summarize_conversation(conversation_id, frontend_message, additional_params)

    # Prepare additional parameters for the chat response.
    conversation_context = get_all_messages_for_conversation(conversation_id, 'user')
    
    # Step 4: Retrieve relevant documents from Pinecone via the search module.
    search_results = search(frontend_message, additional_params={
        "index_name": "test",
        "namespace": "default-namespace",
        "top_k": 3
    })
    
    retrieved_docs = ""
    for match in search_results.get("results", []):
        retrieved_docs += match.get("text", "") + "\n"
    
    # Combine context and documents.
    combined_context = f"{conversation_context}\nRetrieved Documents:\n{retrieved_docs}"
    messages_context = {"context": combined_context}
    
    # Step 5: Get AI response using the enriched context.
    ai_api_response = send_to_api(frontend_message, openai_api_logic, messages_context)
    ai_reply_text = ai_api_response if ai_api_response else "No response"
    
    # Step 6: Store the AI's response.
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
        "ai_response": ai_message.message,
        "context": messages_context,
        "new_conversation_id": conversation_id if is_new else None
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

    
def get_all_conversation_ids():
    """
    Retrieve all conversation IDs from the database.
    Returns a list of IDs.
    """
    conversations = Conversation.query.all()
    return [conversation.id for conversation in conversations]

def model_to_dict(instance):
    result = {}
    for column in instance.__table__.columns:
        value = getattr(instance, column.name, None)
        if isinstance(value, datetime.datetime):
            # Convert the datetime object into a Pendulum object and then format it.
            value = pendulum.instance(value).to_iso8601_string()
        result[column.name] = value
    return result

def get_all_messages_for_conversation(conversation_id, sender=None):
    """
    Retrieve all messages for a given conversation ID.
    
    If a sender is provided, only messages from that sender will be retrieved.
    Otherwise, all messages for the conversation are returned.
    
    :param conversation_id: The ID of the conversation.
    :param sender: (Optional) The sender whose messages to filter by.
    :return: A list of dictionaries representing the messages.
    """
    query = ConversationMessage.query.filter_by(conversation_id=conversation_id)
    if sender is not None:
        query = query.filter_by(sender=sender)
    messages = query.all()
    return [model_to_dict(message) for message in messages]

def get_metadata(files):
    return

def delete_conversation(conversation_id):
    """
    Deletes a conversation and all its associated messages and files.
    Uses cascade deletion as defined in the Conversation model.
    """
    conversation = Conversation.query.get(conversation_id)
    if not conversation:
        return {"error": "Conversation not found."}
    db.session.delete(conversation)
    try:
        db.session.commit()
        return {"message": f"Conversation {conversation_id} deleted successfully."}
    except Exception as e:
        db.session.rollback()
        return {"error": f"Error deleting conversation: {e}"}


def rename_conversation(conversation_id, new_title):
    """
    Renames a conversation by updating its title.
    """
    conversation = Conversation.query.get(conversation_id)
    if not conversation:
        return {"error": "Conversation not found."}
    conversation.title = new_title
    try:
        db.session.commit()
        return {"message": f"Conversation {conversation_id} renamed successfully."}
    except Exception as e:
        db.session.rollback()
        return {"error": f"Error renaming conversation: {e}"}
    
