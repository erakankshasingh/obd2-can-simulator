"""
CAN Bus Frame Simulator
Generates realistic CAN frames for common OBD-II PIDs.
"""

import random
import time
import struct
from dataclasses import dataclass
from typing import Optional


# OBD-II standard PIDs (Service 01)
OBD2_PIDS = {
    0x0C: "Engine RPM",
    0x0D: "Vehicle Speed",
    0x05: "Coolant Temp",
    0x11: "Throttle Position",
    0x04: "Engine Load",
    0x0F: "Intake Air Temp",
}


@dataclass
class CANFrame:
    arbitration_id: int   # 11-bit standard ID
    dlc: int              # Data Length Code (0-8)
    data: bytes
    timestamp: float

    def __str__(self):
        data_hex = " ".join(f"{b:02X}" for b in self.data)
        return (
            f"[{self.timestamp:.3f}] "
            f"ID: 0x{self.arbitration_id:03X}  "
            f"DLC: {self.dlc}  "
            f"Data: {data_hex}"
        )


def generate_obd2_response(pid: int) -> Optional[CANFrame]:
    """Generate a realistic OBD-II response frame for a given PID."""
    if pid == 0x0C:  # Engine RPM: range 600-6000
        rpm = random.randint(600, 6000)
        raw = rpm * 4  # OBD-II: RPM = (A*256 + B) / 4
        a = (raw >> 8) & 0xFF
        b = raw & 0xFF
        data = bytes([0x04, 0x41, pid, a, b, 0x00, 0x00, 0x00])

    elif pid == 0x0D:  # Vehicle Speed: 0-200 km/h
        speed = random.randint(0, 200)
        data = bytes([0x03, 0x41, pid, speed, 0x00, 0x00, 0x00, 0x00])

    elif pid == 0x05:  # Coolant Temp: 70-105 C (raw = C + 40)
        temp = random.randint(70, 105)
        data = bytes([0x03, 0x41, pid, temp + 40, 0x00, 0x00, 0x00, 0x00])

    elif pid == 0x11:  # Throttle position: 0-100%
        throttle = random.randint(0, 100)
        raw = int(throttle * 255 / 100)
        data = bytes([0x03, 0x41, pid, raw, 0x00, 0x00, 0x00, 0x00])

    elif pid == 0x04:  # Engine Load: 0-100%
        load = random.randint(10, 90)
        raw = int(load * 255 / 100)
        data = bytes([0x03, 0x41, pid, raw, 0x00, 0x00, 0x00, 0x00])

    elif pid == 0x0F:  # Intake air temp: 10-60 C
        temp = random.randint(10, 60)
        data = bytes([0x03, 0x41, pid, temp + 40, 0x00, 0x00, 0x00, 0x00])

    else:
        return None

    return CANFrame(
        arbitration_id=0x7E8,  # Standard OBD-II response ID
        dlc=8,
        data=data,
        timestamp=time.time(),
    )


def simulate(pids: Optional[list] = None, count: int = 20, interval: float = 0.1):
    """
    Simulate a stream of CAN frames.

    Args:
        pids: List of OBD-II PIDs to simulate. Defaults to all known PIDs.
        count: Number of frames to generate.
        interval: Seconds between frames.
    """
    if pids is None:
        pids = list(OBD2_PIDS.keys())

    frames = []
    for _ in range(count):
        pid = random.choice(pids)
        frame = generate_obd2_response(pid)
        if frame:
            frames.append(frame)
        time.sleep(interval)

    return frames


if __name__ == "__main__":
    print("=== CAN Bus Simulator ===\n")
    frames = simulate(count=10, interval=0.05)
    for frame in frames:
        print(frame)
