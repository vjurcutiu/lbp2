import os
import logging
from typing import Optional, Dict, Any, List

from utils.ai_apis import send_to_api, openai_api_logic
from utils.pinecone_client import PineconeClient

# Configure module-level defaults from environment
DEFAULT_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
DEFAULT_TOP_K = int(os.getenv("RAG_TOP_K", 10))
DEFAULT_THRESHOLD = float(os.getenv("RAG_THRESHOLD", 0.7))


class Embedder:
    """
    A simple embedding interface. Uses OpenAI API via send_to_api().
    """
    def __init__(self, model: Optional[str] = None):
        self.model = model or DEFAULT_EMBEDDING_MODEL

    def embed(self, text: str) -> List[float]:
        """
        Returns an embedding vector for the given text.
        """
        prompt = f"Represent this sentence for searching relevant passages: {text}"
        try:
            return send_to_api(prompt, openai_api_logic, purpose="embeddings")
        except Exception as e:
            logging.error("Embedder.embed failed: %s", e, exc_info=True)
            raise


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
