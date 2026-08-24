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
- Test suite and CI ([#19](https://github.com/keraattin/CertTracker/issues/19)):
  - 64 tests covering the routes, the expiry thresholds, the check failure path, the notification thresholds, the schema sync and the frontend scripts.
  - No network access and no docker required. The suite generates its own certificate and serves it over TLS on localhost, so the fetcher is tested against known dates and a known issuer instead of whatever a public host serves today. A small smtp server does the same for the notifications, and a socket that accepts a connection and then says nothing proves the TLS timeout works.
  - The frontend scripts run in an embedded javascript engine, so a syntax error fails the build rather than appearing as a blank page.
  - GitHub Actions runs the tests and a `docker compose build` on every push and pull request, on the same Python version as the image.
- Same origin frontend ([#21](https://github.com/keraattin/CertTracker/issues/21)):
  - The api address was written into the frontend javascript in eleven places as `http://localhost:5000`, so the project only ever worked on the machine it was built on. nginx now proxies `/api` to the api service and every call is a relative path.
  - A test fails the build if an absolute address finds its way back into the scripts.
  - The frontend waits for the api healthcheck before starting, since nginx resolves the api hostname once, at startup.
- Certificate sources ([#5](https://github.com/keraattin/CertTracker/issues/5)):
  - A record now says where its certificate comes from. `tls` connects as before and stays the default, so nothing changes for existing records.
  - `saml` follows the metadata document an identity provider publishes and reads the certificate out of it. Those certificates are not served by a TLS handshake anywhere, which is what made them impossible to track. Where a document lists several, the one expiring soonest is recorded, since that is the one worth warning about.
  - `upload` takes the certificate directly, in PEM or DER, for hosts this installation cannot reach. There is nothing to re-fetch, so the daily job skips these records and `Check Cert` is disabled for them. Uploading again replaces the certificate.
  - `ssl_port` is now optional and defaults to 443: only the tls source connects to a port.
- Fixes found by running the stack for real:
  - The api could fail to start on a fresh installation, and did so about half the time. `entrypoint.sh` starts the scheduler and the web server, both of which import `app.py` and call `db.create_all()`. Against an empty database the two processes raced, and whichever lost died with `table already exists`. The schema is now created once, before either of them starts. This had been the case since the scheduler was added; it went unnoticed because the database is kept in a volume, so the race only exists on the very first run.
  - The api never started in a container built on Windows. Git rewrites `entrypoint.sh` to CRLF on checkout, `COPY` carries that into the image, and the shell reads the carriage return as part of the command, so waitress looked for a module named `app:app` followed by a CR. A `.gitattributes` now keeps the line endings of anything the container executes.
  - CI ran the images through `docker compose build` but never started them, so a container that built perfectly and died on startup counted as a pass. It now brings the stack up and calls `/health` and `/api/dns` through the proxy.
  - The container healthcheck asked for `localhost`, which resolves to `::1` first, while the server binds `0.0.0.0` and answers on IPv4 only. It now addresses `127.0.0.1`, as do the CI checks.
  - One test compared two timestamps that the api serializes to whole seconds. It passed on a slow machine and failed on a fast one, which is why CI had been red since the suite was added. It now compares the stored values, which keep microseconds.

## [Version 2.0](https://github.com/keraattin/CertTracker/releases/tag/2.0)
- [#1](https://github.com/keraattin/CertTracker/issues/1) Scheduled jobs added. All certificates will be checked everyday at 00:05 UTC
- [#4](https://github.com/keraattin/CertTracker/issues/4) CORS Policy error resolved.

You can access the [Full Changelog from here](https://github.com/keraattin/CertTracker/compare/1.0...2.0)

## [Version 1.0](https://github.com/keraattin/CertTracker/releases/tag/1.0)
- Initial release