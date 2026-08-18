#!/usr/bin/env python3


# Libraries
##############################################################################
from email.message import EmailMessage
import os
import smtplib

from .exceptions import ExternalServiceError
##############################################################################


# Values
##############################################################################
# Notifications stay off until a host is configured, so an installation
# that sets none of these keeps behaving exactly as it did before.
SMTP_HOST     = os.environ.get('SMTP_HOST') or ''
SMTP_PORT     = int(os.environ.get('SMTP_PORT') or 587)
SMTP_USER     = os.environ.get('SMTP_USER') or ''
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD') or ''
SMTP_TLS      = os.environ.get('SMTP_TLS', 'True') == 'True'
MAIL_FROM     = os.environ.get('MAIL_FROM') or ''
MAIL_TO       = os.environ.get('MAIL_TO') or ''

# Same reasoning as TLS_TIMEOUT: an unresponsive server must not hold the
# daily job open forever.
SMTP_TIMEOUT  = 30
##############################################################################


# Mailer
##############################################################################
# Sends plain text mail over smtp. Configuration comes from the
# environment, so the service layer only has to ask whether mail can be
# sent at all and then hand over a subject and a body.
##############################################################################

# MAIL_TO holds one or more addresses separated by commas.
def recipients():
    return [
        address.strip() for address in MAIL_TO.split(',') if address.strip()
    ]


def is_configured():
    return bool(SMTP_HOST and MAIL_FROM and recipients())


def send_mail(subject, body):
    message = EmailMessage()
    message['Subject'] = subject
    message['From'] = MAIL_FROM
    message['To'] = ", ".join(recipients())
    message.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT) as server:
            if SMTP_TLS:
                server.starttls()
            # An empty user means the server accepts unauthenticated mail,
            # which is common for an internal relay.
            if SMTP_USER:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(message)
    except Exception as e:
        raise ExternalServiceError(
            message="failed to send mail through "
                    + str(SMTP_HOST) + ":" + str(SMTP_PORT) + " - " + str(e),
        )
##############################################################################
