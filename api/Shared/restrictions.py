#!/usr/bin/env python3

# Libraries
##############################################################################

##############################################################################

# Values
##############################################################################
LEN_ID          = 15
LEN_ID_POSTFIX  = 5

# Seconds to wait for the TLS connect + handshake before giving up. A host
# that silently drops packets would otherwise block the request, and the
# whole cron run, forever.
TLS_TIMEOUT     = 10

# The element a SAML metadata document carries its certificate in, with
# the xmldsig namespace ElementTree reports it under.
SAML_CERT_TAG   = "{http://www.w3.org/2000/09/xmldsig#}X509Certificate"

# Metadata documents are a few kilobytes. The cap keeps a hostile or
# broken endpoint from feeding the parser without end.
SAML_MAX_BYTES  = 1024 * 1024
##############################################################################

# Enums
##############################################################################

##############################################################################