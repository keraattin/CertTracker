#!/usr/bin/env python3


# Libraries
##############################################################################
from datetime import timedelta

import pytest

from Cert.models import Cert
from DnsRecord.models import DnsRecord
from Notification.service import NotificationService
from Shared.timezone import utc_now
##############################################################################


# Helpers
##############################################################################
def make_cert(dns="notify.example", days_remaining=90):
    record = DnsRecord.create({"dns": dns, "ssl_port": 443})
    now = utc_now()
    return Cert.create({
        "dns_record_id": record["id"],
        "not_before": now - timedelta(days=90),
        "not_after": now + timedelta(days=days_remaining, hours=1),
        "issuer": "Test CA",
        "subject": dns,
        "last_update": now,
        "last_check": now,
        "last_check_status": "ok",
    })


def set_days(cert_id, days):
    Cert.update(cert_id, {"not_after": utc_now() + timedelta(days=days, hours=1)})
##############################################################################


# Thresholds
##############################################################################
@pytest.mark.parametrize("days,expected", [
    (90, None),
    (31, None),
    (30, 30),
    (15, 30),
    (14, 14),
    (8, 14),
    (7, 7),
    (2, 7),
    (1, 1),
    (0, 1),
    (-1, -1),
    (-30, -1),
])
def test_threshold_for_days(ctx, days, expected):
    assert NotificationService._threshold_for({"days_remaining": days}) == expected
##############################################################################


# Sending
##############################################################################
# The point of remembering a threshold is that a certificate about to
# expire produces a handful of mails over its lifetime, not one every
# morning the job runs.
##############################################################################
def test_nothing_is_sent_while_the_certificate_has_time(client, smtp_server):
    with client.application.app_context():
        make_cert(days_remaining=90)
    assert client.post("/api/notification/run").get_json()["sent"] == 0
    assert smtp_server == []


def test_crossing_a_threshold_sends_one_mail(client, smtp_server):
    with client.application.app_context():
        cert = make_cert()
        set_days(cert["id"], 25)

    assert client.post("/api/notification/run").get_json()["sent"] == 1
    assert len(smtp_server) == 1
    assert "notify.example:443" in smtp_server[0]
    assert "expires in 25 day/s" in smtp_server[0]


def test_staying_inside_a_threshold_sends_nothing_more(client, smtp_server):
    with client.application.app_context():
        cert = make_cert()
        set_days(cert["id"], 25)
    client.post("/api/notification/run")

    with client.application.app_context():
        set_days(cert["id"], 24)
    assert client.post("/api/notification/run").get_json()["sent"] == 0
    assert len(smtp_server) == 1


def test_each_tighter_threshold_sends_again(client, smtp_server):
    with client.application.app_context():
        cert = make_cert()

    for days in (25, 12, 5, 0):
        with client.application.app_context():
            set_days(cert["id"], days)
        assert client.post("/api/notification/run").get_json()["sent"] == 1

    assert len(smtp_server) == 4


def test_expiry_itself_sends_one_last_mail(client, smtp_server):
    with client.application.app_context():
        cert = make_cert()
        set_days(cert["id"], 1)
    client.post("/api/notification/run")

    with client.application.app_context():
        set_days(cert["id"], -3)
    assert client.post("/api/notification/run").get_json()["sent"] == 1
    assert "expired 3 day/s ago" in smtp_server[-1]

    # And then stays quiet.
    with client.application.app_context():
        set_days(cert["id"], -4)
    assert client.post("/api/notification/run").get_json()["sent"] == 0


def test_renewal_starts_the_thresholds_over(client, smtp_server, tls_server):
    # A real check against the local TLS server, so the renewal path is
    # the one run_check actually takes rather than a hand written update.
    record = client.post(
        "/api/dns", json={"dns": "127.0.0.1", "ssl_port": tls_server["port"]}
    ).get_json()
    cert = client.post("/api/cert/cert_check/" + record["id"]).get_json()

    with client.application.app_context():
        set_days(cert["id"], 25)
    assert client.post("/api/notification/run").get_json()["sent"] == 1

    # Checking again restores the real expiry date, which differs from the
    # one just written, so the remembered threshold no longer applies.
    client.post("/api/cert/cert_check/" + record["id"])
    with client.application.app_context():
        stored = Cert.get(cert["id"])
        assert stored["notified_days"] is None

        set_days(cert["id"], 25)
    assert client.post("/api/notification/run").get_json()["sent"] == 1


def test_the_mail_names_a_failed_check(client, smtp_server):
    with client.application.app_context():
        cert = make_cert()
        set_days(cert["id"], 5)
        Cert.update(cert["id"], {
            "last_check_status": "failed",
            "last_error": "connection refused",
        })

    client.post("/api/notification/run")
    assert "last check failed: connection refused" in smtp_server[-1]
##############################################################################


# Configuration
##############################################################################
def test_without_smtp_settings_nothing_happens(client, monkeypatch):
    import Shared.mailer as mailer
    monkeypatch.setattr(mailer, "SMTP_HOST", "")

    with client.application.app_context():
        cert = make_cert()
        set_days(cert["id"], 1)

    body = client.post("/api/notification/run").get_json()
    assert body["sent"] == 0
    assert "not configured" in body["reason"]


def test_a_failing_server_leaves_the_certificate_due(client, monkeypatch):
    import Shared.mailer as mailer
    # Configured, but pointing at a port nothing listens on.
    monkeypatch.setattr(mailer, "SMTP_HOST", "127.0.0.1")
    monkeypatch.setattr(mailer, "SMTP_PORT", 9)
    monkeypatch.setattr(mailer, "SMTP_TLS", False)
    monkeypatch.setattr(mailer, "MAIL_FROM", "certtracker@example.com")
    monkeypatch.setattr(mailer, "MAIL_TO", "ops@example.com")

    with client.application.app_context():
        cert = make_cert()
        set_days(cert["id"], 1)

    assert client.post("/api/notification/run").status_code == 502
    with client.application.app_context():
        # Not marked as notified, so the next run tries again.
        assert Cert.get(cert["id"])["notified_days"] is None
##############################################################################
