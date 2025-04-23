import traceback
from openai import OpenAI

def openai_api_logic(text, additional_params=None, purpose='chat'):
    """
    Generic OpenAI API logic that can generate metadata, embeddings, or chat messages,
    based on the provided endpoint or parameters.
    """
    print("Entering openai_api_logic")
    print(f"Received additional_params: {additional_params}")
    print(f"Purpose: {purpose}")

    client = OpenAI()

    # Build the payload. Adjust keys based on the API you are using.
    payload = {
        "prompt": text,
    }
    if additional_params:
        payload.update(additional_params)


    try:
        if purpose == 'chat':
            # Check that 'context' exists in the payload
            if 'context' not in payload:
                print("Warning: No 'context' found in payload. This may lead to an error.")
            
            completion = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant. The context represents the previous messages sent by the "
                            "user in the conversation. Try to infer what the general direction of the conversation is "
                            "based on those messages. The prompt is the current question. Answer the current question "
                            "only, unless the user brings up previous information in the conversation."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"{payload.get('context','[NO CONTEXT PROVIDED]')} "
                                   f"this is where the context ends. "
                                   f"This is where the prompt starts: {payload['prompt']}"
                    }
                ]
            )
            
            print("Chat completion response received from OpenAI.")
            return completion.choices[0].message

        elif purpose == 'keywords':
            completion = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Generate keywords in Romanian for this legal document. The keywords will be used for a "
                            "search engine. If the document is empty, or has just a few words in it, the keyword "
                            "should be 'broken'."
                        )
                    },
                    {
                        "role": "user",
                        "content": payload['prompt']
                    }
                ]
            )
            print("Keywords response received from OpenAI.")
            return completion.choices[0].message

        elif purpose == 'summary':
            completion = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Summarize this document in romanian."
                    },
                    {
                        "role": "user",
                        "content": payload['prompt']
                    }
                ]
            )
            print("Summary response received from OpenAI.")
            return completion.choices[0].message

        elif purpose == 'embeddings':
            response = client.embeddings.create(
                model="text-embedding-ada-002",
                input=payload['prompt'],
            )
            print("Embeddings response received from OpenAI.")
            return response.data[0].embedding

        elif purpose == 'convo-name':
            completion = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Generate a conversation title based on this initial message. Please make it in Romanian."
                    },
                    {
                        "role": "user",
                        "content": payload['prompt']
                    }
                ]
            )
            print("Conversation name response received from OpenAI.")
            return completion.choices[0].message

        else:
            print(f"Warning: Unrecognized purpose '{purpose}'. No API call made.")
            return None

    except Exception as e:
        print("Error occurred in openai_api_logic:")
        traceback.print_exc()
        return None


def send_to_api(text, api_logic_func, additional_params=None, purpose='chat'):
    """
    Interface layer that sends text to a chosen API using the provided api_logic_func.
    """
    print("Entering send_to_api")
    print(f"Additional params: {additional_params}")
    print(f"Purpose: {purpose}")

    try:
        result = api_logic_func(text, additional_params, purpose)
        print("API call completed successfully.")
        return result
    except Exception as e:
        print("Error sending to AI API in send_to_api:")
        traceback.print_exc()
        return None
