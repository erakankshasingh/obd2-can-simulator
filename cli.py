"""
CAN Bus Simulator - Interactive CLI
Run the simulator and see decoded OBD-II output live.
"""

import argparse
import time
from simulator import simulate, OBD2_PIDS, generate_obd2_response
from decoder import decode


def print_header():
    print("\n" + "=" * 60)
    print("       CAN Bus Simulator & OBD-II Decoder")
    print("=" * 60)
    print(f"{'Timestamp':<12} {'PID':<6} {'Signal':<22} {'Value':<10} Unit")
    print("-" * 60)


def run(count: int, interval: float, pids: list):
    print_header()
    generated = 0

    while generated < count:
        import random
        pid = random.choice(pids)
        frame = generate_obd2_response(pid)
        if not frame:
            continue

        decoded = decode(frame)
        if decoded and decoded["value"] is not None:
            ts = f"{frame.timestamp % 1000:.3f}"
            print(
                f"{ts:<12} "
                f"0x{decoded['pid']:02X}   "
                f"{decoded['name']:<22} "
                f"{decoded['value']:<10} "
                f"{decoded['unit']}"
            )
        generated += 1
        time.sleep(interval)

    print("-" * 60)
    print(f"\nDone. {count} frames generated.")


def main():
    parser = argparse.ArgumentParser(description="CAN Bus Simulator & OBD-II Decoder")
    parser.add_argument("-n", "--count",    type=int,   default=20,  help="Number of frames (default: 20)")
    parser.add_argument("-i", "--interval", type=float, default=0.2, help="Interval between frames in seconds (default: 0.2)")
    parser.add_argument("-p", "--pids",     nargs="+",  type=lambda x: int(x, 16),
                        help="PIDs to simulate in hex, e.g. --pids 0x0C 0x0D")
    args = parser.parse_args()

    pids = args.pids if args.pids else list(OBD2_PIDS.keys())

    print("\nAvailable PIDs:")
    for pid, name in OBD2_PIDS.items():
        marker = " <-- selected" if pid in pids else ""
        print(f"  0x{pid:02X}  {name}{marker}")

    run(count=args.count, interval=args.interval, pids=pids)


if __name__ == "__main__":
    main()
