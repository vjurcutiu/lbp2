import json
import logging
from typing import Any, Dict, List, Optional, Literal, Tuple

from utils.models.chat_payload import ChatPayload
from utils.services.ai_api_manager import OpenAIService, OpenAIAPIError

logger = logging.getLogger(__name__)

IntentType = Literal['keyword', 'semantic', 'conversational']

DEFAULT_INTENT_INSTRUCTION = (
    "You are a query intent classifier. Given the user's query, choose exactly one "
    "intent: 'semantic' (they want a semantic document search) or 'conversational' "
    "(they want a chat-style response)."
)

MODE_INSTRUCTION = (
    "You are a smart search router. Given the user's query, reply with exactly one word—"
    "either 'keyword' or 'semantic'—to pick the best search strategy."
)

KEYWORD_INSTRUCTION = (
    "You are an intent classifier. Given a user’s query and a fixed list of topic names, first determine whether the query matches one of the topics. If it does, output the matching topic name followed by the most relevant keyword from the query. If it does not match any topic, output exactly NONE."
)

def identify_intent(
    query: str,
    keyword_topics: List[str],
    openai_service: OpenAIService,
    system_instruction: Optional[str] = None,
) -> IntentType:
    # Try keyword match
    topic = _llm_extract_keyword(query, keyword_topics, openai_service, system_instruction=system_instruction)
        
    if topic:
        logger.debug("identify_intent: matched keyword topic=%s", topic)
        return 'keyword', topic

    # Fallback to semantic vs conversational
    instruction = system_instruction or DEFAULT_INTENT_INSTRUCTION
    response = _ask_llm(query, openai_service, instruction)
    intent = response.lower().strip()
    if intent in ('semantic', 'conversational'):
        return intent, None  # type: ignore
    logger.warning("identify_intent: unexpected intent=%s, defaulting to semantic", intent)
    return 'semantic'


def decide_mode(
    query: str,
    openai_service: OpenAIService,
    system_instruction: Optional[str] = None,
) -> Literal['keyword', 'semantic']:
    instruction = system_instruction or MODE_INSTRUCTION
    response = _ask_llm(query, openai_service, instruction)
    mode = response.lower().strip()
    if mode in ('keyword', 'semantic'):
        return mode  # type: ignore
    logger.warning("decide_mode: unexpected mode=%s, defaulting to semantic", mode)
    return 'semantic'


def _llm_extract_keyword(
    query: str,
    keyword_topics: List[str],
    openai_service: OpenAIService,
    system_instruction: Optional[str] = None,
) -> Optional[str]:
    instruction = system_instruction or KEYWORD_INSTRUCTION
    topics_str = ", ".join(keyword_topics)
    prompt = f"Topics: {topics_str}\nQuery: \"{query}\"\nAnswer with one topic or NONE."
    response = _ask_llm_raw(prompt, openai_service, instruction)
    normalized = response.strip().lower()
    for topic in keyword_topics:
        if normalized == topic.lower():
            return topic
    return None


def _ask_llm(
    query: str,
    openai_service: OpenAIService,
    system_instruction: str,
) -> str:
    payload = ChatPayload(
        model=openai_service.model_map['chat'],
        messages=[
            {'role': 'system', 'content': system_instruction},
            {'role': 'user', 'content': f'Query: "{query}"'},
        ],
        stream=False,
        temperature=0,
        top_p=1.0,
    )
    try:
        return openai_service.chat(payload)
    except OpenAIAPIError as e:
        logger.error("LLM call failed: %s", e)
        raise


def _ask_llm_raw(
    prompt: str,
    openai_service: OpenAIService,
    system_instruction: str,
) -> str:
    payload = ChatPayload(
        model=openai_service.model_map['chat'],
        messages=[
            {'role': 'system', 'content': system_instruction},
            {'role': 'user', 'content': prompt},
        ],
        stream=False,
        temperature=0,
        top_p=1.0,
    )
    try:
        return openai_service.chat(payload)
    except OpenAIAPIError:
        return ""


def process_keyword_results(
    raw_items: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    return [
        {
            "id": item["id"],
            "score": None,
            "keywords": json.loads(item.get("metadata", {}).get("keywords", "{}"))
                          .get("keywords", []),
            "summary": None,
            "text": item.get("text", ""),
        }
        for item in raw_items
    ]


def process_semantic_results(
    semantic_output: Dict[str, Any],
) -> List[Dict[str, Any]]:
    return semantic_output.get("results", [])

class QueryProcessor:
    def __init__(self, ai_service: OpenAIService, keyword_topics: List[str]):
        self.ai = ai_service
        self.keyword_topics = keyword_topics

    def identify_intent(self, query: str) -> Tuple[Literal['keyword','semantic','conversational'], Optional[str]]:
        # re-use your free function
        intent, topic = identify_intent(
            query=query,
            keyword_topics=self.keyword_topics,
            openai_service=self.ai,
        )
        return intent, topic

    def decide_mode(self, query: str) -> Literal['keyword','semantic']:
        return decide_mode(query, self.ai)

    def process_keyword_results(self, raw_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return process_keyword_results(raw_items)

    def process_semantic_results(self, semantic_output: Dict[str, Any]) -> List[Dict[str, Any]]:
        return process_semantic_results(semantic_output)