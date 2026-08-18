#!/usr/bin/env python3


# Libraries
##############################################################################
import socket
import ssl

from cryptography import x509
from cryptography.x509.oid import NameOID

from .exceptions import ExternalServiceError
from .restrictions import TLS_TIMEOUT
##############################################################################


# Helpers
##############################################################################
# Reads a single attribute out of an x509 name. Returns an empty string
# when the certificate does not carry it, which is common: plenty of
# certificates leave the subject common name out these days.
def _name_attribute(name, oid):
    attributes = name.get_attributes_for_oid(oid)
    if not attributes:
        return ""
    return str(attributes[0].value)


# Every hostname and ip address the certificate is valid for. Joined into
# a string because SQLite has no list column type.
def _subject_alt_names(cert):
    try:
        extension = cert.extensions.get_extension_for_class(
            x509.SubjectAlternativeName
        )
    except x509.ExtensionNotFound:
        return ""
    names = extension.value.get_values_for_type(x509.DNSName)
    addresses = extension.value.get_values_for_type(x509.IPAddress)
    return ", ".join(names + [str(address) for address in addresses])
##############################################################################


# Certificate Fetcher
##############################################################################
# In-process replacement for the previously standalone cert-checker service.
# Establishes a TLS connection to (dns, ssl_port), grabs the peer
# certificate, and returns the validity window as datetime objects.
#
# TLS verification is intentionally disabled so that expired or
# self-signed certificates can still be inspected: the whole point of
# this tool is to track such certificates.
##############################################################################
def fetch_certificate(dns, ssl_port):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with ctx.wrap_socket(socket.socket(), server_hostname=dns) as sock:
            # Set before connect() so the timeout covers both the TCP
            # connect and the TLS handshake.
            sock.settimeout(TLS_TIMEOUT)
            sock.connect((dns, ssl_port))
            der_data = sock.getpeercert(True)
    except Exception as e:
        raise ExternalServiceError(
            message="failed to fetch certificate from "
                    + str(dns) + ":" + str(ssl_port) + " - " + str(e),
        )

    pem_data = ssl.DER_cert_to_PEM_cert(der_data)
    cert = x509.load_pem_x509_certificate(pem_data.encode())

    # Fall back to the organization name: some CAs, and some certificates
    # issued to them, carry no common name at all.
    issuer = (
        _name_attribute(cert.issuer, NameOID.COMMON_NAME)
        or _name_attribute(cert.issuer, NameOID.ORGANIZATION_NAME)
    )
    subject = (
        _name_attribute(cert.subject, NameOID.COMMON_NAME)
        or _name_attribute(cert.subject, NameOID.ORGANIZATION_NAME)
    )

    # None for signature schemes that do not use a separate hash, such as
    # ed25519.
    hash_algorithm = cert.signature_hash_algorithm

    # The *_utc properties return timezone-aware UTC datetimes. The older
    # not_valid_before / not_valid_after pair returns naive ones and is
    # deprecated since cryptography 42.
    return {
        "not_before": cert.not_valid_before_utc,
        "not_after": cert.not_valid_after_utc,
        "issuer": issuer,
        "subject": subject,
        "sans": _subject_alt_names(cert),
        # Hex, the way browsers and openssl print serial numbers.
        "serial_number": format(cert.serial_number, 'x'),
        "signature_algorithm": hash_algorithm.name if hash_algorithm else "",
        # Issued to itself. Not a full chain validation, but enough to
        # tell the self-signed certificates apart in the list.
        "self_signed": cert.issuer == cert.subject,
    }
