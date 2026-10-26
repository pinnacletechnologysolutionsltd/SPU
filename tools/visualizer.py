import serial
import time
import sys
import math

AXIS_COUNT = 13


def draw_hud(q_str, a_str, is_boot=False, frame_str=None, snapshot=None, status=None):
    try:
        energy = int(q_str, 16)
        axis = int(a_str, 16)
    except ValueError:
        energy = 0
        axis = 0

    if snapshot:
        peak_axis = max(snapshot, key=lambda idx: int(snapshot[idx], 16))
        energy = int(snapshot[peak_axis], 16)
        axis = peak_axis

    # Clear terminal (ANSI escape codes)
    sys.stdout.write("\033[2J\033[H")
    
    # Header
    if is_boot:
        print(f"\033[1;33m=== SPU-13 SOVEREIGN MANIFOLD [INHALING] ===\033[0m\n")
    else:
        print(f"\033[1;36m=== SPU-13 SOVEREIGN MANIFOLD [ACTIVE] ===\033[0m\n")
    if frame_str is not None:
        print(f"\033[1;32mSnapshot Frame:     \033[1;37m0x{frame_str}\033[0m")
    if status is not None:
        print(f"\033[1;32mLink Status:        \033[1;37m{status}\033[0m")
    print(f"\033[1;32mQuadrance (Energy): \033[1;37m0x{q_str}\033[0m")
    print(f"\033[1;32mPeak Axis:          \033[1;37m{axis}\033[0m")
    print("\n")

    # Render a simple text-based orbital manifold
    radius = 10
    grid_size = 25
    grid = [[" " for _ in range(grid_size)] for _ in range(grid_size)]
    cx, cy = grid_size//2, grid_size//2

    # Draw nodes
    for i in range(AXIS_COUNT):
        angle = (i / AXIS_COUNT) * math.pi * 2
        # Scale X by 1.5 to account for terminal character aspect ratio
        x = int(cx + math.cos(angle) * radius * 1.5)
        y = int(cy + math.sin(angle) * radius)
        
        if 0 <= x < grid_size and 0 <= y < grid_size:
            if i == axis:
                grid[y][x] = "\033[1;31mO\033[0m" # Red active axis
            else:
                grid[y][x] = "\033[1;36mo\033[0m" # Cyan inactive axis

    # Draw Energy Core (size based on energy modulo to simulate pulsing)
    core_size = min(4, max(1, (energy % 100) // 20))
    for dy in range(-core_size, core_size+1):
        for dx in range(-core_size, core_size+1):
            if dx*dx + dy*dy <= core_size*core_size:
                # Scale X for aspect ratio here too
                plot_x = cx + int(dx * 1.5)
                plot_y = cy + dy
                if 0 <= plot_x < grid_size and 0 <= plot_y < grid_size:
                    if grid[plot_y][plot_x] == " ":
                        grid[plot_y][plot_x] = "\033[1;32m*\033[0m"

    for row in grid:
        print(" " * 10 + "".join(row))

    if snapshot:
        print("")
        for base in range(0, AXIS_COUNT, 4):
            chunk = []
            for idx in range(base, min(base + 4, AXIS_COUNT)):
                chunk.append(f"{idx:X}:0x{snapshot.get(idx, '00000000')}")
            print(" " * 6 + "   ".join(chunk))

    print("\n\033[1;30mPress Ctrl+C to exit.\033[0m")
    sys.stdout.flush()

def main():
    port = "/dev/tty.usbserial-20250303171" 
    if len(sys.argv) > 1:
        port = sys.argv[1]

    # The FPGA telemetry path is now fixed to 115200.
    baud_rates = [115200]
    current_baud_idx = 0
    
    def open_ser(port, baud):
        try:
            s = serial.Serial(port, baud, timeout=0.1)
            return s
        except:
            return None

    print(f"Connecting to {port}...")
    ser = open_ser(port, baud_rates[current_baud_idx])
    if not ser:
        print(f"Could not open serial port {port}")
        return

    print(f"Syncing at {baud_rates[current_baud_idx]} baud...")
    
    last_sync_attempt = time.time()
    rx_buffer = ""
    burst_frame = None
    burst_seq = 0
    burst_axes = {}
    burst_locked = False
    burst_complete = False
    last_snapshot = None
    last_frame = None
    link_status = "Waiting for snapshot delimiter"

    def maybe_render_snapshot():
        nonlocal last_snapshot, last_frame, link_status
        if burst_frame is None or len(burst_axes) != AXIS_COUNT:
            return
        ordered = {idx: burst_axes[idx] for idx in sorted(burst_axes)}
        peak_axis = max(ordered, key=lambda idx: int(ordered[idx], 16))
        last_snapshot = ordered
        last_frame = burst_frame
        link_status = "Frame locked"
        draw_hud(
            ordered[peak_axis],
            f"{peak_axis:X}",
            False,
            burst_frame,
            ordered,
            link_status,
        )

    while True:
        try:
            if ser.in_waiting > 0:
                # Read whatever is available
                raw = ser.read(ser.in_waiting)
                
                # Try to decode and find lines
                try:
                    rx_buffer += raw.decode('ascii', errors='ignore')
                    while "\n" in rx_buffer:
                        line, rx_buffer = rx_buffer.split("\n", 1)
                        line = line.strip()
                        if not line:
                            continue

                        is_boot = line.startswith("B:")
                        is_oper = line.startswith("Q:")
                        is_snapshot = line.startswith("S:")

                        if is_boot or is_oper or is_snapshot:
                            last_sync_attempt = time.time()

                        if is_snapshot:
                            burst_seq += 1
                            burst_frame = f"{burst_seq:08X}"
                            burst_axes = {}
                            burst_locked = True
                            burst_complete = False
                            link_status = "Frame delimiter received"
                        elif is_oper:
                            parts = line.split()
                            if len(parts) >= 2:
                                q_str = parts[0][2:]
                                axis_field = parts[1][2:] if parts[1].startswith("A:") else parts[1]
                                try:
                                    axis_idx = int(axis_field, 16)
                                except ValueError:
                                    continue

                                if not burst_locked or burst_frame is None:
                                    if last_snapshot is not None and last_frame is not None:
                                        draw_hud(q_str, axis_field, False, last_frame, last_snapshot, "Waiting for next delimiter")
                                    else:
                                        draw_hud(q_str, axis_field, False, status="Unsynced; waiting for S:")
                                else:
                                    if burst_complete:
                                        continue

                                    if axis_idx >= AXIS_COUNT:
                                        continue

                                    burst_axes[axis_idx] = q_str
                                    if len(burst_axes) == AXIS_COUNT:
                                        burst_complete = True
                                        burst_locked = False
                                        link_status = "Frame complete; waiting for next delimiter"
                                        maybe_render_snapshot()
                        elif is_boot:
                            parts = line.split()
                            if len(parts) >= 2:
                                q_str = parts[0][2:]
                                a_str = parts[1][2:] if parts[1].startswith("A:") else parts[1]
                                draw_hud(q_str, a_str, True, status="Boot telemetry")
                except Exception:
                    pass
            
            # Auto-Baud Logic: retained only as a reconnect path; single fixed baud by default.
            if time.time() - last_sync_attempt > 2.0:
                current_baud_idx = (current_baud_idx + 1) % len(baud_rates)
                new_baud = baud_rates[current_baud_idx]
                ser.close()
                ser = open_ser(port, new_baud)
                # Position print above the raw line
                sys.stdout.write(f"\033[25;1H\033[KScanning at {new_baud} baud...")
                sys.stdout.flush()
                last_sync_attempt = time.time()

            time.sleep(0.01)
        except KeyboardInterrupt:
            # Clear screen one last time on exit
            sys.stdout.write("\033[2J\033[H")
            print("Visualizer terminated.")
            if last_snapshot is not None and last_frame is not None:
                peak_axis = max(last_snapshot, key=lambda idx: int(last_snapshot[idx], 16))
                print(f"\n--- LAST MANIFOLD SNAPSHOT ---")
                print(f"Frame: {last_frame}")
                print(f"Quadrance: {last_snapshot[peak_axis]}")
                print(f"Active Axis: {peak_axis:X}")
                print(f"------------------------------")
            break
        except Exception as e:
            pass

if __name__ == "__main__":
    main()
