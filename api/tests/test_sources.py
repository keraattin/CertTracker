#!/usr/bin/env python3


# Libraries
##############################################################################
import base64
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from cryptography.hazmat.primitives import serialization
import pytest

from Cert.restrictions import STATUS_VALID
from DnsRecord.restrictions import SOURCE_TLS, SOURCE_UPLOAD
from Shared.cert_checker import load_certificate
from Shared.exceptions import ValidationError
from conftest import build_certificate, free_port
##############################################################################


# Helpers
##############################################################################
SAML_TEMPLATE = """<?xml version="1.0"?>
<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata"
                  entityID="https://idp.example.com/">
  <IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
%s
  </IDPSSODescriptor>
</EntityDescriptor>
"""

KEY_DESCRIPTOR = """    <KeyDescriptor use="%s">
      <KeyInfo xmlns="http://www.w3.org/2000/09/xmldsig#">
        <X509Data>
          <X509Certificate>%s</X509Certificate>
        </X509Data>
      </KeyInfo>
    </KeyDescriptor>"""


def metadata_for(certificates):
    blocks = []
    for use, certificate in certificates:
        der = certificate.public_bytes(serialization.Encoding.DER)
        blocks.append(KEY_DESCRIPTOR % (use, base64.b64encode(der).decode()))
    return SAML_TEMPLATE % "\n".join(blocks)


@pytest.fixture
def metadata_server():
    # Serves whatever document the test puts in it, so the fetcher is
    # exercised over real HTTP rather than through a stubbed reader.
    state = {"body": "", "status": 200}
    port = free_port()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = state["body"].encode()
            self.send_response(state["status"])
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    state["url"] = "http://127.0.0.1:" + str(port) + "/metadata.xml"
    yield state
    server.shutdown()


def saml_record(client, url):
    return client.post("/api/dns", json={
        "dns": "idp.example.com",
        "source": "saml",
        "source_url": url,
    }).get_json()
##############################################################################


# Defaults
##############################################################################
def test_a_record_without_a_source_is_tls(client):
    body = client.post(
        "/api/dns", json={"dns": "example.com", "ssl_port": 443}
    ).get_json()
    assert body["source"] == SOURCE_TLS


def test_the_port_may_be_left_out(client):
    # Nothing connects anywhere for an uploaded certificate.
    assert client.post("/api/dns", json={"dns": "example.com"}).status_code == 201


def test_saml_without_a_url_is_rejected(client):
    response = client.post(
        "/api/dns", json={"dns": "idp.example.com", "source": "saml"}
    )
    assert response.status_code == 400


def test_an_unknown_source_is_rejected(client):
    response = client.post(
        "/api/dns", json={"dns": "example.com", "source": "carrier-pigeon"}
    )
    assert response.status_code == 400
##############################################################################


# SAML
##############################################################################
def test_reads_the_certificate_out_of_saml_metadata(client, metadata_server):
    certificate, _ = build_certificate("idp.example.com", days_valid=200)
    metadata_server["body"] = metadata_for([("signing", certificate)])

    record = saml_record(client, metadata_server["url"])
    body = client.post("/api/cert/cert_check/" + record["id"]).get_json()

    assert body["subject"] == "idp.example.com"
    assert body["issuer"] == "idp.example.com"
    assert body["serial_number"] == format(1234567890, "x")
    assert body["status"] == STATUS_VALID


def test_the_soonest_to_expire_certificate_wins(client, metadata_server):
    # Documents commonly list a signing and an encryption certificate,
    # and during a rollover the next one as well. The one about to expire
    # is the one worth warning about.
    near, _ = build_certificate("idp.example.com", days_valid=10)
    far, _ = build_certificate("idp.example.com", days_valid=300)
    metadata_server["body"] = metadata_for(
        [("encryption", far), ("signing", near)]
    )

    record = saml_record(client, metadata_server["url"])
    body = client.post("/api/cert/cert_check/" + record["id"]).get_json()

    assert body["days_remaining"] == 10


def test_metadata_without_a_certificate_is_an_error(client, metadata_server):
    metadata_server["body"] = SAML_TEMPLATE % ""
    record = saml_record(client, metadata_server["url"])

    response = client.post("/api/cert/cert_check/" + record["id"])
    assert response.status_code == 502
    assert "no usable certificate" in response.get_json()["message"]


