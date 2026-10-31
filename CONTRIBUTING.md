# Contributing

## Engineering evidence

For technical claims, prefer current manufacturer documentation and cite an exact URL, publisher, revision/date if available, verification date, applicable model/firmware, limitations and required physical tests. Do not silently promote a hypothesis to verified.

## Structured data

Keep IDs stable and unique. Update `data/sources.json` and `data/findings.json` together when adding an evidence-backed finding. Use only the defined evidence statuses. Never mark a project task complete without evidence. Keep the website datasets valid JSON and run `npm run validate` from `web/`.

## Safety and privacy

Do not add VINs, plates, personal addresses, credentials, Wi-Fi secrets, or identifiable diagnostic logs. Telemetry integrations must remain read-only. Do not add commands that transmit CAN frames. Do not publish copyrighted engine recordings or proprietary source code.

## Changes

Use focused commits and descriptive messages. Update relevant requirements, ADRs, risks, tests and website content when behavior changes. CI must pass before merge or publication.
