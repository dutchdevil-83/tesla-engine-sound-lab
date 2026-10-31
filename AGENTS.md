# Agent guide — Tesla Engine Sound Lab

## Objective and known context

Develop a locally operating, low-latency virtual engine sound system for a European Tesla Model 3 Highland. Vehicle data is intended to drive deterministic DSP synthesis on a Raspberry Pi and feed a HELIX DSP by optical S/PDIF while original Tesla audio continues. This is a design hypothesis, not a proven installation.

Known from the project owner: S3XY Commander and S3XY Dash are installed; Raspberry Pi 4 is available; a HELIX DSP is installed and was previously identified as HELIX V TWELVE DSP MK2, which must be checked against the physical label. The passenger-side woofer remains to be installed, tweeter wiring must be split for independent DSP channels, and final DSP commissioning is incomplete. HELIX DIRECTOR ownership/version are unconfirmed. S3XY Buttons are not owned and must not become a dependency.

## Mandatory safety boundaries

- Read-only/passive telemetry only. Never transmit/inject CAN, change vehicle/Commander firmware, or send control commands.
- Never compromise Tesla safety or warning audio. Loss, invalidity, or staleness of telemetry must fade engine sound to silence.
- No physical work, live DSP changes, purchases, active vehicle tests, or deployment to installed automotive hardware without separate authorization.
- Do not guess vehicle year/variant, signal mappings, pinouts, wiring, fuse values, crossover frequencies, gains, polarity, delays or speaker assignments.
- Do not publish VINs, plates, addresses, credentials, Wi-Fi passwords or identifiable logs.
- Use original deterministic synthesis. Do not vendor proprietary code, paid sound libraries or unlicensed recordings.

## Evidence and research

Prefer current official manuals/specifications. Every material finding needs a stable ID, exact URL, publisher, date verified, applicability, evidence status, technical conclusion, limitations, remaining uncertainty and physical test. Statuses: `Verified`, `Partially verified`, `Hypothesis`, `Requires physical test`, `Rejected`. Product documentation only verifies documented capability; it does not prove this car's configuration or simultaneous operation.

## Repository layout and traceability

- `docs/requirements/`: REQ IDs and acceptance criteria.
- `docs/research/`: topic reports and cited evidence.
- `docs/architecture/`: diagrams and ADRs.
- `docs/hardware/`, `docs/s3xy/`, `docs/raspberry-pi/`, `docs/helix-dsp/`: component engineering.
- `docs/installation/`, `docs/commissioning/`, `docs/testing/`: controlled procedures and records.
- `docs/risks/`: risk register and open questions.
- `data/*.json`: canonical portal data. Keep stable IDs and schema-compatible values.
- `web/`: static React/TypeScript portal, no backend and no secret-bearing client integration.
- `software/`: future Raspberry Pi software; do not imply production-ready code exists.

Maintain `requirement → decision → implementation → test → evidence` traceability. No phase is complete without attached evidence. Browser localStorage is device/browser-local; export a backup before clearing browser data.

## Portal development

From `web/`: `npm ci`, `npm run typecheck`, `npm run lint`, `npm test`, `npm run build`, `npm run validate`. Use accessible semantic HTML, keyboard-operable controls, responsive layouts and explicit empty/error states. Add tests for data validation and progress import/export. Internal links must resolve. Do not mark example content as completed project work.

## Deployment and contribution

CI runs on pull requests and pushes. GitHub Pages deployment is via GitHub Actions after repository configuration. Use relative/base-aware asset paths. Never commit build secrets, personal access tokens or private vehicle data. Cite external content; link rather than copy proprietary materials. Use focused commits. Create issues for unresolved engineering work and retain physical verification as open until measured.