def test_metadata_that_is_not_xml_is_an_error(client, metadata_server):
    metadata_server["body"] = "<html>not metadata"
    record = saml_record(client, metadata_server["url"])

    response = client.post("/api/cert/cert_check/" + record["id"])
    assert response.status_code == 502
    assert "not valid xml" in response.get_json()["message"]


def test_an_unreachable_metadata_url_is_recorded_as_a_failure(client):
    record = client.post("/api/dns", json={
        "dns": "idp.example.com",
        "source": "saml",
        "source_url": "http://127.0.0.1:9/metadata.xml",
    }).get_json()

    response = client.post("/api/cert/cert_check/" + record["id"])
    assert response.status_code == 502
    assert "failed to fetch saml metadata" in response.get_json()["message"]
##############################################################################


# Upload
##############################################################################
def test_uploading_a_pem_certificate(client):
    certificate, _ = build_certificate("offline.example", days_valid=120)
    pem = certificate.public_bytes(serialization.Encoding.PEM).decode()

    record = client.post("/api/dns", json={"dns": "offline.example"}).get_json()
    body = client.post(
        "/api/cert/upload/" + record["id"], json={"certificate": pem}
    ).get_json()

    assert body["subject"] == "offline.example"
    assert body["days_remaining"] == 120
    assert body["self_signed"] is True


def test_uploading_der_works_too(client):
    certificate, _ = build_certificate("offline.example", days_valid=60)
    der = certificate.public_bytes(serialization.Encoding.DER)

    record = client.post("/api/dns", json={"dns": "offline.example"}).get_json()
    response = client.post(
        "/api/cert/upload/" + record["id"],
        data=der, content_type="application/octet-stream"
    )
    assert response.status_code == 200
    assert response.get_json()["days_remaining"] == 60


def test_uploading_switches_the_record_to_the_upload_source(client):
    certificate, _ = build_certificate("offline.example", days_valid=90)
    pem = certificate.public_bytes(serialization.Encoding.PEM).decode()

    record = client.post("/api/dns", json={"dns": "offline.example"}).get_json()
    assert record["source"] == SOURCE_TLS

    client.post("/api/cert/upload/" + record["id"], json={"certificate": pem})
    stored = client.get("/api/dns/" + record["id"]).get_json()
    assert stored["source"] == SOURCE_UPLOAD


def test_an_uploaded_record_cannot_be_re_fetched(client):
    certificate, _ = build_certificate("offline.example", days_valid=90)
    pem = certificate.public_bytes(serialization.Encoding.PEM).decode()

    record = client.post("/api/dns", json={"dns": "offline.example"}).get_json()
    client.post("/api/cert/upload/" + record["id"], json={"certificate": pem})

    response = client.post("/api/cert/cert_check/" + record["id"])
    assert response.status_code == 400
    assert "cannot be re-fetched" in response.get_json()["message"]


def test_uploading_again_replaces_the_certificate(client):
    first, _ = build_certificate("offline.example", days_valid=30)
    second, _ = build_certificate("offline.example", days_valid=300)
    record = client.post("/api/dns", json={"dns": "offline.example"}).get_json()

    for certificate in (first, second):
        pem = certificate.public_bytes(serialization.Encoding.PEM).decode()
        body = client.post(
            "/api/cert/upload/" + record["id"], json={"certificate": pem}
        ).get_json()

    assert body["days_remaining"] == 300
    assert len(client.get("/api/cert").get_json()) == 1


def test_rubbish_is_not_accepted_as_a_certificate(client):
    record = client.post("/api/dns", json={"dns": "offline.example"}).get_json()
    response = client.post(
        "/api/cert/upload/" + record["id"], json={"certificate": "hello"}
    )
    assert response.status_code == 400


def test_upload_to_a_missing_record_is_not_found(client):
    certificate, _ = build_certificate("offline.example", days_valid=90)
    pem = certificate.public_bytes(serialization.Encoding.PEM).decode()
    response = client.post(
        "/api/cert/upload/dns-nope", json={"certificate": pem}
    )
    assert response.status_code == 404


def test_load_certificate_rejects_empty_input():
    with pytest.raises(ValidationError):
        load_certificate(b"")
##############################################################################
