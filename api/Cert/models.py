#!/usr/bin/env python3


# Libraries
##############################################################################
from dataclasses import dataclass
import os
from datetime import datetime

from Shared.restrictions import LEN_ID,LEN_ID_POSTFIX
from Shared.models import Base,db
from DnsRecord.models import DnsRecord
##############################################################################

# Cert Class
##############################################################################
@dataclass
class Cert(Base):
    __tablename__ = 'cert'

    id          : str
    dns_record  : DnsRecord
    not_after   : datetime
    not_before  : datetime
    last_update : datetime

    id = db.Column(
        db.String(LEN_ID), primary_key=True
    )
    dns_record_id = db.Column(
        db.String(LEN_ID), db.ForeignKey('dns_record.id'), unique=True
    )
    dns_record = db.relation(
        "DnsRecord", foreign_keys=[dns_record_id]
    )
    not_after = db.Column(
        db.DateTime, nullable=False
    )
    not_before = db.Column(
        db.DateTime, nullable=False
    )
    last_update = db.Column(
	    db.DateTime, nullable=False,
    )

    @classmethod
    def create_custom_id(self):
        return "crt-" + str(os.urandom(LEN_ID_POSTFIX).hex())
##############################################################################