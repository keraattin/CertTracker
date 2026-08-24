#!/usr/bin/env python3

# Libraries
##############################################################################
from apscheduler.schedulers.blocking import BlockingScheduler
from app import app
import logging
import os
from Shared.timezone import TZ
##############################################################################

##############################################################################
# Relative to the working directory (/api in the container). Overridable so
# the scheduler can also run from somewhere else.
LOG_FILE = os.environ.get('LOG_FILE') or './Logs/cron.log'

# When the daily run happens, in the TIMEZONE the container runs with.
# Overridable so an installation can move it off the hour everyone else
# also picked.
CRON_HOUR   = os.environ.get('CRON_HOUR') or '00'
CRON_MINUTE = os.environ.get('CRON_MINUTE') or '05'

log = logging.getLogger(__name__)
logging.basicConfig(filename = LOG_FILE,
                    level = logging.INFO,
                    format = '%(asctime)s:%(levelname)s:%(name)s:%(message)s')
##############################################################################

# Define Scheduler
##############################################################################
scheduler = BlockingScheduler(timezone=TZ)
##############################################################################

# Scheduled Job
##############################################################################
@scheduler.scheduled_job('cron', hour=CRON_HOUR, minute=CRON_MINUTE)
def job():
    log.info("job started")
    with app.app_context():
        from DnsRecord.models import DnsRecord
        from Cert.service import CertService
        from Notification.service import NotificationService
        from DnsRecord.restrictions import SOURCE_TLS, FETCHABLE_SOURCES
        dns_records = DnsRecord.query.all()
        for dns_record in dns_records:
            # An uploaded certificate has nowhere to be fetched from
            # again; it stays until someone uploads a new one.
            if (dns_record.source or SOURCE_TLS) not in FETCHABLE_SOURCES:
                continue
            try:
                CertService.run_check(dns_record.id)
                log.info(
                    "checked %s:%s", dns_record.dns, dns_record.ssl_port
                )
            except Exception as e:
                log.error(
                    "failed to check %s:%s - %s",
                    dns_record.dns, dns_record.ssl_port, e,
                )
        # Runs on the results of the checks above, so a certificate that
        # was renewed this morning is not reported as expiring.
        try:
            log.info("notification: %s", NotificationService.run())
        except Exception as e:
            log.error("failed to send notifications - %s", e)
    log.info("job finished")
##############################################################################


# Main
##############################################################################
# Guarded so importing this module does not block on the scheduler loop.
if __name__ == '__main__':
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled
        # but should be done if possible
        scheduler.shutdown()
##############################################################################
