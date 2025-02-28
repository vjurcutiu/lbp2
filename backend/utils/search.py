import os
from dotenv import load_dotenv
from pinecone.grpc import PineconeGRPC as Pinecone

# Load environment variables from .env file
load_dotenv()

def search(chat_message, additional_params=None):
    """
    Embeds a chat message and searches a Pinecone vector index, returning results 
    that include keywords, summary, and text.

    Args:
        chat_message (str): The message from the frontend to search.
        additional_params (dict, optional): Dictionary that may include:
            - 'index_name': The Pinecone index name (default: "test")
            - 'namespace': The namespace to query (default: "default-namespace")
            - 'top_k': Number of results to return (default: 3)

    Returns:
        dict: A dictionary containing search results, each with keywords, summary, and text.
    """
    # Set default additional parameters if not provided.
    if additional_params is None:
        additional_params = {}
    index_name = additional_params.get("index_name", "test")
    namespace = additional_params.get("namespace", "default-namespace")
    top_k = additional_params.get("top_k", 3)
    
    # Load the Pinecone API key from the environment variables.
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY is not set in the environment variables.")
    
    # Initialize the Pinecone client with the API key.
    pc = Pinecone(api_key=api_key)
    
    # Embed the chat message using the query embedding (using the same model as for upsert).
    query_embedding = pc.inference.embed(
        model="multilingual-e5-large",
        inputs=[chat_message],
        parameters={"input_type": "query"}
    )
    
    # Get a handle for the desired index.
    index = pc.Index(index_name)
    
    # Query the index using the generated embedding.
    results = index.query(
        namespace=namespace,
        vector=query_embedding[0].values,
        top_k=top_k,
        include_metadata=True,
        include_values=False  # values not needed for this example
    )
    
    # Process results: each match should include metadata fields for keywords, summary, and text.
    processed_results = []
    for match in results.get("matches", []):
        metadata = match.get("metadata", {})
        processed_results.append({
            "id": match.get("id"),
            "score": match.get("score"),
            "keywords": metadata.get("keywords", ""),
            "summary": metadata.get("summary", ""),
            "text": metadata.get("source_text", "")
        })
    
    return {"results": processed_results}
