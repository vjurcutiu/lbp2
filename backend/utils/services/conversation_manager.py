from flask import current_app
from db.models import db, Conversation, ConversationMessage
from utils.ai_apis import send_to_api, openai_api_logic
from utils.search import search as default_search
from utils.websockets.sockets import socketio
import logging
import datetime
import pendulum


# --- services/conversation_manager.py ---
class ConversationManager:
    def __init__(self, session, ai_client, notifier):
        self.session = session
        self.ai_client = ai_client
        self.notifier = notifier

    def get_or_create(self, conversation_id=None):
        if conversation_id:
            convo = Conversation.query.get(conversation_id)
            if not convo:
                convo = Conversation()
                self.session.add(convo)
                self.session.commit()
                self.notifier.emit_new_conversation(convo)
            return convo
        convo = Conversation()
        self.session.add(convo)
        self.session.commit()
        self.notifier.emit_new_conversation(convo)
        return convo

    def is_new(self, conversation):
        return len(conversation.messages) < 2

    def generate_title(self, first_message: str, conversation: Conversation) -> str:
        resp = send_to_api(first_message, openai_api_logic, purpose="convo-name")
        title = getattr(resp, 'content', '').strip() or "Untitled"
        conversation.title = title
        try:
            self.session.commit()
            self.notifier.emit_title(conversation.id, title)
        except Exception:
            self.session.rollback()
            logging.error("Failed to save generated title", exc_info=True)
        return title

    def update_summary(self, conversation: Conversation, new_message: str, additional_params=None) -> str:
        # Retrieve existing summary or build full context
        base_context = None
        if conversation.meta_data and conversation.meta_data.get("summary"):
            base_context = conversation.meta_data.get("summary")
        else:
            lines = []
            for msg in conversation.messages:
                lines.append(f"{msg.sender.capitalize()}: {msg.message}")
            base_context = "\n".join(lines)

        updated_context = f"{base_context}\nUser (new): {new_message}"
        # Prepare params for summarization
        params = dict(additional_params) if additional_params else {}
        params.setdefault("endpoint", "https://api.openai.com/v1/engines/davinci-codex/completions")
        params.setdefault("prompt", f"Summarize the following conversation:\n\n{updated_context}\n\nSummary:")
        params.setdefault("max_tokens", 100)

        # Call summarization API
        api_resp = send_to_api(updated_context, openai_api_logic, params)
        new_summary = getattr(api_resp, 'content', '').strip() or ""
        # Persist summary
        conversation.meta_data = conversation.meta_data or {}
        conversation.meta_data["summary"] = new_summary
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            logging.error("Error updating conversation summary", exc_info=True)
        return new_summary

    def build_context(self, conversation: Conversation) -> str:
        # Return existing summary or full message history
        if conversation.meta_data and conversation.meta_data.get("summary"):
            return conversation.meta_data.get("summary")
        lines = []
        for msg in conversation.messages:
            timestamp = None
            if hasattr(msg, 'created_at') and msg.created_at:
                timestamp = pendulum.instance(msg.created_at).to_iso8601_string()
            prefix = f"[{timestamp}] " if timestamp else ""
            lines.append(f"{prefix}{msg.sender.capitalize()}: {msg.message}")
        return "\n".join(lines)


# --- services/message_repository.py ---
class MessageRepository:
    def __init__(self, session):
        self.session = session

    def add_user_message(self, conversation_id: int, text: str) -> ConversationMessage:
        msg = ConversationMessage(
            conversation_id=conversation_id,
            sender='user',
            message=text,
            metadata={}
        )
        self.session.add(msg)
        self.session.flush()
        return msg

    def add_ai_message(self, conversation_id: int, text: str) -> ConversationMessage:
        msg = ConversationMessage(
            conversation_id=conversation_id,
            sender='ai',
            message=text
        )
        self.session.add(msg)
        return msg

    def get_messages(self, conversation_id: int, sender: str = None):
        query = ConversationMessage.query.filter_by(conversation_id=conversation_id)
        if sender:
            query = query.filter_by(sender=sender)
        return query.all()


# --- services/ai_orchestrator.py ---
class AIOrchestrator:
    def __init__(self, ai_client, search_client, summarizer=None):
        self.ai_client = ai_client
        self.search_client = search_client
        self.summarizer = summarizer or send_to_api

    def get_response(self, user_message: str, context: str, docs: list) -> str:
        retrieved = "\n".join(docs)
        prompt = f"{context}\nRetrieved Documents:\n{retrieved}\nUser: {user_message}\nAI:"
        resp = send_to_api(user_message, openai_api_logic, {'context': prompt})
        return getattr(resp, 'content', 'No response')


# --- services/socket_notifier.py ---
class SocketNotifier:
    def __init__(self, socketio, app):
        self.socketio = socketio
        self.app = app

    def emit_conversation_list(self):
        with self.app.app_context():
            convos = Conversation.query.all()
            payload = [c.to_dict() for c in convos]
            self.socketio.emit('conversation_list', payload)

    def emit_new_conversation(self, conversation):
        self.emit_conversation_list()
        self.socketio.emit('new_conversation', {'id': conversation.id})

    def emit_title(self, conversation_id: int, title: str):
        self.socketio.emit('conversation_title', {'id': conversation_id, 'title': title})

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'meta_data': self.meta_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# --- controllers/chat_controller.py ---
def handle_frontend_message(
    text: str,
    conversation_id: int = None,
    additional_params: dict = None,
    session=db.session,
    ai_client=openai_api_logic,
    search_client=default_search,
    notifier=SocketNotifier(socketio, current_app)
) -> dict:
    conv_mgr = ConversationManager(session, ai_client, notifier)
    msg_repo = MessageRepository(session)
    ai_orch = AIOrchestrator(ai_client, search_client)

    # 1. Ensure conversation
    conversation = conv_mgr.get_or_create(conversation_id)
    new_convo = conv_mgr.is_new(conversation)

    # 2. Store user message
    user_msg = msg_repo.add_user_message(conversation.id, text)
    session.commit()

    # 3. Set title if new
    if new_convo:
        conv_mgr.generate_title(text, conversation)

    # 4. Update summary
    summary = conv_mgr.update_summary(conversation, text, additional_params)

    # 5. Build context and retrieve docs
    context = conv_mgr.build_context(conversation)
    results = search_client(text, additional_params={
        'index_name': 'test', 'namespace': 'default-namespace', 'top_k': 3
    })
    docs = [m['text'] for m in results.get('results', [])]

    # 6. Get AI response
    ai_reply = ai_orch.get_response(text, context, docs)

    # 7. Store AI message
    ai_msg = msg_repo.add_ai_message(conversation.id, ai_reply)
    session.commit()

    return {
        'conversation_id': conversation.id,
        'conversation_title': conversation.title,
        'user_message': text,
        'ai_response': ai_reply,
        'new_conversation_id': conversation.id if new_convo else None
    }
