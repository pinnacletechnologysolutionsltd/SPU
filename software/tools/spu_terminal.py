#!/usr/bin/env python3
"""
spu_terminal.py — SPU-13 Laminar Terminal  v1.1
================================================
Modes:
  (default)    Emulator — live Jitterbug orbit, Rich display
  --serial PORT  Hardware bridge — 104-byte Whisper frames from RP2040
  --repl         Lithic-L REPL (SAS opcodes + Ghost OS commands)
  --graphical    Full Rich Layout with Hex-IVM panel
  --ascii        Plain ANSI, no Rich required

Ghost OS REPL commands (in addition to SAS opcodes):
  focus <a> <b> <c> <d>   — set view focus to Quadray coordinate
  pulse                   — print 61.44 kHz heartbeat status
  inject <addr> <a> <b>   — write RationalSurd to hardware register (serial mode)
  quit / exit             — stop

Usage:
  python3 spu_terminal.py
  python3 spu_terminal.py --serial /dev/ttyACM0
  python3 spu_terminal.py --repl
  python3 spu_terminal.py --serial /dev/ttyACM0 --repl --graphical
"""

import sys
import os
import argparse
import struct
import threading
import time
import math
from typing import Optional, List, Tuple

# ---------------------------------------------------------------------------
# Optional dependencies
# ---------------------------------------------------------------------------
try:
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.text import Text
    from rich.columns import Columns
    from rich import box
    RICH = True
except ImportError:
    RICH = False

try:
    import serial as pyserial
    SERIAL = True
except ImportError:
    SERIAL = False

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from spu_vm import SPUCore, assemble_source, RationalSurd, QuadrayVector

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
AXES        = 13
FRAME_BYTES = AXES * 8   # 104 bytes per Whisper frame
Q12         = 4096.0     # Fixed-point scale used by RP2040 firmware

# SPI commands (matches rp2350_spu_interface.c v2.0)
CMD_READ_MANIFOLD = 0xA0
CMD_READ_STATUS   = 0xAC
CMD_WRITE_CHORD   = 0xB1

JITTERBUG_SAS = """\
QLOAD QR0  1 0
QLOAD QR1  1 0
QLOAD QR2  1 0
QLOAD QR3  1 0
QLOAD QR4  1 0
QLOAD QR5  1 0
QLOAD QR6  1 0
QLOAD QR7  1 0
QLOAD QR8  1 0
QLOAD QR9  1 0
QLOAD QR10 1 0
QLOAD QR11 1 0
QLOAD QR12 1 0
LOOP:
QROT QR0
QROT QR1
QROT QR2
QROT QR3
QROT QR4
QROT QR5
QROT QR6
QROT QR7
QROT QR8
QROT QR9
QROT QR10
QROT QR11
QROT QR12
SNAP
JMP LOOP
"""

# ---------------------------------------------------------------------------
# Quadray → Cartesian projection  (from laminar_sandbox.py)
# Standard IVM basis vectors: A=(0,0,1) B=(√(8/9),0,-1/3)
#                              C=(-√(2/9),√(2/3),-1/3) D=(-√(2/9),-√(2/3),-1/3)
# ---------------------------------------------------------------------------
_S8_9  = math.sqrt(8/9)
_S2_9  = math.sqrt(2/9)
_S2_3  = math.sqrt(2/3)

def qray_to_xyz(a: float, b: float, c: float, d: float) -> Tuple[float,float,float]:
    x = _S8_9*b - _S2_9*c - _S2_9*d
    y = _S2_3*c - _S2_3*d
    z = a - b/3 - c/3 - d/3
    return x, y, z

def qray_simplify(a, b, c, d):
    m = min(a, b, c, d)
    return a-m, b-m, c-m, d-m

# ---------------------------------------------------------------------------
# Hex IVM ASCII panel  (inspired by hex_sim.py)
# Renders a 21×9 staggered hex grid; marks the focus cell and active axes
# ---------------------------------------------------------------------------
HEX_COLS = 21
HEX_ROWS = 9

def _hex_char(col, row, focus_col, focus_row, active_set: set) -> str:
    coord = (col, row)
    if col == focus_col and row == focus_row:
        return "[bold yellow]⬡[/]"
    if coord in active_set:
        return "[green]●[/]"
    return "[dim]·[/]"

