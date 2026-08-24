#!/usr/bin/env python3


# Libraries
##############################################################################
from dataclasses import dataclass
import os

from Shared.restrictions import LEN_ID,LEN_ID_POSTFIX
from Shared.models import Base,db
from .restrictions import (
    LEN_DNS,LEN_SOURCE,LEN_SOURCE_URL,SOURCE_TLS,PORT_DEFAULT
)
##############################################################################

# DnsRecord Class
##############################################################################
@dataclass
class DnsRecord(Base):
    __tablename__ = 'dns_record'

    id          : str
    dns         : str
    ssl_port    : int
    source      : str
    source_url  : str

    id = db.Column(
        db.String(LEN_ID), primary_key=True
    )
    dns = db.Column(
        db.String(LEN_DNS), unique=True, nullable=False
    )
    # Defaulted rather than required: only the tls source connects to
    # a port, so an uploaded certificate has none to give.
    ssl_port = db.Column(
        db.Integer, nullable=False, default=PORT_DEFAULT,
        server_default=str(PORT_DEFAULT)
    )
    # Defaults to tls so records created before this column existed, and
    # callers that do not mention a source, keep the original behaviour.
    source = db.Column(
        db.String(LEN_SOURCE), nullable=False, default=SOURCE_TLS,
        server_default=SOURCE_TLS
    )
    # Only used by the saml source: where to download the metadata from.
    source_url = db.Column(
        db.String(LEN_SOURCE_URL)
    )


    @classmethod
    def create_custom_id(self):
        return "dns-" + str(os.urandom(LEN_ID_POSTFIX).hex())
##############################################################################