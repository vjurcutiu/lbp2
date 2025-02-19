# vector_apis.py
import requests
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
import time

from db.models import File, db

def pinecone_vector_logic(embeddings, additional_params=None, filetext=''):
    """
    Example logic for upserting embeddings to a Pinecone-like vector database.
    
    Args:
        embeddings (dict or list): The embeddings generated from your file data.
        endpoint (str): The API endpoint for the vector database.
        additional_params (dict, optional): Extra parameters for the API call.
    
    Returns:
        dict: The response from the vector database.
    """
    pc = Pinecone(api_key="YOUR_API_KEY")    
        
    payload = embeddings
    
    response = requests.post(json=payload)
    response.raise_for_status()
    return response.json()

def send_to_vector_db(embeddings, endpoint, vector_logic_func, additional_params=None, filetext=''):
    """
    Interface layer for sending embeddings to a vector database.
    
    Args:
        embeddings (dict or list): The embeddings to upsert.
        endpoint (str): The API endpoint for the vector database.
        vector_logic_func (function): The function implementing the vector upsert logic.
        additional_params (dict, optional): Extra parameters for the API call.
    
    Returns:
        dict: The response from the vector API.
    """
    try:
        result = vector_logic_func(embeddings, endpoint, additional_params)
        return result
    except Exception as e:
        print(f"Error sending to vector database: {e}")
        return None
