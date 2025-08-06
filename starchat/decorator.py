import logging
from typing import Callable
from functools import wraps
from .exceptions import (
    ChatwootAPIError,
    ChatwootAuthenticationError,
    ChatwootAuthorizationError,
    ChatwootValidationError,
    ChatwootNotFoundError,
    ChatwootRateLimitError,
    ChatwootTimeoutError,
    ChatwootServerError,
    ChatwootNetworkError
)

logger = logging.getLogger(__name__)

def handle_chatwoot_exceptions(operation_name: str, allow_not_found: bool = False):
    """
    Decorator para tratar exceções do Chatwoot de forma centralizada.
    
    Args:
        operation_name: Nome da operação para logging
        allow_not_found: Se True, trata ChatwootNotFoundError como warning ao invés de error
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ChatwootAuthenticationError as e:
                logger.error(f"Authentication error in {operation_name}: {e}")
                raise
            except ChatwootAuthorizationError as e:
                logger.error(f"Authorization error in {operation_name}: {e}")
                raise
            except ChatwootValidationError as e:
                logger.error(f"Validation error in {operation_name}: {e}")
                raise
            except ChatwootNotFoundError as e:
                if allow_not_found:
                    logger.warning(f"Resource not found in {operation_name}: {e}")
                else:
                    logger.error(f"Resource not found in {operation_name}: {e}")
                raise
            except ChatwootRateLimitError as e:
                logger.warning(f"Rate limit exceeded in {operation_name}: {e}")
                raise
            except ChatwootTimeoutError as e:
                logger.error(f"Timeout error in {operation_name}: {e}")
                raise
            except ChatwootServerError as e:
                logger.error(f"Server error in {operation_name}: {e}")
                raise
            except ChatwootNetworkError as e:
                logger.error(f"Network error in {operation_name}: {e}")
                raise
            except ChatwootAPIError as e:
                logger.error(f"API error in {operation_name}: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error in {operation_name}: {e}")
                raise
        return wrapper
    return decorator