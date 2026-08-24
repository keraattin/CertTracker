#!/usr/bin/env python3

# Libraries
##############################################################################

##############################################################################

# Values
##############################################################################
# 253 is the maximum length of a fully qualified domain name, and matches
# the upper bound of the dns regex in schema.py.
LEN_DNS = 253

LEN_SOURCE      = 16
LEN_SOURCE_URL  = 2048

# Used when no port is given. Only the tls source connects anywhere,
# so for the others the value is carried but never read.
PORT_DEFAULT    = 443
##############################################################################

# Enums
##############################################################################
# Where the certificate of a record comes from.
#
#   tls     open a connection to dns:ssl_port and read the peer
#           certificate. The original behaviour, and the default, so
#           records created before this existed keep working.
#   saml    download a SAML metadata document and read the certificate
#           embedded in it, for identity providers that publish one.
#   upload  the certificate was handed to us directly, for hosts this
#           installation cannot reach. Nothing to re-fetch, so the daily
#           job leaves these alone.
SOURCE_TLS      = "tls"
SOURCE_SAML     = "saml"
SOURCE_UPLOAD   = "upload"

SOURCES = [SOURCE_TLS, SOURCE_SAML, SOURCE_UPLOAD]

# Sources the scheduler can refresh on its own.
FETCHABLE_SOURCES = [SOURCE_TLS, SOURCE_SAML]

##############################################################################