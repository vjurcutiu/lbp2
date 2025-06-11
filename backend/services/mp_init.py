import os
import sys
from multiprocessing import Pool, Manager, freeze_support, get_start_method
from utils.logging import logger, log_call

manager = None
pool = None

@log_call()
def init_multiprocessing():
    """
    Initialise the task-launcher Pool and Manager exactly once.
    """
    global manager, pool
    if manager is not None and pool is not None:
        logger.debug("Multiprocessing already initialised — skipping")
        return

    if sys.platform == "win32" and __name__ != "__main__":
        logger.error(
            "Multiprocessing primitives must be created in the main process on Windows. "
            "Current __name__ is '%s'. This can cause deadlocks/hangs.",
            __name__,
        )
        raise RuntimeError(
            "Multiprocessing primitives must be created in the main process on Windows."
        )

    if get_start_method(allow_none=True) != "fork":
        freeze_support()

    manager = Manager()
    pool = Pool(processes=os.cpu_count())
    logger.info("Initialised task-pool (size=%s) and Manager", os.cpu_count())

def get_pool():
    """
    Returns the global process pool.
    """
    return pool

def get_manager():
    """
    Returns the global manager.
    """
    return manager

def set_pool_and_manager(mgr, pl):
    global manager, pool
    manager = mgr
    pool = pl
