#!/usr/bin/env python3

# HTTP Helpers
##############################################################################
# Map service-layer exceptions to JSON responses. Routes wrap their handler
# with @handle_errors and call services; raised AppError subclasses are
# converted into HTTP responses with the correct status code.
##############################################################################
from functools import wraps
from flask import jsonify
from werkzeug.exceptions import HTTPException

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
        except HTTPException as e:
            # Flask raises these before the view gets a say: a malformed
            # body or the wrong content type is the caller's mistake, and
            # answering 500 would blame the wrong side.
            return error_response(e.description, e.code)
        except Exception as e:
            return error_response(str(e), SRV_ERR)
    return wrapper
