# ADR-003: Deterministic offline synthesis

- **Status:** Accepted as direction; algorithm remains open
- **Date:** 2026-10-31
- **Requirements:** REQ-OFF-001, REQ-SAF-001, REQ-LAT-001

The production audio path will use deterministic local DSP. AI can support research and offline tuning but is not a production dependency. Sound profiles will be authored from original procedural synthesis; proprietary source and unlicensed recordings are excluded. The callback must have bounded CPU work, predictable buffering, stale-input fade-to-mute and limiting.
