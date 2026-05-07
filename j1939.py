"""
J1939 PGN Simulator & Decoder

Simulates and decodes J1939 CAN frames used in heavy commercial vehicles.
J1939 uses 29-bit extended CAN IDs and broadcasts data periodically from ECUs.

Frame structure (29-bit arbitration ID):
  Bits 28-26: Priority (3 bits)
  Bits 25-24: Reserved + Data Page (2 bits)
  Bits 23-16: PGN high byte (8 bits)
  Bits 15-8:  PGN low byte (8 bits)
  Bits 7-0:   Source address (8 bits)
"""

import random
import time
from dataclasses import dataclass
from typing import Optional


# J1939 source addresses (which ECU is broadcasting)
SA_ENGINE   = 0x00  # Engine controller
SA_TRANSMISSION = 0x03  # Transmission controller
SA_BRAKE    = 0x0B  # Brake controller


@dataclass
class J1939Frame:
    """Represents a single J1939 CAN message."""
    pgn: int            # Parameter Group Number
    source_address: int # Which ECU sent this
    priority: int       # 0-7, lower = higher priority
    data: bytes         # 8 bytes of payload
    timestamp: float

    def __str__(self):
        data_hex = " ".join(f"{b:02X}" for b in self.data)
        return (
            f"[{self.timestamp:.3f}] "
            f"PGN: 0x{self.pgn:04X} "
            f"SA: 0x{self.source_address:02X} "
            f"Priority: {self.priority} "
            f"Data: {data_hex}"
        )

    @property
    def arbitration_id(self) -> int:
        """Reconstruct the 29-bit CAN arbitration ID from PGN components."""
        return (self.priority << 26) | (self.pgn << 8) | self.source_address


# PGN_MAP: each entry maps PGN → (human name, list of signal decoders)
# Each signal decoder is a dict with: name, unit, formula(data_bytes)
PGN_MAP = {
    0xF004: {
        "name": "Electronic Engine Controller 1 (EEC1)",
        "source": SA_ENGINE,
        "signals": [
            {
                "name": "Engine RPM",
                "unit": "RPM",
                "formula": lambda d: ((d[3] | (d[4] << 8)) * 0.125),  # bytes 4-5, resolution 0.125 RPM/bit
            },
            {
                "name": "Driver Demand Engine Torque",
                "unit": "%",
                "formula": lambda d: d[1] - 125,  # byte 2, offset -125%
            },
        ],
    },
    0xFEF1: {
        "name": "Cruise Control / Vehicle Speed (CCVS)",
        "source": SA_ENGINE,
        "signals": [
            {
                "name": "Vehicle Speed",
                "unit": "km/h",
                "formula": lambda d: ((d[1] | (d[2] << 8)) * 0.00390625),  # resolution 1/256 km/h per bit
            },
        ],
    },
    0xFEEE: {
        "name": "Engine Temperature 1 (ET1)",
        "source": SA_ENGINE,
        "signals": [
            {
                "name": "Engine Coolant Temperature",
                "unit": "°C",
                "formula": lambda d: d[0] - 40,  # byte 1, offset -40°C
            },
            {
                "name": "Engine Oil Temperature",
                "unit": "°C",
                "formula": lambda d: ((d[2] | (d[3] << 8)) * 0.03125) - 273,  # bytes 3-4, Kelvin offset
            },
        ],
    },
    0xFEF2: {
        "name": "Fuel Economy (LFE)",
        "source": SA_ENGINE,
        "signals": [
            {
                "name": "Engine Fuel Rate",
                "unit": "L/h",
                "formula": lambda d: ((d[0] | (d[1] << 8)) * 0.05),  # resolution 0.05 L/h per bit
            },
        ],
    },
    0xFECA: {
        "name": "DM1 — Active Diagnostics",
        "source": SA_ENGINE,
        "signals": [
            {
                "name": "Malfunction Indicator Lamp",
                "unit": "",
                "formula": lambda d: "ON" if (d[0] & 0xC0) >> 6 == 1 else "OFF",
            },
            {
                "name": "Amber Warning Lamp",
                "unit": "",
                "formula": lambda d: "ON" if (d[0] & 0x30) >> 4 == 1 else "OFF",
            },
        ],
    },
}