def build_hex_panel(focus_q: Tuple[int,int,int,int], axes_q) -> Panel:
    """
    Project all 13 QR axes into 2D hex grid coords and mark them.
    focus_q: (a,b,c,d) Quadray focus — shown as yellow hexagon.
    axes_q:  list of (a_raw, b_raw) Q12 pairs for the 13 QR axes.
    """
    # Project focus
    fa, fb, fc, fd = focus_q
    fx, fy, _ = qray_to_xyz(fa/Q12, fb/Q12, fc/Q12, fd/Q12)
    focus_col = int((fx * 3 + HEX_COLS/2)) % HEX_COLS
    focus_row = int((fy * 3 + HEX_ROWS/2)) % HEX_ROWS

    # Project each QR axis (use a + b components as proxy quadray)
    active: set = set()
    for i, (a_raw, b_raw) in enumerate(axes_q):
        av, bv = a_raw / Q12, b_raw / Q12
        # Treat QR as (|av|, |bv|, 0, 0) for 2D hex projection
        a2, b2, c2, d2 = qray_simplify(abs(av), abs(bv), 0, 0)
        px, py, _ = qray_to_xyz(a2, b2, c2, d2)
        col = int((px * 3 + HEX_COLS/2)) % HEX_COLS
        row = int((py * 3 + HEX_ROWS/2)) % HEX_ROWS
        active.add((col, row))

    lines = []
    for row in range(HEX_ROWS):
        offset = " " if row % 2 == 0 else ""   # 60° stagger
        cells = [_hex_char(col, row, focus_col, focus_row, active)
                 for col in range(HEX_COLS)]
        lines.append(offset + " ".join(cells))
    return Panel("\n".join(lines), title="IVM Hex-Grid  (60°)", border_style="cyan")

# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------
class FrameState:
    def __init__(self):
        self._lock    = threading.Lock()
        self.axes     : List[Tuple[int,int]] = [(0,0)] * AXES
        self.source   : str  = "emulator"
        self.frame_no : int  = 0
        self.gasket   : str  = ""
        self.fib      : str  = ""
        self.sdf      : str  = ""
        self.repl_log : List[Tuple[str,str]] = []
        self.focus_q  : Tuple[int,int,int,int] = (1, 0, 0, 0)

    def update_from_vm(self, core: SPUCore):
        with self._lock:
            # QuadrayVector slots: a, b, c, d (each a RationalSurd)
            # Use rational part (.a) of component 'a' as the display scalar
            self.axes     = [(qr.a.a, qr.a.b) for qr in core.qregs]
            self.gasket   = repr(core.gasket)
            self.fib      = repr(core.fib)
            self.sdf      = repr(core.sdf)
            self.frame_no += 1

    def update_from_frame(self, buf: bytes):
        axes = []
        for i in range(AXES):
            off   = i * 8
            a_raw = struct.unpack_from('>h', buf, off)[0]
            b_raw = struct.unpack_from('>h', buf, off + 4)[0]
            axes.append((a_raw, b_raw))
        with self._lock:
            self.axes     = axes
            self.source   = "hardware"
            self.frame_no += 1

    def snapshot(self):
        with self._lock:
            return (list(self.axes), self.source, self.frame_no,
                    self.gasket, self.fib, self.sdf,
                    list(self.repl_log), self.focus_q)

    def log_repl(self, cmd: str, result: str):
        with self._lock:
            self.repl_log.append((cmd, result))
            if len(self.repl_log) > 10:
                self.repl_log.pop(0)

    def set_focus(self, a, b, c, d):
        with self._lock:
            self.focus_q = (int(a), int(b), int(c), int(d))

# ---------------------------------------------------------------------------
# Producers
# ---------------------------------------------------------------------------
def emulator_loop(state: FrameState, stop: threading.Event):
    words = assemble_source(JITTERBUG_SAS)
    core  = SPUCore(max_steps=9999, verbose=False, proof=False,
                    sdf_trace=False, gasket_trace=False)
    core.load(words)
    while not stop.is_set():
        core.step()
        state.update_from_vm(core)
        if core.pc >= len(core.program):
            core.pc = 0
        time.sleep(0.05)

