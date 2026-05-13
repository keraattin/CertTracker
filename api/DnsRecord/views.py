#!/usr/bin/env python3


# Libraries
##############################################################################
from flask import Blueprint, jsonify, request

from .schema import CreateSchema, UpdateSchema
from .service import DnsRecordService
from Shared.http import handle_errors
from Shared.status_codes import OK, CREATED
from Shared.validators import validate_request
##############################################################################


# Blueprint
##############################################################################
dns_bp = Blueprint('dns_record_blueprint', __name__)
##############################################################################


# Views
##############################################################################
@dns_bp.route('/', methods=['POST'])
@handle_errors
def create():
    data = request.get_json()
    errors = validate_request(data=data, schema=CreateSchema)
    if errors:
        return errors
    return jsonify(DnsRecordService.create(data)), CREATED


@dns_bp.route('/<id>', methods=['GET'])
@handle_errors
def get(id):
    return jsonify(DnsRecordService.get(id)), OK


@dns_bp.route('/', methods=['GET'])
@handle_errors
def get_all():
    return jsonify(DnsRecordService.list()), OK


@dns_bp.route('/<id>', methods=['PUT'])
@handle_errors
def update(id):
    data = request.get_json()
    errors = validate_request(data=data, schema=UpdateSchema)
    if errors:
        return errors
    return jsonify(DnsRecordService.update(id, data)), OK


@dns_bp.route('/<id>', methods=['DELETE'])
@handle_errors
def delete(id):
    DnsRecordService.delete(id)
    return jsonify({
        "status": "ok",
        "message": str(id) + " deleted successfully",
    }), OK
##############################################################################
