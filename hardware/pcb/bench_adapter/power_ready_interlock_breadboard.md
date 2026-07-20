# J2 Power-Ready Interlock — Breadboard Prototype

This is the mandatory pre-PCB experiment for the bench adapter Rev B.  It
proves that a powered Pico cannot energise an unpowered FPGA I/O bank through
the SPI cable.

**Part substitution note (2026-07-21):** the originally specified
SN74CBTLV3125PW and TLV3011BIDBVR were hard to source. SN74CBTLV3125PW is
listed **Obsolete** at DigiKey, which explains the difficulty. Both
substitutes below are confirmed Active parts at DigiKey (74CBTLV3125PGG:
346 units in stock at time of writing; MAX9063EUK+T: listed, price
confirmed, live quantity not confirmed). Do not substitute MAX9062 for U2 —
despite being the same family and package, it has the *opposite* input
polarity from what this circuit needs (datasheet Table 1: MAX9062 asserts
its output low when the sense input is *below* threshold, which would enable
the switch exactly when the target is unpowered).

## Circuit

Use one **74CBTLV3125PGG** (U1, Renesas/IDT — pin- and function-compatible
second source for the obsolete SN74CBTLV3125PW). It is a four-channel
bidirectional switch with independent active-low enables and powered-off
(`Ioff`) isolation. Join all four `OE#` pins as `J2_OE_N`. Its `A` ports face
the Pico; its `B` ports face J2/target. Put the existing 100 Ω resistors
between Pico GPIO and U1 A ports. Do not omit the common ground.

Power U1 from the Pico's regulated 3.3 V. Pull `J2_OE_N` to Pico 3.3 V with
10 kΩ. Thus U1 is *off* by default, including while the target is absent.

Use **MAX9063EUK+T** (U2, Analog Devices/Maxim — open-drain, inverting
input: asserts output low when `VIN > 0.2V`, exactly the polarity this
circuit needs) powered from Pico 3.3 V and ground. Its internal reference is
**0.2 V**, not TLV3011B's 1.242 V, so the divider is different: feed J2-6
(`TARGET_3V3_SENSE`) through **137 kΩ** to the comparator sense node and use
**10 kΩ** (not 100 kΩ) from that node to ground — 10k/(137k+10k) × 2.94 V ≈
0.200 V, preserving the same ~2.94 V trip point at J2-6. Wire the comparator
so its open-drain output pulls `J2_OE_N` low only when the sense voltage is
above the threshold (MAX9063's documented behavior); verify this logic
polarity on the bench before connecting U1, exactly as before.

**No external hysteresis tuning on this part.** The original 1 MΩ feedback
resistor trick for widening hysteresis after bench measurement does **not**
work on the MAX9063 — its datasheet states the noninverting input needed for
that feedback network isn't externally accessible on this part. You get its
fixed internal hysteresis only (~±0.9 mV at the sense pin, roughly ±13 mV
reflected at the 2.94 V threshold through the divider). Bring-up step 1 below
must confirm that's wide enough to avoid chatter near the threshold; there is
no escape hatch if it isn't — falling back to a genuine TLV3011B (or
MAX9062 plus an external inverter to restore correct polarity) would be the
next move if so. The comparator is powered locally by the Pico, and its
target-voltage input relies on the same fail-safe-input property TLV3011B
provided (MAX9060–9064 datasheet: inputs stay high-impedance and safe even
with VCC or REF at 0V, across -0.3V to +5.5V independent of supply); no
target 3.3 V rail is permitted to connect directly to Pico 3.3 V.

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
