#!/usr/bin/env python3

# Libraries
##############################################################################
import os
##############################################################################

# Values
##############################################################################
# Days before expiry that a mail goes out, widest first. A certificate is
# notified for the tightest threshold it has fallen under, and remembers
# it, so each threshold produces one mail instead of one every day.
NOTIFY_DAYS = sorted(
    [
        int(day) for day in
        (os.environ.get('NOTIFY_DAYS') or '30,14,7,1').split(',')
        if day.strip()
    ],
    reverse=True
)

# Threshold used once a certificate has actually expired. Without it the
# last warning before expiry would also be the last mail ever sent about
# it, since every configured threshold was already reported by then.
EXPIRED_DAYS = -1

# How the expiry date is written in the mail body. The stored value has
# microseconds, which are noise in a notification.
DATE_FORMAT = '%Y-%m-%d %H:%M UTC'
##############################################################################

# Enums
##############################################################################

##############################################################################
