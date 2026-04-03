"""Retry logic with exponential backoff."""

import time
import logging
from functools import wraps
from typing import Callable, Optional, Type, Tuple

logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_failure: Optional[Callable] = None
):
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        backoff: Backoff multiplier (2.0 = double wait time each retry)
        exceptions: Tuple of exceptions to catch and retry
        on_failure: Optional callback function called on final failure
        
    Example:
        @retry(max_attempts=3, backoff=2.0)
        def call_api():
            response = external_api.call()
            return response
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        if on_failure:
                            on_failure(e)
                        raise
                    
                    wait_time = backoff ** (attempt - 1)
                    logger.warning(
                        f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    time.sleep(wait_time)
            
            raise last_exception
        
        return wrapper
    return decorator
