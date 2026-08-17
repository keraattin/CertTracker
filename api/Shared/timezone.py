#!/usr/bin/env python3


# Libraries
##############################################################################
from datetime import datetime, timezone
import pytz
import os
##############################################################################


# Values
##############################################################################
# Timezone the scheduler runs its daily job in. Falls back to UTC so the
# app also starts outside of Docker, where TIMEZONE is not exported.
TZ = pytz.timezone(os.environ.get('TIMEZONE') or 'Etc/UTC')
##############################################################################


# Helpers
##############################################################################
# Every datetime written to the database is UTC, no matter which TIMEZONE
# the container runs with. Certificate validity dates come from the peer
# certificate in UTC, so storing everything else in UTC keeps the values
# comparable. Converting to the user's local time is the frontend's job.
def utc_now():
    return datetime.now(timezone.utc)
##############################################################################
