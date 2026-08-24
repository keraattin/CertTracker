#!/usr/bin/env python3

# Libraries
##############################################################################
from .exceptions import ValidationError
##############################################################################

# Validators
##############################################################################
# Raises rather than returning a response: the route layer turns
# application errors into JSON through @handle_errors, the same way the
# service layer does. This was the last place that reached for Flask
# from outside a view.
##############################################################################
def validate_request(data,schema):
    schema_obj = schema()
    # Validate the Request Data
    errors = schema_obj.validate(data)
    # If any Error Occurs
    if errors:
        raise ValidationError(message=str(errors), details=errors)
##############################################################################
