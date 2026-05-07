"""
CAN Bus Simulator - Interactive CLI
Run the simulator and see decoded OBD-II output live.
"""

import argparse
import random
import time

from simulator import OBD2_PIDS, generate_obd2_response
from decoder import decode, decode_all
from logger import log_to_csv, replay_from_csv
from j1939 import simulate_j1939, decode_j1939, PGN_MAP


def print_header():
    print("\n" + "=" * 60)
    print("       CAN Bus Simulator & OBD-II Decoder")
    print("=" * 60)
    print(f"{'Timestamp':<12} {'PID':<6} {'Signal':<22} {'Value':<10} Unit")
    print("-" * 60)


def print_row(frame, decoded):
    ts = f"{frame.timestamp % 1000:.3f}"
    print(
        f"{ts:<12} "
        f"0x{decoded['pid']:02X}   "
        f"{decoded['name']:<22} "
        f"{decoded['value']:<10} "
        f"{decoded['unit']}"
    )


def run(count: int, interval: float, pids: list, log_file: str = None):
    """Generate and decode CAN frames live, optionally saving to CSV."""
    print_header()
    frames_decoded = []
    generated = 0

    while generated < count:
        pid = random.choice(pids)
        frame = generate_obd2_response(pid)
        if not frame:
            continue

        decoded = decode(frame)
        if decoded and decoded["value"] is not None:
            print_row(frame, decoded)
            frames_decoded.append((frame, decoded))

        generated += 1
        time.sleep(interval)

    print("-" * 60)
    print(f"\nDone. {count} frames generated.")

    if log_file:
        log_to_csv(frames_decoded, log_file)


def run_replay(filepath: str, interval: float):
    """Replay frames from a saved CSV log and decode them."""
    frames = replay_from_csv(filepath, interval=0)  # load all at once
    if not frames:
        return

    frames_decoded = decode_all(frames)
    if not frames_decoded:
        print("No decodable frames found in log.")
        return

    print_header()
    for frame, decoded in frames_decoded:
        print_row(frame, decoded)
        time.sleep(interval)

    print("-" * 60)
    print(f"\nDone. {len(frames_decoded)} frames replayed from {filepath}")


def main():
    parser = argparse.ArgumentParser(description="CAN Bus Simulator & OBD-II Decoder")

    parser.add_argument("-n", "--count",    type=int,   default=20,  help="Number of frames (default: 20)")
    parser.add_argument("-i", "--interval", type=float, default=0.2, help="Interval between frames in seconds (default: 0.2)")
    parser.add_argument("-p", "--pids",     nargs="+",  type=lambda x: int(x, 16),
                        help="PIDs to simulate in hex, e.g. --pids 0x0C 0x0D")
    parser.add_argument("-l", "--log",      type=str,   default=None,
                        help="Save output to CSV file, e.g. --log can_log.csv")
    parser.add_argument("-r", "--replay",   type=str,   default=None,
                        help="Replay frames from a CSV log file, e.g. --replay can_log.csv")
    parser.add_argument("--protocol", type=str, default="obd2", 
                        choices=["obd2", "j1939"], 
                        help="Protocol to simulate: obd2 (default) or j1939")
    parser.add_argument("--hardware",   action="store_true",
                    help="Use python-can hardware backend instead of simulator")
    parser.add_argument("--interface",  type=str, default="virtual",
                    help="python-can interface type (default: virtual)")
    parser.add_argument("--channel",    type=str, default="vcan0",
                    help="CAN channel/device (default: vcan0)")

    args = parser.parse_args()

    # --- REPLAY MODE ---
    if args.replay:
        run_replay(args.replay, args.interval)
        return
    
    # --- J1939 MODE ---   <-- ADD THE BLOCK HERE
    if args.protocol == "j1939":
        print("\nAvailable J1939 PGNs:")
        for pgn, info in PGN_MAP.items():
            print(f"  0x{pgn:04X}  {info['name']}")
        frames = simulate_j1939(count=args.count, interval=args.interval)
        print("\n" + "=" * 70)
        print("       J1939 CAN Bus Simulator")
        print("=" * 70)
        for frame in frames:
            decoded = decode_j1939(frame)
            if decoded:
                print(f"\n[{frame.timestamp % 1000:.3f}] PGN 0x{frame.pgn:04X} — {decoded['name']}")
                for sig in decoded["signals"]:
                    unit = f" {sig['unit']}" if sig["unit"] else ""
                    print(f"    {sig['name']:<35} {sig['value']}{unit}")
        print("\n" + "=" * 70)
        print(f"Done. {len(frames)} J1939 frames generated.")
        return
    
    # Define pids early — needed by hardware and OBD-II modes
    pids = args.pids if args.pids else list(OBD2_PIDS.keys())

    # --- HARDWARE BACKEND MODE ---
    if args.hardware:
        from can_backend import CANBackend
        backend = CANBackend(interface=args.interface, channel=args.channel)
        frames = backend.receive(count=args.count, interval=args.interval, pids=pids)
        frames_decoded = decode_all(frames)
        print_header()
        for frame, decoded in frames_decoded:
            print_row(frame, decoded)
        backend.shutdown()
        if args.log:
            log_to_csv(frames_decoded, args.log)
        return

    # --- OBD-II MODE (existing code) ---
    print("\nAvailable PIDs:")
    for pid, name in OBD2_PIDS.items():
        marker = " <-- selected" if pid in pids else ""
        print(f"  0x{pid:02X}  {name}{marker}")

    run(count=args.count, interval=args.interval, pids=pids, log_file=args.log)



if __name__ == "__main__":
    main()