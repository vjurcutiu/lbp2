import os
import logging
import re
import json
import spacy
from openai import OpenAI
try:
    from openai.error import OpenAIError
except ImportError:
    class OpenAIError(Exception):
        pass
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_selection import SelectKBest, chi2
from rake_nltk import Rake
import yake
import pke
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer
from gensim import corpora, models
from flashtext import KeywordProcessor
from thefuzz import fuzz

# --- New imports for ontology integration ---
import rdflib
from owlready2 import get_ontology

# Load Romanian NLP model
nlp = spacy.load("ro_core_news_sm")
DEFAULT_KEYWORD_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

# -----------------------------------------------------------------------------
#                    Ontology & Taxonomy Integration
# -----------------------------------------------------------------------------

def load_rdf_ontology(path: str, format: str = "xml") -> rdflib.Graph:
    """
    Load an RDF/OWL ontology file into an rdflib.Graph.
    Supported formats: xml, ttl, owl, rdf, json-ld
    """
    g = rdflib.Graph()
    g.parse(path, format=format)
    logging.getLogger("KeywordGenerator").info(f"Loaded RDF ontology from {path}")
    return g


def load_owl_ontology(path: str):
    """
    Load an OWL ontology using Owlready2.
    Returns an Owlready2 ontology object.
    """
    onto = get_ontology(path).load()
    logging.getLogger("KeywordGenerator").info(f"Loaded OWL ontology from {path}")
    return onto


def index_labels_from_rdf(graph: rdflib.Graph, lang: str = "ro") -> dict[str, rdflib.URIRef]:
    """
    Build a mapping from label (rdfs:label, skos:prefLabel, skos:altLabel) to URI.
    Filters labels by language tag if present.
    """
    from rdflib.namespace import RDFS
    SKOS = rdflib.Namespace("http://www.w3.org/2004/02/skos/core#")
    label_predicates = [RDFS.label, SKOS.prefLabel, SKOS.altLabel]
    label_map: dict[str, rdflib.URIRef] = {}
    for subj, pred, obj in graph:
        if pred in label_predicates and isinstance(obj, rdflib.Literal):
            if obj.language and obj.language != lang:
                continue
            text = str(obj).lower()
            label_map[text] = subj
    logging.getLogger("KeywordGenerator").debug(f"Indexed {len(label_map)} labels from RDF graph")
    return label_map


def map_terms_to_ontology(
    terms: list[str],
    label_map: dict[str, rdflib.URIRef],
    matcher: str = "exact",
    fuzzy_threshold: int = 85
) -> dict[str, str]:
    """
    Map extracted terms to ontology URIs using label_map.
    matcher: 'exact' or 'fuzzy'.
    Returns dict of term -> URI (string) or None if no match.
    """
    mapped: dict[str, str] = {}
    for term in terms:
        key = term.lower()
        if matcher == "exact" and key in label_map:
            mapped[term] = str(label_map[key])
        elif matcher == "fuzzy":
            # find best fuzzy match
            best, score = None, 0
            for label, uri in label_map.items():
                s = fuzz.token_set_ratio(key, label)
                if s > score:
                    best, score = label, s
            if score >= fuzzy_threshold:
                mapped[term] = str(label_map[best])
            else:
                mapped[term] = None
        else:
            mapped[term] = None
    return mapped

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

def extract_flashtext_keywords(text: str,
                               vocabulary: list[str],
                               case_sensitive: bool = False) -> list[str]:
    """
    Use FlashText's KeywordProcessor for O(n) keyword lookup.
    Returns all vocabulary items found in text (deduped by default, order = appearance).
    """
    kp = KeywordProcessor(case_sensitive=case_sensitive)
    # you can also pass a dict mapping synonyms → normalized form
    for term in vocabulary:
        kp.add_keyword(term)
    found = kp.extract_keywords(text)
    # FlashText returns duplicates if terms repeat; dedupe while preserving order:
    seen = set()
    uniq = []
    for kw in found:
        if kw not in seen:
            seen.add(kw)
            uniq.append(kw)
    return uniq

