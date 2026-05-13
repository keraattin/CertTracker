#!/usr/bin/env python3


# Libraries
##############################################################################
from flask import Blueprint, jsonify

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
##############################################################################
