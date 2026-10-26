"""python3 -m spu_host --port /dev/ttyACM0 <command> [args...]

Thin CLI over SPUHostClient, for bench use and scripting. `command` is
either one of the typed methods (status, manifold, scale_table, qr_commit,
hex_projection, rplu_config_telemetry) or `raw <console-command...>` to
fall through to any firmware console command verbatim.
"""

import argparse
import sys

import serial

from .client import SPUHostClient, SPUProtocolError

TYPED_COMMANDS = {
    "status": lambda c, _a: c.status(),
    "manifold": lambda c, _a: c.manifold().hex(),
    "scale_table": lambda c, _a: c.scale_table().hex(),
    "qr_commit": lambda c, _a: c.qr_commit(),
    "hex_projection": lambda c, _a: c.hex_projection(),
    "rplu_config_telemetry": lambda c, _a: c.rplu_config_telemetry(),
    "som1_result": lambda c, _a: c.som1_result(),
}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True, help="e.g. /dev/ttyACM0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("command", choices=list(TYPED_COMMANDS) + ["raw"])
    parser.add_argument("args", nargs="*")
    ns = parser.parse_args(argv)

    ser = serial.Serial(ns.port, ns.baud, timeout=0.05)
    client = SPUHostClient(ser, timeout_s=ns.timeout)
    try:
        client.connect()
        if ns.command == "raw":
            for line in client.raw(" ".join(ns.args)):
                print(line)
        else:
            print(TYPED_COMMANDS[ns.command](client, ns.args))
    except SPUProtocolError as exc:
        print("ERROR:", exc, file=sys.stderr)
        return 1
    finally:
        ser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
