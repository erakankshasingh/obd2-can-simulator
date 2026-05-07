"""
python-can Hardware Backend (Optional)

Provides real CAN hardware integration via python-can.
Falls back gracefully if python-can is not installed.

Supported interfaces (when python-can is available):
  - virtual    : Software virtual bus (no hardware needed, testing only)
  - socketcan  : Linux SocketCAN (e.g. can0, vcan0)
  - pcan       : PEAK PCAN USB adapters
  - vector     : Vector CANalyzer/CANoe interfaces
  - kvaser     : Kvaser CAN interfaces

Usage:
  backend = CANBackend(interface='virtual', channel='vcan0')
  backend.send(frame)
  frames = backend.receive(count=10)
  backend.shutdown()
"""

# Try to import python-can — if not available, fall back to simulator
try:
    import can
    PYTHON_CAN_AVAILABLE = True
except ImportError:
    PYTHON_CAN_AVAILABLE = False

from simulator import CANFrame, generate_obd2_response, OBD2_PIDS
from decoder import decode
import random
import time


class CANBackend:
    """
    Unified CAN interface — real hardware via python-can or simulated fallback.
    Automatically falls back to simulation if python-can is not installed.
    """

    def __init__(self, interface: str = "virtual", channel: str = "vcan0"):
        self.interface = interface
        self.channel = channel
        self.bus = None
        self.using_hardware = False

        if PYTHON_CAN_AVAILABLE:
            try:
                self.bus = can.interface.Bus(
                    interface=interface,
                    channel=channel
                )
                self.using_hardware = True
                print(f"[CAN Backend] Connected: interface={interface}, channel={channel}")
            except Exception as e:
                print(f"[CAN Backend] Hardware init failed ({e}) — falling back to simulator")
        else:
            print("[CAN Backend] python-can not installed — using built-in simulator")

    def send(self, frame: CANFrame) -> bool:
        """
        Send a CAN frame.
        Uses python-can if available, otherwise no-op with confirmation.
        """
        if self.using_hardware and self.bus:
            try:
                msg = can.Message(
                    arbitration_id=frame.arbitration_id,
                    data=frame.data,
                    is_extended_id=False,
                    timestamp=frame.timestamp,
                )
                self.bus.send(msg)
                return True
            except Exception as e:
                print(f"[CAN Backend] Send error: {e}")
                return False
        else:
            # Simulate a successful send
            return True

    def receive(self, count: int = 20, interval: float = 0.1,
                pids: list = None) -> list:
        """
        Receive CAN frames.
        Reads from real bus if hardware available, otherwise generates simulated frames.
        """
        if pids is None:
            pids = list(OBD2_PIDS.keys())

        frames = []

        if self.using_hardware and self.bus:
            # Read real frames from hardware
            print(f"[CAN Backend] Listening for {count} frames on {self.channel}...")
            received = 0
            timeout = count * interval * 2  # generous timeout
            start = time.time()

            while received < count and (time.time() - start) < timeout:
                msg = self.bus.recv(timeout=1.0)
                if msg:
                    frame = CANFrame(
                        arbitration_id=msg.arbitration_id,
                        dlc=msg.dlc,
                        data=bytes(msg.data),
                        timestamp=msg.timestamp,
                    )
                    frames.append(frame)
                    received += 1
        else:
            # Fall back to simulator
            for _ in range(count):
                pid = random.choice(pids)
                frame = generate_obd2_response(pid)
                if frame:
                    frames.append(frame)
                time.sleep(interval)

        return frames

    def shutdown(self):
        """Clean up hardware connection."""
        if self.bus:
            self.bus.shutdown()
            print("[CAN Backend] Connection closed.")

    @staticmethod
    def available_interfaces() -> list:
        """Return list of supported interfaces."""
        interfaces = ["virtual (simulation, no hardware required)"]
        if PYTHON_CAN_AVAILABLE:
            interfaces += [
                "socketcan (Linux SocketCAN — vcan0, can0)",
                "pcan      (PEAK PCAN USB adapter)",
                "vector    (Vector CANalyzer/CANoe)",
                "kvaser    (Kvaser CAN interfaces)",
            ]
        return interfaces