#!/usr/bin/env python3


# Libraries
##############################################################################
import time

import pytest

from Shared import cert_checker
from Shared.cert_checker import fetch_certificate
from Shared.exceptions import ExternalServiceError
##############################################################################


# Fetching
##############################################################################
# Checked against a certificate this test suite generated itself, so the
# expected issuer, dates and alternative names are known rather than
# whatever a public host happens to serve today.
##############################################################################
def test_reads_the_validity_window(tls_server):
    result = fetch_certificate("127.0.0.1", tls_server["port"])
    certificate = tls_server["certificate"]

    assert result["not_before"] == certificate.not_valid_before_utc
    assert result["not_after"] == certificate.not_valid_after_utc


def test_reads_the_certificate_details(tls_server):
    result = fetch_certificate("127.0.0.1", tls_server["port"])

    assert result["issuer"] == "certtracker.test"
    assert result["subject"] == "certtracker.test"
    assert result["sans"] == "certtracker.test, alt.certtracker.test"
    assert result["serial_number"] == format(1234567890, 'x')
    assert result["signature_algorithm"] == "sha256"
    # The certificate names itself as its own issuer.
    assert result["self_signed"] is True


def test_expired_certificates_are_still_readable(tls_server):
    # Verification stays off on purpose: a tracker has to be able to
    # inspect exactly the certificates that would fail validation.
    result = fetch_certificate("127.0.0.1", tls_server["port"])
    assert result["not_after"] is not None
##############################################################################


# Failure Handling
##############################################################################
def test_refused_connection_raises_external_service_error():
    # Port 9 is the discard service and is not listening here.
    with pytest.raises(ExternalServiceError) as error:
        fetch_certificate("127.0.0.1", 9)
    assert error.value.status_code == 502


def test_a_silent_host_times_out_instead_of_hanging(black_hole, monkeypatch):
    # The real timeout is ten seconds; shorten it so the suite stays fast.
    monkeypatch.setattr(cert_checker, "TLS_TIMEOUT", 1)

    started = time.time()
    with pytest.raises(ExternalServiceError):
        fetch_certificate("127.0.0.1", black_hole)
    elapsed = time.time() - started

    # Without the timeout this call never returns at all.
    assert elapsed < 5
##############################################################################
