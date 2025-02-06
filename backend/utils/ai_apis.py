# ai_apis.py
import requests

def openai_api_logic(file_text, additional_params=None):
    """
    Generic OpenAI API logic that can generate metadata, embeddings, or chat messages,
    based on the provided endpoint or parameters.
    
    Args:
        file_text (str): The text to process.
        additional_params (dict, optional): Additional parameters including an 'endpoint' key.
        
    Returns:
        dict: The API response.
    """
    # Default endpoint for metadata generation
    endpoint = additional_params.get("endpoint") if additional_params else None
    if not endpoint:
        # Provide a default endpoint (this might be for metadata or embeddings)
        endpoint = "https://api.openai.com/v1/engines/davinci-codex/completions"
    
    headers = {
        "Authorization": "Bearer YOUR_OPENAI_API_KEY",
        "Content-Type": "application/json"
    }
    
    # Build the payload. Adjust keys based on the API you are using.
    payload = {
        "prompt": file_text,
        "max_tokens": 50,   # Default value; may be overridden by additional_params
    }
    
    if additional_params:
        payload.update(additional_params)
    
    response = requests.post(endpoint, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

def another_api_logic(file_text, additional_params=None):
    """
    Example of another API logic function. Replace with your actual logic.
    """
    api_url = "https://api.another-ai.com/metadata"
    headers = {
        "Authorization": "Bearer YOUR_ANOTHER_API_KEY",
        "Content-Type": "application/json"
    }
    payload = {
        "text": file_text,
    }
    if additional_params:
        payload.update(additional_params)
    
    response = requests.post(api_url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

def send_to_api(file_text, api_logic_func, additional_params=None):
    """
    Interface layer that sends file_text to a chosen API using the provided api_logic_func.
    
    Args:
        file_text (str): The text extracted from the file.
        api_logic_func (function): A function that implements the logic for a specific API.
        additional_params (dict, optional): Additional parameters for the API call.
        
    Returns:
        dict: The response from the API.
    """
    try:
        result = api_logic_func(file_text, additional_params)
        return result
    except Exception as e:
        # Log the error as needed.
        print(f"Error sending to API: {e}")
        return None
