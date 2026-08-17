#!/usr/bin/env python3


# Libraries
##############################################################################
from datetime import datetime

from DnsRecord.models import DnsRecord
from .models import Cert
from Shared.cert_checker import fetch_certificate
from Shared.exceptions import NotFoundError, ConflictError
from Shared.timezone import TZ
##############################################################################


# Cert Service
##############################################################################
# Business rules for SSL/TLS certificate records. Cert fetching now happens
# in-process via Shared.cert_checker; routes and the cron worker share the
# same code path.
##############################################################################
class CertService:

    @staticmethod
    def get(id):
        return Cert.get(id)

    @staticmethod
    def list():
        return Cert.get_all()

    @staticmethod
    def run_check(dns_record_id):
        dns_record = DnsRecord.query.filter_by(id=dns_record_id).first()
        if dns_record is None:
            raise NotFoundError(str(dns_record_id) + " not found")

        validity = fetch_certificate(
            dns=str(dns_record.dns),
            ssl_port=int(dns_record.ssl_port),
        )

        cert_data = {
            "dns_record_id": dns_record.id,
            "not_after": validity["not_after"],
            "not_before": validity["not_before"],
            "last_update": datetime.now(TZ),
        }

        try:
            return Cert.create(cert_data)
        except ConflictError:
            existing = Cert.query.filter_by(dns_record_id=dns_record.id).first()
            if existing is None:
                # Race: the conflicting row vanished between create attempt
                # and lookup. Re-raise as a generic 500-style error.
                raise
            return Cert.update(existing.id, cert_data)
