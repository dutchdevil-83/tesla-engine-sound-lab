# Tesla Engine Sound Lab

An offline, real-time virtual engine sound research and engineering project for Tesla. The portal tracks evidence, decisions, hardware, risks, commissioning tasks and acceptance tests. It does not claim that vehicle telemetry, simultaneous audio mixing, or an installed system has been validated.

## Current status

- **Project phase:** Phase 0 — Project preparation
- **Overall status:** Feasibility research and synthetic-telemetry software bench prototype; physical verification remains open
- **Known hardware:** S3XY Commander, S3XY Dash, HELIX DSP (model to confirm), Raspberry Pi 4 available; exact revisions/configuration not yet verified
- **Not owned/confirmed:** S3XY Buttons are not owned; HELIX DIRECTOR ownership and version are unconfirmed
- **Incomplete installation:** passenger-side woofer installation, independent tweeter wiring, final DSP tuning

## Portal

The Dutch-language interactive project portal is in [`web/`](web/). It includes a dashboard, evidence catalog, architecture, BOM, phase plan, engineering checklists, search/filtering, local progress persistence, and JSON/CSV export/import.

## Development

```bash
cd web
npm ci
npm run validate
npm run dev
```

## Safety

Telemetry access must be passive/read-only. Never inject CAN messages or alter Tesla/Commander firmware. Do not perform physical vehicle modifications, live DSP changes, purchases, or active vehicle tests based on this repository alone. All installation-specific DSP values require measurement and qualified installer confirmation. See [`AGENTS.md`](AGENTS.md) and [`docs/installation/safety.md`](docs/installation/safety.md).

## Evidence convention

`Verified` means supported by current cited documentation for the stated hardware/software scope; it does not mean tested in this vehicle. Physical compatibility is marked `Requires physical test`. Each finding has a verification date, source URL and limitation. See [`docs/research/`](docs/research/) and [`data/findings.json`](data/findings.json).

## Project files

- [`docs/`](docs/) — requirements, research, architecture, risks and commissioning
- [`data/`](data/) — structured requirements, sources, findings, tasks, components and milestones
- [`software/`](software/) — offline synthetic-telemetry sound generator, WAV rendering, optional local playback and bench tests
- [`web/`](web/) — portal source
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — change and evidence rules
