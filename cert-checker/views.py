#!/usr/bin/env python3


# Libraries
##############################################################################
from flask import Blueprint, request, jsonify
import ssl, socket
import logging
from dataclasses import dataclass,asdict
from datetime import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
##############################################################################

# Global Values
##############################################################################
SRV_ERR = 500

log = logging.getLogger(__name__)
logging.basicConfig(filename = './logs/app.log',
                    level = logging.DEBUG,
                    format = '%(asctime)s:%(levelname)s:%(name)s:%(message)s')
##############################################################################

# Class
##############################################################################
@dataclass
class Cert:
    not_before : datetime
    not_after  : datetime

    def __init__(self):
        pass
##############################################################################


# Blueprint
##############################################################################
crt_chck_bp = Blueprint('cert_check_blueprint', __name__)
##############################################################################


# Views
##############################################################################
@crt_chck_bp.route('/', methods=['POST'])
def post():
    data = request.get_json()   # Get Data

    dns         = data["dns"]
    ssl_port    = data["ssl_port"]
    return get_cert(dns=dns,ssl_port=ssl_port)
##############################################################################


# Get Certificate of Host
##############################################################################
def get_cert(dns,ssl_port):
    ctx = ssl.create_default_context()
    ctx.check_hostname  = False
    ctx.verify_mode     = ssl.CERT_NONE
    try:
        with ctx.wrap_socket(socket.socket(), server_hostname=dns) as s:
            s.connect((dns, ssl_port))
            data = s.getpeercert(True)
            pem_data = ssl.DER_cert_to_PEM_cert(data)
            cert_data = x509.load_pem_x509_certificate(str.encode(pem_data))
            cert = Cert()
            cert.not_before = cert_data.not_valid_before
            cert.not_after = cert_data.not_valid_after
            log.info("Connected to {}:{}".format(dns,ssl_port))
            return asdict(cert)
    except Exception as e:
        log.error(
            "Failed to Connect to {}:{} \n Error: {}".format(
                dns,ssl_port,str(e)
            )
        )
        return jsonify(
            {
                "status":"error",
                "message":str(e)
            }
        ),SRV_ERR
##############################################################################