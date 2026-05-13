#!/usr/bin/env python3


# Libraries
##############################################################################
from datetime import datetime
import json

import requests

from DnsRecord.models import DnsRecord
from .models import Cert
from Shared.exceptions import (
    NotFoundError, ConflictError, ExternalServiceError
)
from Shared.timezone import TZ
##############################################################################


# Module Configuration
##############################################################################
CERT_CHECKER_URL = "http://cert-checker:5001/api/cert_check"
CERT_CHECKER_HEADERS = {"Content-Type": "application/json"}
TIME_FORMAT = '%a, %d %b %Y %H:%M:%S %Z'  # Flask jsonify default for datetime
##############################################################################


# Cert Service
##############################################################################
# Business rules for SSL/TLS certificate records, including the orchestration
# that calls the external cert-checker service. Routes and the cron worker
# both go through this class so the same logic runs in both contexts.
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

        payload = json.dumps({
            "dns": str(dns_record.dns),
            "ssl_port": int(dns_record.ssl_port),
        })

        response = requests.request(
            "POST", CERT_CHECKER_URL,
            headers=CERT_CHECKER_HEADERS, data=payload,
        )

        if response.status_code != 200:
            body = response.json() if response.content else {}
            raise ExternalServiceError(
                message=body.get("message", "cert-checker error"),
                details=body or None,
                status_code=response.status_code,
            )

        cert_payload = response.json()
        cert_data = {
            "dns_record_id": dns_record.id,
            "not_after": datetime.strptime(
                str(cert_payload["not_after"]), TIME_FORMAT
            ),
            "not_before": datetime.strptime(
                str(cert_payload["not_before"]), TIME_FORMAT
            ),
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
