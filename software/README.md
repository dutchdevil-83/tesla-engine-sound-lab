# Future Raspberry Pi software

Production vehicle software does not exist yet. Before implementing vehicle input, use synthetic telemetry. Keep interfaces separated:

1. receive-only telemetry adapter with no transmit API;
2. schema validation, freshness and plausibility checks;
3. deterministic engine state model;
4. bounded audio callback and soft limiter;
5. ALSA output at verified 48 kHz stereo;
6. health supervisor that fades to silence on invalid/stale data;
7. structured local diagnostics with privacy-safe fields only.

Do not add network/cloud inference, CAN write functions, proprietary sound assets, or unmeasured car-specific mappings. Target OS and audio scheduling configuration remain open until bench tests select them.
