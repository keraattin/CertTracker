#!/usr/bin/env python3


# Libraries
##############################################################################
from flask import Blueprint, jsonify, request

from .service import CertService
from Shared.http import handle_errors
from Shared.status_codes import OK
##############################################################################


# Blueprint
##############################################################################
crt_bp = Blueprint('cert_check_blueprint', __name__)
##############################################################################


# Views
##############################################################################
@crt_bp.route('/<id>', methods=['GET'])
@handle_errors
def get(id):
    return jsonify(CertService.get(id)), OK


@crt_bp.route('/', methods=['GET'])
@handle_errors
def get_all():
    return jsonify(CertService.list()), OK


@crt_bp.route('/cert_check/<id>', methods=['POST'])
@handle_errors
def cert_check(id):
    return jsonify(CertService.run_check(id)), OK


# Takes the certificate itself, for a host this installation cannot
# reach. The body is the certificate in PEM or DER form, either as the
# raw request body or as a "certificate" field in json.
@crt_bp.route('/upload/<id>', methods=['POST'])
@handle_errors
def upload(id):
    data = None
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        data = payload.get("certificate")
    if not data:
        data = request.get_data()
    return jsonify(CertService.store_upload(id, data)), OK
##############################################################################
