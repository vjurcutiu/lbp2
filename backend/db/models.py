from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Conversation(db.Model):
    __tablename__ = "conversation"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=True)
    # JSON field to store additional conversation-specific metadata.
    metadata = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Establish relationships to messages and files.
    messages = db.relationship(
        "ConversationMessage", backref="conversation", cascade="all, delete-orphan", lazy=True
    )
    files = db.relationship(
        "File", backref="conversation", lazy=True
    )

    def __repr__(self):
        return f"<Conversation {self.id} - {self.title or 'No Title'}>"


class ConversationMessage(db.Model):
    __tablename__ = "conversation_message"
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer, db.ForeignKey("conversation.id"), nullable=False
    )
    sender = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    # Optional JSON field for additional metadata related to the message.
    metadata = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ConversationMessage {self.id} from {self.sender}>"


class File(db.Model):
    __tablename__ = "file"
    id = db.Column(db.Integer, primary_key=True)
    # The file field could store the file path or URL.
    file_path = db.Column(db.String(255), nullable=False)
    file_extension = db.Column(db.String(20), nullable=False)
    # Optional JSON field to store extra file metadata.
    metadata = db.Column(db.JSON, nullable=True)
    # Optionally associate this file with a conversation.
    conversation_id = db.Column(
        db.Integer, db.ForeignKey("conversation.id"), nullable=True
    )
    # Field to confirm whether the file has been uploaded.
    is_uploaded = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<File {self.id} at {self.created_at}>"
