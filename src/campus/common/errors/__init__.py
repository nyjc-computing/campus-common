"""campus.common.errors

API error handling for Campus.

`handlers` is the Flask integration surface; flask/werkzeug are
imported lazily inside it (#861).
"""

from . import api_errors, auth_errors, handlers, token_errors, validation
from .api_errors import (
    ConflictError,
    ForbiddenError,
    InternalError,
    InvalidRequestError,
    NotFoundError,
    UnauthorizedError,
)
from .base import JsonDict
from .validation import FieldError, ValidationError

__all__ = [
    "init_app",
    "JsonDict",
    "api_errors",
    "auth_errors",
    "base",
    "handlers",
    "token_errors",
    "validation",
    "ValidationError",
    "FieldError",
    "ConflictError",
    "ForbiddenError",
    "InternalError",
    "InvalidRequestError",
    "NotFoundError",
    "UnauthorizedError",
]

# Re-export init_app for backward compatibility
init_app = handlers.init_app
