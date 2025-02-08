# ai_apis.py
import requests
from openai import OpenAI


def openai_api_logic(text, additional_params=None):
    """
    Generic OpenAI API logic that can generate metadata, embeddings, or chat messages,
    based on the provided endpoint or parameters.
    
    Args:
        file_text (str): The text to process.
        additional_params (dict, optional): Additional parameters including an 'endpoint' key.
        
    Returns:
        dict: The API response.
    """
    client = OpenAI()
    
    # Build the payload. Adjust keys based on the API you are using.
    payload = {
        "prompt": text,
        }
    
    if additional_params:
        payload.update(additional_params)
    
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": payload['prompt']
            }
        ]
    )
    
    return completion.choices[0].message


def send_to_api(text, api_logic_func, additional_params=None):
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
        result = api_logic_func(text, additional_params)
        return result
    except Exception as e:
        # Log the error as needed.
        print(f"Error sending to API: {e}")
        return None
