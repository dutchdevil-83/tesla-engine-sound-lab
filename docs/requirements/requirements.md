# Requirements and verification matrix

| ID | Requirement | Verification method | Current status | Decision / implementation / evidence |
|---|---|---|---|---|
| REQ-AUD-001 | Tesla audio and engine sound play simultaneously without interruption. | Bench routing test, then controlled integration test | Open | ADR-002; FND-DSP-002; T-002 |
| REQ-CAN-001 | Vehicle telemetry is passive/read-only. | Architecture review and receive-only interface review | Design constraint | ADR-001; T-003 |
| REQ-S3XY-001 | Existing S3XY Dash remains fully functional. | Concurrent operation across wake/reconnect and streaming cases | Open | FND-S3XY-001; T-003 |
| REQ-DSP-001 | Digital engine source has independent volume and mute. | HELIX DIRECTOR test while analog input remains active | Open | FND-DSP-003; T-002 |
| REQ-SAF-001 | Stale/invalid telemetry safely fades engine sound to silence. | Synthetic fault injection; later integration fault test | Open | T-006 |
| REQ-LAT-001 | Measure accelerator-to-audio latency against <50 ms target. | Common-clock measurement and repeated statistics | Open | T-008 |
| REQ-OFF-001 | Production sound synthesis operates offline. | Network-isolated runtime test | Design constraint | T-006 |
| REQ-PWR-001 | Power/shutdown behavior avoids unsafe draw and corruption. | Applicable service-document review and installer tests | Open | T-005 |
| REQ-COM-001 | Commissioning can be repeated using traceable measured values and backups. | Independent checklist execution and archive review | Open | T-007 |

No requirement is marked complete from documentation alone when physical evidence is required.
