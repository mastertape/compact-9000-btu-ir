"""Tests for Compact 9000 BTU IR capture helpers."""

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "custom_components.compact_9000_btu_ir"
PACKAGE_PATH = ROOT / "custom_components" / "compact_9000_btu_ir"

package = types.ModuleType(PACKAGE_NAME)
package.__path__ = [str(PACKAGE_PATH)]
sys.modules.setdefault(PACKAGE_NAME, package)

infrared_protocols = types.ModuleType("infrared_protocols")
commands = types.ModuleType("infrared_protocols.commands")


class Command:
    """Minimal test stub for infrared_protocols.commands.Command."""

    def __init__(self, *, modulation: int, repeat_count: int = 0) -> None:
        self.modulation = modulation
        self.repeat_count = repeat_count


commands.Command = Command
sys.modules.setdefault("infrared_protocols", infrared_protocols)
sys.modules.setdefault("infrared_protocols.commands", commands)

const_spec = importlib.util.spec_from_file_location(
    f"{PACKAGE_NAME}.const", PACKAGE_PATH / "const.py"
)
const = importlib.util.module_from_spec(const_spec)
sys.modules[f"{PACKAGE_NAME}.const"] = const
const_spec.loader.exec_module(const)

ir_spec = importlib.util.spec_from_file_location(f"{PACKAGE_NAME}.ir", PACKAGE_PATH / "ir.py")
ir = importlib.util.module_from_spec(ir_spec)
sys.modules[f"{PACKAGE_NAME}.ir"] = ir
ir_spec.loader.exec_module(ir)

Compact9000BtuCommand = ir.Compact9000BtuCommand
Compact9000BtuValidationError = ir.Compact9000BtuValidationError
build_max_cool_state = ir.build_max_cool_state
build_state = ir.build_state
calc_checksum = ir.calc_checksum
decode_state = ir.decode_state
decode_timings = ir.decode_timings
encode_timings = ir.encode_timings
format_state = ir.format_state
parse_hex_code = ir.parse_hex_code
valid_checksum = ir.valid_checksum


def test_parse_hex_accepts_known_frame() -> None:
    """Known stable frame parses and validates."""
    state = parse_hex_code("55 D2 00 19 00 00 31 80 F1")
    assert state == bytes.fromhex("55 D2 00 19 00 00 31 80 F1")
    assert valid_checksum(state)
    assert calc_checksum(state) == 0xF1


def test_parse_hex_rejects_bad_checksum() -> None:
    """Checksum mismatches are rejected."""
    try:
        parse_hex_code("55 D2 00 19 00 00 31 80 F0")
    except Compact9000BtuValidationError as err:
        assert "checksum mismatch" in str(err)
    else:
        raise AssertionError("bad checksum was accepted")


def test_build_state_matches_stable_capture() -> None:
    """The v0.1 state builder reproduces the confirmed 17 C high fan capture."""
    state = build_state(
        power=True,
        mode="cool",
        temperature=17,
        fan="high",
        swing=False,
    )
    assert format_state(state) == "55 12 00 04 00 00 31 88 24"


def test_build_max_cool_state_matches_confirmed_sendable_state() -> None:
    """Max cool is the strongest confirmed remote-sendable COOL state."""
    assert format_state(build_max_cool_state()) == "55 12 00 04 00 00 31 88 24"
    assert format_state(build_max_cool_state(swing=True)) == "55 13 00 04 00 00 31 88 25"


def test_decode_state_decodes_confirmed_state() -> None:
    """Known frames decode into semantic fields for future receiver sync."""
    decoded = decode_state(bytes.fromhex("55 12 00 04 00 00 31 88 24"))

    assert decoded.power is True
    assert decoded.mode == "cool"
    assert decoded.temperature_c == 17
    assert decoded.temperature_f == 63
    assert decoded.temperature_unit == "celsius"
    assert decoded.fan == "high"
    assert decoded.swing is False
    assert decoded.timer_hours is None
    assert decoded.context == "celsius_stable"


def test_decode_state_decodes_fahrenheit_and_timer_contexts() -> None:
    """Byte-7 context variants are preserved while decoding fields."""
    fahrenheit = decode_state(bytes.fromhex("55 12 00 03 00 00 31 40 DB"))
    assert fahrenheit.temperature_unit == "fahrenheit"
    assert fahrenheit.temperature_f == 62
    assert fahrenheit.context == "fahrenheit"

    timer = decode_state(bytes.fromhex("55 1A 18 04 00 00 31 82 3E"))
    assert timer.timer_hours == 24
    assert timer.context == "timer_selected"


