#!/usr/bin/env python3


# Libraries
##############################################################################
from marshmallow import Schema, fields, validate
from  marshmallow.validate import Range
##############################################################################

# Global Values
##############################################################################
# Raw strings: "\." is not a valid escape sequence in a normal string and
# raises a SyntaxWarning on Python 3.12+, a SyntaxError on later versions.
dns_regex = (
    r"(?=^.{4,253}$)(^((?!-)[a-zA-Z0-9-]{1,63}(?<!-)\.)+[a-zA-Z]{2,63}$)|"
    r"((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.|$)){4}$"
)
port_regex = (
    r"^()([1-9]|[1-5]?[0-9]{2,4}|6[1-4][0-9]{3}|65[1-4][0-9]{2}|"
    r"655[1-2][0-9]|6553[1-5])$"
)
PORT_MIN = 1
PORT_MAX = 65535
##############################################################################

# Schemas
##############################################################################
class CreateSchema(Schema):
    dns = fields.Str(
        required = True,
        validate = validate.Regexp(dns_regex)
    )
    ssl_port = fields.Int(
        required = True,
        validate = [Range(
            min = PORT_MIN, 
            max = PORT_MAX,
            error = "Value must be between 1-65535"
        )]
    )

class UpdateSchema(Schema):
    dns = fields.Str(
        required = False,
        validate = validate.Regexp(dns_regex)
    )
    ssl_port = fields.Int(
        required = False,
        validate = [Range(
            min = PORT_MIN, 
            max = PORT_MAX,
            error = "Value must be between 1-65535"
        )]
    )
##############################################################################