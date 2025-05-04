import os
import logging
from typing import Optional, Dict, Any, List
import json

from utils.services.ai_api_manager import OpenAIService
from utils.pinecone_client import PineconeClient

# Configure module-level defaults from environment
DEFAULT_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
DEFAULT_TOP_K = int(os.getenv("RAG_TOP_K", 10))
DEFAULT_THRESHOLD = float(os.getenv("RAG_THRESHOLD", 0.7))


class Embedder:
    """
    A simple embedding interface. Uses OpenAIService for embeddings.
    """
    def __init__(self, model: Optional[str] = None):
        self.model = model or DEFAULT_EMBEDDING_MODEL
        self.ai_service = OpenAIService()

    def embed(self, text: str) -> List[float]:
        """
        Returns an embedding vector for the given text.
        """
        try:
            return self.ai_service.embeddings(text)
        except Exception as e:
            logging.error("Embedder.embed failed: %s", e, exc_info=True)
            raise

class KeywordSearch:
    """
    Performs exact keyword matching over items whose metadata['keywords'] is a JSON string:
      {"keywords": ["term1", "term2", ...]}
    """

    def __init__(self, items: List[Dict[str, Any]]):
        """
        items: list of dicts, each having at least:
          - 'id'
          - 'metadata': containing a JSON-string under metadata['keywords']
          - other fields you want to return (e.g. 'file_path', 'text', etc.)
        """
        self.items = items

    def search(
        self, 
        term: str, 
        case_insensitive: bool = True, 
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Return items whose keywords list contains the exact term.
        If case_insensitive=True, matching is done in lowercase.
        limit: max number of results to return (None means no limit).
        """
        matches = []
        t = term.lower() if case_insensitive else term

        for item in self.items:
            raw = item.get("metadata", {}).get("keywords", "")
            try:
                data = json.loads(raw)
                kws = data.get("keywords", [])
            except json.JSONDecodeError:
                continue

            # Normalize
            norm_kws = [k.lower() for k in kws] if case_insensitive else kws

            if t in norm_kws:
                matches.append(item)

        # Optionally limit and return
        if limit:
            return matches[:limit]
        return matches

class VectorSearch:
    """
    Performs semantic search over a Pinecone vector index using an Embedder
    and PineconeClient. Supports configurable parameters and soft fallback.
    """
    def __init__(
        self,
        embedder: Optional[Embedder] = None,
        vector_store: Optional[PineconeClient] = None,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None
    ):
        self.embedder = embedder or Embedder()
        # Delay instantiation of vector store to avoid import-time env errors
        self.vector_store = vector_store
        self.top_k = top_k or DEFAULT_TOP_K
        self.threshold = threshold or DEFAULT_THRESHOLD

    def search(
        self,
        query: str,
        index_name: Optional[str] = None,
        namespace: Optional[str] = None,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Embed a query and retrieve top_k results from Pinecone, filtering by score.

        Args:
            query: text query to embed and search.
            index_name: override the default index name.
            namespace: override the default namespace.
            top_k: override the default number of results.
            threshold: override the default score threshold.

        Returns:
            A dict with a "results" list, each item containing id, score,
            keywords, summary, and text.
        """
        # Step 1: embed the query
        try:
            vector = self.embedder.embed(query)
        except Exception:
            raise RuntimeError("Failed to generate embedding for query.")

        # Lazy-load vector store
        if not self.vector_store:
            try:
                self.vector_store = PineconeClient()
            except Exception as e:
                logging.error("PineconeClient init failed: %s", e, exc_info=True)
                raise RuntimeError("Failed to initialize Pinecone client: " + str(e))

        vs = self.vector_store
        idx = index_name or vs.index_name
        ns = namespace or vs.namespace
        k = top_k or self.top_k
        t = threshold or self.threshold

        # Step 2: query vector store
        try:
            response = vs.query(
                vector=vector,
                top_k=k,
                namespace=ns,
                include_values=False,
                include_metadata=True
            )
        except Exception as e:
            logging.error("Vector store query failed: %s", e, exc_info=True)
            raise RuntimeError(f"Vector store query error: {e}")

        matches = response.get("matches", [])

        # Step 3: filter and sort by score
        filtered = [m for m in matches if m.get("score", 0) >= t]
        filtered.sort(key=lambda m: m.get("score", 0), reverse=True)

        # Soft fallback: if no hits above threshold, return the single best match
        if not filtered and matches:
            best = max(matches, key=lambda m: m.get("score", 0))
            logging.warning(
                "No matches above threshold %.2f. Falling back to top match (score=%.3f).",
                t,
                best.get("score", 0)
            )
            filtered = [best]

        # Build structured results
        results: List[Dict[str, Any]] = []
        for match in filtered:
            md = match.get("metadata", {}) or {}
            results.append({
                "id": match.get("id"),
                "score": match.get("score"),
                "keywords": md.get("keywords", ""),
                "summary": md.get("summary", ""),
                "text": md.get("source_text", "")
            })

        return {"results": results}


def default_search(query: str, additional_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Backwards-compatible facade. Instantiates a fresh VectorSearch on each call,
    ensuring env-based errors occur at runtime, not import.
    """
    params = additional_params or {}
    vs = VectorSearch(
        top_k=params.get("top_k"),
        threshold=params.get("threshold")
    )
    return vs.search(
        query,
        index_name=params.get("index_name"),
        namespace=params.get("namespace")
    )


class HybridSearch:
    """
    Combines semantic vector search with keyword filtering using Pinecone metadata.
    Runs two queries (with and without keyword filter), merges and boosts results.
    """

    def __init__(
        self,
        embedder: Optional[Embedder] = None,
        vector_store: Optional[PineconeClient] = None,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
        keyword_boost: float = 0.2,
    ):
        self.embedder = embedder or Embedder()
        self.vector_store = vector_store
        self.top_k = top_k or DEFAULT_TOP_K
        self.threshold = threshold or DEFAULT_THRESHOLD
        self.keyword_boost = keyword_boost

    def search(
        self,
        query: str,
        keywords: Optional[List[str]] = None,
        index_name: Optional[str] = None,
        namespace: Optional[str] = None,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Perform hybrid search combining semantic and keyword filtering.

        Args:
            query: text query to embed and search.
            keywords: list of keywords to filter by in metadata.
            index_name: override the default index name.
            namespace: override the default namespace.
            top_k: override the default number of results.
            threshold: override the default score threshold.

        Returns:
            A dict with a "results" list, each item containing id, score,
            keywords, summary, and text.
        """
        logging.debug("HybridSearch.search called with query=%s, keywords=%s, index_name=%s, namespace=%s, top_k=%s, threshold=%s",
                      query, keywords, index_name, namespace, top_k, threshold)

        # Embed the query
        try:
            vector = self.embedder.embed(query)
            logging.debug("HybridSearch: Query embedding generated successfully.")
        except Exception:
            logging.error("HybridSearch: Failed to generate embedding for query.", exc_info=True)
            raise RuntimeError("Failed to generate embedding for query.")

        # Lazy-load vector store
        if not self.vector_store:
            try:
                self.vector_store = PineconeClient()
                logging.debug("HybridSearch: PineconeClient initialized successfully.")
            except Exception as e:
                logging.error("HybridSearch: PineconeClient init failed: %s", e, exc_info=True)
                raise RuntimeError("Failed to initialize Pinecone client: " + str(e))

        vs = self.vector_store
        idx = index_name or vs.index_name
        ns = namespace or vs.namespace
        k = top_k or self.top_k
        t = threshold or self.threshold

        logging.debug("HybridSearch: Using index_name=%s, namespace=%s, top_k=%d, threshold=%.3f", idx, ns, k, t)

        # Prepare filter for keyword search if keywords provided
        filter_dict = None
        if keywords:
            filter_dict = {"keywords": {"$in": keywords}}
            logging.debug("HybridSearch: Keyword filter prepared: %s", filter_dict)
        else:
            logging.debug("HybridSearch: No keywords provided, skipping keyword filter.")

        # Query 1: Semantic search without filter
        try:
            semantic_response = vs.query(
                vector=vector,
                top_k=k,
                namespace=ns,
                include_values=False,
                include_metadata=True,
            )
            logging.debug("HybridSearch: Semantic search query successful, %d matches found.", len(semantic_response.get("matches", [])))
        except Exception as e:
            logging.error("HybridSearch: Vector store semantic query failed: %s", e, exc_info=True)
            raise RuntimeError(f"Vector store semantic query error: {e}")

        semantic_matches = semantic_response.get("matches", [])

        # Query 2: Keyword filtered search (if keywords provided)
        keyword_matches = []
        if filter_dict:
            try:
                keyword_response = vs.query(
                    vector=vector,
                    top_k=k,
                    namespace=ns,
                    filter=filter_dict,
                    include_values=False,
                    include_metadata=True,
                )
                keyword_matches = keyword_response.get("matches", [])
                logging.debug("HybridSearch: Keyword filtered search query successful, %d matches found.", len(keyword_matches))
            except Exception as e:
                logging.error("HybridSearch: Vector store keyword filtered query failed: %s", e, exc_info=True)
                # Proceed without keyword matches if error occurs

        # Merge and boost scores for items appearing in both results
        merged_dict = {}

        for match in semantic_matches:
            score = match.get("score", 0)
            if score >= t:
                merged_dict[match["id"]] = {
                    "id": match["id"],
                    "score": score,
                    "keywords": match.get("metadata", {}).get("keywords", ""),
                    "summary": match.get("metadata", {}).get("summary", ""),
                    "text": match.get("metadata", {}).get("source_text", ""),
                }
        logging.debug("HybridSearch: %d semantic matches passed threshold %.3f.", len(merged_dict), t)

        for match in keyword_matches:
            if match.get("score", 0) < t:
                continue
            mid = match["id"]
            if mid in merged_dict:
                # Boost score for dual match
                merged_dict[mid]["score"] += self.keyword_boost
                logging.debug("HybridSearch: Boosted score for id %s by keyword boost %.3f.", mid, self.keyword_boost)
            else:
                merged_dict[mid] = {
                    "id": mid,
                    "score": match.get("score", 0),
                    "keywords": match.get("metadata", {}).get("keywords", ""),
                    "summary": match.get("metadata", {}).get("summary", ""),
                    "text": match.get("metadata", {}).get("source_text", ""),
                }
                logging.debug("HybridSearch: Added keyword match id %s with score %.3f.", mid, match.get("score", 0))

        # Sort merged results by score descending
        results = sorted(merged_dict.values(), key=lambda x: x["score"], reverse=True)
        logging.debug("HybridSearch: Total merged results after sorting: %d", len(results))

        # Return top_k results
        final_results = results[:k]
        logging.debug("HybridSearch: Returning top %d results.", len(final_results))
        return {"results": final_results}
