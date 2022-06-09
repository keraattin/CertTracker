#!/usr/bin/env python3

# Libraries
##############################################################################
from flask import jsonify
from .status_codes import BAD_REQ
##############################################################################

# Validators
##############################################################################
def validate_request(data,schema):
    schema_obj = schema()
    # Validate the Request Data
    errors = schema_obj.validate(data)
    # If any Error Occurs
    if errors:
        return jsonify({
            "status":"fail",
            "message":str(errors)
        }),BAD_REQ
##############################################################################