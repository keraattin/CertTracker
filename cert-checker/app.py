#!/usr/bin/env python3

# Libraries
##############################################################################
import os
from flask import Flask
from flask_cors import CORS

from views import crt_chck_bp
##############################################################################

# Configs
##############################################################################
app     = Flask(__name__)
PORT    = os.environ.get('PORT')
DEBUG   = os.environ.get('DEBUG')
HOST    = "0.0.0.0"

# Secret Key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# CORS
CORS(app)
##############################################################################

# Blueprints
##############################################################################
app.register_blueprint(crt_chck_bp, url_prefix='/api/cert_check')
##############################################################################

# Main
##############################################################################
if __name__ == '__main__':
    app.run(debug=DEBUG,port=PORT,host=HOST)
##############################################################################

