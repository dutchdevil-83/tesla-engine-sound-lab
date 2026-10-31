# ADR-001: Read-only telemetry and Dash preservation

- **Status:** Accepted as a safety constraint; hardware path undecided
- **Date:** 2026-10-31
- **Requirements:** REQ-CAN-001, REQ-S3XY-001

Vehicle-facing access must remain receive-only. The installed S3XY Dash must continue working. Enhance Auto documents Commander Wi-Fi/Panda UDP access but also warns about third-party client interactions. Therefore Commander streaming is conditional on physical coexistence testing. An independent passive interface is a fallback subject to vehicle applicability and qualified installation review. No CAN transmit function will be implemented.