def serial_loop(state: FrameState, port: str, stop: threading.Event):
    if not SERIAL:
        print("Error: pyserial not installed. Run: pip install pyserial")
        stop.set()
        return
    try:
        ser = pyserial.Serial(port, baudrate=921600, timeout=1.0)
    except Exception as e:
        print(f"Error opening {port}: {e}")
        stop.set()
        return
    buf = bytearray()
    while not stop.is_set():
        try:
            chunk = ser.read(FRAME_BYTES - len(buf))
            if chunk:
                buf.extend(chunk)
                if len(buf) >= FRAME_BYTES:
                    state.update_from_frame(bytes(buf[:FRAME_BYTES]))
                    buf = buf[FRAME_BYTES:]
        except pyserial.SerialException:
            break
    ser.close()

# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------
def _davis_c(a_raw: int, b_raw: int) -> str:
    a, b = a_raw / Q12, b_raw / Q12
    return "    ∞   " if abs(b) < 0.001 else f"{a/b:+7.3f}"

def _laminar_str(a_raw: int, b_raw: int, rich: bool) -> str:
    a, b = a_raw / Q12, b_raw / Q12
    ok = abs(a*a - 3*b*b) < 0.1
    if rich:
        return "[green]✓[/]" if ok else "[red]⚠[/]"
    return "✓" if ok else "⚠"

def _cartesian_str(a_raw: int, b_raw: int) -> str:
    a, b = a_raw / Q12, b_raw / Q12
    # Treat QR as (|a|,|b|,0,0) Quadray → Cartesian
    qa, qb, qc, qd = qray_simplify(abs(a), abs(b), 0.0, 0.0)
    x, y, z = qray_to_xyz(qa, qb, qc, qd)
    return f"({x:+.2f},{y:+.2f},{z:+.2f})"

def build_manifold_table(axes) -> Table:
    t = Table(title="Manifold  Q(√3)", box=box.SIMPLE_HEAVY, expand=True)
    t.add_column("Axis",   style="cyan",  width=5,  justify="right")
    t.add_column("a",      style="white", width=11, justify="right")
    t.add_column("b·√3",   style="white", width=11, justify="right")
    t.add_column("C=a/b",  style="yellow",width=9,  justify="right")
    t.add_column("xyz",    style="dim",   width=19, justify="left")
    t.add_column("Lam",    width=4,       justify="center")
    for i, (a, b) in enumerate(axes):
        t.add_row(
            f"QR{i}",
            f"{a/Q12:+9.3f}",
            f"{b/Q12:+9.3f}",
            _davis_c(a, b),
            _cartesian_str(a, b),
            _laminar_str(a, b, rich=True),
        )
    total = sum((a/Q12) + (b/Q12) for a, b in axes)
    color = "green" if abs(total) < 0.1 else "red"
    t.add_section()
    t.add_row("ΣABCD", f"[{color}]{total:+9.3f}[/]", "", "", "",
              "[green]✓[/]" if abs(total) < 0.1 else "[red]⚠[/]")
    return t

def build_status_panel(source, frame_no, gasket, fib, sdf, focus_q) -> Panel:
    fx, fy, fz = qray_to_xyz(*(x/max(1,abs(focus_q[0]+focus_q[1]+focus_q[2]+focus_q[3])+1e-9) for x in focus_q))
    lines = [
        f"[bold]Source:[/] {source}   [bold]Frame:[/] {frame_no}",
        f"[bold]Focus:[/]  Quadray{focus_q}  → xyz({fx:+.2f},{fy:+.2f},{fz:+.2f})",
        f"[bold]Gasket:[/] {gasket}",
        f"[bold]Fib:[/]    {fib}",
        f"[bold]SDF:[/]    {sdf}",
    ]
    return Panel("\n".join(lines), title="SPU-13 Status", border_style="blue")

def build_repl_panel(repl_log) -> Panel:
    lines = []
    for cmd, result in repl_log:
        lines.append(f"[cyan]❯ {cmd}[/]")
        if result:
            lines.append(f"  [dim]{result}[/]")
    text = "\n".join(lines) or "[dim]Type a SAS opcode or Ghost OS command.[/]"
    return Panel(text, title="Lithic-L REPL", border_style="magenta")

