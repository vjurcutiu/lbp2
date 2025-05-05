from flask_socketio import SocketIO, emit
import eventlet
from engineio.async_drivers import gevent

# Create a SocketIO instance with CORS allowed (modify cors_allowed_origins as needed)
socketio = SocketIO(cors_allowed_origins="*", async_mode='gevent')

@socketio.on('connect')
def handle_connect():
    print("Client connected")
    # Send a welcome message to the client upon connection
    emit('server_response', {'data': 'Connected to Flask WebSocket server!'})

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

@socketio.on('client_message')
def handle_message(data):
    print(f"Received message: {data}")
    # Process the incoming message conditionally
    if data.get('type') == 'greeting':
        response = {'data': 'Hello from Flask!'}
    elif data.get('type') == 'farewell':
        response = {'data': 'Goodbye from Flask!'}
    else:
        response = {'data': 'Message received'}
    # Emit the response back to the client
    emit('server_response', response)

# --- Streaming chat handler ---
@socketio.on('chat_message_stream')
def handle_chat_message_stream(data):
    """
    Handles a chat message from the client and streams the AI response back chunk by chunk.
    Expects data: { "message": str, "conversation_id": int (optional) }
    Emits: 'chat_stream' events with { "chunk": str, "is_final": bool }
    """
    from utils.services.conversation_manager import ConversationManager
    from db.models import db
    from utils.services.ai_api_manager import OpenAIService
    from utils.services.agentic.search_router import SearchRouter

    # You may need to adjust how you get these instances in your app
    ai_service = OpenAIService()
    # --- Instantiate SearchRouter and dependencies as in app.py ---
    from utils.keyword_loader import load_keyword_items, build_keyword_topics
    from utils.search import KeywordSearch, HybridSearch
    from utils.services.agentic.query_processor import QueryProcessor

    items = load_keyword_items()
    topics = build_keyword_topics()
    keyword_search = KeywordSearch(items)
    vector_search = HybridSearch()
    qp = QueryProcessor(ai_service, topics)
    search_router = SearchRouter(qp, keyword_search, vector_search)
    # --------------------------------------------------------------
    notifier = None  # Not needed for streaming
    conv_manager = ConversationManager(db.session, ai_service, search_router, notifier)

    text = data.get("message")
    conversation_id = data.get("conversation_id")
    additional_params = data.get("params")

    # Get or create conversation and context
    conversation = conv_manager.get_or_create(conversation_id)
    is_new = conv_manager.is_new(conversation)

    from utils.services.conversation_manager import MessageRepository
    msg_repo = MessageRepository(conv_manager.session)
    user_msg = msg_repo.add_user_message(conversation.id, text)
    conv_manager.session.commit()

    if is_new:
        conv_manager.generate_title(text, conversation)
    else:
        conv_manager.update_summary(conversation, text, additional_params)

    chat_history = conv_manager.build_context(conversation)
    results = conv_manager.search_router.search(text)
    docs = [m["text"] for m in results.get("results", [])]

    from utils.models.chat_payload import ChatPayload, OpenAIMessage
    openai_msgs = [
        OpenAIMessage(role=entry["role"], content=entry["content"])
        for entry in chat_history
    ]
    if docs:
        system_content = "\n\n".join(docs)
        openai_msgs.insert(0, OpenAIMessage(role="system", content=f"Relevant documents:\n{system_content}"))
    openai_msgs.append(OpenAIMessage(role="user", content=text))
    payload = ChatPayload(messages=openai_msgs, stream=True)

    # Stream the response
    try:
        response = ai_service.chat(payload)
        full_reply = ""
        for chunk in response:
            # OpenAI API returns objects with .choices[0].delta.content for streamed chunks
            content = ""
            if hasattr(chunk, "choices") and chunk.choices and hasattr(chunk.choices[0], "delta"):
                content = getattr(chunk.choices[0].delta, "content", "")
            elif hasattr(chunk, "choices") and chunk.choices and hasattr(chunk.choices[0], "message"):
                content = getattr(chunk.choices[0].message, "content", "")
            if content:
                full_reply += content
                emit('chat_stream', {"chunk": content, "is_final": False})
        # Save the full AI message to DB
        msg_repo.add_ai_message(conversation.id, full_reply)
        conv_manager.session.commit()
        emit('chat_stream', {"chunk": full_reply, "is_final": True})
    except Exception as e:
        emit('chat_stream', {"chunk": f"[Error: {str(e)}]", "is_final": True})
