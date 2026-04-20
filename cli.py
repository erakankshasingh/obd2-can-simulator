"""
CAN Bus Simulator - Interactive CLI
Run the simulator and see decoded OBD-II output live.
"""

# argparse: handles command-line arguments like --count, --interval, --pids
# time: used to add a delay between frames
import argparse
import time
from simulator import simulate, OBD2_PIDS, generate_obd2_response
from decoder import decode


def print_header():
    # Print a formatted table header before the data starts streaming
    print("\n" + "=" * 60)
    print("       CAN Bus Simulator & OBD-II Decoder")
    print("=" * 60)
    print(f"{'Timestamp':<12} {'PID':<6} {'Signal':<22} {'Value':<10} Unit")
    print("-" * 60)


def run(count: int, interval: float, pids: list):
    # Main loop: generate CAN frames one by one, decode them, and print each row
    print_header()
    generated = 0

    while generated < count:
        import random
        pid = random.choice(pids)           # Pick a random PID from the selected list
        frame = generate_obd2_response(pid) # Simulate a CAN frame for that PID
        if not frame:
            continue                        # Skip unsupported PIDs

        decoded = decode(frame)             # Decode the raw CAN frame into a readable value
        if decoded and decoded["value"] is not None:
            # Print timestamp (last 3 digits of Unix time), PID, signal name, value, and unit
            ts = f"{frame.timestamp % 1000:.3f}"
            print(
                f"{ts:<12} "
                f"0x{decoded['pid']:02X}   "
                f"{decoded['name']:<22} "
                f"{decoded['value']:<10} "
                f"{decoded['unit']}"
            )
        generated += 1
        time.sleep(interval)               # Wait before generating the next frame

    print("-" * 60)
    print(f"\nDone. {count} frames generated.")


def main():
    # Set up CLI argument parsing so the user can customize behavior from the terminal
    parser = argparse.ArgumentParser(description="CAN Bus Simulator & OBD-II Decoder")
    parser.add_argument("-n", "--count",    type=int,   default=20,  help="Number of frames (default: 20)")
    parser.add_argument("-i", "--interval", type=float, default=0.2, help="Interval between frames in seconds (default: 0.2)")
    parser.add_argument("-p", "--pids",     nargs="+",  type=lambda x: int(x, 16),
                        help="PIDs to simulate in hex, e.g. --pids 0x0C 0x0D")
    args = parser.parse_args()

    # Use PIDs from command line if provided, otherwise simulate all known PIDs
    pids = args.pids if args.pids else list(OBD2_PIDS.keys())

    # Show the user which PIDs are available and which ones are selected
    print("\nAvailable PIDs:")
    for pid, name in OBD2_PIDS.items():
        marker = " <-- selected" if pid in pids else ""
        print(f"  0x{pid:02X}  {name}{marker}")

    run(count=args.count, interval=args.interval, pids=pids)


# Only run main() if this file is executed directly (not imported as a module)
if __name__ == "__main__":
    main()
