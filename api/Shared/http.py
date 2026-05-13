#!/usr/bin/env python3

# HTTP Helpers
##############################################################################
# Map service-layer exceptions to JSON responses. Routes wrap their handler
# with @handle_errors and call services; raised AppError subclasses are
# converted into HTTP responses with the correct status code.
##############################################################################
from functools import wraps
from flask import jsonify

from .exceptions import AppError
from .status_codes import SRV_ERR
##############################################################################


def error_response(message, status_code, details=None):
    payload = {"status": "fail", "message": message}
    if details is not None:
        payload["details"] = details
    return jsonify(payload), status_code


def handle_errors(view_fn):
    @wraps(view_fn)
    def wrapper(*args, **kwargs):
        try:
            return view_fn(*args, **kwargs)
        except AppError as e:
            return error_response(e.message, e.status_code, e.details)
        except Exception as e:
            return error_response(str(e), SRV_ERR)
    return wrapper
