"""
OBD-II CAN Frame Decoder
Decodes standard OBD-II PID responses from CAN frames.
"""

from simulator import CANFrame


# PID decode rules: pid -> (name, unit, formula)
PID_MAP = {
    0x0C: ("Engine RPM",       "RPM",  lambda a, b: ((a * 256) + b) / 4),
    0x0D: ("Vehicle Speed",    "km/h", lambda a, b: a),
    0x05: ("Coolant Temp",     "°C",   lambda a, b: a - 40),
    0x11: ("Throttle Position","%%",   lambda a, b: round(a * 100 / 255, 1)),
    0x04: ("Engine Load",      "%%",   lambda a, b: round(a * 100 / 255, 1)),
    0x0F: ("Intake Air Temp",  "°C",   lambda a, b: a - 40),
}


def decode(frame: CANFrame) -> dict:
    """
    Decode an OBD-II response CAN frame.

    Returns a dict with keys: pid, name, value, unit, raw_data
    Returns None if frame is not a recognized OBD-II response.
    """
    # OBD-II ECU response ID is 0x7E8
    if frame.arbitration_id != 0x7E8:
        return None

    if len(frame.data) < 3:
        return None

    mode = frame.data[1]
    pid  = frame.data[2]

    # Mode 0x41 = response to Service 01 (live data)
    if mode != 0x41:
        return None

    if pid not in PID_MAP:
        return {"pid": pid, "name": "Unknown PID", "value": None, "unit": "", "raw_data": frame.data}

    name, unit, formula = PID_MAP[pid]

    # Bytes A and B are at data[3] and data[4]
    a = frame.data[3] if len(frame.data) > 3 else 0
    b = frame.data[4] if len(frame.data) > 4 else 0
    value = formula(a, b)

    return {
        "pid":      pid,
        "name":     name,
        "value":    value,
        "unit":     unit,
        "raw_data": frame.data,
    }


def decode_all(frames: list) -> list:
    """Decode a list of CAN frames, skipping unrecognized ones."""
    results = []
    for frame in frames:
        decoded = decode(frame)
        if decoded and decoded["value"] is not None:
            results.append((frame, decoded))
    return results
