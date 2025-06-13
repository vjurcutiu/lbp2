import os
import json
from flask import current_app
from utils.pinecone_client import PineconeClient
from text_extraction import extract_text_from_file
from chunking import chunk_text
from utils_flatten import flatten_values
from utils.services.ai_api_manager import OpenAIService

aii = OpenAIService()

def upsert_file_to_vector_db(f, chunk_size: int = 1500, overlap: int = 200):
    """
    Upserts embeddings for a single file with metadata to Pinecone in text chunks and marks it uploaded.
    """
    func = "upsert_file_to_vector_db"
    namespace = os.getenv('PINECONE_NAMESPACE')
    client = PineconeClient(
        environment=os.getenv("PINECONE_ENV")
    )

    if not os.path.exists(f.file_path):
        current_app.logger.warning(f"File not found: {f.file_path}")
        return None

    text = extract_text_from_file(f.file_path)
    if not text:
        current_app.logger.error(f"No text extracted from {f.file_path}")
        return None

    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    current_app.logger.info(f"Split {f.file_path} into {len(chunks)} chunks")

    file_metadata = f.meta_data if isinstance(f.meta_data, dict) else {}

    raw_keywords = []
    keys_to_extract = ['locatie', 'data', 'domeniu', 'hotarare', 'legislatie', 'keywords']

    for key in keys_to_extract:
        val = file_metadata.get(key)
        if val:
            if isinstance(val, str):
                try:
                    parsed_val = json.loads(val)
                    val = parsed_val
                except Exception:
                    pass
            flattened = flatten_values(val)
            raw_keywords.extend(flattened)

    unique_keywords = list({str(k).lower() for k in raw_keywords if k})

    results = []
    for idx, chunk in enumerate(chunks):
        prompt = f"Represent this document chunk for searching relevant passages: {chunk}"
        try:
            embeddings = aii.embeddings(prompt)
            record = {
                'id': f"{f.id}_chunk_{idx}",
                'values': embeddings,
                'metadata': {
                    'source_text': chunk,
                    'source_file': f.file_path,
                    'chunk_index': idx,
                    'text_snippet': chunk[:100],
                    'keywords': unique_keywords
                }
            }
            vc_resp = client.upsert([record], namespace)
            results.append({'file_path': f.file_path, 'chunk': idx, 'vector_response': vc_resp})
        except Exception as e:
            current_app.logger.error(f"Error upserting chunk {idx} of {f.file_path}: {e}", exc_info=True)

    f.is_uploaded = True
    return results