def generate_j1939_frame(pgn: int) -> Optional[J1939Frame]:
    """Generate a realistic J1939 broadcast frame for a given PGN."""

    if pgn == 0xF004:  # EEC1 — Engine RPM + torque
        rpm = random.randint(600, 2200)  # truck engine range
        raw_rpm = int(rpm / 0.125)
        torque = random.randint(0, 100) + 125  # offset +125
        data = bytes([
            0xFF,                        # byte 0: engine torque mode (not used)
            torque,                      # byte 1: driver demand torque
            0xFF,                        # byte 2: actual torque (not simulated)
            raw_rpm & 0xFF,              # byte 3: RPM low byte
            (raw_rpm >> 8) & 0xFF,       # byte 4: RPM high byte
            0xFF, 0xFF, 0xFF             # bytes 5-7: unused
        ])

    elif pgn == 0xFEF1:  # CCVS — Vehicle speed
        speed = random.randint(0, 90)   # truck speed range km/h
        raw_speed = int(speed / 0.00390625)
        data = bytes([
            0xFF,
            raw_speed & 0xFF,
            (raw_speed >> 8) & 0xFF,
            0xFF, 0xFF, 0xFF, 0xFF, 0xFF
        ])

    elif pgn == 0xFEEE:  # ET1 — Temperatures
        coolant = random.randint(70, 105) + 40   # offset +40
        oil_k = random.randint(80, 120) + 273    # Kelvin
        raw_oil = int(oil_k / 0.03125)
        data = bytes([
            coolant,
            0xFF,
            raw_oil & 0xFF,
            (raw_oil >> 8) & 0xFF,
            0xFF, 0xFF, 0xFF, 0xFF
        ])

    elif pgn == 0xFEF2:  # LFE — Fuel rate
        fuel_rate = random.uniform(5.0, 40.0)
        raw_fuel = int(fuel_rate / 0.05)
        data = bytes([
            raw_fuel & 0xFF,
            (raw_fuel >> 8) & 0xFF,
            0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF
        ])

    elif pgn == 0xFECA:  # DM1 — Diagnostics
        # Randomly simulate a warning lamp being on
        mil = random.choice([0, 1])
        awl = random.choice([0, 1])
        lamp_byte = (mil << 6) | (awl << 4)
        data = bytes([lamp_byte, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])

    else:
        return None

    pgn_info = PGN_MAP[pgn]
    return J1939Frame(
        pgn=pgn,
        source_address=pgn_info["source"],
        priority=3,
        data=data,
        timestamp=time.time(),
    )


def decode_j1939(frame: J1939Frame) -> Optional[dict]:
    """
    Decode a J1939 frame into human-readable signals.
    Returns dict with pgn, name, and list of decoded signals.
    """
    if frame.pgn not in PGN_MAP:
        return None

    pgn_info = PGN_MAP[frame.pgn]
    decoded_signals = []

    for signal in pgn_info["signals"]:
        try:
            value = signal["formula"](frame.data)
            decoded_signals.append({
                "name":  signal["name"],
                "value": value if isinstance(value, str) else round(value, 2),
                "unit":  signal["unit"],
            })
        except (IndexError, ZeroDivisionError):
            continue

    return {
        "pgn":     frame.pgn,
        "name":    pgn_info["name"],
        "signals": decoded_signals,
    }


def simulate_j1939(pgns: Optional[list] = None, count: int = 20, interval: float = 0.1) -> list:
    """Simulate a stream of J1939 frames."""
    if pgns is None:
        pgns = list(PGN_MAP.keys())

    frames = []
    for _ in range(count):
        pgn = random.choice(pgns)
        frame = generate_j1939_frame(pgn)
        if frame:
            frames.append(frame)
        time.sleep(interval)
    return frames