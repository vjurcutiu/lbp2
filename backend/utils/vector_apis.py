import os
from dotenv import load_dotenv
import requests
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
import time
from db.models import File, db

# Load environment variables from .env file
load_dotenv()

def pinecone_vector_logic(embeddings, additional_params=None, filetext=''):
    """
    Upserts embeddings to a Pinecone vector database.
    
    Args:
        embeddings (list or dict): The embeddings generated from your file data.
            If a dict, it is expected to have a key "values" containing the list of floats.
        additional_params (dict, optional): Extra parameters including:
            - index_name: Name of the Pinecone index (default: "test")
            - namespace: Namespace to use (default: "default-namespace")
            - id: Optional identifier for the record (default: generated from current time)
        filetext (str, optional): The original file text to include in the metadata.
    
    Returns:
        dict: The response from the Pinecone index upsert operation.
    """
    try:
        print(embeddings)
        
        # Set default parameters
        additional_params = additional_params or {}
        index_name = additional_params.get("index_name", "test")
        namespace = additional_params.get("namespace", "default-namespace")
        record_id = additional_params.get("id", f"file-{int(time.time())}")
        
        
        # Load the Pinecone API key from the environment variables.
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY is not set in the environment variables.")
        
        # Initialize the Pinecone client and get the index
        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)
        
        # Prepare the vector values; if embeddings is a dict, extract the "values" key.
        if isinstance(embeddings, dict):
            vector_values = embeddings.get("values", [])
        else:
            vector_values = embeddings
        
        # Create a record for upsert
        record = {
            "id": record_id,
            "values": vector_values,
            "metadata": {
                "source_text": filetext
            }
        }
        
        # Upsert the record into the index under the specified namespace
        upsert_response = index.upsert(vectors=[record], namespace=namespace)
        
        return upsert_response
    except Exception as e:
        print(f"Error in pinecone_vector_logic: {e}")
        raise

def send_to_vector_db(embeddings, vector_logic_func, additional_params=None, filetext=''):
    """
    Interface layer for sending embeddings to a vector database.
    
    Args:
        embeddings (dict or list): The embeddings to upsert.
        vector_logic_func (function): The function implementing the vector upsert logic.
        additional_params (dict, optional): Extra parameters for the API call.
    
    Returns:
        dict: The response from the vector API.
    """
    try:
        print("About to call vector_logic_func in send_to_vector_db")
        result = vector_logic_func(embeddings, additional_params, filetext)
        print("vector_logic_func returned successfully")
        return result
    except Exception as e:
        print(f"Error sending to vector database: {e}")
        return None
