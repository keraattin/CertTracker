#!/usr/bin/env python3


# Libraries
##############################################################################

##############################################################################


# DNS Record Routes
##############################################################################
def test_create_returns_the_record(client):
    response = client.post("/api/dns", json={"dns": "example.com", "ssl_port": 443})
    assert response.status_code == 201
    body = response.get_json()
    assert body["dns"] == "example.com"
    assert body["ssl_port"] == 443
    assert body["id"].startswith("dns-")


def test_create_rejects_a_port_out_of_range(client):
    response = client.post("/api/dns", json={"dns": "example.com", "ssl_port": 99999})
    assert response.status_code == 400


def test_create_rejects_a_malformed_dns(client):
    response = client.post("/api/dns", json={"dns": "not a host", "ssl_port": 443})
    assert response.status_code == 400


def test_create_rejects_a_duplicate(client):
    client.post("/api/dns", json={"dns": "example.com", "ssl_port": 443})
    response = client.post("/api/dns", json={"dns": "example.com", "ssl_port": 8443})
    assert response.status_code == 409


def test_get_missing_record_is_not_found(client):
    response = client.get("/api/dns/dns-doesnotexist")
    assert response.status_code == 404
    assert response.get_json()["status"] == "fail"


def test_update_changes_the_port(client):
    created = client.post(
        "/api/dns", json={"dns": "example.com", "ssl_port": 443}
    ).get_json()
    response = client.put("/api/dns/" + created["id"], json={"ssl_port": 8443})
    assert response.status_code == 200
    assert response.get_json()["ssl_port"] == 8443


def test_delete_removes_the_record(client):
    created = client.post(
        "/api/dns", json={"dns": "example.com", "ssl_port": 443}
    ).get_json()
    assert client.delete("/api/dns/" + created["id"]).status_code == 200
    assert client.get("/api/dns/" + created["id"]).status_code == 404


def test_list_is_empty_to_begin_with(client):
    assert client.get("/api/dns").get_json() == []
##############################################################################


# Validation Errors
##############################################################################
# Validation raises like every other application error, so the shape of a
# 400 matches the shape of a 404 or a 409 rather than being special.
##############################################################################
def test_a_validation_error_looks_like_every_other_error(client):
    body = client.post(
        "/api/dns", json={"dns": "example.com", "ssl_port": 99999}
    ).get_json()
    assert body["status"] == "fail"
    assert "ssl_port" in body["message"]
    # The field errors survive as structured data, not only as a string.
    assert "ssl_port" in body["details"]


def test_a_malformed_body_is_the_callers_fault(client):
    # Flask raises before the view runs. Reporting that as a 500 would
    # blame the server for a request it never accepted.
    response = client.post(
        "/api/dns", data="{not json", content_type="application/json"
    )
    assert response.status_code == 400
    assert response.get_json()["status"] == "fail"


def test_the_wrong_content_type_is_not_a_server_error(client):
    response = client.post("/api/dns", data="dns=example.com")
    assert response.status_code < 500
##############################################################################


# Cascade
##############################################################################
def test_deleting_a_record_takes_its_certificate_with_it(client, tls_server):
    record = client.post(
        "/api/dns", json={"dns": "127.0.0.1", "ssl_port": tls_server["port"]}
    ).get_json()
    cert = client.post("/api/cert/cert_check/" + record["id"]).get_json()
    assert client.get("/api/cert/" + cert["id"]).status_code == 200

    client.delete("/api/dns/" + record["id"])
    # The relationship cascades, so nothing is left pointing at a record
    # that no longer exists.
    assert client.get("/api/cert/" + cert["id"]).status_code == 404
    assert client.get("/api/cert").get_json() == []


def test_deleting_a_record_without_a_certificate_is_fine(client):
    record = client.post(
        "/api/dns", json={"dns": "example.com", "ssl_port": 443}
    ).get_json()
    assert client.delete("/api/dns/" + record["id"]).status_code == 200
##############################################################################


# Health
##############################################################################
def test_health_reports_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
##############################################################################
