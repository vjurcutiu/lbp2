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
        keyword_search: KeywordSearch,
        semantic_search: VectorSearch,
        force_semantic: bool = False  # Disable forced semantic to allow keyword extraction
    ):
        self.qp = query_processor
        self.keyword_search = keyword_search
        self.semantic_search = semantic_search
        self.force_semantic = force_semantic

    def search(self, query: str) -> Dict[str, Any]:
        """
        Routes to semantic or keyword-based search.
        Attempts keyword extraction and passes keywords to hybrid search.
        """
        logger.debug("search_router: search called with query=%s, force_semantic=%s", query, self.force_semantic)

        if self.force_semantic:
            logger.debug("search_router: forced semantic search for query=%s", query)
            sem_results = self.semantic_search.search(query)
            results = self.qp.process_semantic_results(sem_results)
            return {
                'intent': 'semantic',
                'results': results,
            }

        # Extract keywords using QueryProcessor
        keywords = self.qp.extract_keywords(query)
        if keywords:
            logger.debug("search_router: extracted keywords %s for query=%s", keywords, query)
            results = self.semantic_search.search(query, keywords=keywords)
            processed_results = self.qp.process_semantic_results(results)
            return {
                'intent': 'hybrid',
                'results': processed_results,
            }
        else:
            logger.debug("search_router: no keywords extracted, performing semantic search for query=%s", query)
            sem_results = self.semantic_search.search(query)
            results = self.qp.process_semantic_results(sem_results)
            return {
                'intent': 'semantic',
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
