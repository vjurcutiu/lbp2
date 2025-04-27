import logging
import os
import re
import json
from flask import current_app
from db.models import db, Conversation, ConversationMessage, File
from utils.services.ai_api_manager import OpenAIService
from utils.models.chat_payload import ChatPayload, OpenAIMessage
from utils.search import default_search
from utils.websockets.sockets import socketio
import pendulum
from typing import Any, Dict, List, Optional, Union
from utils.services.agentic.search_router import SearchRouter


# Lazy-initialized SearchRouter
_router: Optional[SearchRouter] = None

def load_file_records():
    """
    Pull all uploaded files from the DB, read their text, and return
    a list of dicts suitable for SearchRouter.
    """
    records = []
    files = File.query.filter_by(is_uploaded=True).all()
    for f in files:
        try:
            text = open(f.file_path, encoding="utf-8").read()
        except Exception as e:
            logging.warning("Failed to read file %s: %s", f.file_path, e)
            continue

        records.append({
            "id": f.id,
            "file_path": f.file_path,
            "metadata": f.meta_data or {},
            "text": text,
        })
    return records

def build_keyword_index():
    """
    Build a simple keyword-only index from uploaded File records.
    """
    items = []
    for f in File.query.filter_by(is_uploaded=True).all():
        kws = f.meta_data.get("keywords", [])
        items.append({
            "id": f.id,
            "metadata": {"keywords": json.dumps({"keywords": kws})},
        })
    return items

def build_keyword_topics():
    """
    Extract and clean keyword topics from uploaded files' metadata.
    """
    topics = []
    files = File.query.filter_by(is_uploaded=True).all()
    for f in files:
        kws_raw = f.meta_data.get("keywords", None)
        if not kws_raw:
            continue
        # kws_raw may be a JSON string or a list
        if isinstance(kws_raw, str):
            try:
                kws = json.loads(re.search(r"(\{.*\})", kws_raw, re.DOTALL).group(1))["keywords"]
            except Exception as e:
                logging.warning("Failed to parse keywords for file %s: %s", f.id, e)
                continue
        elif isinstance(kws_raw, list):
            kws = kws_raw
        else:
            continue

        topics.extend(kws)

    # dedupe and normalize
    clean = {t.strip().lower() for t in topics if isinstance(t, str) and t.strip()}
    return list(clean)


def get_search_router() -> SearchRouter:
    """
    Lazily instantiate SearchRouter within an application context,
    rebuilding topics from DB metadata.
    """
    global _router
    if _router is None:
        items = load_file_records()
        topics = build_keyword_topics()
        _router = SearchRouter(
            items_for_keyword=items,
            keyword_topics=topics,
            pinecone_namespace="default-namespace"
        )
    return _router

class ConversationManager:
    def __init__(self, session, ai_service: OpenAIService, notifier):
        self.session = session
        self.ai_service = ai_service
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
        title = self.ai_service.generate_title(first_message)
        conversation.title = title
        try:
            self.session.commit()
            self.notifier.emit_title(conversation.id, title)
        except Exception:
            self.session.rollback()
            logging.error("Failed to save generated title", exc_info=True)
        return title

    def update_summary(self, conversation: Conversation, new_message: str, additional_params: dict = None) -> str:
        if conversation.meta_data and conversation.meta_data.get("summary"):
            base_context = conversation.meta_data.get("summary")
        else:
            lines = [f"{msg.sender.capitalize()}: {msg.message}" for msg in conversation.messages]
            base_context = "\n".join(lines)

        updated_context = f"{base_context}\nUser (new): {new_message}"
        try:
            new_summary = self.ai_service.summarize(updated_context)
            conversation.meta_data = conversation.meta_data or {}
            conversation.meta_data["summary"] = new_summary
            self.session.commit()
            return new_summary
        except Exception:
            self.session.rollback()
            logging.error("Error updating conversation summary", exc_info=True)
            return conversation.meta_data.get("summary", "")

    def build_context(self, conversation: Conversation) -> List[dict]:
        history = []
        for msg in conversation.messages:
            if msg.sender == "ai":
                role = "assistant"
            elif msg.sender == "user":
                role = "user"
            else:
                role = msg.sender

            history.append({"role": role, "content": msg.message})
        return history
    
    def handle_frontend_message(self, text: str, conversation_id: int = None, additional_params: dict = None) -> dict:
        # Fetch or create the conversation
        conversation = self.get_or_create(conversation_id)
        is_new = self.is_new(conversation)

        # Persist the user’s message
        msg_repo = MessageRepository(self.session)
        user_msg = msg_repo.add_user_message(conversation.id, text)
        self.session.commit()

        # Title or summary
        if is_new:
            self.generate_title(text, conversation)
        else:
            self.update_summary(conversation, text, additional_params)

        # Build chat history
        chat_history = self.build_context(conversation)

        # ROUTED SEARCH
        router = get_search_router()
        results = router.search(
            text,
            top_k=(additional_params or {}).get("top_k", 3),
            threshold=(additional_params or {}).get("threshold", 0.7),
            limit=(additional_params or {}).get("limit", 3),
        )
        docs = [m["text"] for m in results.get("results", [])]
        logging.debug("SearchRouter chose %s mode, returned %d docs", results.get("intent"), len(docs))

        # AI REPLY
        ai_orch = AIOrchestrator(self.ai_service, default_search)
        ai_reply = ai_orch.get_response(text, chat_history, docs)

        # Persist AI response
        ai_msg = msg_repo.add_ai_message(conversation.id, ai_reply)
        self.session.commit()

        return {
            "conversation_id": conversation.id,
            "conversation_title": conversation.title,
            "user_message": text,
            "ai_response": ai_reply,
            "new_conversation_id": conversation.id if is_new else None
        }

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

class AIOrchestrator:
    def __init__(self, ai_service: OpenAIService, search_client=default_search):
        self.ai_service = ai_service
        self.search_client = search_client

    def get_response(self, user_message: str, chat_history: List[dict], docs: List[str]) -> str:
        openai_msgs = [
            OpenAIMessage(role=entry["role"], content=entry["content"])
            for entry in chat_history
        ]

        if docs:
            system_content = "\n\n".join(docs)
            openai_msgs.insert(0, OpenAIMessage(role="system", content=f"Relevant documents:\n{system_content}"))

        openai_msgs.append(OpenAIMessage(role="user", content=user_message))
        payload = ChatPayload(messages=openai_msgs)
        return self.ai_service.chat(payload)

class SocketNotifier:
    def __init__(self, socketio, app):
        self.socketio = socketio
        self.app = app

    def emit_conversation_list(self):
        with self.app.app_context():
            convos = Conversation.query.all()
            payload = []
            for c in convos:
                payload.append({
                    'id': c.id,
                    'title': c.title,
                    'meta_data': c.meta_data,
                    'created_at': c.created_at.isoformat() if c.created_at else None,
                    'updated_at': c.updated_at.isoformat() if c.updated_at else None,
                })
            self.socketio.emit('conversation_list', payload)

    def emit_new_conversation(self, conversation):
        self.emit_conversation_list()
        self.socketio.emit('new_conversation', {'id': conversation.id})

    def emit_title(self, conversation_id: int, title: str):
        self.socketio.emit('conversation_title', {'id': conversation_id, 'title': title})

