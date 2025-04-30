import json
import logging
from typing import Any, Dict, List, Optional

from utils.models.chat_payload import ChatPayload
from utils.services.ai_api_manager import OpenAIService, OpenAIAPIError

logger = logging.getLogger(__name__)

def identify_intent(
    query: str,
    keyword_topics: List[str],
    openai_service: OpenAIService,
    system_instruction: Optional[str] = None,
) -> str:
    """
    Decide overall intent: 'keyword', 'semantic', or 'conversational'.

    1) LLM-backed keyword extraction: pick one of keyword_topics or NONE.
    2) If we got a topic, return 'keyword'.
    3) Otherwise ask the LLM to choose 'semantic' vs. 'conversational'.
    """
    # 1) LLM picks topic
    logger.debug("identify_intent: querying LLM for keyword topic match")
    topic = _llm_extract_keyword(query, keyword_topics, openai_service)
    if topic:
        logger.debug("identify_intent: LLM matched keyword topic='%s'", topic)
        return "keyword"

    # 2) Fallback: semantic vs conversational
    logger.debug("identify_intent: no keyword match, fallback to semantic/conversational")
    system_instr = system_instruction or (
        "You are a query intent classifier. Given the user's query, choose exactly one "
        "intent: 'semantic' (they want a semantic document search) or 'conversational' "
        "(they want a chat-style response)."
    )
    prompt = f'Query: "{query}"'
    try:
        payload = ChatPayload(
            model=openai_service.model_map['chat'],
            messages=[
                {'role': 'system', 'content': system_instr},
                {'role': 'user',   'content': prompt},
            ],
            stream=False,
            temperature=0,
            top_p=1.0,
        )
        response = openai_service.chat(payload).strip().lower()
        logger.debug("identify_intent: secondary LLM response='%s'", response)
        if response in {"semantic", "conversational"}:
            return response
        logger.warning("identify_intent: unexpected LLM intent='%s', defaulting to 'semantic'", response)
        return "semantic"
    except OpenAIAPIError as e:
        logger.error("identify_intent: LLM call failed, defaulting to 'semantic'", exc_info=e)
        return "semantic"


def _llm_extract_keyword(
    query: str,
    keyword_topics: List[str],
    openai_service: OpenAIService,
    system_instruction: Optional[str] = None,
) -> Optional[str]:
    """
    Use the LLM to pick exactly one topic from keyword_topics that best matches the query,
    or return None if none apply.
    """
    system_instr = system_instruction or (
        "You are an intent classifier. "
        "Given a user query and a fixed list of topics, "
        "choose exactly one topic name that best matches the query, "
        "or reply exactly NONE if none of the topics apply. "
        "Do NOT output anything else."
    )

    topics_list = ", ".join(keyword_topics)
    prompt = (
        f"Topics: {topics_list}\n"
        f"Query: \"{query}\"\n"
        "Answer with one of the topics, or NONE."
    )

    payload = ChatPayload(
        model=openai_service.model_map['chat'],
        messages=[
            {'role': 'system',  'content': system_instr},
            {'role': 'user',    'content': prompt},
        ],
        stream=False,
        temperature=0,
        top_p=1.0,
    )
    try:
        raw = openai_service.chat(payload).strip()
    except OpenAIAPIError:
        return None

    normalized = raw.lower()
    for topic in keyword_topics:
        if normalized == topic.lower():
            return topic
    return None


def decide_mode(
    query: str,
    openai_service: OpenAIService,
    system_instruction: str = None,
) -> str:
    """
    (Internal) Ask the LLM whether to use 'keyword' or 'semantic' for this query.
    """
    system_instr = system_instruction or (
        "You are a smart search router. Given the user's query, reply with exactly one word—"
        "either 'keyword' or 'semantic'—to pick the best search strategy."
    )
    prompt = f'Query: "{query}"'
    logger.debug("decide_mode: querying LLM for best search strategy")
    try:
        payload = ChatPayload(
            model=openai_service.model_map['chat'],
            messages=[
                {'role': 'system', 'content': system_instr},
                {'role': 'user', 'content': prompt},
            ],
            stream=False,
            temperature=0,
            top_p=1.0,
        )
        response = openai_service.chat(payload)
        mode = response.strip().lower()
        logger.debug("decide_mode: LLM suggested mode='%s'", mode)
    except OpenAIAPIError as e:
        logger.error("decide_mode: LLM error, falling back to 'semantic'", exc_info=e)
        return "semantic"

    logger.debug("decide_mode: final mode='%s'", mode)
    if mode not in {"keyword", "semantic"}:
        logger.warning("decide_mode: unexpected mode='%s', defaulting to 'semantic'", mode)
        return "semantic"
    return mode


def process_keyword_results(
    raw_items: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Given the raw list of items from KeywordSearch.search(),
    return them in unified format.
    """
    processed: List[Dict[str, Any]] = []
    for item in raw_items:
        processed.append({
            "id": item["id"],
            "score": None,
            "keywords": json.loads(item["metadata"].get("keywords", "{}")).get("keywords", []),
            "summary": None,
            "text": item.get("text", ""),
        })
    return processed


def process_semantic_results(
    semantic_output: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Given the dict returned by VectorSearch.search(),
    extract and return its 'results' list.
    """
    return semantic_output.get("results", [])
