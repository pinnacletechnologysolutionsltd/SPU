#!/usr/bin/env python3
"""interactive_capture.py — removes chat/remote-relay lag from a
timing-critical capture (e.g. current_limited_stall) by starting the
existing power_log.py the instant the operator presses Enter, instead of
coordinating "stall now" over a separate channel with its own latency.

Usage: same args as power_log.py, e.g.

    python3 tools/bench_metrics/interactive_capture.py \
        --port /dev/ttyACM0 --probe tamiya_75026_v1 \
        --label current_limited_stall --seconds 1.4 \
        --out build/ina226_capture/captures/b00-current_limited_stall.csv

Stall the actuator and hit Enter in the same motion -- only your own
reaction time is in the loop, not any round-trip to another process/chat.
"""
import subprocess
import sys
from pathlib import Path

POWER_LOG = Path(__file__).resolve().parent / "power_log.py"


def main():
    if "--seconds" not in sys.argv:
        sys.exit("interactive_capture.py needs a fixed --seconds duration "
                 "(this tool is for a timed phase, not open-ended logging -- "
                 "use power_log.py directly for that).")

    input("Ready. Stall the actuator and press Enter in the same motion "
          "to start capturing >>> ")
    subprocess.run([sys.executable, str(POWER_LOG), *sys.argv[1:]], check=False)


if __name__ == "__main__":
    main()
