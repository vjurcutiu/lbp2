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

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_selection import SelectKBest, chi2
from rake_nltk import Rake
import yake

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

def extract_tfidf_keywords(text: str, top_k: int = 8, ngram_range=(1,3)) -> list[str]:
    """
    Use TF–IDF to score n-grams and pick the top_k highest-scoring phrases.
    """
    # Vectorize
    vect = TfidfVectorizer(
        ngram_range=ngram_range,
        stop_words="romanian",
        max_df=0.85,
        min_df=2,
    )
    X = vect.fit_transform([text])
    # chi2 needs at least two samples; we can simulate by duplicating the text and zeroing labels
    X_dup = X.vstack([X])  # two identical samples
    y = [1, 0]
    # Select top features by chi2 score
    skb = SelectKBest(chi2, k=min(top_k, X.shape[1]))
    skb.fit(X_dup, y)
    mask = skb.get_support()
    candidates = [(feat, score) for feat, score in zip(vect.get_feature_names_out(), skb.scores_) if feat and mask[vect.vocabulary_.get(feat)]]
    # sort by score
    best = sorted(candidates, key=lambda x: -x[1])[:top_k]
    return [phrase for phrase, score in best]


def extract_rake_keywords(text: str, top_k: int = 8) -> list[str]:
    """
    Use RAKE (Rapid Automatic Keyword Extraction).
    """
    rake = Rake(language="romanian")  # uses default stopwords & punctuation
    rake.extract_keywords_from_text(text)
    ranked = rake.get_ranked_phrases()
    return ranked[:top_k]


def extract_yake_keywords(text: str, top_k: int = 8, ngram_max=3) -> list[str]:
    """
    Use YAKE (Yet Another Keyword Extractor).
    """
    kw_extractor = yake.KeywordExtractor(
        lan="ro",
        n=ngram_max,
        top=top_k,
        features=None
    )
    keywords = kw_extractor.extract_keywords(text)
    # keywords is list of (phrase, score), lower score = more relevant
    # so sort ascending
    sorted_phrases = sorted(keywords, key=lambda x: x[1])
    return [phrase for phrase, score in sorted_phrases]

def generate_keywords(text: str, method: str = "openai") -> str:
    """
    Generate up to 8 keywords for a Romanian legal document.

    Parameters:
        text: raw document text
        method: one of
            - "openai": use GPT-based extraction (default)
            - "tfidf":  TF–IDF + SelectKBest
            - "rake":   RAKE (rake-nltk)
            - "yake":   YAKE
    Returns:
        A JSON string of the form {"keywords": [...]}.
    """
    # 1. Clean and lemmatize
    cleaned = preprocess_text(text)

    # 2. If too short, return empty list
    if len(cleaned.split()) < 30:
        return json.dumps({"keywords": []}, ensure_ascii=False)

    # 3. Select extraction method
    if method == "openai":
        instruction = (
            "You are a keyword‑extraction assistant. Given a Romanian legal text, "
            "return up to 8 keyphrases that best capture its topics as a JSON array of lowercase strings. "
            "Prefer multi‑word nouns or noun phrases."
        )
        raw = _generic_completion(cleaned, instruction, DEFAULT_KEYWORD_MODEL).strip()
        # Collapse newlines
        compact = re.sub(r"[\r\n]+", " ", raw)
        # Try to parse JSON array directly
        try:
            arr = json.loads(compact)
            # If the top-level is an object, extract its "keywords" field
            if isinstance(arr, dict) and "keywords" in arr:
                arr = arr["keywords"]
        except json.JSONDecodeError:
            # Fallback: split on bullets or lines
            lines = re.split(r"[\r\n]+", raw)
            arr = [ln.strip().lstrip("-•  ").strip() for ln in lines if ln.strip()]
        keywords = arr[:8]

    elif method == "tfidf":
        keywords = extract_tfidf_keywords(cleaned, top_k=8, ngram_range=(1,3))

    elif method == "rake":
        keywords = extract_rake_keywords(cleaned, top_k=8)

    elif method == "yake":
        keywords = extract_yake_keywords(cleaned, top_k=8, ngram_max=3)

    else:
        raise ValueError(f"Unknown extraction method: {method!r}")

    # 4. Wrap and output
    return json.dumps({"keywords": keywords}, ensure_ascii=False)

