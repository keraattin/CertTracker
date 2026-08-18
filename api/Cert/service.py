#!/usr/bin/env python3


# Libraries
##############################################################################
from DnsRecord.models import DnsRecord
from .models import Cert
from .restrictions import (
    DAYS_EXPIRING,CHECK_OK,CHECK_FAILED,
    STATUS_VALID,STATUS_EXPIRING,STATUS_EXPIRED
)
from Shared.cert_checker import fetch_certificate
from Shared.exceptions import NotFoundError, ConflictError, ExternalServiceError
from Shared.timezone import as_utc, utc_now
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
        return CertService._with_status(Cert.get(id))

    @staticmethod
    def list():
        return [CertService._with_status(cert) for cert in Cert.get_all()]

    @staticmethod
    def run_check(dns_record_id):
        dns_record = DnsRecord.query.filter_by(id=dns_record_id).first()
        if dns_record is None:
            raise NotFoundError(str(dns_record_id) + " not found")

        try:
            validity = fetch_certificate(
                dns=str(dns_record.dns),
                ssl_port=int(dns_record.ssl_port),
            )
        except ExternalServiceError as e:
            # Remember the failure before letting the route turn it into
            # a 502, so the list stops presenting a stale certificate as
            # if the host were still answering.
            CertService._record_failure(dns_record.id, e.message)
            raise

        now = utc_now()
        cert_data = {
            "dns_record_id": dns_record.id,
            "not_after": validity["not_after"],
            "not_before": validity["not_before"],
            "issuer": validity["issuer"],
            "subject": validity["subject"],
            "sans": validity["sans"],
            "serial_number": validity["serial_number"],
            "signature_algorithm": validity["signature_algorithm"],
            "self_signed": validity["self_signed"],
            "last_update": now,
            "last_check": now,
            "last_check_status": CHECK_OK,
            "last_error": None,
        }

        try:
            return CertService._with_status(Cert.create(cert_data))
        except ConflictError:
            existing = Cert.query.filter_by(dns_record_id=dns_record.id).first()
            if existing is None:
                # Race: the conflicting row vanished between create attempt
                # and lookup. Re-raise as a generic 500-style error.
                raise
            # A renewed certificate starts over: the threshold it was
            # already mailed about says nothing about the new expiry date.
            if as_utc(existing.not_after) != validity["not_after"]:
                cert_data["notified_days"] = None
            return CertService._with_status(Cert.update(existing.id, cert_data))

    # Only a record that was fetched successfully at least once has a row
    # to write the failure to. A host that never answered has nothing to
    # show in the certificate list yet.
    @staticmethod
    def _record_failure(dns_record_id, message):
        existing = Cert.query.filter_by(dns_record_id=dns_record_id).first()
        if existing is None:
            return
        Cert.update(existing.id, {
            "last_check": utc_now(),
            "last_check_status": CHECK_FAILED,
            "last_error": message,
        })

    # Derives the two values every consumer would otherwise compute on its
    # own: how many whole days are left, and what that means. Keeping it
    # here means the frontend, the cron log and any future notifier all
    # agree on where the thresholds are.
    @staticmethod
    def _with_status(cert):
        not_after = cert.get("not_after")
        if not_after is None:
            return cert

        days_remaining = (as_utc(not_after) - utc_now()).days
        if days_remaining < 0:
            status = STATUS_EXPIRED
        elif days_remaining <= DAYS_EXPIRING:
            status = STATUS_EXPIRING
        else:
            status = STATUS_VALID

        cert["days_remaining"] = days_remaining
        cert["status"] = status
        return cert
