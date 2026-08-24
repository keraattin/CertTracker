#!/usr/bin/env python3


# Libraries
##############################################################################
from datetime import timedelta
import sqlite3

import pytest

from Cert.models import Cert
from Cert.restrictions import STATUS_VALID, STATUS_EXPIRING, STATUS_EXPIRED
from Cert.service import CertService
from Shared.timezone import utc_now
##############################################################################


# Status And Remaining Days
##############################################################################
# The thresholds used to live in the frontend, where a certificate with
# exactly thirty days left matched no branch at all.
##############################################################################
@pytest.mark.parametrize("days,expected", [
    (-1, STATUS_EXPIRED),
    (0, STATUS_EXPIRING),
    (7, STATUS_EXPIRING),
    (30, STATUS_EXPIRING),
    (31, STATUS_VALID),
    (365, STATUS_VALID),
])
def test_status_follows_the_thresholds(ctx, days, expected):
    cert = CertService._with_status(
        {"not_after": utc_now() + timedelta(days=days, hours=1)}
    )
    assert cert["status"] == expected
    assert cert["days_remaining"] == days


def test_status_is_skipped_when_there_is_no_expiry(ctx):
    cert = CertService._with_status({"not_after": None})
    assert "status" not in cert
##############################################################################


# Checking
##############################################################################
def test_check_stores_the_certificate(client, tls_server):
    record = client.post(
        "/api/dns", json={"dns": "127.0.0.1", "ssl_port": tls_server["port"]}
    ).get_json()

    response = client.post("/api/cert/cert_check/" + record["id"])
    assert response.status_code == 200

    body = response.get_json()
    assert body["issuer"] == "certtracker.test"
    assert body["last_check_status"] == "ok"
    assert body["last_error"] is None
    assert body["status"] == STATUS_VALID


def test_checking_twice_updates_the_same_row(client, tls_server):
    record = client.post(
        "/api/dns", json={"dns": "127.0.0.1", "ssl_port": tls_server["port"]}
    ).get_json()

    first = client.post("/api/cert/cert_check/" + record["id"]).get_json()
    second = client.post("/api/cert/cert_check/" + record["id"]).get_json()

    assert first["id"] == second["id"]
    assert len(client.get("/api/cert").get_json()) == 1


def test_check_of_a_missing_record_is_not_found(client):
    assert client.post("/api/cert/cert_check/dns-nope").status_code == 404
##############################################################################


# Failed Checks
##############################################################################
# A failed check used to leave the previous certificate on screen looking
# perfectly healthy, with the error only reaching the cron log.
##############################################################################
def test_failed_check_keeps_the_certificate_and_records_the_error(
    client, tls_server
):
    record = client.post(
        "/api/dns", json={"dns": "127.0.0.1", "ssl_port": tls_server["port"]}
    ).get_json()
    fetched = client.post("/api/cert/cert_check/" + record["id"]).get_json()

    # Point the record at a port nothing answers on.
    client.put("/api/dns/" + record["id"], json={"ssl_port": 9})
    assert client.post("/api/cert/cert_check/" + record["id"]).status_code == 502

    stored = client.get("/api/cert/" + fetched["id"]).get_json()
    assert stored["not_after"] == fetched["not_after"]
    assert stored["last_update"] == fetched["last_update"]
    assert stored["last_check_status"] == "failed"
    assert stored["last_error"] is not None

    # Compared on the model rather than on the json, which serializes
    # datetimes to whole seconds: both checks can land inside the same
    # second, and do on a machine fast enough.
    with client.application.app_context():
        row = Cert.query.filter_by(id=fetched["id"]).first()
        assert row.last_check > row.last_update


def test_failure_without_a_previous_certificate_stores_nothing(client):
    record = client.post(
        "/api/dns", json={"dns": "127.0.0.1", "ssl_port": 9}
    ).get_json()
    assert client.post("/api/cert/cert_check/" + record["id"]).status_code == 502
    assert client.get("/api/cert").get_json() == []
##############################################################################


# Cascade
##############################################################################
def test_deleting_the_dns_record_removes_its_certificate(client, tls_server):
    record = client.post(
        "/api/dns", json={"dns": "127.0.0.1", "ssl_port": tls_server["port"]}
    ).get_json()
    client.post("/api/cert/cert_check/" + record["id"])

    client.delete("/api/dns/" + record["id"])
    assert client.get("/api/cert").get_json() == []
##############################################################################


# Schema Sync
##############################################################################
# Columns are added to models as the project grows, and db.create_all()
# never alters a table that already exists.
##############################################################################
def test_missing_columns_are_added_to_an_existing_database(tmp_path):
    from Shared.models import ensure_columns, db
    from flask import Flask

    path = tmp_path / "legacy.db"
    connection = sqlite3.connect(str(path))
    connection.executescript("""
        CREATE TABLE dns_record (
            id VARCHAR(15) NOT NULL PRIMARY KEY,
            dns VARCHAR(64) NOT NULL UNIQUE,
            ssl_port INTEGER NOT NULL
        );
        CREATE TABLE cert (
            id VARCHAR(15) NOT NULL PRIMARY KEY,
            dns_record_id VARCHAR(15) UNIQUE REFERENCES dns_record(id),
            not_after DATETIME NOT NULL,
            not_before DATETIME NOT NULL,
            last_update DATETIME NOT NULL
        );
        INSERT INTO dns_record VALUES ('dns-legacy01', 'legacy.example', 443);
        INSERT INTO cert VALUES (
            'crt-legacy01', 'dns-legacy01',
            '2020-01-01 00:00:00.000000', '2019-01-01 00:00:00.000000',
            '2019-01-01 00:00:00.000000'
        );
    """)
    connection.commit()
    connection.close()

    # A second app pointed at the legacy file. The same db object serves
    # both, which is what init_app is for.
    legacy = Flask(__name__)
    legacy.config['SQLALCHEMY_DATABASE_URI'] = (
        'sqlite:///' + str(path).replace("\\", "/")
    )
    legacy.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(legacy)

    with legacy.app_context():
        db.create_all()
        ensure_columns()

        # The row survived, and the columns it never had are simply empty.
        stored = Cert.get('crt-legacy01')
        assert stored["issuer"] is None
        assert stored["notified_days"] is None
        assert CertService._with_status(stored)["status"] == STATUS_EXPIRED

        # A column that is NOT NULL needs its default carried across as
        # well, or the existing rows could not satisfy it.
        from DnsRecord.models import DnsRecord
        from DnsRecord.restrictions import SOURCE_TLS, PORT_DEFAULT
        record = DnsRecord.get('dns-legacy01')
        assert record["source"] == SOURCE_TLS
        assert record["source_url"] is None
        assert record["ssl_port"] == 443
        assert PORT_DEFAULT == 443
##############################################################################
