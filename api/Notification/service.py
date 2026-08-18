#!/usr/bin/env python3


# Libraries
##############################################################################
from Cert.models import Cert
from Cert.service import CertService
from .restrictions import NOTIFY_DAYS, EXPIRED_DAYS, DATE_FORMAT
from Shared.mailer import is_configured, send_mail
##############################################################################


# Notification Service
##############################################################################
# Decides which certificates are worth a mail and remembers what was
# already reported. Called by the daily job right after the checks, and
# by the route for a manual run.
##############################################################################
class NotificationService:

    @staticmethod
    def run():
        if not is_configured():
            # Not an error: mail is opt-in, and an installation without
            # smtp settings simply does not use this feature.
            return {"sent": 0, "reason": "smtp is not configured"}

        due = []
        for cert in CertService.list():
            threshold = NotificationService._threshold_for(cert)
            if threshold is None:
                continue
            notified = cert.get("notified_days")
            # A smaller remembered threshold means this certificate was
            # already reported at an equal or tighter one.
            if notified is not None and notified <= threshold:
                continue
            due.append((cert, threshold))

        if not due:
            return {"sent": 0}

        send_mail(
            subject=NotificationService._subject(due),
            body=NotificationService._body(due),
        )

        # Only recorded once the mail is out, so a failing smtp server
        # leaves the certificates due for the next run.
        for cert, threshold in due:
            Cert.update(cert["id"], {"notified_days": threshold})

        return {"sent": len(due)}

    # The tightest configured threshold the certificate has fallen under,
    # or None while it still has more time than the widest one.
    @staticmethod
    def _threshold_for(cert):
        days = cert.get("days_remaining")
        if days is None:
            return None
        # Expiry itself deserves one more mail after the last warning.
        if days < 0:
            return EXPIRED_DAYS
        matched = None
        for threshold in NOTIFY_DAYS:
            if days <= threshold:
                matched = threshold
        return matched

    @staticmethod
    def _subject(due):
        return (
            "[CertTracker] " + str(len(due))
            + " certificate/s need attention"
        )

    @staticmethod
    def _body(due):
        lines = []
        for cert, threshold in due:
            days = cert["days_remaining"]
            if days < 0:
                state = "expired " + str(abs(days)) + " day/s ago"
            else:
                state = "expires in " + str(days) + " day/s"
            lines.append(
                str(cert["dns_record"]["dns"]) + ":"
                + str(cert["dns_record"]["ssl_port"])
            )
            lines.append(
                "  " + state
                + " (" + cert["not_after"].strftime(DATE_FORMAT) + ")"
            )
            lines.append("  issuer: " + str(cert["issuer"] or "unknown"))
            if cert.get("last_check_status") == "failed":
                lines.append("  last check failed: " + str(cert["last_error"]))
            lines.append("")
        return "\n".join(lines)
##############################################################################
