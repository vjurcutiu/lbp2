import logging
import re
import json
from typing import List, Dict, Any
from db.models import File

logger = logging.getLogger(__name__)

def load_keyword_items() -> List[Dict[str, Any]]:
    """
    Build a simple keyword-only index from uploaded File records.
    Each item has:
      - id: File.id (as string)
      - metadata: {'keywords': JSON-string '{"keywords":[...]}' }
    """
    items: List[Dict[str, Any]] = []
    files = File.query.filter_by(is_uploaded=True).all()
    for f in files:
        kws_raw = f.meta_data.get("keywords", [])
        logger.debug("load_keyword_items: file_id=%s raw_kws=%r", f.id, kws_raw)

        # Parse JSON blob if stored as a string
        if isinstance(kws_raw, str):
            match = re.search(r"(\{.*\})", kws_raw, re.DOTALL)
            if match:
                try:
                    kw_dict = json.loads(match.group(1))
                    kws = kw_dict.get("keywords", [])
                except Exception as e:
                    logger.warning("Failed to parse keywords for file %s: %s", f.id, e)
                    kws = []
            else:
                kws = []
        elif isinstance(kws_raw, (list, tuple)):
            kws = kws_raw
        else:
            kws = []

        items.append({
            "id": str(f.id),
            "metadata": {"keywords": json.dumps({"keywords": kws})},
        })
    return items


def build_keyword_topics() -> List[str]:
    """
    Extract and clean keyword topics from uploaded files' metadata.
    Returns a deduped, lowercase list of keyword strings.
    """
    topics: List[str] = []
    files = File.query.all()
    for f in files:
        kws_raw = f.meta_data.get("keywords", None)
        logger.debug("build_keyword_topics: file_id=%s raw_kws=%r", f.id, kws_raw)
        if not kws_raw:
            continue

        # Parse JSON blob if stored as a string
        if isinstance(kws_raw, str):
            match = re.search(r"(\{.*\})", kws_raw, re.DOTALL)
            if match:
                try:
                    kw_dict = json.loads(match.group(1))
                    kws = kw_dict.get("keywords", [])
                except Exception as e:
                    logger.warning("Failed to parse keywords for file %s: %s", f.id, e)
                    continue
            else:
                continue
        elif isinstance(kws_raw, (list, tuple)):
            kws = kws_raw
        else:
            continue

        for value in kws:
            if isinstance(value, str):
                topics.append(value)

    # Deduplicate and normalize
    clean = {t.strip().lower() for t in topics if isinstance(t, str) and t.strip()}
    logger.debug("build_keyword_topics: deduped topics=%s", clean)
    return list(clean)
