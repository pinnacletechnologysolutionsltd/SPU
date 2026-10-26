"""Exact T1d board-clock and UART-divisor checks.

This is a small executable model of the board wrapper's clock relationship.
It intentionally checks the source anchors as well as the arithmetic so a
future wrapper edit cannot silently invalidate the frozen contract.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOP = (ROOT / "hardware/boards/artix7/spu_a7_gpu_vga_top.v").read_text()
XDC = (ROOT / "hardware/boards/artix7/spu_a7_gpu_vga_t1d.xdc").read_text()


def check(condition, message):
    if not condition:
        raise AssertionError(message)


# Source-clock model: clk_div starts low and toggles once per sys_clk edge.
# Therefore its rising edges occur on odd-numbered source edges and repeat
# every two source edges. BUFG changes insertion delay, not this cycle ratio.
sys_hz = 50_000_000
sys_period_ns = 1_000_000_000 // sys_hz
div = 0
pixel_rising_edges = []
for sys_edge in range(1, 9):
    div ^= 1
    if div:
        pixel_rising_edges.append(sys_edge)

check(sys_period_ns == 20, "sys_clk must be exactly 20 ns / 50 MHz")
check(pixel_rising_edges == [1, 3, 5, 7],
      "clk_pixel must rise every second sys_clk edge")
check(all(b - a == 2 for a, b in zip(pixel_rising_edges, pixel_rising_edges[1:])),
      "clk_pixel edge ratio must remain divide-by-two")
check(sys_hz // 2 == 25_000_000, "clk_pixel must be 25 MHz")

# The receiver is in the derived pixel domain. Its integer divisor is frozen
# at 217 cycles: 25 MHz / 217 = 115207.37 baud.
pixel_hz = sys_hz // 2
baud = 115_200
bit_cycles = pixel_hz // baud
realized_baud = pixel_hz / bit_cycles
check(bit_cycles == 217, "T1d UART divisor must be 217 pixel clocks")
check(abs(realized_baud - baud) / baud < 0.0001,
      "T1d UART baud error must remain below 0.01 percent")

# Structural anchors: all UART and video logic must remain in clk_pixel, with
# only the divider and reset debounce clocked by sys_clk.
check("always @(posedge sys_clk) clk_div <= ~clk_div;" in TOP,
      "wrapper clock divider source anchor changed")
check("BUFG u_bufg_pix (.I(clk_div), .O(clk_pixel));" in TOP,
      "wrapper pixel-clock BUFG source anchor changed")
check(".clk(clk_pixel), .rst_n(pix_rst_n), .rx(uart_rx)" in TOP,
      "UART must remain in clk_pixel domain")
check("pix_rst_sync <= {pix_rst_sync[1:0], rst_n_db};" in TOP,
      "pixel reset synchronizer source anchor changed")
check("create_clock -period 20.000 -name sys_clk [get_ports sys_clk]" in XDC,
      "sys_clk XDC constraint missing")
check("PACKAGE_PIN E5 [get_ports vga_vsync]" in XDC,
      "frozen VSYNC FPGA pin mapping missing")
check("J10-10/E5 -> VSYNC" in XDC,
      "frozen J10 VSYNC mapping missing")
check("J10-7/G6 is unused" in XDC,
      "stale J10-7 VSYNC mapping remains")

print("PASS: T1d exact sys_clk-to-clk_pixel timing model")
