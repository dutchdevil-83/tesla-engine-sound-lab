"""Validated synthetic telemetry. No CAN, network, or vehicle control code."""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Telemetry:
    pedal: float
    speed_kph: float
    timestamp: float

    def valid_at(self, now: float, timeout: float) -> bool:
        """Accept only finite, plausible and fresh values on one monotonic clock."""
        try:
            return (
                all(math.isfinite(v) for v in (self.pedal, self.speed_kph, self.timestamp, now, timeout))
                and 0 <= self.pedal <= 1
                and 0 <= self.speed_kph <= 300
                and timeout > 0
                and 0 <= now - self.timestamp <= timeout
            )
        except (TypeError, ValueError):
            return False


def synthetic_telemetry(elapsed: float, timestamp: float) -> Telemetry:
    """A repeatable stationary-to-acceleration-to-overrun demonstration cycle."""
    phase = max(0.0, elapsed) % 12.0
    if phase < 2:
        pedal, speed = .08, 0.0
    elif phase < 6:
        pedal, speed = .25 + .15 * (phase - 2), 20 * (phase - 2)
    elif phase < 9:
        pedal, speed = .85 - .25 * (phase - 6), 80 - 10 * (phase - 6)
    else:
        pedal, speed = .05, max(0, 50 - 15 * (phase - 9))
    return Telemetry(pedal=pedal, speed_kph=speed, timestamp=timestamp)
