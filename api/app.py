#!/usr/bin/env python3

# Libraries
##############################################################################
from flask import Flask, jsonify
import os
from flask_cors import CORS

from Shared.models import db
from Shared.status_codes import OK
from DnsRecord.views import dns_bp
from Cert.views import crt_bp
##############################################################################


# Configs
##############################################################################
app     = Flask(__name__)
PORT    = int(os.environ.get('PORT') or 5000)
# Read as a string from the environment, so "False" has to be compared
# rather than used as a boolean: any non-empty string is truthy.
DEBUG   = os.environ.get('DEBUG', 'False') == 'True'
HOST    = "0.0.0.0"

# Secret Key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# Database URI
# Absolute path by default so it works regardless of Flask-SQLAlchemy
# version: 3.x resolves relative SQLite URIs against app.instance_path,
# not the CWD. Overridable so the app can also run outside the container.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URI') or 'sqlite:////api/Database/database.db'
)

# SQLAlchemy Configs
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inıt Database
db.init_app(app)

# Create Database
with app.app_context():
    db.create_all()

# CORS
CORS(app)

# If the flask returned a 308 redirect response,
# It is not allowed by Cors preflight request
# This is why setting url_map.strict_slashes to False
# https://github.com/keraattin/CertTracker/issues/4
app.url_map.strict_slashes = False
##############################################################################

# Blueprints
##############################################################################
app.register_blueprint(dns_bp, url_prefix='/api/dns')
app.register_blueprint(crt_bp, url_prefix='/api/cert')
##############################################################################

# Health Check
##############################################################################
# Liveness probe for container orchestrators and uptime monitors. Kept out
# of the blueprints on purpose: it answers for the app as a whole.
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), OK
##############################################################################

# Main
##############################################################################
if __name__ == '__main__':
    app.run(debug=DEBUG,port=PORT,host=HOST)
##############################################################################