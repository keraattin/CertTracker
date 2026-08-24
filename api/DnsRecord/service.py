#!/usr/bin/env python3


# Libraries
##############################################################################
from .models import DnsRecord
##############################################################################


# DNS Record Service
##############################################################################
# Business rules for DNS records. A thin pass through to the repository
# helpers today: the cascade that used to live here now belongs to the
# relationship between a record and its certificate.
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
        # The certificate goes with the record: the relationship in
        # Cert.models cascades, so there is nothing to tidy up here.
        return DnsRecord.delete(id)
