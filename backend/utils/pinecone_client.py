import os
from typing import List, Dict, Optional, Any
from pinecone import Pinecone
import logging

logger = logging.getLogger(__name__)

class PineconeClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        environment: Optional[str] = None,
        index_name: Optional[str] = None,
        namespace: Optional[str] = None,
    ):
        """
        A thin wrapper around the Pinecone Python client (v3+).
        Reads index and namespace from .env if not explicitly provided.
        """
        # Credentials
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.environment = environment or os.getenv("PINECONE_ENV")
        if not self.api_key or not self.environment:
            raise ValueError("PINECONE_API_KEY and PINECONE_ENV must be set")

        # Index and namespace configuration
        self.index_name = (
            index_name 
            or os.getenv("PINECONE_INDEX") 
            or "default-index"
        )
        self.namespace = (
            namespace 
            or os.getenv("PINECONE_NAMESPACE")
        )

        # Instantiate the Pinecone v3 client
        self.client = Pinecone(
            api_key=self.api_key,
            environment=self.environment
        )
        # Get a handle to the desired index
        self.index = self.client.Index(self.index_name)

    def upsert(
        self,
        vectors: List[Dict[str, Any]],
        namespace: Optional[str] = None,
        batch_size: int = 100,
    ) -> Dict:
        """
        Upsert a batch of vector records into the index.
        Each record must be: {"id": str, "values": List[float], "metadata": {...}}
        """
        resp: Dict = {}
        ns = namespace or self.namespace
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]
            # v3 API: upsert directly on the Index instance
            resp_part = self.index.upsert(batch, ns )
            logger.debug(
                "[%s.upsert] before update: resp=%r, resp_part=%r",
                self.__class__.__name__,
                resp,
                resp_part,
            )
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
        ns = namespace or self.namespace
        if ids:
            return self.index.delete(ids=ids, namespace=ns)
        elif filter:
            return self.index.delete(filter=filter, namespace=ns)
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
        Perform a similarity search against the index.
        """
        ns = namespace or self.namespace
        return self.index.query(
            vector=vector,
            top_k=top_k,
            namespace=ns,
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
        Fetch specific vectors by their IDs.
        """
        ns = namespace or self.namespace
        return self.index.fetch(ids=ids, namespace=ns)

    def describe_index(self) -> Dict:
        """
        Get index stats, dimensions, pods, etc.
        """
        return self.client.describe_index(self.index_name)

    def info(self) -> Dict:
        """
        Shortcut to index.describe_index_stats().
        """
        return self.index.describe_index_stats()
