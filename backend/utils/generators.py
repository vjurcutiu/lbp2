# conversation_generator.py

from ai_apis import openai_api_logic, send_to_api

def generate_conversation_title(first_message):
    """
    Generate a conversation title based on the first message.
    
    Args:
        first_message (str): The first message of the conversation.
    
    Returns:
        str: A generated title for the conversation.
    """
    # Use send_to_api with purpose 'convo-name' which leverages the appropriate AI prompt.
    response = send_to_api(first_message, api_logic_func=openai_api_logic, purpose='convo-name')
    
    # Assuming the API returns a dictionary with a "content" key that holds the generated title.
    title = response.get("content", "").strip()
    return title

# Example usage:
if __name__ == '__main__':
    test_message = "Bună ziua, aș dori să aflu mai multe despre serviciile dumneavoastră."
    generated_title = generate_conversation_title(test_message)
    print("Generated Conversation Title:", generated_title)
