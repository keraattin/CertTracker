#!/usr/bin/env python3

# Application Exception Hierarchy
##############################################################################
# Service layer raises these; the HTTP layer (Shared/http.py) maps them to
# JSON responses with the appropriate status code. Routes / cron / CLI can
# all share the same business logic without depending on Flask Response.
##############################################################################


class AppError(Exception):
    """Base class for application errors."""

    status_code = 500
    default_message = "internal server error"

    def __init__(self, message=None, details=None):
        self.message = message if message is not None else self.default_message
        self.details = details
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = 404
    default_message = "resource not found"


class ConflictError(AppError):
    status_code = 409
    default_message = "resource conflict"


class ValidationError(AppError):
    status_code = 400
    default_message = "validation failed"


class ExternalServiceError(AppError):
    """Raised when an upstream service (e.g. cert-checker) misbehaves."""

    status_code = 502
    default_message = "external service error"

    def __init__(self, message=None, details=None, status_code=None):
        super().__init__(message, details)
        if status_code is not None:
            self.status_code = status_code
