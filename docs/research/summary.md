# Technical research summary

**Verification date:** 2026-10-31. Sources are linked in [`../../data/sources.json`](../../data/sources.json); per-topic findings are in [`../../data/findings.json`](../../data/findings.json).

## HELIX DSP — highest-priority gate

Audiotec Fischer's V TWELVE DSP MK2 specifications list one optical S/PDIF input, accepted at 12–96 kHz, and a 48 kHz DSP sample rate. DSP PC-Tool documentation describes Main Routing and additional digital routing paths. DIRECTOR documentation describes Digital Volume control (−60 to 0 dB, 0.5 dB steps), input selection and sound setup selection. These documents support a plausible integration path, but do **not** prove that this vehicle's installed model/revision and current preset mix analog Tesla audio with optical Pi audio continuously. That physical test is a go/no-go before buying a S/PDIF HAT.

The DIRECTOR's digital input volume is a HELIX source-volume function. It is not a documented command channel to the Raspberry Pi. Input Select can switch sources and therefore is not by itself proof of an isolated digital mute while Tesla audio remains active. See FND-DSP-001 through FND-DSP-003.

## S3XY Commander and Dash

Enhance Auto publishes a third-party CAN/Panda Wi-Fi setup using `192.168.4.1`, UDP port `1338`. Its help content warns about client limits and possible Dash data pauses/disconnections while other apps connect. No manufacturer guarantee of reliable concurrent Dash plus persistent embedded telemetry streaming was found. Treat the Commander path as **requires physical test**. If it degrades the Dash, stop using this route and assess an independent passive interface. Do not transmit frames or rely on older DBC mappings without Highland compatibility evidence.

Tesla service bulletin CD-20-17-001 revision R3, dated 2023-12-01, adds 2024+ Model 3 third-party interface information for certain production/market configurations. It does not prove exact vehicle applicability. Tesla states third-party hard-wiring is unsupported and at installer risk. This is research context only, not permission or an installation instruction.

## Raspberry Pi and optical audio

Official Raspberry Pi specs list Pi 4B as 1.8 GHz Cortex-A72 and Pi 3B+ as 1.4 GHz Cortex-A53; both have a 40-pin header. Pi 4 is the initial bench candidate for processing headroom, subject to exact board revision, thermal and ALSA underrun testing. HiFiBerry lists Digi2 Pro board release 2.2 and 40-pin Pi support. Its datasheet covers optical S/PDIF rates; the manufacturer also documents a Pi 4 Rev 1.5 compatibility caveat. Identify the actual board revision and verify 48 kHz stereo PCM before any purchase.

## Sound generation and timing

Use deterministic synthesis in the production audio callback: smoothed virtual RPM/load, cylinder pulse trains/harmonics, resonant filtering, profile-specific firing intervals and a bounded limiter. Network and AI are excluded from the runtime path. Engine Sim is a research reference; check its license and portability before any code reuse. Do not use proprietary/copyrighted audio assets without permission.

The <50 ms accelerator-to-audible requirement is a project target only. No supplier specification establishes it end to end. Measure telemetry receipt → decoding → model update → ALSA buffer → optical output → DSP → acoustic response on a common clock; report median, p95, max and dropouts.

## Power and vehicle installation

No complete, Highland-specific low-voltage power design is established here. Tesla's X181 bulletin is not a general Pi power specification. Verify exact vehicle service information, supply voltage behavior, wake/sleep strategy, transient protection, fuse, current, shutdown and parked draw with a qualified installer before selecting a converter. Do not splice wiring based on generic 12 V assumptions.

## Sources and dates

All URLs were checked 2026-10-31. Manufacturer web pages may change; archive product/manual revision and applicable firmware when decisions are made. Prices are omitted because a current VAT-inclusive Dutch/EU supplier price was not verified.
