# Provisional Wukong V3 board inventory

Disposition: **provisional board-support inventory, not hardware-qualified board support**.
Documentation and metadata only; these files are not constraints or a build target.

Source: `QMTECH-XC7A100T_200T-Wukong-Board-V03-20240121.pdf`, revision 3.0,
seven sheets, supplied in `~/Downloads`. SHA-256:
`bec53e6201c5c47a7059ce5b5af86e0f3a48535ebdf5643af7583171f7331aee`.
Vendor location: [QMTECH V3 hardware documentation](https://github.com/ChinaQMTECH/QM_XC7A100T_WUKONG_BOARD/tree/master/V3/Hardware).
Sheet 2 is dated January 27, 2024; other inspected sheets are dated December 12, 2023.
Sheet numbers below mean the printed schematic sheets, numbered from 1.

## Files and evidence

- `pins.csv`: one row per included FPGA signal ball, with exact schematic net name,
  peripheral endpoint, bank, sheet, differential-pair identity and evidence references.
  Bank numbers come from FPGA symbols on sheet 2 or sheet 4; connector sheets
  additionally encode banks in their `BANKxx_ball` net names.
- `banks.csv`: schematic supply connections, not measured voltages. Empty voltage
  or electrical-standard fields mean unresolved or deliberately unassigned.
- `peripherals.json`: component identities, unresolved groups, exclusions and provenance.
- `validation.json`: bounded validation findings for this preparation step.

Evidence fields are independent booleans. `schematic_derived` means the net/ball
mapping was read from the source; `constraint_matched` means its existing XDC
assignment was checked; `physically_verified` means the cited historical evidence
supports that narrow function. False means no such claim is made here, not that a
signal failed. No hardware testing occurred for this inventory.

Clock M21 (50 MHz), KEY0 H7, UART TX E3 and UART RX F3 match the existing
[V3-derived constraints](../cpu_v02/constraints/cpu_board_3.xdc) and/or
[UART loopback constraints](../../spu_a7_uart_loopback.xdc).
The loopback XDC supplies the RX assignment absent from the V3 CPU XDC.
UART physical classifications cite [hardware evidence section 3.11](../../../../../docs/hardware_evidence.md),
which records one 115200 8N1 session with 20/20 echoed bytes, not sustained-throughput
or cross-power-cycle qualification. M21 has a historical toggling observation in
section 3.35.1, not a frequency measurement; it is conservatively not marked
physically verified in this metadata. H7 is constraint-matched, not marked as a
physically verified button function.

## Wiring findings

HDMI P3 uses FPGA differential clock/data outputs in bank 35. U16 TPD12S016
provides protection, sideband level shifting and HDMI power switching; it is not
a video serializer. LS_OE and CT_HPD are tied to 3V3. FPGA serialization,
clocking, I/O standards and usable video rates are not qualified here.

V3 user LEDs are D5/LED0 on G21 and D6/LED1 on G20, active low. Older four-LED
assignments V17/W21/Y21/V26 are not reused. V3 KEY0 has an external R37 4.7 kohm
pull-up; an older comment claiming no external pull-up is contradicted by sheet 2.
Existing XDC and evidence files are left unchanged.

## Unresolved and excluded

- The entire DDR3 control group (`DDR_RESETN`, `DDR_CKE`, `DDR_CS`, `DDR_RAS`,
  `DDR_CAS`, `DDR_WE`, `DDR_ODT`) is unresolved and has **no ball assignments**.
  An earlier conversational control-pin table was inconsistent and is not a source.
- Bank 13's fitted R14/R15 voltage option is unverified. Sheet 1 shows selection
  between regulated 3V3 and VIN, whose input is labelled regulated 5V only.
  This does not establish a permissible FPGA operating voltage. No bank 13
  electrical standard is assigned. No blanket standard is assigned to other banks.
- The schematic says `XC7A100T-200T_FGG676`; it does not establish the fitted
  device or speed grade. `xc7a100tfgg676-1` is the owner-reported target only.
- J12 bank-13 signal mapping, parallel SDRAM, configuration/JTAG and power pins
  are not enumerated in `pins.csv`. This is a partial peripheral inventory,
  not an exhaustive package or connector pinout.
- No claim is made about current health of individual board I/O, Project X-Ray
  coverage, openXC7 compatibility or physical operation of untested peripherals.
  Historical unit-specific observations must not become generic V3 wiring rules.

## Validation

127 included signals have unique FPGA balls. Seven declared differential pairs
contain exactly one positive and one negative member. Net and ball tokens were
checked on every cited sheet and connectivity reviewed against rendered sheets
2, 4, 5 and 6. Token presence alone is not proof of connectivity.
Included banks agree with the schematic supply inventory; no unexplained voltage
conflict was found. Bank 13 remains explicitly unresolved. No constraint,
RTL, frozen CPU package, synthesis, implementation or programming change is included.
