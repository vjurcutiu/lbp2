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
        "Ești un clasificator de intenții. "
        "Primești o listă fixă de topicuri (hotarare, locatie, data, legislatie, domeniu) și o interogare în limba română. "
        "Pentru topicul data, transforma informatia in format dd/mm/yy. "
        "Pentru topicul locatie, extrage doar numele orasului, localitatii, sau a judetului. "
        "Daca ai mai multe topicuri, de exemplu: 'Ce caz avem in Arad pe 13 iulie 1993?' extrage ambele topicuri cu keywordurile adecvate. "
        "Dacă interogarea se potrivește cu unul sau mai multe topicuri, răspunde EXACT în format JSON fără alte comentarii:\n"        
        "{ \"topic\": \"<topic>\", \"keyword\": \"<cuvânt_cheie>\" }\n"
        "Dacă nu se potrivește cu niciun topic, răspunde exact:\n"
        "NONE")

def identify_intent(
    query: str,
    keyword_topics: List[str],
    openai_service: OpenAIService,
    system_instruction: Optional[str] = None,
) -> IntentType:
    logger.debug("identify_intent called with query='%s'", query)
    # Try keyword match
    topic = _llm_extract_keyword(query, keyword_topics, openai_service, system_instruction=system_instruction)
    if topic:
        logger.debug("identify_intent: matched keyword topic=%s", topic)
        return 'keyword', topic

    # Fallback to semantic vs conversational
    instruction = system_instruction or DEFAULT_INTENT_INSTRUCTION
    response = _ask_llm(query, openai_service, instruction)
    intent = response.lower().strip()
    logger.debug("identify_intent: llm returned intent=%s", intent)
    if intent in ('semantic', 'conversational'):
        return intent, None  # type: ignore
    logger.warning("identify_intent: unexpected intent=%s, defaulting to semantic", intent)
    return 'semantic', None  # type: ignore


def decide_mode(
    query: str,
    openai_service: OpenAIService,
    system_instruction: Optional[str] = None,
) -> Literal['keyword', 'semantic']:
    logger.debug("decide_mode called with query='%s'", query)
    instruction = system_instruction or MODE_INSTRUCTION
    response = _ask_llm(query, openai_service, instruction)
    mode = response.lower().strip()
    logger.debug("decide_mode: llm returned mode=%s", mode)
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
    import json as jsonlib
    logger.debug("_llm_extract_keyword called with query='%s'", query)
    instruction = system_instruction or KEYWORD_INSTRUCTION
    topics_str = ", ".join(keyword_topics)
    prompt = f"Topics: {topics_str}\nQuery: \"{query}\"\nAnswer with one topic or NONE."
    response = _ask_llm_raw(prompt, openai_service, instruction)
    normalized = response.strip()
    logger.debug("_llm_extract_keyword: llm returned topic candidate=%s", normalized)
    try:
        data = jsonlib.loads(normalized)
        keyword = data.get("keyword")
        if keyword:
            return keyword
    except Exception as e:
        logger.warning("_llm_extract_keyword: failed to parse JSON response: %s", e)
    # Fallback: check if response matches any topic string
    for topic in keyword_topics:
        if normalized.lower() == topic.lower():
            return topic
    return None


def _ask_llm(
    query: str,
    openai_service: OpenAIService,
    system_instruction: str,
) -> str:
    logger.debug("_ask_llm sending payload for query='%s'", query)
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
        result = openai_service.chat(payload)
        logger.debug("_ask_llm received response=%s", result)
        return result
    except OpenAIAPIError as e:
        logger.error("LLM call failed: %s", e)
        raise


def _ask_llm_raw(
    prompt: str,
    openai_service: OpenAIService,
    system_instruction: str,
) -> str:
    logger.debug("_ask_llm_raw sending prompt=%s", prompt)
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
    logger.debug("_ask_llm_raw sending payload=%s", payload)

    try:
        result = openai_service.chat(payload)
        logger.debug("_ask_llm_raw received response=%s", result)
        return result
    except OpenAIAPIError:
        logger.error("_ask_llm_raw failed for prompt=%s", prompt)
        return ""


def process_keyword_results(
    raw_items: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    logger.debug("process_keyword_results called with %d items", len(raw_items))
    processed = [
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
    logger.debug("process_keyword_results returning %d processed items", len(processed))
    return processed


def process_semantic_results(
    semantic_output: Dict[str, Any],
) -> List[Dict[str, Any]]:
    results = semantic_output.get("results", [])
    logger.debug("process_semantic_results returning %d results", len(results))
    return results

class QueryProcessor:
    def __init__(self, ai_service: OpenAIService, keyword_topics: List[str]):
        logger.debug("Initializing QueryProcessor with topics=%s", keyword_topics)
        self.ai = ai_service
        self.keyword_topics = keyword_topics

    def identify_intent(self, query: str) -> Tuple[Literal['keyword','semantic','conversational'], Optional[str]]:
        logger.debug("QueryProcessor.identify_intent called with query='%s'", query)
        intent, topic = identify_intent(
            query=query,
            keyword_topics=self.keyword_topics,
            openai_service=self.ai,
        )
        logger.info("Decision made in identify_intent: intent=%s, topic=%s", intent, topic)
        return intent, topic

    def decide_mode(self, query: str) -> Literal['keyword','semantic']:
        logger.debug("QueryProcessor.decide_mode called with query='%s'", query)
        mode = decide_mode(query, self.ai)
        logger.info("Decision made in decide_mode: mode=%s", mode)
        return mode

    def extract_keywords(self, query: str) -> List[str]:
        """
        Extract keywords from the query based on the configured keyword topics.
        Returns a list of keywords (empty if none found).
        """
        logger.debug("QueryProcessor.extract_keywords called with query='%s'", query)
        keywords = []
        for topic in self.keyword_topics:
            # Use the existing _llm_extract_keyword function to check if query matches topic
            keyword = _llm_extract_keyword(query, [topic], self.ai)
            if keyword and keyword.upper() != "NONE":
                keywords.append(keyword.lower())
        # Deduplicate keywords
        unique_keywords = list(set(keywords))
        logger.info("Extracted keywords (deduplicated): %s", unique_keywords)
        return unique_keywords

    def process_keyword_results(self, raw_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logger.debug("QueryProcessor.process_keyword_results called")
        results = process_keyword_results(raw_items)
        logger.info("Processed %d keyword results", len(results))
        return results

    def process_semantic_results(self, semantic_output: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.debug("QueryProcessor.process_semantic_results called")
        results = process_semantic_results(semantic_output)
        logger.info("Processed %d semantic results", len(results))
        return results
