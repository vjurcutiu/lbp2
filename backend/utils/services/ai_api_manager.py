import os
import logging
from typing import Any, Dict, List, Optional, Union
from utils.services.generators.keyword_generator import generate_keywords

from openai import OpenAI

# Fallback for OpenAIError import on clients lacking openai.error module
try:
    from openai.error import OpenAIError
except ImportError:
    class OpenAIError(Exception):
        """Fallback exception when openai.error cannot be imported."""
        pass

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from utils.models.chat_payload import ChatPayload


class OpenAIAPIError(Exception):
    """Custom exception to wrap OpenAI API errors."""
    pass


class OpenAIService:
    """
    Service wrapper around the OpenAI client, with retry, logging, and
    a unified chat endpoint that consumes our ChatPayload model.
    """

    def __init__(
        self,
        client: Optional[OpenAI] = None,
        model_map: Optional[Dict[str, str]] = None
    ):
        # Allow injection of a preconfigured OpenAI client
        self.client = client or OpenAI()
        # Configure default models, overridable via environment variables
        self.model_map = model_map or {
            "chat": os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
            "embeddings": os.getenv("OPENAI_EMBED_MODEL", "text-embedding-ada-002"),
        }
        self.logger = logging.getLogger(self.__class__.__name__)

    @retry(
        retry=retry_if_exception_type(OpenAIError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _chat_completion(
        self,
        context: str,
        prompt: str,
        stream: bool = False
    ) -> Union[str, Any]:
        """
        Legacy helper: wraps chat by embedding prompt into a single user message.
        Keeps backward compatibility for any code still calling _chat_completion.
        """
        self.logger.debug("Chat request [model=%s, stream=%s]", self.model_map["chat"], stream)
        messages = [
            {"role": "system", "content": (
                "You are a helpful assistant. The context represents the previous messages in the conversation."
            )},
            {"role": "user", "content": f"{context}\nThis is where the prompt starts: {prompt}"}
        ]
        response = self.client.chat.completions.create(
            model=self.model_map["chat"],
            messages=messages,
            stream=stream
        )
        if stream:
            return response
        return response.choices[0].message.content

    @retry(
        retry=retry_if_exception_type(OpenAIError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _create_embeddings(self, input_text: str) -> List[float]:
        """
        Internal method for generating embeddings.
        """
        self.logger.debug("Embedding request [model=%s]", self.model_map["embeddings"])
        resp = self.client.embeddings.create(
            model=self.model_map["embeddings"],
            input=input_text
        )
        return resp.data[0].embedding

    @retry(
        retry=retry_if_exception_type(OpenAIError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _generic_completion(
        self,
        prompt: str,
        system_instruction: str,
        model: str
    ) -> str:
        """
        Generic single-turn completion for summary, title, keywords, etc.
        """
        self.logger.debug("Generic completion [model=%s]", model)
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ]
        response = self.client.chat.completions.create(
            model=model,
            messages=messages
        )
        return response.choices[0].message.content

    def chat(self, payload: ChatPayload) -> Union[str, Any]:
        """
        Unified chat entrypoint: consumes a ChatPayload, passes all its
        parameters directly to the OpenAI API, and returns text or stream.
        """
        self.logger.debug(
            "ChatPayload request [model=%s, stream=%s, temperature=%s, top_p=%s]",
            payload.model, payload.stream, payload.temperature, payload.top_p
        )

        # pydantic .dict() will drop None fields (exclude_none = True in Config)
        params = payload.dict()

        # Ensure we use our env-default model if none specified
        params.setdefault("model", self.model_map["chat"])

        # Call OpenAI
        response = self.client.chat.completions.create(**params)

        if payload.stream:
            return response
        return response.choices[0].message.content

    def summarize(self, text: str) -> str:
        """
        Summarize the given text in Romanian.
        """
        if not text:
            raise ValueError("Text for summarization is empty")
        instruction = "Summarize this document in Romanian."
        try:
            return self._generic_completion(text, instruction, self.model_map["chat"]).strip()
        except Exception as e:
            self.logger.error("Summarization failed", exc_info=True)
            raise OpenAIAPIError("Summarization failed") from e

    def keywords(self, text: str) -> str:
        """
        Generate keywords in Romanian for a legal document.
        Returns 'broken' if the input is too short.
        """
        try:
            return generate_keywords(text)
        except Exception as e:
            self.logger.error("Keyword extraction failed", exc_info=True)
            raise OpenAIAPIError("Keyword extraction failed") from e

    def generate_title(self, text: str) -> str:
        """
        Generate a conversation title based on the initial message, in Romanian.
        """
        if not text:
            return "Untitled"
        instruction = (
            "Generate a concise conversation title based on this initial message in Romanian."
        )
        try:
            return self._generic_completion(text, instruction, self.model_map["chat"]).strip()
        except Exception as e:
            self.logger.error("Title generation failed", exc_info=True)
            raise OpenAIAPIError("Title generation failed") from e

    def embeddings(self, text: str) -> List[float]:
        """
        Public method for generating embeddings.
        """
        if not text:
            raise ValueError("Text for embeddings must not be empty")
        try:
            return self._create_embeddings(text)
        except Exception as e:
            self.logger.error("Embedding generation failed", exc_info=True)
            raise OpenAIAPIError("Embedding generation failed") from e
