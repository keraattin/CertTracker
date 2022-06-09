#!/usr/bin/env python3


# Libraries
##############################################################################
from flask import Blueprint, request

from .models import DnsRecord
from .schema import CreateSchema,UpdateSchema
from Shared.status_codes import OK
from Shared.validators import validate_request
from Cert.models import Cert
##############################################################################


# Blueprint
##############################################################################
dns_bp = Blueprint('dns_record_blueprint', __name__)
##############################################################################


# Views
##############################################################################
@dns_bp.route('/', methods=['POST'])
def create():
    data = request.get_json()   # Get Data
    # Validate Request
    errors = validate_request(data=data,schema=CreateSchema)
    # If any Error Occurs
    if errors:
        return errors
    return DnsRecord.create(data)

@dns_bp.route('/<id>', methods=['GET'])
def get(id):
    return DnsRecord.get(id)

@dns_bp.route('/', methods=['GET'])
def get_all():
    return DnsRecord.get_all()

@dns_bp.route('/<id>', methods=['PUT'])
def update(id):
    data = request.get_json()   # Get Data
    # Validate Request
    errors = validate_request(data=data,schema=UpdateSchema)
    if errors:
        return errors
    return DnsRecord.update(id,data)

@dns_bp.route('/<id>', methods=['DELETE'])
def delete(id):
    deleted = DnsRecord.delete(id) # Delete the Record
    # If Successfully Deleted
    if int(deleted[1]) == int(OK):
        cert = Cert.query.filter_by(dns_record_id=id).first()
        if cert:
            Cert.delete(cert.id)
    return deleted
##############################################################################