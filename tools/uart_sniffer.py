import serial
import sys


DEFAULT_PORTS = [
    "/dev/tty.usbserial-20250303171",
    "/dev/cu.usbserial-20250303171",
    "/dev/tty.usbserial-20250303170",
    "/dev/cu.usbserial-20250303170",
]
DEFAULT_BAUD = 115200


def parse_args():
    ports = []
    baud = DEFAULT_BAUD

    for arg in sys.argv[1:]:
        if arg.isdigit():
            baud = int(arg)
        else:
            ports.append(arg)

    if not ports:
        ports = DEFAULT_PORTS

    return ports, baud


def main():
    ports, baud = parse_args()

    for port in ports:
        print(f"--- Attempting to open {port} at {baud} baud ---")
        try:
            with serial.Serial(port, baud, timeout=1) as ser:
                print(f"Connected to {port}. Listening for data (Ctrl+C to stop)...")
                while True:
                    data = ser.read(ser.in_waiting or 1)
                    if data:
                        sys.stdout.write(data.decode("ascii", errors="replace"))
                        sys.stdout.flush()
        except KeyboardInterrupt:
            print("\n--- Stopped ---")
            return
        except Exception as e:
            print(f"Could not open {port}: {e}")

    print("--- Done ---")


if __name__ == "__main__":
    main()
