# S3XY telemetry research

## Evidence status

| Claim | Status | Evidence | Limitation / physical verification |
|---|---|---|---|
| Panda-compatible Commander Wi-Fi can expose data to third-party CAN applications via UDP 1338 at 192.168.4.1. | Partially verified | [Enhance Auto setup](https://www.enhauto.com/blogs/all/scanmytesla-and-other-apps), checked 2026-10-31 | No stable embedded SDK contract, packet schema, signal list or rate guarantee established. |
| Additional app connectivity may pause Dash data or disconnect devices. | Partially verified | [Dash FAQ](https://www.enhauto.com/blogs/all/s3xy-dash-installation-tutorials-faq-tesla-model-3-y), checked 2026-10-31 | Exact behavior depends on generation/firmware/client; Pi coexistence requires physical test. |
| 2024+ Model 3 has third-party CAN interface details in Tesla bulletin R3 for certain builds. | Partially verified | [Tesla CD-20-17-001 R3](https://service.tesla.com/docs/ServiceBulletins/External/CD/CD-20-17-001_Model_3Y_Third-Party_CAN_Bus_Interface_R3.pdf), revision 2023-12-01 | Exact Highland applicability is market/build-specific and must be verified against service documentation. Tesla does not support third-party hard-wiring. |

## Signal matrix

No exact CAN signal IDs or DBC mappings are approved for Highland use at this stage.

| Signal | Needed for | Status | Validation |
|---|---|---|---|
| Accelerator pedal position | Primary response / load | Unknown | Verify signal meaning, range, update period, invalid values and Highland compatibility. |
| Vehicle speed | Engine/transmission model | Unknown | Compare passive stream with an independent reference. |
| Longitudinal acceleration | Transient response | Unknown | Consider local IMU/GPS fallback, with documented limitations. |
| Requested/actual motor torque | Load behavior | Unknown | Do not infer from unrelated or older-model signals. |
| Regenerative braking/deceleration | Overrun profile | Unknown | Validate sign, units and availability. |

## Candidate comparison

| Option | Latency / data | Dash compatibility | Offline / safety | Current decision |
|---|---|---|---|---|
| Commander Panda Wi-Fi | UDP path documented; actual latency/rate unknown | Risk of client conflict | Local; test strictly passive | Candidate only; test first |
| Tesla X181 third-party interface | CAN access documented for certain vehicles; decoded signals unknown | Independent of Commander | Passive interface possible; installation unsupported by Tesla | Research alternative; qualified review required |
| GPS + IMU | Speed/acceleration, no pedal or torque | Independent | Local; lower semantic precision | Fallback/supplement only |
| Tesla Fleet API | Cloud-mediated and not guaranteed low-latency | Independent | Not reliably offline | Rejected for real-time runtime |

## Read-only test protocol

1. Record device generation and firmware without modifying firmware.
2. Verify Dash behavior first with no third-party client.
3. Receive-only capture the documented stream; no writes or frame transmission.
4. Record monotonic receive timestamps, packet interval, loss, malformed frames and reconnect behavior.
5. Monitor Dash update continuity through drive-mode-free, stationary wake/sleep and reconnect cases. Do not perform distracted driving tests.
6. Stop the test if Dash functionality degrades. Select another telemetry path rather than accepting the regression.
7. Do not publish raw diagnostic captures; redact personal and vehicle identifiers.
