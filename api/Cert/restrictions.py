#!/usr/bin/env python3

# Libraries
##############################################################################

##############################################################################

# Values
##############################################################################
LEN_ISSUER  = 253
LEN_SUBJECT = 253
LEN_SERIAL  = 64
LEN_SIG_ALG = 32
LEN_STATUS  = 16
LEN_ERROR   = 512

# A certificate is reported as expiring once it has this many days left
# or fewer. Same threshold the frontend used to hardcode.
DAYS_EXPIRING = 30
##############################################################################

# Enums
##############################################################################
# Outcome of the last check attempt, whatever the certificate itself says.
CHECK_OK        = "ok"
CHECK_FAILED    = "failed"

# Validity of the certificate that was last fetched successfully.
STATUS_VALID    = "valid"
STATUS_EXPIRING = "expiring"
STATUS_EXPIRED  = "expired"
##############################################################################