# ---------------------------------------------------------------------------
# Display: ASCII (no Rich)
# ---------------------------------------------------------------------------
def ascii_display(state: FrameState, stop: threading.Event):
    while not stop.is_set():
        axes, source, frame_no, gasket, fib, sdf, _, focus_q = state.snapshot()
        os.write(1, b"\033[H\033[2J")
        print(f"━━━ SPU-13 Sovereign Terminal [{source} frame {frame_no}] ━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"Focus: Quadray{focus_q}")
        print(f"{'Axis':<6} {'a':>10} {'b·√3':>10} {'C=a/b':>9} {'xyz':>22} Lam")
        print("─" * 66)
        total = 0.0
        for i, (a, b) in enumerate(axes):
            av, bv = a/Q12, b/Q12
            total += av + bv
            c_str = f"{av/bv:+7.3f}" if abs(bv) > 0.001 else "      ∞"
            lam   = "✓" if abs(av*av - 3*bv*bv) < 0.1 else "⚠"
            cart  = _cartesian_str(a, b)
            print(f"QR{i:<4} {av:>+10.3f} {bv:>+10.3f} {c_str:>9} {cart:>22} {lam}")
        print("─" * 66)
        status = "✓ LAMINAR" if abs(total) < 0.1 else "⚠ CUBIC LEAK"
        print(f"ΣABCD = {total:+.4f}   {status}")
        print(f"\nGasket: {gasket}\nFib: {fib}\nSDF: {sdf}")
        time.sleep(0.1)

# ---------------------------------------------------------------------------
# Display: Rich live
# ---------------------------------------------------------------------------
def rich_display(state: FrameState, stop: threading.Event, graphical: bool, repl: bool):
    console = Console()

    def make_renderable():
        axes, source, frame_no, gasket, fib, sdf, repl_log, focus_q = state.snapshot()
        manifold = build_manifold_table(axes)
        status   = build_status_panel(source, frame_no, gasket, fib, sdf, focus_q)

        if graphical:
            layout = Layout()
            rows = [Layout(name="top", ratio=4),
                    Layout(name="bottom", ratio=3)]
            layout.split_column(*rows)
            layout["top"].split_row(
                Layout(manifold,              name="manifold", ratio=3),
                Layout(build_hex_panel(focus_q, axes), name="hex",      ratio=2),
            )
            if repl:
                layout["bottom"].split_row(
                    Layout(status,                        name="status", ratio=2),
                    Layout(build_repl_panel(repl_log),    name="repl",   ratio=2),
                )
            else:
                layout["bottom"].update(status)
            return layout
        else:
            parts = [manifold, status]
            if repl:
                parts.append(build_repl_panel(repl_log))
            return Columns(parts)

    with Live(make_renderable(), console=console,
              refresh_per_second=10, screen=True) as live:
        while not stop.is_set():
            live.update(make_renderable())
            time.sleep(0.1)

# ---------------------------------------------------------------------------
# REPL loop
# ---------------------------------------------------------------------------
def repl_loop(state: FrameState, core: Optional[SPUCore],
              ser, stop: threading.Event):
    """
    Supports two command classes:
      1. SAS opcodes — assembled via assemble_source(), single-stepped in VM
         and/or sent as 8-byte Chord over serial.
      2. Ghost OS commands — focus, pulse, inject, quit.
    """
    print("\nLithic-L REPL ready. Type SAS opcodes or Ghost OS commands ('pulse', 'focus a b c d', 'inject addr a b', 'quit').")
    while not stop.is_set():
        try:
            line = input("❯ ").strip()
        except (EOFError, KeyboardInterrupt):
            stop.set()
            break
        if not line:
            continue

        parts = line.lower().split()
        cmd   = parts[0]

        # ── Ghost OS commands ──────────────────────────────────────────────
        if cmd in ("quit", "exit", "q"):
            stop.set()
            break

        elif cmd == "pulse":
            result = "Heartbeat: 61.44 kHz | Source: {} | Frame: {} | State: Laminar".format(
                state.source, state.frame_no)
            state.log_repl(line, result)
            print(f"  {result}")
            continue

        elif cmd == "focus" and len(parts) == 5:
            try:
                a, b, c, d = (int(x) for x in parts[1:5])
                state.set_focus(a, b, c, d)
                fx, fy, fz = qray_to_xyz(a, b, c, d)
                result = f"Focus → Quadray({a},{b},{c},{d}) xyz({fx:+.3f},{fy:+.3f},{fz:+.3f})"
            except ValueError:
                result = "error: expected 4 integers"
            state.log_repl(line, result)
            print(f"  {result}")
            continue

        elif cmd == "inject" and len(parts) == 4:
            # inject <addr> <a> <b>  — write RationalSurd to hardware
            if not ser:
                result = "error: no serial port connected"
            else:
                try:
                    addr   = int(parts[1], 0)
                    a_val  = int(parts[2]) & 0xFFFF
                    b_val  = int(parts[3]) & 0xFFFF
                    packed = (a_val << 16) | b_val
                    # Encode as Chord: CMD_WRITE_CHORD | addr, packed 32-bit
                    chord  = struct.pack('>BBBBBBBB',
                                        CMD_WRITE_CHORD, addr,
                                        (packed >> 24) & 0xFF,
                                        (packed >> 16) & 0xFF,
                                        (packed >>  8) & 0xFF,
                                        packed & 0xFF, 0, 0)
                    ser.write(chord)
                    result = f"injected 0x{packed:08X} → addr 0x{addr:02X}"
                except Exception as e:
                    result = f"error: {e}"
            state.log_repl(line, result)
            print(f"  {result}")
            continue

        # ── SAS opcode ────────────────────────────────────────────────────
        result = ""
        try:
            words = assemble_source(line)
            if not words:
                result = "assembly error: no words"
            else:
                if core:
                    core.load(words)
                    core.step()
                    result = f"ok  word={words[0]:#018x}"
                    state.update_from_vm(core)
                if ser:
                    chord = words[0].to_bytes(8, 'big')
                    ser.write(chord)
                    result += "  (sent to hardware)"
        except Exception as e:
            result = f"error: {e}"

        state.log_repl(line, result)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="SPU-13 Laminar Terminal v1.1")
    parser.add_argument("--serial",    metavar="PORT",
                        help="Hardware serial port, e.g. /dev/ttyACM0")
    parser.add_argument("--repl",      action="store_true",
                        help="Enable Lithic-L REPL")
    parser.add_argument("--graphical", action="store_true",
                        help="Full Rich Layout with Hex-IVM panel")
    parser.add_argument("--ascii",     action="store_true",
                        help="Plain ANSI output (no Rich)")
    args = parser.parse_args()

    state = FrameState()
    stop  = threading.Event()
    core  = None
    ser   = None

    # ── Producer ──────────────────────────────────────────────────────────
    if args.serial:
        state.source = "hardware"
        producer = threading.Thread(
            target=serial_loop, args=(state, args.serial, stop), daemon=True)
        if SERIAL and not args.ascii:
            try:
                ser = pyserial.Serial(args.serial, baudrate=921600, timeout=1.0)
            except Exception:
                ser = None
    else:
        state.source = "emulator"
        words = assemble_source(JITTERBUG_SAS)
        core  = SPUCore(max_steps=9999, verbose=False, proof=False,
                        sdf_trace=False, gasket_trace=False)
        core.load(words)
        producer = threading.Thread(
            target=emulator_loop, args=(state, stop), daemon=True)

    producer.start()

    # ── Display ───────────────────────────────────────────────────────────
    use_rich = RICH and not args.ascii
    if not use_rich and not args.ascii:
        print("[warn] rich not installed — falling back to ASCII mode")
    DisplayFn = rich_display if use_rich else ascii_display
    disp_args = (state, stop, args.graphical, args.repl) if use_rich else (state, stop)
    display   = threading.Thread(target=DisplayFn, args=disp_args, daemon=True)
    display.start()

    # ── REPL / main loop ──────────────────────────────────────────────────
    if args.repl:
        repl_loop(state, core, ser, stop)
    else:
        try:
            while not stop.is_set():
                time.sleep(0.25)
        except KeyboardInterrupt:
            stop.set()

    stop.set()
    producer.join(timeout=1.0)

if __name__ == "__main__":
    main()
