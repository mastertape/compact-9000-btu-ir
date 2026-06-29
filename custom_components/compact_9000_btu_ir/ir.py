"""Infrared helpers for reverse-engineered Compact 9000 BTU AC captures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from infrared_protocols.commands import Command

if TYPE_CHECKING:
    from homeassistant.core import Context, HomeAssistant

from .const import (
    FAN_VALUES,
    MODE_VALUES,
    TEMP_MAX_C,
    TEMP_MAX_F,
    TEMP_MIN_C,
    TEMP_MIN_F,
    TEMP_UNIT_CELSIUS,
    TEMP_UNIT_FAHRENHEIT,
    TEMP_UNITS,
    TIMER_MAX_HOURS,
    TIMER_MIN_HOURS,
    COMPACT_9000_BTU_BIT_MARK,
    COMPACT_9000_BTU_BITS,
    COMPACT_9000_BTU_CELSIUS_STABLE,
    COMPACT_9000_BTU_CELSIUS_TIMER_SELECTED,
    COMPACT_9000_BTU_FAHRENHEIT,
    COMPACT_9000_BTU_HDR_MARK,
    COMPACT_9000_BTU_HDR_SPACE,
    COMPACT_9000_BTU_INTRO,
    COMPACT_9000_BTU_MESSAGE_GAP,
    COMPACT_9000_BTU_MIN_TEMP_C,
    COMPACT_9000_BTU_MIN_TEMP_F,
    COMPACT_9000_BTU_MODULATION,
    COMPACT_9000_BTU_ONE_SPACE,
    COMPACT_9000_BTU_STATE_LENGTH,
    COMPACT_9000_BTU_TIMER_SET_BIT,
    COMPACT_9000_BTU_ZERO_SPACE,
)


class Compact9000BtuValidationError(ValueError):
    """Raised when a Compact 9000 BTU capture frame or state is invalid."""


@dataclass
class Compact9000BtuCommand(Command):
    """Raw Compact 9000 BTU command compatible with Home Assistant infrared emitters."""

    state: bytes
    repeat_count: int = 0
    modulation: int = COMPACT_9000_BTU_MODULATION

    def __post_init__(self) -> None:
        """Initialize the infrared-protocols base command fields."""
        super().__init__(modulation=self.modulation, repeat_count=self.repeat_count)

    def get_raw_timings(self) -> list[int]:
        """Return raw mark/space timings in microseconds.

        The Compact 9000 BTU captures are MSB-first with a 100 ms message gap.
        Positive values are marks; negative values are spaces.
        """
        frame = encode_timings(self.state)
        timings = list(frame)
        for _ in range(self.repeat_count):
            timings.append(-COMPACT_9000_BTU_MESSAGE_GAP)
            timings.extend(frame)
        return timings


@dataclass(frozen=True)
class DecodedCompact9000BtuState:
    """Decoded Compact 9000 BTU state suitable for future receive-side state sync."""

    state: bytes
    power: bool
    mode: str
    temperature_c: int
    temperature_f: int
    temperature_unit: str
    fan: str
    swing: bool
    timer_hours: int | None
    context: str


FAN_NAMES = {value: key for key, value in FAN_VALUES.items()}
MODE_NAMES = {value: key for key, value in MODE_VALUES.items() if key != "off"}
FRAME_CONTEXTS = {
    COMPACT_9000_BTU_CELSIUS_STABLE: "celsius_stable",
    0x80: "celsius_remote_adjust",
    0xC0: "celsius_temperature_adjust",
    COMPACT_9000_BTU_FAHRENHEIT: "fahrenheit",
    COMPACT_9000_BTU_CELSIUS_TIMER_SELECTED: "timer_selected",
    0x83: "timer_entry",
}


def calc_checksum(state: bytes | bytearray) -> int:
    """Calculate the Compact 9000 BTU capture checksum."""
    return sum(state[: COMPACT_9000_BTU_STATE_LENGTH - 1]) & 0xFF


def valid_checksum(state: bytes | bytearray) -> bool:
    """Return whether the Compact 9000 BTU capture checksum is valid."""
    return len(state) == COMPACT_9000_BTU_STATE_LENGTH and state[-1] == calc_checksum(state)


def format_state(state: bytes | bytearray) -> str:
    """Format a Compact 9000 BTU state as spaced uppercase hex bytes."""
    return " ".join(f"{byte:02X}" for byte in state)


def parse_hex_code(code: str) -> bytes:
    """Parse and validate a 9-byte Compact 9000 BTU capture frame."""
    raw_parts = code.replace(",", " ").split()
    if len(raw_parts) != COMPACT_9000_BTU_STATE_LENGTH:
        raise Compact9000BtuValidationError(
            f"expected exactly {COMPACT_9000_BTU_STATE_LENGTH} bytes, got {len(raw_parts)}"
        )

    parsed: list[int] = []
    for part in raw_parts:
        normalized = part[2:] if part.lower().startswith("0x") else part
        if len(normalized) != 2:
            raise Compact9000BtuValidationError(f"invalid byte '{part}'")
        try:
            value = int(normalized, 16)
        except ValueError as err:
            raise Compact9000BtuValidationError(f"invalid hex byte '{part}'") from err
        if not 0 <= value <= 0xFF:
            raise Compact9000BtuValidationError(f"byte out of range '{part}'")
        parsed.append(value)

    state = bytes(parsed)
    if state[0] != COMPACT_9000_BTU_INTRO:
        raise Compact9000BtuValidationError(
            f"byte 0 must be 0x{COMPACT_9000_BTU_INTRO:02X}, got 0x{state[0]:02X}"
        )
    if not valid_checksum(state):
        raise Compact9000BtuValidationError(
            "checksum mismatch: "
            f"expected 0x{calc_checksum(state):02X}, got 0x{state[-1]:02X}"
        )
    return state


def celsius_to_fahrenheit(celsius: int) -> int:
    """Convert Celsius to rounded Fahrenheit for the captured byte-3 field."""
    return round(celsius * 9 / 5 + 32)


def fahrenheit_to_celsius(fahrenheit: int) -> int:
    """Convert Fahrenheit to rounded Celsius for the captured byte-1 field."""
    return round((fahrenheit - 32) * 5 / 9)


def decode_state(state: bytes | bytearray) -> DecodedCompact9000BtuState:
    """Decode and validate a 9-byte Compact 9000 BTU state frame."""
    if len(state) != COMPACT_9000_BTU_STATE_LENGTH:
        raise Compact9000BtuValidationError(
            f"expected exactly {COMPACT_9000_BTU_STATE_LENGTH} bytes, got {len(state)}"
        )
    if state[0] != COMPACT_9000_BTU_INTRO:
        raise Compact9000BtuValidationError(
            f"byte 0 must be 0x{COMPACT_9000_BTU_INTRO:02X}, got 0x{state[0]:02X}"
        )
    if not valid_checksum(state):
        raise Compact9000BtuValidationError(
            "checksum mismatch: "
            f"expected 0x{calc_checksum(state):02X}, got 0x{state[-1]:02X}"
        )

    fan_value = state[6] >> 4
    mode_value = state[6] & 0x0F
    if fan_value not in FAN_NAMES:
        raise Compact9000BtuValidationError(f"unknown fan value 0x{fan_value:X}")
    if mode_value not in MODE_NAMES:
        raise Compact9000BtuValidationError(f"unknown mode value 0x{mode_value:X}")

    temperature_c = (state[1] >> 4) + COMPACT_9000_BTU_MIN_TEMP_C
    temperature_f = state[3] + COMPACT_9000_BTU_MIN_TEMP_F
    temperature_unit = (
        TEMP_UNIT_FAHRENHEIT if state[7] == COMPACT_9000_BTU_FAHRENHEIT else TEMP_UNIT_CELSIUS
    )
    timer_hours = state[2] if state[1] & COMPACT_9000_BTU_TIMER_SET_BIT else None

    return DecodedCompact9000BtuState(
        state=bytes(state),
        power=bool(state[1] & 0x02),
        mode=MODE_NAMES[mode_value],
        temperature_c=temperature_c,
        temperature_f=temperature_f,
        temperature_unit=temperature_unit,
        fan=FAN_NAMES[fan_value],
        swing=bool(state[1] & 0x01),
        timer_hours=timer_hours,
        context=FRAME_CONTEXTS.get(state[7], f"unknown_0x{state[7]:02X}"),
    )


def build_state(
    *,
    power: bool,
    mode: str,
    temperature: int,
    fan: str,
    swing: bool,
    temperature_unit: str = TEMP_UNIT_CELSIUS,
    timer_hours: int | None = None,
) -> bytes:
    """Build a 9-byte Compact 9000 BTU state from supported v0.1 fields."""
    if mode not in MODE_VALUES:
        raise Compact9000BtuValidationError(f"unsupported mode '{mode}'")
    if fan not in FAN_VALUES:
        raise Compact9000BtuValidationError(f"unsupported fan '{fan}'")
    if temperature_unit not in TEMP_UNITS:
        raise Compact9000BtuValidationError(
            f"unsupported temperature_unit '{temperature_unit}'"
        )
    if temperature_unit == TEMP_UNIT_CELSIUS and not TEMP_MIN_C <= temperature <= TEMP_MAX_C:
        raise Compact9000BtuValidationError(
            f"temperature must be between {TEMP_MIN_C} and {TEMP_MAX_C} °C"
        )
    if (
        temperature_unit == TEMP_UNIT_FAHRENHEIT
        and not TEMP_MIN_F <= temperature <= TEMP_MAX_F
    ):
        raise Compact9000BtuValidationError(
            f"temperature must be between {TEMP_MIN_F} and {TEMP_MAX_F} °F"
        )
    if mode == "dry" and fan != "low":
        raise Compact9000BtuValidationError(
            "dry mode is currently captured only with fan='low'"
        )
    if mode in {"auto", "fan_only"} and fan != "high":
        raise Compact9000BtuValidationError(
            f"{mode} mode is currently captured only with fan='high'"
        )
    if timer_hours is not None and not TIMER_MIN_HOURS <= timer_hours <= TIMER_MAX_HOURS:
        raise Compact9000BtuValidationError(
            f"timer_hours must be between {TIMER_MIN_HOURS} and {TIMER_MAX_HOURS}"
        )
    if timer_hours is not None and temperature_unit == TEMP_UNIT_FAHRENHEIT:
        raise Compact9000BtuValidationError(
            "timer_hours with temperature_unit='fahrenheit' is not captured yet"
        )

    effective_power = False if mode == "off" else power
    if temperature_unit == TEMP_UNIT_FAHRENHEIT:
        temperature_c = fahrenheit_to_celsius(temperature)
        temperature_f = temperature
    else:
        temperature_c = temperature
        temperature_f = celsius_to_fahrenheit(temperature)

    temp_c = temperature_c - COMPACT_9000_BTU_MIN_TEMP_C
    temp_f = temperature_f - COMPACT_9000_BTU_MIN_TEMP_F

    state = bytearray(COMPACT_9000_BTU_STATE_LENGTH)
    state[0] = COMPACT_9000_BTU_INTRO
    state[1] = (temp_c << 4) | (0x02 if effective_power else 0) | (0x01 if swing else 0)
    if timer_hours is not None:
        state[1] |= COMPACT_9000_BTU_TIMER_SET_BIT
        state[2] = timer_hours
    else:
        state[2] = 0x00
    state[3] = temp_f & 0x1F
    state[4] = 0x00
    state[5] = 0x00
    state[6] = (FAN_VALUES[fan] << 4) | MODE_VALUES[mode]
    if timer_hours is not None:
        state[7] = COMPACT_9000_BTU_CELSIUS_TIMER_SELECTED
    elif temperature_unit == TEMP_UNIT_FAHRENHEIT:
        state[7] = COMPACT_9000_BTU_FAHRENHEIT
    else:
        state[7] = COMPACT_9000_BTU_CELSIUS_STABLE
    state[8] = calc_checksum(state)
    return bytes(state)


def build_max_cool_state(*, swing: bool = False) -> bytes:
    """Build the v0.1 max-cool convenience state.

    This is the strongest confirmed remote-sendable COOL state: 17 C, fan high,
    power on. It is not asserted to be the panel-only Super-Kuehlung mode.
    """
    return build_state(
        power=True,
        mode="cool",
        temperature=TEMP_MIN_C,
        fan="high",
        swing=swing,
    )


def encode_timings(state: bytes | bytearray) -> list[int]:
    """Encode a Compact 9000 BTU capture frame to raw mark/space timings."""
    if len(state) != COMPACT_9000_BTU_STATE_LENGTH:
        raise Compact9000BtuValidationError(
            f"expected exactly {COMPACT_9000_BTU_STATE_LENGTH} bytes, got {len(state)}"
        )

    timings: list[int] = [COMPACT_9000_BTU_HDR_MARK, -COMPACT_9000_BTU_HDR_SPACE]
    for byte in state:
        for bit_index in range(7, -1, -1):
            bit = (byte >> bit_index) & 1
            timings.append(COMPACT_9000_BTU_BIT_MARK)
            timings.append(
                -COMPACT_9000_BTU_ONE_SPACE if bit else -COMPACT_9000_BTU_ZERO_SPACE
            )
    timings.append(COMPACT_9000_BTU_BIT_MARK)
    return timings


def _matches_timing(value: int, expected: int, tolerance: float = 0.35) -> bool:
    """Return whether a measured timing roughly matches an expected duration."""
    return abs(abs(value) - expected) <= expected * tolerance


def decode_timings(timings: list[int]) -> bytes:
    """Decode raw mark/space timings into a Compact 9000 BTU state frame.

    Home Assistant receiver signals should include the full header mark. ESPHome
    debug logs often start at the header space; this decoder accepts both forms.
    """
    if len(timings) < (COMPACT_9000_BTU_BITS * 2) + 1:
        raise Compact9000BtuValidationError("not enough timings for a Compact 9000 BTU frame")

    if (
        len(timings) >= (COMPACT_9000_BTU_BITS * 2) + 3
        and _matches_timing(timings[0], COMPACT_9000_BTU_HDR_MARK)
        and _matches_timing(timings[1], COMPACT_9000_BTU_HDR_SPACE)
    ):
        bit_start = 2
    elif _matches_timing(timings[0], COMPACT_9000_BTU_HDR_SPACE):
        bit_start = 1
    else:
        raise Compact9000BtuValidationError("missing Compact 9000 BTU header")

    bit_timings = timings[bit_start : bit_start + (COMPACT_9000_BTU_BITS * 2)]
    if len(bit_timings) != COMPACT_9000_BTU_BITS * 2:
        raise Compact9000BtuValidationError("incomplete Compact 9000 BTU bit timings")

    bits: list[int] = []
    one_threshold = (COMPACT_9000_BTU_ONE_SPACE + COMPACT_9000_BTU_ZERO_SPACE) / 2
    for index in range(0, len(bit_timings), 2):
        mark = bit_timings[index]
        space = bit_timings[index + 1]
        if not _matches_timing(mark, COMPACT_9000_BTU_BIT_MARK):
            raise Compact9000BtuValidationError(
                f"invalid bit mark at bit {index // 2}: {mark}"
            )
        if not (
            _matches_timing(space, COMPACT_9000_BTU_ZERO_SPACE)
            or _matches_timing(space, COMPACT_9000_BTU_ONE_SPACE)
        ):
            raise Compact9000BtuValidationError(
                f"invalid bit space at bit {index // 2}: {space}"
            )
        bits.append(1 if abs(space) > one_threshold else 0)

    decoded = bytearray(COMPACT_9000_BTU_STATE_LENGTH)
    for byte_index in range(COMPACT_9000_BTU_STATE_LENGTH):
        value = 0
        for bit in bits[byte_index * 8 : (byte_index + 1) * 8]:
            value = (value << 1) | bit
        decoded[byte_index] = value

    state = bytes(decoded)
    decode_state(state)
    return state


async def async_send_compact_9000_btu(
    hass: HomeAssistant,
    emitter_entity_id: str,
    state: bytes,
    repeat: int = 0,
    context: Context | None = None,
) -> None:
    """Send a Compact 9000 BTU state through a Home Assistant infrared emitter."""
    from homeassistant.components import infrared

    command = Compact9000BtuCommand(state=state, repeat_count=repeat)
    await infrared.async_send_command(
        hass,
        emitter_entity_id,
        command,
        context=context,
    )
