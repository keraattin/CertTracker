## Unreleased
- Introduced an internal service layer so models no longer return Flask responses, making the codebase easier to test and reuse outside of HTTP routes. ([#6](https://github.com/keraattin/CertTracker/issues/6))
- Merged the standalone `cert-checker` service back into the `api` service. The certificate fetch is now an in-process Python call, removing one container, one port, and a network round-trip per check. ([#8](https://github.com/keraattin/CertTracker/issues/8))
- Hardening pass ([#10](https://github.com/keraattin/CertTracker/issues/10)):
  - Certificate checks now time out after 10 seconds. A host that silently drops packets used to block the request, and the whole daily cron run, forever.
  - All dependencies are pinned. `db.relation()` was removed in SQLAlchemy 2.0, so an unpinned rebuild would have failed on import. Dropped the unused `requests` and the `dataclasses` backport, which shadows the stdlib module on Python 3.10.
  - Every stored datetime is UTC. `last_update` previously used the container `TIMEZONE` while certificate dates came in as UTC, which silently skewed the remaining-day calculation on non-UTC deployments.
  - Served by waitress instead of the Flask development server, and `DEBUG` now defaults to `False` (the value was read as a string, so even `"False"` enabled debug mode).
  - The API image is Debian based, so `cryptography` installs from a prebuilt wheel instead of being compiled from source on every build.
  - Added a `/health` endpoint and a compose healthcheck.
  - `TIMEZONE` defaults to `Etc/UTC` and the database path is configurable via `DATABASE_URI`, so the app also runs outside the container.
  - Raised the `dns` column to 253 characters to match the validation regex, and made the regex patterns raw strings.
- Certificate details and failed check visibility ([#11](https://github.com/keraattin/CertTracker/issues/11)):
  - Certificates now record their issuer, subject, alternative names, serial number, signature algorithm and whether they are self-signed. A `Details` button on the certificates page shows all of it.
  - A failed check no longer leaves the previous certificate looking healthy. The row keeps the last certificate that could be fetched and is marked `CHECK FAILED`, with the error behind the badge.
  - The api returns `days_remaining` and `status` (`valid` / `expiring` / `expired`), so the thresholds are defined once instead of being repeated in the frontend. A certificate with exactly 30 days left used to fall through every branch and render an uncoloured badge.
  - A host that could not be reached during `Check All Certs` is now listed with a cross instead of being dropped from the table entirely.
  - Columns added to a model are applied to an existing database on startup, so upgrading does not require recreating it.
- Dashboard on the home page ([#15](https://github.com/keraattin/CertTracker/issues/15)):
  - The home page was an empty container. It now summarizes how many certificates are valid, expiring within 30 days, expired, or failed their last check, and how many tracked DNS records have never been checked at all.
  - Below the cards, everything that is not plainly valid is listed soonest to expire first, so the page answers "what do I need to do today" without opening the certificates list.
- Mail notifications ([#2](https://github.com/keraattin/CertTracker/issues/2)):
  - The daily job now sends a summary mail after it checks the certificates. Configured through `SMTP_HOST`, `MAIL_FROM`, `MAIL_TO` and friends; notifications stay off until those are set, so nothing changes for an installation that ignores them.
  - `NOTIFY_DAYS` (default `30,14,7,1`) decides when a mail goes out. Each certificate is reported once per threshold and once more when it actually expires, instead of every morning. Renewing a certificate starts its thresholds over.
  - `POST /api/notification/run` runs the same pass on demand, to verify the smtp settings without waiting for the scheduled run.
- Local time in the frontend ([#3](https://github.com/keraattin/CertTracker/issues/3)):
  - Dates were printed exactly as the api sent them, which is UTC, so a certificate expiring at `23:59:59 GMT` read as the wrong day for anyone east of London. They are now rendered in the timezone of the browser, and each table says which timezone that is.
  - Hovering a date shows the original UTC value the api sent, so the converted value stays verifiable.
  - Mail notifications keep writing UTC and label it as such: the recipient's timezone is not knowable from the server.

## [Version 2.0](https://github.com/keraattin/CertTracker/releases/tag/2.0)
- [#1](https://github.com/keraattin/CertTracker/issues/1) Scheduled jobs added. All certificates will be checked everyday at 00:05 UTC
- [#4](https://github.com/keraattin/CertTracker/issues/4) CORS Policy error resolved.

You can access the [Full Changelog from here](https://github.com/keraattin/CertTracker/compare/1.0...2.0)

## [Version 1.0](https://github.com/keraattin/CertTracker/releases/tag/1.0)
- Initial release