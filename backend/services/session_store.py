import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from utils.logging import log_call

@dataclass
class ProcessingSession:
    """
    Represents an active file processing session.
    """
    session_id: str
    progress: int = 0
    final: Optional[Dict[str, Any]] = None
    cancelled: bool = False
    file_items: List[Any] = field(default_factory=list)
    sse_queue: Any = None
    ws_queue: Any = None

class SessionStore:
    """
    In-memory store for managing ProcessingSession objects.
    """
    def __init__(self):
        self._store: Dict[str, ProcessingSession] = {}

    @log_call()
    def create(self):
        session_id = uuid.uuid4().hex
        sess = ProcessingSession(session_id=session_id)
        # Multiprocessing queues will be attached after creation
        self._store[session_id] = sess
        return sess

    @log_call()
    def get(self, session_id: str):
        return self._store.get(session_id)

    @log_call()
    def delete(self, session_id: str):
        self._store.pop(session_id, None)
