# search_router.py

import logging
from typing import Any, Dict, List

from utils.models.chat_payload import ChatPayload
from utils.services.ai_api_manager import OpenAIService
from utils.search import KeywordSearch, VectorSearch

from .query_processor import QueryProcessor   # <- relative import

logger = logging.getLogger(__name__)

class SearchRouter:
    def __init__(
        self,
        query_processor: QueryProcessor,
        keyword_search: KeywordSearch,
        semantic_search: VectorSearch,
    ):
        self.qp = query_processor
        self.keyword_search = keyword_search
        self.semantic_search = semantic_search

    def search(self, query: str) -> Dict[str, Any]:
        intent, topic = self.qp.identify_intent(query)
        logger.debug("search_router: intent=%s, topic=%s", intent, topic)

        if intent == 'keyword' and topic:
            raw = self.keyword_search.search(topic)
            results = self.qp.process_keyword_results(raw)
            return {
                'intent': 'keyword',
                'topic': topic,
                'results': results,
            }

        if intent == 'semantic':
            sem = self.semantic_search.search(query)
            results = self.qp.process_semantic_results(sem)
            return {
                'intent': 'semantic',
                'results': results,
            }

        # conversational fallback
        return self._conversational_fallback(query)

    def _conversational_fallback(self, query: str) -> Dict[str, Any]:
        system_instruction = (
            "You are a helpful assistant. Continue the conversation given the query."
        )
        payload = ChatPayload(
            model=self.qp.ai.model_map['chat'],
            messages=[
                {'role': 'system', 'content': system_instruction},
                {'role': 'user', 'content': query},
            ],
            stream=False,
            temperature=0.7,
            top_p=1.0,
        )
        chat_response = self.qp.ai.chat(payload)
        return {
            'intent': 'conversational',
            'response': chat_response,
        }
