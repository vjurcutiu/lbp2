import json
from datetime import datetime
from utils.logging import log_call

@log_call()
def format_sse(event: str, data: dict) -> str:
    """
    Formats data as an SSE (Server Sent Event) message.
    """
    payload = {"event": event, "timestamp": datetime.utcnow().isoformat(), "data": data}
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"
