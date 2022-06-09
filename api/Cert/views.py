#!/usr/bin/env python3


# Libraries
##############################################################################
from datetime import datetime
from flask import Blueprint, jsonify
import requests
import json

from DnsRecord.models import DnsRecord
from .models import Cert
from Shared.status_codes import CONFLICT,OK,NOT_FND
from Shared.timezone import TZ
##############################################################################

# Blueprint
##############################################################################
crt_bp = Blueprint('cert_check_blueprint', __name__)
##############################################################################

# Global Values
##############################################################################
url = "http://cert-checker:5001/api/cert_check"
headers = {
    'Content-Type': 'application/json'
}

TF = '%a, %d %b %Y %H:%M:%S %Z' # Time Format
##############################################################################

# Views
##############################################################################
@crt_bp.route('/<id>', methods=['GET'])
def get(id):
    return Cert.get(id)

@crt_bp.route('/', methods=['GET'])
def get_all():
    return Cert.get_all()

@crt_bp.route('/cert_check/<id>', methods=['POST'])
def cert_check(id):
    # Get DNS Record by ID
    dns_record = DnsRecord.query.filter_by(id=id).first()

    # If ID not Exist
    if not dns_record:
        return jsonify({"status":"fail","message":id+" not found"}),NOT_FND

    # Create Payload for SSL Cert Check
    payload = json.dumps({
        "dns"       :str(dns_record.dns),
        "ssl_port"  :int(dns_record.ssl_port)
    })

    # Get Cert Information
    cert = requests.request("POST", url, headers=headers, data=payload)

    # If the Certificate was Obtained Successfully
    if cert.status_code == OK:
        cert = cert.json()  # Convert Request Object to Json
        # Create Cert Data
        cert_data = {
            "dns_record_id" :dns_record.id,
            "not_after"     :datetime.strptime(str(cert["not_after"]),TF),
            "not_before"    :datetime.strptime(str(cert["not_before"]),TF),
            "last_update"   :datetime.now(TZ)
        }

        created = Cert.create(cert_data)    # Try Create New Record
        # If Already Exist -> Update
        if int(created[1]) == int(CONFLICT):
            # Get Existing Record
            exist_cert = Cert.get_by({"dns_record_id":dns_record.id})
            # Update Cert Record
            updated = Cert.update(exist_cert["id"],cert_data)
            return updated
        return created
    return jsonify(cert.json()),cert.status_code # Return Error
##############################################################################
    
    