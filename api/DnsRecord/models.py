#!/usr/bin/env python3


# Libraries
##############################################################################
from dataclasses import dataclass
import os

from Shared.restrictions import LEN_ID,LEN_ID_POSTFIX
from Shared.models import Base,db
from .restrictions import LEN_DNS
##############################################################################

# DnsRecord Class
##############################################################################
@dataclass
class DnsRecord(Base):
    __tablename__ = 'dns_record'

    id          : str
    dns         : str
    ssl_port    : int

    id = db.Column(
        db.String(LEN_ID), primary_key=True
    )
    dns = db.Column(
        db.String(LEN_DNS), unique=True, nullable=False
    )
    ssl_port = db.Column(
        db.Integer, nullable=False
    )


    @classmethod
    def create_custom_id(self):
        return "dns-" + str(os.urandom(LEN_ID_POSTFIX).hex())
##############################################################################