def test_build_state_matches_fahrenheit_captures() -> None:
    """Fahrenheit states match the captured 86-62 F COOL run."""
    expected = {
        86: "55 E2 00 1B 00 00 31 40 C3",
        85: "55 D2 00 1A 00 00 31 40 B2",
        84: "55 D2 00 19 00 00 31 40 B1",
        83: "55 C2 00 18 00 00 31 40 A0",
        82: "55 C2 00 17 00 00 31 40 9F",
        81: "55 B2 00 16 00 00 31 40 8E",
        80: "55 B2 00 15 00 00 31 40 8D",
        79: "55 A2 00 14 00 00 31 40 7C",
        78: "55 A2 00 13 00 00 31 40 7B",
        77: "55 92 00 12 00 00 31 40 6A",
        76: "55 82 00 11 00 00 31 40 59",
        75: "55 82 00 10 00 00 31 40 58",
        74: "55 72 00 0F 00 00 31 40 47",
        73: "55 72 00 0E 00 00 31 40 46",
        72: "55 62 00 0D 00 00 31 40 35",
        71: "55 62 00 0C 00 00 31 40 34",
        70: "55 52 00 0B 00 00 31 40 23",
        69: "55 52 00 0A 00 00 31 40 22",
        68: "55 42 00 09 00 00 31 40 11",
        67: "55 32 00 08 00 00 31 40 00",
        66: "55 32 00 07 00 00 31 40 FF",
        65: "55 22 00 06 00 00 31 40 EE",
        64: "55 22 00 05 00 00 31 40 ED",
        63: "55 12 00 04 00 00 31 40 DC",
        62: "55 12 00 03 00 00 31 40 DB",
    }
    for temperature, frame in expected.items():
        assert (
            format_state(
                build_state(
                    power=True,
                    mode="cool",
                    temperature=temperature,
                    temperature_unit="fahrenheit",
                    fan="high",
                    swing=False,
                )
            )
            == frame
        )


def test_build_state_rejects_out_of_range_fahrenheit() -> None:
    """Fahrenheit mode supports the captured 62-86 F range."""
    try:
        build_state(
            power=True,
            mode="cool",
            temperature=61,
            temperature_unit="fahrenheit",
            fan="high",
            swing=False,
        )
    except Compact9000BtuValidationError as err:
        assert "temperature must be between 62 and 86 °F" in str(err)
    else:
        raise AssertionError("out-of-range Fahrenheit temperature was accepted")


def test_build_state_rejects_below_manual_cool_range() -> None:
    """The Compact 9000 BTU manual documents COOL setpoints as 17-30 C."""
    try:
        build_state(
            power=True,
            mode="cool",
            temperature=16,
            fan="high",
            swing=False,
        )
    except Compact9000BtuValidationError as err:
        assert "temperature must be between 17 and 30" in str(err)
    else:
        raise AssertionError("16 C was accepted for Compact 9000 BTU send_state")


def test_build_state_matches_fan_and_swing_captures() -> None:
    """Fan and swing bits match the stable captures."""
    assert (
        format_state(
            build_state(
                power=True,
                mode="cool",
                temperature=29,
                fan="low",
                swing=False,
            )
        )
        == "55 D2 00 19 00 00 11 88 D9"
    )
    assert (
        format_state(
            build_state(
                power=True,
                mode="cool",
                temperature=29,
                fan="mid",
                swing=False,
            )
        )
        == "55 D2 00 19 00 00 21 88 E9"
    )
    assert (
        format_state(
            build_state(
                power=True,
                mode="cool",
                temperature=29,
                fan="high",
                swing=True,
            )
        )
        == "55 D3 00 19 00 00 31 88 FA"
    )


def test_build_state_matches_mode_captures() -> None:
    """Mode low bits match the captured Compact 9000 BTU MODE cycle."""
    assert (
        format_state(
            build_state(
                power=True,
                mode="fan_only",
                temperature=17,
                fan="high",
                swing=False,
            )
        )
        == "55 12 00 04 00 00 33 88 26"
    )
    assert (
        format_state(
            build_state(
                power=True,
                mode="dry",
                temperature=17,
                fan="low",
                swing=False,
            )
        )
        == "55 12 00 04 00 00 12 88 05"
    )
    assert (
        format_state(
            build_state(
                power=True,
                mode="auto",
                temperature=17,
                fan="high",
                swing=False,
            )
        )
        == "55 12 00 04 00 00 30 88 23"
    )


def test_build_state_rejects_uncaptured_mode_fan_combinations() -> None:
    """Avoid generating mode/fan combinations not yet seen in captures."""
    try:
        build_state(
            power=True,
            mode="dry",
            temperature=17,
            fan="high",
            swing=False,
        )
    except Compact9000BtuValidationError as err:
        assert "dry mode" in str(err)
    else:
        raise AssertionError("uncaptured dry fan setting was accepted")

    try:
        build_state(
            power=True,
            mode="fan_only",
            temperature=17,
            fan="low",
            swing=False,
        )
    except Compact9000BtuValidationError as err:
        assert "fan_only mode" in str(err)
    else:
        raise AssertionError("uncaptured fan_only fan setting was accepted")


