## Unreleased
- Introduced an internal service layer so models no longer return Flask responses, making the codebase easier to test and reuse outside of HTTP routes. ([#6](https://github.com/keraattin/CertTracker/issues/6))
- Merged the standalone `cert-checker` service back into the `api` service. The certificate fetch is now an in-process Python call, removing one container, one port, and a network round-trip per check. ([#8](https://github.com/keraattin/CertTracker/issues/8))

## [Version 2.0](https://github.com/keraattin/CertTracker/releases/tag/2.0)
- [#1](https://github.com/keraattin/CertTracker/issues/1) Scheduled jobs added. All certificates will be checked everyday at 00:05 UTC
- [#4](https://github.com/keraattin/CertTracker/issues/4) CORS Policy error resolved.

You can access the [Full Changelog from here](https://github.com/keraattin/CertTracker/compare/1.0...2.0)

## [Version 1.0](https://github.com/keraattin/CertTracker/releases/tag/1.0)
- Initial release