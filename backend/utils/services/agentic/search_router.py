import logging
from typing import Any, Dict

from utils.models.chat_payload import ChatPayload
from utils.services.ai_api_manager import OpenAIService
from utils.search import VectorSearch, KeywordSearch


from .query_processor import QueryProcessor   # <- relative import

logger = logging.getLogger(__name__)

class SearchRouter:
    def __init__(
        self,
        query_processor: QueryProcessor,
        semantic_search: VectorSearch,
        keyword_search: KeywordSearch,
        force_semantic: bool = True  # Temporary bypass flag
    ):
        self.qp = query_processor
        self.semantic_search = semantic_search
        self.force_semantic = force_semantic

    def search(self, query: str) -> Dict[str, Any]:
        """
        Routes to semantic or intent-based search.
        If force_semantic is True, always uses semantic search.
        """
        logger.debug("search_router: search called with query=%s, force_semantic=%s", query, self.force_semantic)

        if self.force_semantic:
            # Temporary bypass: always semantic
            logger.debug("search_router: forced semantic search for query=%s", query)
            sem_results = self.semantic_search.search(query)
            results = self.qp.process_semantic_results(sem_results)
            return {
                'intent': 'semantic',
                'results': results,
            }

        # Default behavior: determine intent then route
        intent = self.qp.detect_intent(query)
        logger.debug("search_router: detected intent '%s' for query=%s", intent, query)

        if intent == 'semantic':
            sem_results = self.semantic_search.search(query)
            results = self.qp.process_semantic_results(sem_results)
            return {
                'intent': 'semantic',
                'results': results,
            }
        elif intent == 'conversational':
            return self._conversational_fallback(query)
        else:
            # Keyword or other
            kw_results = self.qp.keyword_search(query)
            results = self.qp.process_keyword_results(kw_results)
            return {
                'intent': intent,
                'results': results,
            }

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
