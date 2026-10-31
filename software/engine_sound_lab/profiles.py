"""Original procedural sound profiles; no recorded or proprietary assets."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EngineProfile:
    id: str
    label: str
    cylinders: int
    idle_rpm: float
    redline_rpm: float
    harmonic_2: float
    harmonic_3: float
    resonance_hz: float
    turbo_mix: float


PROFILES = {
    p.id: p for p in (
        EngineProfile("i5_turbo", "Five-cylinder turbo", 5, 850, 7000, .38, .16, 185, .10),
        EngineProfile("inline_six", "Inline-six", 6, 750, 7200, .30, .13, 220, .02),
        EngineProfile("v8_na", "Naturally aspirated V8", 8, 700, 6800, .48, .22, 160, 0),
        EngineProfile("v8_turbo", "Turbocharged V8", 8, 750, 6800, .40, .18, 150, .08),
        EngineProfile("v12", "V12", 12, 800, 8500, .23, .10, 290, 0),
    )
}
