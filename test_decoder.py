7"""
Unit tests for the OBD-II decoder.
Run with: pytest test_decoder.py -v
"""

import pytest
from simulator import CANFrame, generate_obd2_response
from decoder import decode, decode_all


# --- Helpers ---

def make_frame(pid: int, a: int, b: int = 0) -> CANFrame:
    """Build a minimal OBD-II response frame for a given PID and data bytes."""
    return CANFrame(
        arbitration_id=0x7E8,
        dlc=8,
        data=bytes([0x04, 0x41, pid, a, b, 0x00, 0x00, 0x00]),
        timestamp=0.0,
    )


# --- PID formula tests ---

def test_rpm_decoding():
    # RPM = (A*256 + B) / 4  →  A=0x1B, B=0xB0 → (27*256+176)/4 = 1788.0
    frame = make_frame(0x0C, 0x1B, 0xB0)
    result = decode(frame)
    assert result is not None
    assert result["pid"] == 0x0C
    assert result["name"] == "Engine RPM"
    assert result["unit"] == "RPM"
    assert result["value"] == (0x1B * 256 + 0xB0) / 4


def test_speed_decoding():
    # Speed = A directly  →  A=87 → 87 km/h
    frame = make_frame(0x0D, 87)
    result = decode(frame)
    assert result["pid"] == 0x0D
    assert result["value"] == 87
    assert result["unit"] == "km/h"


def test_coolant_temp_decoding():
    # Coolant = A - 40  →  A=132 → 92°C
    frame = make_frame(0x05, 132)
    result = decode(frame)
    assert result["pid"] == 0x05
    assert result["value"] == 92
    assert result["unit"] == "°C"


def test_throttle_decoding():
    # Throttle = A * 100 / 255  →  A=128 → ~50.2%
    frame = make_frame(0x11, 128)
    result = decode(frame)
    assert result["pid"] == 0x11
    assert result["value"] == round(128 * 100 / 255, 1)
    assert "%" in result["unit"]


def test_engine_load_decoding():
    # Engine load = A * 100 / 255  →  A=255 → 100%
    frame = make_frame(0x04, 255)
    result = decode(frame)
    assert result["pid"] == 0x04
    assert result["value"] == round(255 * 100 / 255, 1)


def test_intake_air_temp_decoding():
    # Intake air temp = A - 40  →  A=60 → 20°C
    frame = make_frame(0x0F, 60)
    result = decode(frame)
    assert result["pid"] == 0x0F
    assert result["value"] == 20
    assert result["unit"] == "°C"


# --- Edge cases ---

def test_unknown_pid_returns_none_value():
    frame = make_frame(0xFF, 0x00)
    result = decode(frame)
    assert result is not None
    assert result["name"] == "Unknown PID"
    assert result["value"] is None


def test_wrong_arbitration_id_ignored():
    # Not an ECU response — should be ignored
    frame = CANFrame(
        arbitration_id=0x123,
        dlc=8,
        data=bytes([0x04, 0x41, 0x0C, 0x1B, 0xB0, 0x00, 0x00, 0x00]),
        timestamp=0.0,
    )
    assert decode(frame) is None


def test_wrong_mode_ignored():
    # Mode 0x40 instead of 0x41 — should be ignored
    frame = CANFrame(
        arbitration_id=0x7E8,
        dlc=8,
        data=bytes([0x04, 0x40, 0x0C, 0x1B, 0xB0, 0x00, 0x00, 0x00]),
        timestamp=0.0,
    )
    assert decode(frame) is None


def test_short_frame_ignored():
    # Only 2 bytes — too short to be a valid OBD-II response
    frame = CANFrame(
        arbitration_id=0x7E8,
        dlc=2,
        data=bytes([0x04, 0x41]),
        timestamp=0.0,
    )
    assert decode(frame) is None


def test_decode_all_filters_unknowns():
    # Mix of valid and unknown PID frames — decode_all should only return valid ones
    frames = [
        make_frame(0x0C, 0x1B, 0xB0),  # valid RPM
        make_frame(0xFF, 0x00),          # unknown PID
        make_frame(0x0D, 87),            # valid speed
    ]
    results = decode_all(frames)
    assert len(results) == 2


# --- Simulator integration ---

def test_simulator_generates_decodable_frames():
    # Frames from the simulator should always decode cleanly
    for pid in [0x0C, 0x0D, 0x05, 0x11, 0x04, 0x0F]:
        frame = generate_obd2_response(pid)
        assert frame is not None
        result = decode(frame)
        assert result is not None
        assert result["value"] is not None