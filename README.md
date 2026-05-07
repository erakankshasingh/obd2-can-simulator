# CAN Bus Simulator & OBD-II Decoder

A Python-based CAN bus frame simulator and OBD-II decoder for automotive signal analysis — no hardware required.

Simulates realistic ECU responses for standard OBD-II PIDs (Service 01) and decodes them into human-readable signal values.

---

## Features

- Generates CAN frames with realistic OBD-II encoded data
- Decodes 6 standard PIDs: RPM, Speed, Coolant Temp, Throttle, Engine Load, Intake Air Temp
- J1939 PGN support for heavy trucks and commercial vehicles (EEC1, CCVS, ET1, LFE, DM1)
- Live terminal output with configurable frame count and interval
- Filter by specific PIDs via CLI flags
- Log decoded frames to CSV for offline analysis
- Replay saved CAN logs through the decoder
- 12 unit tests covering all PIDs, edge cases, and simulator integration
- Pure Python — no external dependencies (pytest for tests only)

---

## Project Structure

```
can-simulator/
├── simulator.py      # CAN frame generator (OBD-II encoded data)
├── decoder.py        # OBD-II PID decoder
├── j1939.py          # J1939 PGN simulator and decoder
├── logger.py         # CSV logger and replayer
├── cli.py            # Interactive terminal interface
├── test_decoder.py   # Unit tests (pytest)
└── README.md
```

---

## Quick Start

```bash
# Run with defaults (20 frames, all OBD-II PIDs)
python3 cli.py

# Custom: 10 frames, fast interval, RPM and Speed only
python3 cli.py --count 10 --interval 0.1 --pids 0x0C 0x0D

# Run in J1939 mode (heavy truck protocol)
python3 cli.py --protocol j1939 --count 10

# Save frames to CSV log
python3 cli.py --count 20 --log can_log.csv

# Replay a saved log
python3 cli.py --replay can_log.csv

# Replay with custom interval
python3 cli.py --replay can_log.csv --interval 0.5

# Run J1939 mode faster
python3 cli.py --protocol j1939 --count 20 --interval 0.05

# Save J1939 session to CSV
python3 cli.py --protocol j1939 --count 10 --log j1939_log.csv
```

### Example Output

```
============================================================
       CAN Bus Simulator & OBD-II Decoder
============================================================
Timestamp    PID    Signal                 Value      Unit
------------------------------------------------------------
123.045      0x0C   Engine RPM             2750.0     RPM
123.247      0x0D   Vehicle Speed          87         km/h
123.449      0x05   Coolant Temp           92         °C
123.651      0x11   Throttle Position      34.5       %
------------------------------------------------------------
Done. 10 frames generated.
```

---

## Supported OBD-II PIDs

| PID  | Signal            | Unit  | Formula                    |
|------|-------------------|-------|----------------------------|
| 0x0C | Engine RPM        | RPM   | (A×256 + B) / 4            |
| 0x0D | Vehicle Speed     | km/h  | A                          |
| 0x05 | Coolant Temp      | °C    | A − 40                     |
| 0x11 | Throttle Position | %     | A × 100 / 255              |
| 0x04 | Engine Load       | %     | A × 100 / 255              |
| 0x0F | Intake Air Temp   | °C    | A − 40                     |

---

## Supported J1939 PGNs

| PGN    | Name                                      | Key Signals                        |
|--------|-------------------------------------------|------------------------------------|
| 0xF004 | Electronic Engine Controller 1 (EEC1)    | Engine RPM, Driver Demand Torque   |
| 0xFEF1 | Cruise Control / Vehicle Speed (CCVS)    | Vehicle Speed                      |
| 0xFEEE | Engine Temperature 1 (ET1)               | Coolant Temp, Oil Temp             |
| 0xFEF2 | Fuel Economy (LFE)                        | Engine Fuel Rate                   |
| 0xFECA | DM1 — Active Diagnostics                 | MIL Status, Amber Warning Lamp     |

---

## Running Tests

```bash
pip install pytest
pytest test_decoder.py -v
```

12 tests covering all 6 OBD-II PID formulas, edge cases (unknown PID, wrong arbitration ID, wrong mode, short frames), and simulator integration.

---


## Background

OBD-II (On-Board Diagnostics II) is the standard diagnostic protocol used in all cars sold in the US after 1996 and in Europe after 2001. ECUs respond to PID requests over CAN bus at arbitration ID `0x7E8`. This project simulates those responses without requiring a vehicle or CAN interface hardware.


J1939 is the heavy-duty vehicle standard built on top of CAN, used in trucks, buses, and construction equipment. It uses 29-bit extended CAN IDs and a broadcast-based communication model where ECUs periodically transmit Parameter Group Numbers (PGNs).

---

## Roadmap

- [x] Add J1939 PGN support (heavy trucks / commercial vehicles)
- [x]  Log frames to CSV for offline analysis
- [x]  Replay recorded CAN logs
- [ ] Add `python-can` backend for real hardware support

---

## Author

Built as a portfolio project demonstrating automotive embedded systems knowledge.