def dedupe_keywords_fuzzy(keywords: list[str],
                          threshold: int = 85,
                          scorer=fuzz.token_set_ratio) -> list[str]:
    """
    Remove near‑duplicates from a list by fuzzy similarity.
    Keeps the first occurrence of each cluster whose similarity ≥ threshold.
    """
    deduped = []
    for kw in keywords:
        if not any(scorer(kw, existing) >= threshold for existing in deduped):
            deduped.append(kw)
    return deduped


def generate_keywords(
    text: str,
    method: str = "openai",
    flash_vocab: list[str] | None = None,
    fuzzy_threshold: int = 85,
) -> str:
    """
    Generate up to 8 keywords for a Romanian legal document.

    New methods:
      - "flashtext"    : FlashText lookup against flash_vocab
      - "flash_fuzzy"  : FlashText lookup + fuzzy deduplication (threshold=fuzzy_threshold)

    Existing methods unchanged:
      - "openai"      : GPT-based extraction (default)
      - "tfidf", "rake", "yake"
      - "pke"         : Graph-based via pke (TextRank)
      - "keybert"     : Embedding-based via KeyBERT
      - "lda"         : Topic modeling via Gensim LDA
      - "word2vec"    : Embedding-based via Gensim Word2Vec
    """
    cleaned = preprocess_text(text)
    if len(cleaned.split()) < 30:
        return json.dumps({"keywords": []}, ensure_ascii=False)

    # FlashText-only
    if method == "flashtext":
        if not flash_vocab:
            raise ValueError("flash_vocab must be provided for flashtext method")
        keywords = extract_flashtext_keywords(cleaned, flash_vocab)

    # FlashText + fuzzy dedupe
    elif method == "flash_fuzzy":
        if not flash_vocab:
            raise ValueError("flash_vocab must be provided for flash_fuzzy method")
        found = extract_flashtext_keywords(cleaned, flash_vocab)
        keywords = dedupe_keywords_fuzzy(found, threshold=fuzzy_threshold)

    # GPT-based extraction
    elif method == "openai":
        instruction = (
            """SYSTEM:
            You are a highly accurate AI assistant specialized in extracting keywords from Romanian legal documents.

            USER:
            Mai jos ai textul unei hotărâri judecătorești în limba română. Din acest text, generează întotdeauna, în această ordine, un obiect JSON valid cu următoarele câmpuri:

            - Locatie (string)  
            - Data (string, format "ZZ.MM.AAAA")  
            - Domeniu (string)  
            - Hotarare (string)  
            - cuvinte_cheie (listă de 8 string‑uri)

            Exemplu de schemă de răspuns:

            ```json
            {
            "locatie": "…, instanța …",
            "data": "ZZ.MM.AAAA",
            "domeniu": "drept penal",
            "hotarare": "condamnare/acord de recunoaștere etc.",
            "cuvinte_cheie": [
                "primul cuvânt",
                "al doilea cuvânt",
                "…",
                "al optulea cuvânt"
            ]
            }"""
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

    # TF‑IDF, RAKE, YAKE
    elif method in ("tfidf", "rake", "yake"):
        extractor = {
            "tfidf": extract_tfidf_keywords,
            "rake":  extract_rake_keywords,
            "yake":  extract_yake_keywords,
        }[method]
        keywords = extractor(cleaned)

    # Graph‑based (TextRank, etc.)
    elif method == "pke":
        keywords = extract_pke_keywords(cleaned)

    # Embedding‑based KeyBERT
    elif method == "keybert":
        keywords = extract_keybert_keywords(cleaned)

    # Topic modeling via LDA
    elif method == "lda":
        keywords = extract_gensim_lda_keywords(cleaned)

    # Embedding‑based Word2Vec centroid
    elif method == "word2vec":
        keywords = extract_gensim_word2vec_keywords(cleaned)

    else:
        raise ValueError(f"Unknown extraction method: {method!r}")

    return json.dumps({"keywords": keywords}, ensure_ascii=False)

