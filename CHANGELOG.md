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

## [Version 2.0](https://github.com/keraattin/CertTracker/releases/tag/2.0)
- [#1](https://github.com/keraattin/CertTracker/issues/1) Scheduled jobs added. All certificates will be checked everyday at 00:05 UTC
- [#4](https://github.com/keraattin/CertTracker/issues/4) CORS Policy error resolved.

You can access the [Full Changelog from here](https://github.com/keraattin/CertTracker/compare/1.0...2.0)

## [Version 1.0](https://github.com/keraattin/CertTracker/releases/tag/1.0)
- Initial release