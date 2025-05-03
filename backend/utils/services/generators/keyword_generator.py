import os
import logging
import re
import json
from openai import OpenAI
try:
    from openai.error import OpenAIError
except ImportError:
    class OpenAIError(Exception):
        pass
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

#Lazy-loaded NLP model 
placeholder_nlp = None

DEFAULT_KEYWORD_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")

# -----------------------------------------------------------------------------
#                    Ontology & Taxonomy Integration
# -----------------------------------------------------------------------------

def load_rdf_ontology(path: str, format: str = "xml") -> 'rdflib.Graph':
    import rdflib
    g = rdflib.Graph()
    g.parse(path, format=format)
    logging.getLogger("KeywordGenerator").info(f"Loaded RDF ontology from {path}")
    return g


def load_owl_ontology(path: str):
    from owlready2 import get_ontology
    onto = get_ontology(path).load()
    logging.getLogger("KeywordGenerator").info(f"Loaded OWL ontology from {path}")
    return onto


def index_labels_from_rdf(graph: 'rdflib.Graph', lang: str = "ro") -> dict[str, str]:
    from rdflib.namespace import RDFS
    import rdflib
    SKOS = rdflib.Namespace("http://www.w3.org/2004/02/skos/core#")
    label_predicates = [RDFS.label, SKOS.prefLabel, SKOS.altLabel]
    label_map: dict[str, rdflib.URIRef] = {}
    for subj, pred, obj in graph:
        if pred in label_predicates and isinstance(obj, rdflib.Literal):
            if obj.language and obj.language != lang:
                continue
            label_map[str(obj).lower()] = subj
    logging.getLogger("KeywordGenerator").debug(f"Indexed {len(label_map)} labels from RDF graph")
    return label_map


def map_terms_to_ontology(terms: list[str], label_map: dict[str, str], matcher: str = "exact", fuzzy_threshold: int = 85) -> dict[str, str]:
    from thefuzz import fuzz
    mapped: dict[str, str] = {}
    for term in terms:
        key = term.lower()
        if matcher == "exact" and key in label_map:
            mapped[term] = str(label_map[key])
        elif matcher == "fuzzy":
            best, score = None, 0
            for label, uri in label_map.items():
                s = fuzz.token_set_ratio(key, label)
                if s > score:
                    best, score = label, s
            mapped[term] = str(label_map[best]) if score >= fuzzy_threshold else None
        else:
            mapped[term] = None
    return mapped


