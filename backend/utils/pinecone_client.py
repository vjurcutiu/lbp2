# pinecone_client.py

import os
import time
from typing import List, Dict, Optional, Any

import pinecone

class PineconeClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        environment: Optional[str] = None,
        index_name: str = "default-index",
    ):
        """
        A thin wrapper around the Pinecone Python client.
        """
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.environment = environment or os.getenv("PINECONE_ENV")
        if not self.api_key or not self.environment:
            raise ValueError("PINECONE_API_KEY and PINECONE_ENV must be set")
        
        pinecone.init(api_key=self.api_key, environment=self.environment)
        self.index_name = index_name
        self.index = pinecone.Index(self.index_name)

    def upsert(
        self,
        vectors: List[Dict[str, Any]],
        namespace: Optional[str] = None,
        batch_size: int = 100,
    ) -> Dict:
        """
        Upsert a batch (or list) of vector records.
        Each record must be: {"id": str, "values": List[float], "metadata": {...}}
        """
        resp = {}
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]
            resp_part = self.index.upsert(vectors=batch, namespace=namespace)
            resp.update(resp_part)
        return resp

    def delete(
        self,
        ids: Optional[List[str]] = None,
        filter: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None,
    ) -> Dict:
        """
        Delete by explicit IDs or by metadata filter.
        """
        if ids:
            return self.index.delete(ids=ids, namespace=namespace)
        elif filter:
            return self.index.delete(filter=filter, namespace=namespace)
        else:
            raise ValueError("Must provide ids or filter to delete")

    def query(
        self,
        vector: List[float],
        top_k: int = 10,
        namespace: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
        include_values: bool = False,
        include_metadata: bool = True,
    ) -> Dict:
        """
        Perform a similarity search.
        """
        return self.index.query(
            vector=vector,
            top_k=top_k,
            namespace=namespace,
            filter=filter,
            include_values=include_values,
            include_metadata=include_metadata,
        )

    def fetch(
        self,
        ids: List[str],
        namespace: Optional[str] = None,
    ) -> Dict:
        """
        Fetch specific vectors by ID.
        """
        return self.index.fetch(ids=ids, namespace=namespace)

    def describe_index(self) -> Dict:
        """
        Get index stats, dimensions, pods, etc.
        """
        return pinecone.describe_index(self.index_name)

    def info(self) -> Dict:
        """
        Shortcut to index.describe_index_stats()
        """
        return self.index.describe_index_stats()
