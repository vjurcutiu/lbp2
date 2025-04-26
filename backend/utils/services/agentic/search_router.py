import logging
import structlog
from typing import Any, Dict, List, Optional

from utils.search import KeywordSearch, VectorSearch, Embedder
from utils.services.ai_api_manager import OpenAIService

from utils.services.agentic.query_processor import (
    identify_intent,
    extract_keyword,
    process_keyword_results,
    process_semantic_results,
)

class SearchRouter:
    """
    Routes queries by intent: keyword-topic lookup, semantic search, or conversational.
    """
    def __init__(
        self,
        items_for_keyword: List[Dict[str, Any]],
        keyword_topics: List[str],
        embedder_model: str = None,
        pinecone_namespace: str = None,
        openai_service: Optional[OpenAIService] = None,
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.keyword_topics = keyword_topics
        self.keyword_search = KeywordSearch(items_for_keyword)
        self.semantic_search = VectorSearch(embedder=Embedder(embedder_model))
        self.namespace = pinecone_namespace
        self.ai = openai_service or OpenAIService()

    def search(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.7,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        1. Identify intent: 'keyword', 'semantic', or 'conversational'.
        2. If 'keyword', extract the topic and run keyword search.
        3. If 'semantic', run vector search.
        4. If 'conversational', return a placeholder for chat handling.
        """
        self.logger.info("search_router.search: received query=%r top_k=%d threshold=%s limit=%d",
                         query, top_k, threshold, limit)

        intent = identify_intent(query, self.keyword_topics, self.ai)
        self.logger.info("search_router.search: intent=%s", intent)

        if intent == "keyword":
            topic = extract_keyword(query, self.keyword_topics)
            self.logger.debug("search_router.search: extract_keyword returned %s", topic)
            if topic is None:
                self.logger.warning("search_router.search: no topic extracted, switching to semantic")
                intent = "semantic"
            else:
                self.logger.info("search_router.search: keyword topic=%s", topic)
                raw_hits = self.keyword_search.search(
                    topic, case_insensitive=True, limit=limit
                )
                self.logger.debug("search_router.search: raw keyword hits count=%d", len(raw_hits))
                results = process_keyword_results(raw_hits)
                self.logger.debug("search_router.search: processed keyword results count=%d", len(results))
                return {"intent": "keyword", "topic": topic, "results": results}

        if intent == "semantic":
            self.logger.info("search_router.search: routing to semantic search")
            sem = self.semantic_search.search(
                query, top_k=top_k, namespace=self.namespace, threshold=threshold
            )
            self.logger.debug("search_router.search: semantic output keys=%s", list(sem.keys()))
            results = process_semantic_results(sem)
            self.logger.debug("search_router.search: processed semantic results count=%d", len(results))
            return {"intent": "semantic", "results": results}

        # conversational
        self.logger.info("search_router.search: routing to conversational handler")
        return {"intent": "conversational", "response": None}

# Example usage
if __name__ == "__main__":
    # Assume `files` is defined
    file_records = [
        {
            "id": f["id"],
            "file_path": f["file_path"],
            "metadata": f["meta_data"],
            "text": open(f["file_path"], encoding="utf-8").read(),
        }
        for f in files
    ]
    topics = ["billing", "pricing", "installation", "troubleshooting"]

    router = SearchRouter(items_for_keyword=file_records, keyword_topics=topics)
    q = input("Enter your search or question: ")
    out = router.search(q)
    if out["intent"] == "conversational":
        print("Route to chat handler")
    else:
        print(f"Intent={out['intent']}", f"Topic={out.get('topic')}", sep="\n")
        for r in out["results"]:
            print(f" • {r['id']} — {r.get('text','')[:80]}…")
