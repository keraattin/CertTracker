#!/usr/bin/env python3


# Libraries
##############################################################################
import socket
import ssl

from cryptography import x509

from .exceptions import ExternalServiceError
##############################################################################


# Certificate Fetcher
##############################################################################
# In-process replacement for the previously standalone cert-checker service.
# Establishes a TLS connection to (dns, ssl_port), grabs the peer
# certificate, and returns the validity window as datetime objects.
#
# TLS verification is intentionally disabled so that expired or
# self-signed certificates can still be inspected — the whole point of
# this tool is to track such certificates.
##############################################################################
def fetch_certificate(dns, ssl_port):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with ctx.wrap_socket(socket.socket(), server_hostname=dns) as sock:
            sock.connect((dns, ssl_port))
            der_data = sock.getpeercert(True)
    except Exception as e:
        raise ExternalServiceError(
            message="failed to fetch certificate from "
                    + str(dns) + ":" + str(ssl_port) + " - " + str(e),
        )

    pem_data = ssl.DER_cert_to_PEM_cert(der_data)
    cert = x509.load_pem_x509_certificate(pem_data.encode())

    return {
        "not_before": cert.not_valid_before,
        "not_after": cert.not_valid_after,
    }
