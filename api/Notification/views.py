#!/usr/bin/env python3


# Libraries
##############################################################################
from flask import Blueprint, jsonify

from .service import NotificationService
from Shared.http import handle_errors
from Shared.status_codes import OK
##############################################################################


# Blueprint
##############################################################################
notification_bp = Blueprint('notification_blueprint', __name__)
##############################################################################


# Views
##############################################################################
# Runs the same pass the daily job runs. Useful to verify the smtp
# settings without waiting for the scheduled run.
@notification_bp.route('/run', methods=['POST'])
@handle_errors
def run():
    return jsonify(NotificationService.run()), OK
##############################################################################
