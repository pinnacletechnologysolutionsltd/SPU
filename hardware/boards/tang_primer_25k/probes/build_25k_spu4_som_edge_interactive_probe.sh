#!/usr/bin/env bash
# build_25k_spu4_som_edge_interactive_probe.sh -- Tang 25K interactive bench
# probe for the SPU-4 edge SOM product, spu4_som_edge_wrapper (Track B,
# see the interactive-probe design pass referenced from
# spu13_tang25k_spu4_som_edge_interactive_probe.v's own header).
#
# `uart_rx` pin RESOLVED 2026-08-18: B3, per the Sipeed
# Tang_Primer_25K_Dock_60033 schematic (page 1, "Peripherals -> Debugger") --
# IOB56A_FPGA_UART_RX, wired to net 616_UART_TX, the exact RX partner to C3
# (uart_tx, "Host-bound TX"), both through the onboard BL616 USB-JTAG-UART
# bridge chip out to its USB-C port. Constrained in tang_primer_25k.cst.
#
# B3 is ALSO the pin a legacy scheme bodge-wires an external RP2350's UART
# TX onto (docs/rp_mcu_bringup_plan.md, hardware/rp2350/rp2350_uart_injector.c,
# spu13_tang25k_top.v:158) -- confirmed NOT currently wired on this board
# (2026-08-18). If that bodge wire is ever reconnected on a board that also
# needs this probe, the two would contend (two live TX drivers on one pad) --
# see knowledge memory tang25k-b3-pin-contention-risk before assuming
# otherwise on a different board. Simulation (see
# hardware/tests/spu4/spu4_som_edge_interactive_probe_tb.v) needs none of
# this and already passes.
#
# Before flashing this bitstream, a boot image must be on the PMOD J4 SPI
# flash chip at FLASH_SPU4_SOM_BASE (0x120000), same chip/pins as the
# fixed probe:
#   python3 tools/gen_spu4_som_boot_image.py --profile demo \
#       --output tools/build/spu4_som_boot_image.bin
#   tools/rp2040_flash_pmod.py --port <tty> id     # must report JEDEC EF4018 first
#   tools/rp2040_flash_pmod.py --port <tty> write tools/build/spu4_som_boot_image.bin \
#       --offset 0x120000
# (--profile oracle_fixture also works, and is what
# tools/spu4_som_edge_demo.py defaults to assuming -- match --profile on
# both sides.)
#
# Once flashed and wired, drive it with tools/spu4_som_edge_demo.py
# (arbitrary queries) or tools/spu4_som_edge_smoketest.py does NOT apply
# here -- that one is the fixed probe's smoke test, not this probe's.
set -e
mkdir -p build

echo "--- 1. Yosys Synthesis (SPU-4 SOM edge interactive probe) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_spu4_som_edge_interactive_probe.ys

echo "--- 2. NextPNR ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k.cst \
    --json build/spu4_som_edge_interactive_probe.json \
    --write build/spu4_som_edge_interactive_probe_pnr.json \
    --freq 12

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A --sspi_as_gpio --mspi_as_gpio --cpu_as_gpio \
    build/spu4_som_edge_interactive_probe_pnr.json \
    -o build/tang_primer_25k_spu4_som_edge_interactive_probe.fs

echo ""
echo "=== SPU-4 SOM Edge Interactive Probe Build Complete ==="
echo "SRAM load: openFPGALoader -b tangprimer25k build/tang_primer_25k_spu4_som_edge_interactive_probe.fs"
echo "Drive with: python3 tools/spu4_som_edge_demo.py --port <tty> --profile <matching profile>"
