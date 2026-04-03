# hardware/boards/icesugar/smoke/Makefile
# SPU-13 iCEsugar Smoke Test Build
# Requires: yosys, nextpnr-ice40, icepack, icesprog (OSS iCE40 toolchain)
#
# Usage:
#   make blinky    — build + program Level 0 (Fibonacci RGB, no deps)
#   make uart      — build + program Level 1 (UART "SPU-13 LAMINAR")
#   make clean     — remove build artefacts

DEVICE    := up5k
PACKAGE   := sg48
PCF       := icesugar.pcf
BUILD_DIR := build

.PHONY: all blinky uart flash clean check

all: blinky

check:
	@which yosys      || (echo "ERROR: yosys not found — install with: sudo apt install yosys" && exit 1)
	@which nextpnr-ice40 || (echo "ERROR: nextpnr-ice40 not found — install with: sudo apt install nextpnr-ice40" && exit 1)
	@which icepack    || (echo "ERROR: icepack not found — install with: sudo apt install icestorm" && exit 1)
	@echo "Toolchain OK"

# ── Level 0: Fibonacci RGB Blinky ────────────────────────────────────────────
blinky: check $(BUILD_DIR)/blinky.bin
	icesprog $(BUILD_DIR)/blinky.bin
	@echo ""
	@echo "Level 0 PROGRAMMED — watch for: BLUE (8s) → GREEN (13s) → RED (21s) cycle"

$(BUILD_DIR)/blinky.json: spu_smoke_blinky.v | $(BUILD_DIR)
	yosys -p "synth_ice40 -top spu_smoke_blinky -json $@" $<

$(BUILD_DIR)/blinky.asc: $(BUILD_DIR)/blinky.json $(PCF)
	nextpnr-ice40 --$(DEVICE) --package $(PACKAGE) \
	    --json $< --pcf $(PCF) --asc $@

$(BUILD_DIR)/blinky.bin: $(BUILD_DIR)/blinky.asc
	icepack $< $@

# ── Level 1: UART Hello ───────────────────────────────────────────────────────
uart: check $(BUILD_DIR)/uart.bin
	icesprog $(BUILD_DIR)/uart.bin
	@echo ""
	@echo "Level 1 PROGRAMMED — connect terminal: picocom -b 115200 /dev/ttyACM0"
	@echo "Expected: 'SPU-13 LAMINAR' every ~1 second. Green LED during TX."

$(BUILD_DIR)/uart.json: spu_smoke_uart.v | $(BUILD_DIR)
	yosys -p "synth_ice40 -top spu_smoke_uart -json $@" $<

$(BUILD_DIR)/uart.asc: $(BUILD_DIR)/uart.json $(PCF)
	nextpnr-ice40 --$(DEVICE) --package $(PACKAGE) \
	    --json $< --pcf $(PCF) --asc $@

$(BUILD_DIR)/uart.bin: $(BUILD_DIR)/uart.asc
	icepack $< $@

# ── Level 2: Flash JEDEC ID (after soldering complete) ───────────────────────
flash: check $(BUILD_DIR)/flash.bin
	icesprog $(BUILD_DIR)/flash.bin
	@echo ""
	@echo "Level 2 PROGRAMMED — connect terminal: picocom -b 115200 /dev/ttyACM0"
	@echo "Expected: 'JEDEC: EF 40 18'  (Winbond W25Q128JVSQ)"
	@echo "Red LED = bad/missing solder.  Green LED = chip responding correctly."

$(BUILD_DIR)/flash.json: spu_smoke_flash.v | $(BUILD_DIR)
	yosys -p "synth_ice40 -top spu_smoke_flash -json $@" $<

$(BUILD_DIR)/flash.asc: $(BUILD_DIR)/flash.json $(PCF)
	nextpnr-ice40 --$(DEVICE) --package $(PACKAGE) \
	    --json $< --pcf $(PCF) --asc $@

$(BUILD_DIR)/flash.bin: $(BUILD_DIR)/flash.asc
	icepack $< $@

$(BUILD_DIR):
	mkdir -p $@

clean:
	rm -rf $(BUILD_DIR)
