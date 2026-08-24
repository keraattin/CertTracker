#!/usr/bin/env python3


# Libraries
##############################################################################
from marshmallow import Schema, fields, validate, validates_schema
from marshmallow import ValidationError
from  marshmallow.validate import OneOf, Range

from .restrictions import LEN_SOURCE_URL, SOURCES, SOURCE_SAML, PORT_DEFAULT
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
# Shared by both schemas: a record only connects somewhere when its
# source is tls, so the fields describing where to look are optional.
class SourceMixin:
    source = fields.Str(
        required = False,
        validate = OneOf(SOURCES)
    )
    source_url = fields.Url(
        required = False,
        schemes = {"http", "https"},
        validate = validate.Length(max=LEN_SOURCE_URL)
    )

    @validates_schema
    def check_source_url(self, data, **kwargs):
        # A saml record is nothing without the document to read it from.
        if data.get("source") == SOURCE_SAML and not data.get("source_url"):
            raise ValidationError(
                "source_url is required when source is saml", "source_url"
            )


class CreateSchema(Schema, SourceMixin):
    dns = fields.Str(
        required = True,
        validate = validate.Regexp(dns_regex)
    )
    # Optional: only the tls source connects to a port.
    ssl_port = fields.Int(
        required = False,
        validate = [Range(
            min = PORT_MIN, 
            max = PORT_MAX,
            error = "Value must be between 1-65535"
        )]
    )

class UpdateSchema(Schema, SourceMixin):
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