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

# Graph‑based & embedding‑based methods
import pke
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer
from gensim import corpora, models

# Load Romanian tokenizer and lemmatizer
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
    text = re.sub(r"^\s*\[?\d+\]?\s.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"Pagina\s+\d+\s+din\s+\d+", "", text)
    text = re.sub(r"[\r\n]+", " ", text)
    text = re.sub(r"[\s\f\t\v]+", " ", text).strip()
    corrections = {'0': 'O', '1': 'I'}
    for wrong, right in corrections.items():
        text = text.replace(wrong, right)
    doc = nlp(text)
    with doc.retokenize() as retokenizer:
        for ent in doc.ents:
            retokenizer.merge(ent)
    tokens = [token.lemma_ for token in doc if not token.is_space]
    return " ".join(tokens)


def extract_tfidf_keywords(text: str, top_k: int = 8, ngram_range=(1,3)) -> list[str]:
    vect = TfidfVectorizer(
        ngram_range=ngram_range,
        stop_words="romanian",
        max_df=0.85,
        min_df=2,
    )
    X = vect.fit_transform([text])
    X_dup = X.vstack([X])  # two identical samples
    y = [1, 0]
    skb = SelectKBest(chi2, k=min(top_k, X.shape[1]))
    skb.fit(X_dup, y)
    mask = skb.get_support()
    candidates = [
        (feat, score) for feat, score in zip(vect.get_feature_names_out(), skb.scores_)
        if mask[vect.vocabulary_.get(feat)]
    ]
    best = sorted(candidates, key=lambda x: -x[1])[:top_k]
    return [phrase for phrase, score in best]


def extract_rake_keywords(text: str, top_k: int = 8) -> list[str]:
    rake = Rake(language="romanian")
    rake.extract_keywords_from_text(text)
    return rake.get_ranked_phrases()[:top_k]


def extract_yake_keywords(text: str, top_k: int = 8, ngram_max=3) -> list[str]:
    kw_extractor = yake.KeywordExtractor(lan="ro", n=ngram_max, top=top_k)
    keywords = kw_extractor.extract_keywords(text)
    sorted_phrases = sorted(keywords, key=lambda x: x[1])
    return [phrase for phrase, score in sorted_phrases]


def extract_pke_keywords(text: str, top_k: int = 8, method: str = "TextRank") -> list[str]:
    """
    Graph-based extraction via pke (TextRank, SingleRank, PositionRank, TopicRank, etc.)
    """
    extractor_cls = getattr(pke.unsupervised, method)
    extractor = extractor_cls()
    extractor.load_document(input=text, language='ro')
    extractor.candidate_selection()  # default POS-based selection
    extractor.candidate_weighting()
    keyphrases = extractor.get_n_best(n=top_k)
    return [kp for kp, _ in keyphrases]


def extract_keybert_keywords(text: str, top_k: int = 8,
                               model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2') -> list[str]:
    """
    Embedding-based extraction using KeyBERT.
    """
    bert_model = SentenceTransformer(model_name)
    kw_model = KeyBERT(model=bert_model)
    results = kw_model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 3),
        stop_words='romanian',
        top_n=top_k
    )
    return [kw for kw, _ in results]


def extract_gensim_lda_keywords(text: str, top_k: int = 8, num_topics: int = 1, passes: int = 10) -> list[str]:
    """
    Topic modeling via Gensim LDA to extract top topic words.
    """
    tokens = [t.lemma_ for t in nlp(text) if t.is_alpha and not t.is_stop]
    dictionary = corpora.Dictionary([tokens])
    corpus = [dictionary.doc2bow(tokens)]
    lda = models.LdaModel(corpus=corpus, id2word=dictionary,
                          num_topics=num_topics, passes=passes)
    topics = lda.show_topic(0, topn=top_k)
    return [word for word, _ in topics]


def extract_gensim_word2vec_keywords(text: str, top_k: int = 8,
                                      vector_size: int = 100, window: int = 5, min_count: int = 2) -> list[str]:
    """
    Embedding-based extraction via Gensim Word2Vec: find words closest to document centroid.
    """
    sentences = [[t.lemma_ for t in sent if t.is_alpha and not t.is_stop] for sent in nlp(text).sents]
    model = models.word2vec.Word2Vec(sentences, vector_size=vector_size,
                                     window=window, min_count=min_count)
    # compute centroid
    centroid = sum(model.wv[w] for sent in sentences for w in sent) / sum(len(sent) for sent in sentences)
    similar = model.wv.similar_by_vector(centroid, topn=top_k)
    return [word for word, _ in similar]


def generate_keywords(text: str, method: str = "openai") -> str:
    """
    Generate up to 8 keywords for a Romanian legal document.

    method: one of
      - "openai"      : GPT-based extraction (default)
      - "tfidf", "rake", "yake"
      - "pke"         : Graph-based via pke (default uses TextRank)
      - "keybert"     : Embedding-based via KeyBERT
      - "lda"         : Topic modeling via Gensim LDA
      - "word2vec"    : Embedding-based via Gensim Word2Vec
    """
    cleaned = preprocess_text(text)
    if len(cleaned.split()) < 30:
        return json.dumps({"keywords": []}, ensure_ascii=False)

    if method == "openai":
        instruction = (
            "You are a keyword‑extraction assistant. Given a Romanian legal text, "
            "return up to 8 keyphrases that best capture its topics as a JSON array of lowercase strings. "
            "Prefer multi‑word nouns or noun phrases."
        )
        raw = _generic_completion(cleaned, instruction, DEFAULT_KEYWORD_MODEL).strip()
        compact = re.sub(r"[\r\n]+", " ", raw)
        try:
            arr = json.loads(compact)
            if isinstance(arr, dict) and "keywords" in arr:
                arr = arr["keywords"]
        except json.JSONDecodeError:
            lines = re.split(r"[\r\n]+", raw)
            arr = [ln.strip().lstrip("-•  ").strip() for ln in lines if ln.strip()]
        keywords = arr[:8]
    elif method in ("tfidf", "rake", "yake"):
        extractor = {
            "tfidf": extract_tfidf_keywords,
            "rake": extract_rake_keywords,
            "yake": extract_yake_keywords
        }[method]
        keywords = extractor(cleaned)
    elif method == "pke":
        keywords = extract_pke_keywords(cleaned)
    elif method == "keybert":
        keywords = extract_keybert_keywords(cleaned)
    elif method == "lda":
        keywords = extract_gensim_lda_keywords(cleaned)
    elif method == "word2vec":
        keywords = extract_gensim_word2vec_keywords(cleaned)
    else:
        raise ValueError(f"Unknown extraction method: {method!r}")

    return json.dumps({"keywords": keywords}, ensure_ascii=False)
