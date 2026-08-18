#!/usr/bin/env python3


# Libraries
##############################################################################
from datetime import datetime, timedelta, timezone
import os
import socket
import ssl
import sys
import tempfile
import threading

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
import pytest
##############################################################################


# Import Path
##############################################################################
# The api modules import each other as top level packages (Shared, Cert,
# DnsRecord), so the api directory itself has to be importable.
API_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, API_DIR)
##############################################################################


# Environment
##############################################################################
# Set before app is imported: app.py reads the database uri, and mailer.py
# reads the smtp settings, at import time.
TEST_DB = os.path.join(tempfile.gettempdir(), "certtracker_test.db")
os.environ["DATABASE_URI"] = "sqlite:///" + TEST_DB.replace("\\", "/")
os.environ.setdefault("TIMEZONE", "Etc/UTC")
##############################################################################


# Helpers
##############################################################################
# Picks a port the operating system says is free. Racy in theory, fine for
# a test that binds it immediately afterwards.
def free_port():
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    return port
##############################################################################


# Fixtures
##############################################################################
@pytest.fixture(scope="session")
def app():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    from app import app as flask_app
    return flask_app


@pytest.fixture
def client(app):
    # Every test starts from an empty database rather than depending on
    # what the previous one left behind.
    from Cert.models import Cert
    from DnsRecord.models import DnsRecord
    from Shared.models import db

    with app.app_context():
        db.session.query(Cert).delete()
        db.session.query(DnsRecord).delete()
        db.session.commit()
    return app.test_client()


@pytest.fixture
def ctx(app):
    with app.app_context():
        yield
##############################################################################


# TLS Server
##############################################################################
# Generates a self-signed certificate and serves it on localhost, so the
# certificate fetcher can be tested for real without reaching out to the
# internet and without depending on what some public host happens to
# serve today.
##############################################################################
def build_certificate(common_name, days_valid):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "CertTracker Tests"),
    ])
    now = datetime.now(timezone.utc)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(1234567890)
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=days_valid))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(common_name),
                x509.DNSName("alt." + common_name),
            ]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    return certificate, key


def write_pem(directory, certificate, key):
    cert_path = os.path.join(directory, "cert.pem")
    key_path = os.path.join(directory, "key.pem")
    with open(cert_path, "wb") as handle:
        handle.write(certificate.public_bytes(serialization.Encoding.PEM))
    with open(key_path, "wb") as handle:
        handle.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    return cert_path, key_path


@pytest.fixture(scope="session")
def tls_server(tmp_path_factory):
    certificate, key = build_certificate("certtracker.test", days_valid=45)
    directory = str(tmp_path_factory.mktemp("tls"))
    cert_path, key_path = write_pem(directory, certificate, key)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert_path, key_path)

    port = free_port()
    listener = socket.socket()
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", port))
    listener.listen(5)

    def serve():
        while True:
            try:
                connection, _ = listener.accept()
            except OSError:
                return
            try:
                with context.wrap_socket(connection, server_side=True) as tls:
                    tls.recv(1024)
            except Exception:
                # The client only wants the certificate and hangs up; a
                # broken handshake is not the server's problem here.
                pass

    threading.Thread(target=serve, daemon=True).start()
    yield {"port": port, "certificate": certificate}
    listener.close()


@pytest.fixture(scope="session")
def black_hole():
    # Accepts the connection and then says nothing at all, which is what
    # the TLS timeout exists for.
    port = free_port()
    listener = socket.socket()
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", port))
    listener.listen(5)

    held = []

    def serve():
        while True:
            try:
                connection, _ = listener.accept()
            except OSError:
                return
            # Kept referenced so the socket is not closed and the client
            # keeps waiting for a handshake that never comes.
            held.append(connection)

    threading.Thread(target=serve, daemon=True).start()
    yield port
    listener.close()
##############################################################################


# SMTP Server
##############################################################################
# Speaks just enough of the protocol for smtplib to deliver a message,
# and records what arrived.
##############################################################################
@pytest.fixture
def smtp_server(monkeypatch):
    import Shared.mailer as mailer

    port = free_port()
    listener = socket.socket()
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", port))
    listener.listen(5)
    inbox = []

    def serve():
        while True:
            try:
                connection, _ = listener.accept()
            except OSError:
                return
            connection.sendall(b"220 localhost test\r\n")
            body = []
            in_data = False
            buffer = ""
            while True:
                try:
                    chunk = connection.recv(4096).decode("utf-8", "replace")
                except OSError:
                    break
                if not chunk:
                    break
                buffer += chunk
                done = False
                while "\r\n" in buffer:
                    line, buffer = buffer.split("\r\n", 1)
                    if in_data:
                        if line == ".":
                            in_data = False
                            inbox.append("\n".join(body))
                            body = []
                            connection.sendall(b"250 Ok\r\n")
                        else:
                            body.append(line)
                        continue
                    command = line.upper()
                    if command.startswith(("EHLO", "HELO")):
                        connection.sendall(b"250-localhost\r\n250 HELP\r\n")
                    elif command.startswith("DATA"):
                        in_data = True
                        connection.sendall(b"354 End with .\r\n")
                    elif command.startswith("QUIT"):
                        connection.sendall(b"221 Bye\r\n")
                        done = True
                        break
                    else:
                        connection.sendall(b"250 Ok\r\n")
                if done:
                    break
            connection.close()

    threading.Thread(target=serve, daemon=True).start()

    monkeypatch.setattr(mailer, "SMTP_HOST", "127.0.0.1")
    monkeypatch.setattr(mailer, "SMTP_PORT", port)
    monkeypatch.setattr(mailer, "SMTP_TLS", False)
    monkeypatch.setattr(mailer, "SMTP_USER", "")
    monkeypatch.setattr(mailer, "MAIL_FROM", "certtracker@example.com")
    monkeypatch.setattr(mailer, "MAIL_TO", "ops@example.com")

    yield inbox
    listener.close()
##############################################################################
