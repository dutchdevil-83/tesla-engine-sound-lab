# Security policy

This is a personal engineering project. Report security issues privately to the repository owner through GitHub Security Advisories when enabled. Do not disclose vehicle identifiers, account tokens, network credentials, or private diagnostic traces in issues.

Vehicle-facing code must be passive/read-only and fail silent on invalid or stale telemetry. No CAN transmit path is accepted. Browser progress data is local to that browser profile and is not an authentication mechanism. Never store GitHub tokens in the portal.
