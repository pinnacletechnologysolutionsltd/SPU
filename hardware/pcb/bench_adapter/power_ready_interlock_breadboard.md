# J2 Power-Ready Interlock — Breadboard Prototype

This is the mandatory pre-PCB experiment for the bench adapter Rev B.  It
proves that a powered Pico cannot energise an unpowered FPGA I/O bank through
the SPI cable.

## Circuit

Use one **SN74CBTLV3125PW** (U1).  It is a four-channel bidirectional switch
with independent active-low enables and powered-off (`Ioff`) isolation.  Join
all four `OE#` pins as `J2_OE_N`.  Its `A` ports face the Pico; its `B` ports
face J2/target.  Put the existing 100 Ω resistors between Pico GPIO and U1 A
ports.  Do not omit the common ground.

Power U1 from the Pico's regulated 3.3 V.  Pull `J2_OE_N` to Pico 3.3 V with
10 kΩ.  Thus U1 is *off* by default, including while the target is absent.

Use **TLV3011BIDBVR** (U2) powered from Pico 3.3 V and ground.  Feed J2-6
(`TARGET_3V3_SENSE`) through 137 kΩ to the comparator sense node and use
100 kΩ from that node to ground.  Compare it with U2's 1.242 V reference.  It
corresponds to 2.94 V at J2-6.  Wire the comparator inputs/polarity so its
open-drain output pulls `J2_OE_N` low only when the sense voltage is above
the threshold; verify this logic polarity on the bench before connecting U1.

The optional 1 MΩ feedback resistor is deliberately DNP for the first test.
Fit it only after measuring the transition threshold, and tune it for a
roughly 0.1–0.2 V hysteresis window.  The comparator is powered locally by
the Pico, and its target-voltage input must use the TLV3011B fail-safe input;
no target 3.3 V rail is permitted to connect directly to Pico 3.3 V.

## Bring-up order

1. Build and test U2 alone. With its target-sense input at 0 V,
   `J2_OE_N` must be Pico 3.3 V. Increase a current-limited bench source at
   the sense input and verify it falls only near 2.94 V.
2. Add U1 with no FPGA connected. Confirm all channels are open below the
   threshold and conduct above it.
3. Attach an unpowered target header. Drive CS#/SCK/MOSI continuously from
   the Pico. With a temporary 10 kΩ pull-down on each target-side line,
   verify the target 3.3 V rail remains at 0 V and no target-side signal
   exceeds 100 mV.
4. Power the target normally; verify U1 enables, then run the 2 MHz
   southbridge smoke test.
5. Power down the target while leaving the Pico active. The switch must
   disable before any target-side signal is driven. Repeat with Pico
   unpowered and the target powered.

Do not use a breadboard result as permission to omit the 100 Ω resistors or
the normal operating rule: never deliberately connect a powered driver to an
unpowered target.  The interlock is the second line of defence.
