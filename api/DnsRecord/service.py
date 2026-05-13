#!/usr/bin/env python3


# Libraries
##############################################################################
from .models import DnsRecord
from Cert.models import Cert
from Shared.exceptions import NotFoundError
##############################################################################


# DNS Record Service
##############################################################################
# Business rules for DNS records. Wraps the underlying repository helpers
# and adds cross-aggregate concerns (e.g. cleaning up the cert that
# references a deleted DNS record).
##############################################################################
class DnsRecordService:

    @staticmethod
    def create(data):
        return DnsRecord.create(data)

    @staticmethod
    def get(id):
        return DnsRecord.get(id)

    @staticmethod
    def list():
        return DnsRecord.get_all()

    @staticmethod
    def update(id, data):
        return DnsRecord.update(id, data)

    @staticmethod
    def delete(id):
        # Behavior preserved from previous implementation: delete the DNS
        # record first, then remove the associated cert if any. The
        # ordering / cascade question is tracked separately as a follow-up.
        result = DnsRecord.delete(id)
        cert = Cert.query.filter_by(dns_record_id=id).first()
        if cert is not None:
            try:
                Cert.delete(cert.id)
            except NotFoundError:
                pass
        return result
