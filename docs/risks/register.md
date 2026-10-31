# Risk register

| ID | Risk | Likelihood / impact | Mitigation | Owner evidence / status |
|---|---|---|---|---|
| R-001 | Commander streaming degrades Dash | Medium / High | Concurrent test; fail over to independent read-only interface | Open, T-003 |
| R-002 | HELIX cannot continuously mix analog + optical or isolate mute | Medium / High | Mandatory bench go/no-go before purchase | Open, T-002 |
| R-003 | Highland telemetry mapping invalid or unavailable | High / High | No unverified DBC; validate exact vehicle applicability and signals | Open |
| R-004 | Generic 12 V supply damages Pi or drains low-voltage battery | Medium / High | Verify service info, qualified supply design, sleep behavior | Open, T-005 |
| R-005 | Audio underrun or stale telemetry leaves sound stuck | Medium / High | Watchdog/staleness mute, bounded callback, fault tests | Open, T-006 |
| R-006 | DSP configuration loses Tesla warning sounds | Low / Critical | Backup, retain original path, dedicated alert tests; qualified commissioning | Open, T-007 |
| R-007 | Thermal or storage failure under vehicle conditions | Medium / Medium | Environmental/thermal and power-loss bench test before installation | Open |
| R-008 | Public repository exposes vehicle identifiers or secrets | Low / High | Privacy scan, no raw vehicle logs, secret scanning and review | Ongoing |
