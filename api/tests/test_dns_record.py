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


# Health
##############################################################################
def test_health_reports_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
##############################################################################
