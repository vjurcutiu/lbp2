import os
import logging
import re
import json
import spacy
from openai import OpenAI
# Fallback for OpenAIError import on clients without openai.error
try:
    from openai.error import OpenAIError
except ImportError:
    class OpenAIError(Exception):
        """Fallback exception when openai.error cannot be imported."""
        pass
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


# Load Romanian tokenizer and lemmatizer
# Ensure you've installed: pip install spacy ro-core-news-sm
nlp = spacy.load("ro_core_news_sm")

# Default model for keyword generation
DEFAULT_KEYWORD_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

@retry(
    retry=retry_if_exception_type(OpenAIError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def _generic_completion(prompt: str, system_instruction: str, model: str) -> str:
    """
    Internal helper for single-turn completions.
    """
    logger = logging.getLogger("KeywordGenerator")
    logger.debug("Generic completion for keywords [model=%s]", model)
    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": prompt}
    ]
    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    return response.choices[0].message.content


def preprocess_text(text: str) -> str:
    """
    Clean and normalize document text:
    - Strip boilerplate legal citations, headers/footers, footnotes
    - Normalize whitespace & punctuation, remove newlines
    - Correct common OCR errors (placeholder)
    - Lemmatize and preserve multi-word entities
    """
    logger = logging.getLogger("KeywordGenerator")
    # Remove numbered citations/footnotes lines
    text = re.sub(r"^\s*\[?\d+\]?\s.*$", "", text, flags=re.MULTILINE)
    # Remove headers/footers like 'Pagina X din Y'
    text = re.sub(r"Pagina\s+\d+\s+din\s+\d+", "", text)

    # Normalize line breaks explicitly
    text = re.sub(r"[\r\n]+", " ", text)
    # Normalize other whitespace
    text = re.sub(r"[\s\f\t\v]+", " ", text).strip()

    # Placeholder OCR corrections
    corrections = {'0': 'O', '1': 'I'}
    for wrong, right in corrections.items():
        text = text.replace(wrong, right)

    # Tokenize & lemmatize, merge entities into single tokens
    doc = nlp(text)
    with doc.retokenize() as retokenizer:
        for ent in doc.ents:
            retokenizer.merge(ent)
    tokens = [token.lemma_ for token in doc if not token.is_space]
    return " ".join(tokens)


def generate_keywords(text: str) -> str:
    """
    Generate keywords in Romanian for a legal document.
    Returns 'broken' if the input is empty or too short.
    Cleans up newline and whitespace in the output, and ensures valid JSON formatting as
    {"keywords": [...] }.
    """
    logger = logging.getLogger("KeywordGenerator")
    cleaned = preprocess_text(text)
    # Consider text too short if under 30 words
    if len(cleaned.split()) < 30:
        return json.dumps({"keywords": []}, ensure_ascii=False)

    instruction = (
        "You are a keyword‑extraction assistant. Given a Romanian legal text, "
        "return up to 8 keyphrases that best capture its topics as a JSON array of lowercase strings. "
        "Prefer multi‑word nouns or noun phrases."
    )
    try:
        raw = _generic_completion(cleaned, instruction, DEFAULT_KEYWORD_MODEL).strip()
        # Collapse internal whitespace and newlines
        compact = re.sub(r"[\r\n]+", " ", raw)
        # Try parsing JSON array
        try:
            arr = json.loads(compact)
        except json.JSONDecodeError:
            # Fallback parsing for bullet lists
            lines = re.split(r"[\r\n]+", compact)
            arr = [ln.strip().lstrip("- ").strip() for ln in lines if ln.strip()]
        # Wrap into object
        return json.dumps({"keywords": arr}, ensure_ascii=False)
    except Exception as e:
        logger.error("Keyword extraction failed", exc_info=True)
        raise e
