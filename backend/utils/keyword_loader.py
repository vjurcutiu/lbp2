import logging
import re
import json
from typing import List, Dict, Any, Set
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
    Extracts top-level metadata fields (as lowercase strings)
    from every File.meta_data['keywords'] JSON blob,
    excluding 'cuvinte_cheie'.
    """
    topics: Set[str] = set()
    files = File.query.all()

    for f in files:
        kws_raw: Any = f.meta_data.get("keywords")
        logger.debug("build_keyword_topics: file_id=%s raw_kws=%r", f.id, kws_raw)
        if not kws_raw:
            continue

        # 1) If it's a string, try to pull out the JSON object
        if isinstance(kws_raw, str):
            match = re.search(r"(\{.*\})", kws_raw, re.DOTALL)
            if not match:
                continue
            try:
                kw_dict: Dict[str, Any] = json.loads(match.group(1))
            except json.JSONDecodeError as e:
                logger.warning("Invalid JSON in file %s: %s", f.id, e)
                continue

        # 2) If it's already a dict (rare), use it directly
        elif isinstance(kws_raw, dict):
            kw_dict = kws_raw

        # 3) Any other type (list, None, etc.) — skip
        else:
            continue

        # 4) Add each top-level key (except 'cuvinte_cheie')
        for key in kw_dict:
            if key != "cuvinte_cheie":
                topics.add(key.lower())

    logger.debug("build_keyword_topics: deduped topics=%s", topics)
    return list(topics)