#!/usr/bin/env python3

# Libraries
##############################################################################
from pytz import timezone
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from app import app
import logging
from Shared.timezone import TZ
##############################################################################

##############################################################################
log = logging.getLogger(__name__)
logging.basicConfig(filename = './Logs/cron.log',
                    level = logging.INFO,
                    format = '%(asctime)s:%(levelname)s:%(name)s:%(message)s')
##############################################################################

# Define Scheduler
##############################################################################
scheduler = BlockingScheduler(timezone=TZ)
##############################################################################

# Scheduled Job
##############################################################################
@scheduler.scheduled_job('cron', hour="00", minute="05")
def job():
    log.info("job started")
    with app.app_context():
        from DnsRecord.models import DnsRecord
        from Cert.views import cert_check
        dns_records = DnsRecord.query.all()
        for dns_record in dns_records:
            cert_check(dns_record.id)
    log.info("job finished")
##############################################################################


# Main
##############################################################################
try:
    scheduler.start()
except (KeyboardInterrupt, SystemExit):
    # Not strictly necessary if daemonic mode is enabled 
    # but should be done if possible
    scheduler.shutdown()
##############################################################################