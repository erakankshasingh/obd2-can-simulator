"""
CAN Frame CSV Logger & Replayer

Logs decoded OBD-II frames to CSV for offline analysis.
Replays saved CSV logs back as CANFrame objects.
"""

import csv
import time
from simulator import CANFrame


CSV_HEADER = ["timestamp", "arbitration_id", "dlc", "data_hex", "pid", "signal", "value", "unit"]


def log_to_csv(frames_decoded: list, filepath: str = "can_log.csv") -> None:
    """
    Write decoded CAN frames to a CSV file.

    Args:
        frames_decoded: List of (CANFrame, decoded_dict) tuples from decoder.decode_all()
        filepath: Output CSV file path
    """
    with open(filepath, mode="w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        writer.writeheader()
        for frame, decoded in frames_decoded:
            data_hex = " ".join(f"{b:02X}" for b in frame.data)
            writer.writerow({
                "timestamp":       round(frame.timestamp, 3),
                "arbitration_id":  f"0x{frame.arbitration_id:03X}",
                "dlc":             frame.dlc,
                "data_hex":        data_hex,
                "pid":             f"0x{decoded['pid']:02X}",
                "signal":          decoded["name"],
                "value":           decoded["value"],
                "unit":            decoded["unit"],
            })
    print(f"Logged {len(frames_decoded)} frames to {filepath}")


def replay_from_csv(filepath: str, interval: float = 0.0) -> list:
    """
    Replay CAN frames from a previously saved CSV log.

    Args:
        filepath: Path to the CSV file
        interval: Optional delay between frames (seconds). 0 = instant replay.

    Returns:
        List of CANFrame objects reconstructed from the log.
    """
    frames = []
    try:
        with open(filepath, mode="r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Reconstruct raw bytes from hex string
                data_bytes = bytes(int(b, 16) for b in row["data_hex"].split())
                frame = CANFrame(
                    arbitration_id=int(row["arbitration_id"], 16),
                    dlc=int(row["dlc"]),
                    data=data_bytes,
                    timestamp=float(row["timestamp"]),
                )
                frames.append(frame)
                if interval > 0:
                    time.sleep(interval)
    except FileNotFoundError:
        print(f"Error: Log file '{filepath}' not found.")
        return []

    print(f"Replayed {len(frames)} frames from {filepath}")
    return frames