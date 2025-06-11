import logging
from functools import wraps

logger = logging.getLogger("lbp2")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "{"  # opening brace for JSON object
        "\"timestamp\": \"%(asctime)s\", "
        "\"level\": \"%(levelname)s\", "
        "\"module\": \"%(module)s\", "
        "\"funcName\": \"%(funcName)s\", "
        "\"lineno\": %(lineno)d, "
        "\"message\": \"%(message)s\""
        "}"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel("INFO")

def log_call(level: int = logging.DEBUG):
    """
    Decorator that logs the entry and exit of the wrapped function.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.log(level, f"ENTER {func.__name__}")
            try:
                result = func(*args, **kwargs)
                logger.log(level, f"EXIT  {func.__name__}")
                return result
            except Exception as exc:
                logger.exception(f"{func.__name__} raised {exc}")
                raise
        return wrapper
    return decorator
