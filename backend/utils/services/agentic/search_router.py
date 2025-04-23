import json
from typing import Any, Dict, List

from utils.ai_apis import send_to_api, openai_api_logic
from utils.pinecone_client import PineconeClient

from utils.search import KeywordSearch, VectorSearch, Embedder, default_search
# (Assume Embedder, VectorSearch, default_search, and KeywordSearch from earlier are defined here.)

class SearchRouter:
    """
    Agent that decides, via an LLM call, whether to use keyword or semantic search,
    then invokes the chosen strategy.
    """
    def __init__(
        self,
        items_for_keyword: List[Dict[str, Any]],
        embedder_model: str = None,
        pinecone_namespace: str = None,
    ):
        # Prepare our two backends
        self.keyword_search = KeywordSearch(items_for_keyword)
        self.semantic_search = VectorSearch(embedder=Embedder(embedder_model))
        self.namespace = pinecone_namespace

    def _decide_mode(self, query: str) -> str:
        """
        Ask the LLM whether to use 'keyword' or 'semantic' for this query.
        """
        prompt = f"""
            You are a smart search router.  
            Given the user’s query, reply with exactly one word—either "keyword" or "semantic"—
            to pick the best search strategy.  
            Query: "{query}"
            """
        resp = send_to_api(prompt, openai_api_logic, purpose="chat_completion")
        mode = resp.strip().lower()
        if mode not in {"keyword", "semantic"}:
            # fallback to semantic if LLM misbehaves
            mode = "semantic"
        return mode

    def search(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.7,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Routes the query through keyword or semantic search depending on the LLM’s decision.
        Returns a unified {"mode": ..., "results": [...]} structure.
        """
        mode = self._decide_mode(query)

        if mode == "keyword":
            # exact-match keyword search
            kws = self.keyword_search.search(query, case_insensitive=True, limit=limit)
            # Wrap into the same envelope as semantic results:
            results = [
                {
                    "id": item["id"],
                    "score": None,
                    "keywords": json.loads(item["metadata"]["keywords"])["keywords"],
                    "summary": None,
                    "text": item.get("text", ""),
                }
                for item in kws
            ]
        else:
            # semantic / vector search
            sem = self.semantic_search.search(
                query,
                top_k=top_k,
                namespace=self.namespace,
                threshold=threshold
            )
            results = sem["results"]

        return {"mode": mode, "results": results}


# Example wiring in your application code:
if __name__ == "__main__":
    # Load your file records once
    file_records = [
        {
            "id": f["id"],
            "file_path": f["file_path"],
            "metadata": f["meta_data"],
            "text": open(f["file_path"], encoding="utf-8").read(),
        }
        for f in files  # however you inject that list
    ]

    router = SearchRouter(items_for_keyword=file_records)
    user_query = input("Enter your search: ")
    out = router.search(user_query)
    print(f"Using {out['mode']} search:")
    for r in out["results"]:
        print(f" • {r['id']} — {r['text'][:80]}…")
