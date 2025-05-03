# sitecustomize.py
import logging, types

logging.basicConfig(level=logging.DEBUG, format="%(message)s")
logger = logging.getLogger()

_orig_setattr = type.__setattr__

def tracing_setattr(cls, name, value):
    if cls is dict and name == 'update':
        logger.error("Monkey‐patch detected in %s: dict.%s = %r",
                     cls.__module__, name, value)
    return _orig_setattr(cls, name, value)

type.__setattr__ = tracing_setattr