def test_build_state_matches_timer_captures() -> None:
    """Timer fields match the captured selected-hour frames."""
    expected = {
        0: "55 1A 00 04 00 00 31 82 26",
        1: "55 1A 01 04 00 00 31 82 27",
        2: "55 1A 02 04 00 00 31 82 28",
        3: "55 1A 03 04 00 00 31 82 29",
        4: "55 1A 04 04 00 00 31 82 2A",
        5: "55 1A 05 04 00 00 31 82 2B",
        6: "55 1A 06 04 00 00 31 82 2C",
        7: "55 1A 07 04 00 00 31 82 2D",
        8: "55 1A 08 04 00 00 31 82 2E",
        9: "55 1A 09 04 00 00 31 82 2F",
        10: "55 1A 0A 04 00 00 31 82 30",
        11: "55 1A 0B 04 00 00 31 82 31",
        12: "55 1A 0C 04 00 00 31 82 32",
        13: "55 1A 0D 04 00 00 31 82 33",
        14: "55 1A 0E 04 00 00 31 82 34",
        15: "55 1A 0F 04 00 00 31 82 35",
        16: "55 1A 10 04 00 00 31 82 36",
        17: "55 1A 11 04 00 00 31 82 37",
        18: "55 1A 12 04 00 00 31 82 38",
        19: "55 1A 13 04 00 00 31 82 39",
        20: "55 1A 14 04 00 00 31 82 3A",
        21: "55 1A 15 04 00 00 31 82 3B",
        22: "55 1A 16 04 00 00 31 82 3C",
        23: "55 1A 17 04 00 00 31 82 3D",
        24: "55 1A 18 04 00 00 31 82 3E",
    }
    for timer_hours, frame in expected.items():
        assert (
            format_state(
                build_state(
                    power=True,
                    mode="cool",
                    temperature=17,
                    fan="high",
                    swing=False,
                    timer_hours=timer_hours,
                )
            )
            == frame
        )


def test_build_state_rejects_out_of_range_timer_hour() -> None:
    """Timer supports the captured 0-24 hour range."""
    try:
        build_state(
            power=True,
            mode="cool",
            temperature=17,
            fan="high",
            swing=False,
            timer_hours=25,
        )
    except Compact9000BtuValidationError as err:
        assert "timer_hours must be between 0 and 24" in str(err)
    else:
        raise AssertionError("out-of-range timer hour was accepted")


def test_build_state_rejects_fahrenheit_timer_combination() -> None:
    """Fahrenheit and timer have not been captured together yet."""
    try:
        build_state(
            power=True,
            mode="cool",
            temperature=62,
            temperature_unit="fahrenheit",
            fan="high",
            swing=False,
            timer_hours=1,
        )
    except Compact9000BtuValidationError as err:
        assert "not captured yet" in str(err)
    else:
        raise AssertionError("uncaptured Fahrenheit timer combination was accepted")


def test_build_state_preserves_timer_with_other_captured_modes() -> None:
    """Timer bit composes with captured mode fields."""
    assert (
        format_state(
            build_state(
                power=True,
                mode="cool",
                temperature=17,
                fan="high",
                swing=False,
                timer_hours=18,
            )
        )
        == "55 1A 12 04 00 00 31 82 38"
    )


def test_encode_timings_uses_capture_msb_first() -> None:
    """Timing generation follows the observed Compact 9000 BTU MSB-first captures."""
    state = bytes.fromhex("55 D2 00 19 00 00 31 80 F1")
    timings = encode_timings(state)

    assert timings[:2] == [12000, -5130]
    assert timings[2:18] == [
        550,
        -500,
        550,
        -1950,
        550,
        -500,
        550,
        -1950,
        550,
        -500,
        550,
        -1950,
        550,
        -500,
        550,
        -1950,
    ]
    assert timings[-1] == 550
    assert len(timings) == 147


def test_decode_timings_accepts_full_and_receiver_log_frames() -> None:
    """Raw timing decoder accepts HA-style full frames and ESPHome log frames."""
    state = bytes.fromhex("55 12 00 04 00 00 31 88 24")
    timings = encode_timings(state)

    assert decode_timings(timings) == state
    assert decode_timings(timings[1:]) == state


def test_command_repeat_replays_full_frame_after_gap() -> None:
    """Repeat appends a full second frame after the observed message gap."""
    state = bytes.fromhex("55 D2 00 19 00 00 31 80 F1")
    frame = encode_timings(state)
    timings = Compact9000BtuCommand(state=state, repeat_count=1).get_raw_timings()

    assert timings[: len(frame)] == frame
    assert timings[len(frame)] == -100000
    assert timings[len(frame) + 1 :] == frame
