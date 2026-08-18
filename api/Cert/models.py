#!/usr/bin/env python3


# Libraries
##############################################################################
from dataclasses import dataclass
import os
from datetime import datetime

from Shared.restrictions import LEN_ID,LEN_ID_POSTFIX
from Shared.models import Base,db
from DnsRecord.models import DnsRecord
from .restrictions import (
    LEN_ISSUER,LEN_SUBJECT,LEN_SERIAL,LEN_SIG_ALG,LEN_STATUS,LEN_ERROR
)
##############################################################################

# Cert Class
##############################################################################
# Everything below not_after / not_before is nullable: rows written before
# these columns existed keep their certificate dates and simply have no
# details until the next check fills them in.
##############################################################################
@dataclass
class Cert(Base):
    __tablename__ = 'cert'

    id                  : str
    dns_record          : DnsRecord
    not_after           : datetime
    not_before          : datetime
    last_update         : datetime
    issuer              : str
    subject             : str
    sans                : str
    serial_number       : str
    signature_algorithm : str
    self_signed         : bool
    last_check          : datetime
    last_check_status   : str
    last_error          : str
    notified_days       : int

    id = db.Column(
        db.String(LEN_ID), primary_key=True
    )
    dns_record_id = db.Column(
        db.String(LEN_ID), db.ForeignKey('dns_record.id'), unique=True
    )
    dns_record = db.relationship(
        "DnsRecord", foreign_keys=[dns_record_id]
    )
    not_after = db.Column(
        db.DateTime, nullable=False
    )
    not_before = db.Column(
        db.DateTime, nullable=False
    )
    # Last time the certificate itself was fetched successfully.
    last_update = db.Column(
	    db.DateTime, nullable=False,
    )
    issuer = db.Column(
        db.String(LEN_ISSUER)
    )
    subject = db.Column(
        db.String(LEN_SUBJECT)
    )
    sans = db.Column(
        db.Text
    )
    serial_number = db.Column(
        db.String(LEN_SERIAL)
    )
    signature_algorithm = db.Column(
        db.String(LEN_SIG_ALG)
    )
    self_signed = db.Column(
        db.Boolean
    )
    # Last time a check was attempted, successful or not. Kept apart from
    # last_update so a host that stopped answering is visible instead of
    # silently showing its last known certificate as if nothing changed.
    last_check = db.Column(
        db.DateTime
    )
    last_check_status = db.Column(
        db.String(LEN_STATUS)
    )
    last_error = db.Column(
        db.String(LEN_ERROR)
    )
    # Expiry threshold this certificate was last mailed about, so the
    # daily job does not report the same one again every morning. Reset
    # when the certificate is renewed.
    notified_days = db.Column(
        db.Integer
    )

    @classmethod
    def create_custom_id(self):
        return "crt-" + str(os.urandom(LEN_ID_POSTFIX).hex())
##############################################################################