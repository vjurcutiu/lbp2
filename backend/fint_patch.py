import builtins
import logging
import pkgutil
import importlib

logging.basicConfig(level=logging.DEBUG, format="%(message)s")
logger = logging.getLogger(__name__)

logger.debug("Before any imports: dict.update = %r", builtins.dict.update)

# List all top‑level packages in your environment
for finder, name, ispkg in pkgutil.iter_modules():
    try:
        importlib.import_module(name)
    except Exception:
        # Some packages may error on import; skip them
        continue

    # After each import, check dict.update
    current = builtins.dict.update
    if current is None:
        logger.debug("After importing %s: dict.update = %r  <-- patch here!", name, current)
        break
    else:
        logger.debug("After importing %s: still OK", name)