@retry(
    retry=retry_if_exception_type(OpenAIError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def _generic_completion(prompt: str, system_instruction: str, model: str) -> str:
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


def _get_nlp():
    global placeholder_nlp
    if placeholder_nlp is None:
        import spacy
        placeholder_nlp = spacy.load("ro_core_news_sm")
    return placeholder_nlp


def preprocess_text(text: str) -> str:
    logger = logging.getLogger("KeywordGenerator")
    text = re.sub(r"^\s*\[?\d+\]?\s.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"Pagina\s+\d+\s+din\s+\d+", "", text)
    text = re.sub(r"[\r\n]+", " ", text)
    text = re.sub(r"[\s\f\t\v]+", " ", text).strip()
    for wrong, right in {'0': 'O', '1': 'I'}.items():
        text = text.replace(wrong, right)
    nlp = _get_nlp()
    doc = nlp(text)
    with doc.retokenize() as retokenizer:
        for ent in doc.ents:
            retokenizer.merge(ent)
    tokens = [token.lemma_ for token in doc if not token.is_space]
    return " ".join(tokens)


def extract_tfidf_keywords(text: str, top_k: int = 8, ngram_range=(1,3)) -> list[str]:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.feature_selection import SelectKBest, chi2
    vect = TfidfVectorizer(
        ngram_range=ngram_range,
        stop_words="romanian",
        max_df=0.85,
        min_df=2,
    )
    X = vect.fit_transform([text])
    X_dup = X.vstack([X])
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
    from rake_nltk import Rake
    rake = Rake(language="romanian")
    rake.extract_keywords_from_text(text)
    return rake.get_ranked_phrases()[:top_k]


def extract_yake_keywords(text: str, top_k: int = 8, ngram_max=3) -> list[str]:
    import yake
    kw_extractor = yake.KeywordExtractor(lan="ro", n=ngram_max, top=top_k)
    keywords = kw_extractor.extract_keywords(text)
    return [phrase for phrase, score in sorted(keywords, key=lambda x: x[1])]


def extract_pke_keywords(text: str, top_k: int = 8, method: str = "TextRank") -> list[str]:
    import pke
    extractor_cls = getattr(pke.unsupervised, method)
    extractor = extractor_cls()
    extractor.load_document(input=text, language='ro')
    extractor.candidate_selection()
    extractor.candidate_weighting()
    return [kp for kp, _ in extractor.get_n_best(n=top_k)]


def extract_keybert_keywords(text: str, top_k: int = 8, model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2') -> list[str]:
    from sentence_transformers import SentenceTransformer
    from keybert import KeyBERT
    bert_model = SentenceTransformer(model_name)
    kw_model = KeyBERT(model=bert_model)
    return [kw for kw, _ in kw_model.extract_keywords(text, keyphrase_ngram_range=(1,3), stop_words='romanian', top_n=top_k)]


def extract_gensim_lda_keywords(text: str, top_k: int = 8, num_topics: int = 1, passes: int = 10) -> list[str]:
    nlp = _get_nlp()
    tokens = [t.lemma_ for t in nlp(text) if t.is_alpha and not t.is_stop]
    from gensim import corpora, models
    dictionary = corpora.Dictionary([tokens])
    corpus = [dictionary.doc2bow(tokens)]
    lda = models.LdaModel(corpus=corpus, id2word=dictionary, num_topics=num_topics, passes=passes)
    return [word for word, _ in lda.show_topic(0, topn=top_k)]


def extract_gensim_word2vec_keywords(text: str, top_k: int = 8, vector_size: int = 100, window: int = 5, min_count: int = 2) -> list[str]:
    nlp = _get_nlp()
    sentences = [[t.lemma_ for t in sent if t.is_alpha and not t.is_stop] for sent in nlp(text).sents]
    from gensim import models
    model = models.word2vec.Word2Vec(sentences, vector_size=vector_size, window=window, min_count=min_count)
    centroid = sum(model.wv[w] for sent in sentences for w in sent) / sum(len(sent) for sent in sentences)
    return [word for word, _ in model.wv.similar_by_vector(centroid, topn=top_k)]


def extract_flashtext_keywords(text: str, vocabulary: list[str], case_sensitive: bool = False) -> list[str]:
    from flashtext import KeywordProcessor
    kp = KeywordProcessor(case_sensitive=case_sensitive)
    for term in vocabulary:
        kp.add_keyword(term)
    found = kp.extract_keywords(text)
    seen, uniq = set(), []
    for kw in found:
        if kw not in seen:
            seen.add(kw); uniq.append(kw)
    return uniq


def dedupe_keywords_fuzzy(keywords: list[str], threshold: int = 85) -> list[str]:
    from thefuzz import fuzz
    deduped = []
    for kw in keywords:
        if not any(fuzz.token_set_ratio(kw, existing) >= threshold for existing in deduped):
            deduped.append(kw)
    return deduped


def generate_keywords(text: str, method: str = "openai", flash_vocab: list[str] | None = None, fuzzy_threshold: int = 85) -> str:
    cleaned = preprocess_text(text)
    if len(cleaned.split()) < 30:
        return json.dumps({"locatie": "", "data": "", "domeniu": "", "hotarare": "", "cuvinte_cheie": []}, ensure_ascii=False)

    if method == "flashtext":
        if not flash_vocab: raise ValueError("flash_vocab must be provided for flashtext method")
        keywords = extract_flashtext_keywords(cleaned, flash_vocab)
    elif method == "flash_fuzzy":
        if not flash_vocab: raise ValueError("flash_vocab must be provided for flash_fuzzy method")
        keywords = dedupe_keywords_fuzzy(extract_flashtext_keywords(cleaned, flash_vocab), threshold=fuzzy_threshold)
    elif method == "openai":
        instruction = ("""SYSTEM:\nYou are a highly accurate AI assistant specialized in extracting information from Romanian legal documents.\n\nUSER:\nFrom the following decision text in Romanian..."""
        )
        raw = _generic_completion(cleaned, instruction, DEFAULT_KEYWORD_MODEL).strip()
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw)
            result = json.loads(match.group(0)) if match else {}
        kws = result.get("cuvinte_cheie", [])[:8]
        return json.dumps({"locatie": result.get("locatie",""), "data": result.get("data",""), "domeniu": result.get("domeniu",""), "hotarare": result.get("hotarare",""), "cuvinte_cheie": kws}, ensure_ascii=False)
    else:
        extractor_map = {
            "tfidf": extract_tfidf_keywords,
            "rake": extract_rake_keywords,
            "yake": extract_yake_keywords,
            "pke": extract_pke_keywords,
            "keybert": extract_keybert_keywords,
            "lda": extract_gensim_lda_keywords,
            "word2vec": extract_gensim_word2vec_keywords
        }
        if method not in extractor_map:
            raise ValueError(f"Unknown extraction method: {method!r}")
        keywords = extractor_map[method](cleaned)

    return json.dumps({"locatie": "", "data": "", "domeniu": "", "hotarare": "", "cuvinte_cheie": keywords[:8]}, ensure_ascii=False)
